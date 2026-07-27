"""
Core/Authentication Views
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse, HttpResponse
from django.db import models
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count, Sum, Min, Avg, Max
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import pandas as pd

import json
import re
import csv
import io
import logging
from decimal import Decimal, InvalidOperation
from .models import Product, Sale, UserProfile, PendingOrder, CompletedOrder, Notification, WarehousePrice, PriceComparison, FCMToken, DeviceConnection, ErrorLog, UserActivity, AirtimeProduct, AirtimeSale, AirtimeRequest
from .fcm_service import fcm_service, send_fcm_notification_to_user

# Set up logger
logger = logging.getLogger(__name__)

# Create your views here.


def check_low_stock():
    """Check for low stock products and create notifications"""
    low_stock_products = Product.objects.filter(stock__lt=10)
    for product in low_stock_products:
        # Create notification for admins/managers for low stock
        admin_users = User.objects.filter(
            Q(is_superuser=True) |
            Q(userprofile__role__in=['admin', 'manager'])
        ).distinct()

        for admin_user in admin_users:
            notification = Notification.objects.create(
                title=f"Low Stock Alert: {product.name}",
                message=f"Low stock alert: {product.name} has only {product.stock} units remaining",
                notification_type='low_stock',
                target_role='admin',  # Default to admin role
                target_user=admin_user,
                product=product
            , workspace=workspace)

            # Send FCM notification
            send_fcm_notification_to_user(notification.target_user, notification.title, notification.message)

@login_required


def home(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    # POS Dashboard
    products = Product.objects.all()

    # Check for low stock products when dashboard is loaded
    check_low_stock()

    return render(request, 'nano/home.html', {'products': products})



def register(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    # Check if any users already exist
    existing_users = User.objects.exists()

    if existing_users:
        # If users exist, show the sign_up page which will display "registration closed"
        return redirect('sign_up')
    else:
        # If no users exist, show the sign_up page for first user registration
        return redirect('sign_up')



def sign_up(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    # Check if any users already exist
    existing_users = User.objects.exists()

    if request.method == 'POST':
        # First check if users already exist - if so, don't allow registration
        if existing_users:
            messages.error(request, 'Registration is closed. An admin account already exists. New users must be created by the administrator.')
            return redirect('sign_in')

        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        errors = {}

        if not username:
            errors['username'] = 'Username is required'
        elif len(username) < 3:
            errors['username'] = 'Username must be at least 3 characters'
        elif User.objects.filter(username=username).exists():
            errors['username'] = 'Username already exists'

        if not email:
            errors['email'] = 'Email is required'
        elif '@' not in email or '.' not in email:
            errors['email'] = 'Invalid email format'
        elif User.objects.filter(email=email).exists():
            errors['email'] = 'Email already exists'

        if not password:
            errors['password'] = 'Password is required'
        elif len(password) < 6:
            errors['password'] = 'Password must be at least 6 characters'

        if password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match'

        if errors:
            for field, error in errors.items():
                messages.error(request, error)
            return render(request, 'nano/sign_up.html', {'existing_users': existing_users})

        from django.db import transaction

        try:
            with transaction.atomic():
                user = User.objects.create_user(username=username, email=email, password=password)

                # This is the first user, make them an admin
                user.is_staff = True  # Make staff to access admin
                user.save()

                # Create or update admin profile (not superuser)
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.role = 'admin'
                profile.created_by = None  # First user has no creator
                profile.save()
                messages.success(request, 'Admin account created successfully! You can now manage other users.')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return redirect('sign_in')

        return redirect('sign_in')

    return render(request, 'nano/sign_up.html', {'existing_users': existing_users})



def sign_in(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        errors = {}

        if not username:
            errors['username'] = 'Username is required'

        if not password:
            errors['password'] = 'Password is required'

        if errors:
            for field, error in errors.items():
                messages.error(request, error)
            return redirect('sign_in')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')
            return redirect('sign_in')

    return render(request, 'nano/sign_in.html')



def logout_view(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    
    logout(request)
    return redirect('register')



def forgot_password(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Handle forgot password requests"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()

        if not username:
            messages.error(request, 'Username is required')
            return render(request, 'nano/forgot_password.html')

        try:
            user = User.objects.get(username=username)

            # Create notification for admins/managers
            admin_users = User.objects.filter(
                Q(is_superuser=True) |
                Q(userprofile__role__in=['admin', 'manager'])
            ).distinct()

            if not admin_users.exists():
                messages.error(request, 'No admin users found to handle password reset requests')
                return render(request, 'nano/forgot_password.html')

            notifications_created = []
            for admin_user in admin_users:
                notification = Notification.objects.create(
                    title=f"Password Reset Request: {user.username}",
                    message=f"Password reset requested for user: {user.username} ({user.email}). Click to edit user and set new password.",
                    notification_type='cashier_request',
                    target_role='admin',
                    target_user=admin_user,
                    created_by=user,  # The user requesting the reset
                    request_type='password_reset',
                    request_data={
                        'username': user.username,
                        'email': user.email,
                        'user_id': user.id,
                        'request_time': timezone.now().isoformat()
                    }
                , workspace=workspace)
                notifications_created.append(notification.id)


                # Send FCM notification
                send_fcm_notification_to_user(admin_user, notification.title, notification.message)

            return redirect('sign_in')

        except User.DoesNotExist:
            # Don't reveal if user exists or not for security
            messages.success(request, 'If the username exists, a password reset request has been sent to the administrators.')
            return redirect('sign_in')

    return render(request, 'nano/forgot_password.html')

@login_required


def create_user(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    # Allow only superusers or users with admin role
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['superuser', 'admin'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        role = request.POST.get('role', '')

        errors = {}

        if not username:
            errors['username'] = 'Username is required'
        elif len(username) < 3:
            errors['username'] = 'Username must be at least 3 characters'
        elif User.objects.filter(username=username).exists():
            errors['username'] = 'Username already exists'

        if not email:
            errors['email'] = 'Email is required'
        elif '@' not in email or '.' not in email:
            errors['email'] = 'Invalid email format'
        elif User.objects.filter(email=email).exists():
            errors['email'] = 'Email already exists'

        if not password:
            errors['password'] = 'Password is required'
        elif len(password) < 6:
            errors['password'] = 'Password must be at least 6 characters'

        if password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match'

        if not role:
            errors['role'] = 'Role is required'
        elif role not in ['superuser', 'admin', 'manager', 'cashier']:
            errors['role'] = 'Invalid role'

        # Check if trying to create superuser (only superusers can create superusers)
        if role == 'superuser' and not request.user.is_superuser:
            errors['role'] = 'Only superusers can create other superusers'

        if errors:
            for field, error in errors.items():
                messages.error(request, error)
            return render(request, 'nano/create_user.html')

        user = User.objects.create_user(username=username, email=email, password=password)

        # Set superuser status if role is superuser
        if role == 'superuser':
            user.is_superuser = True
            user.is_staff = True
            user.save()

        # Create or update user profile (handle case where signal already created one)
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.role = role
        profile.created_by = request.user
        profile.save()

        messages.success(request, f'User "{username}" created successfully with role "{role}"!')
        return redirect('manage_users')

    return render(request, 'nano/create_user.html')

@login_required


def manage_users(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    # Allow only superusers or users with admin role
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['superuser', 'admin'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    users = User.objects.all().order_by('username')

    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'nano/manage_users.html', {'users': page_obj})

@login_required


def edit_user(request, user_id):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    # Allow only superusers or users with admin role
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin')):
        return HttpResponseForbidden("You do not have permission to access this page.")

    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', '')

        # Password fields (optional)
        current_password = request.POST.get('current_password', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        errors = {}

        if not username:
            errors['username'] = 'Username is required'
        elif User.objects.filter(username=username).exclude(id=user_id).exists():
            errors['username'] = 'Username already exists'

        if not email:
            errors['email'] = 'Email is required'
        elif User.objects.filter(email=email).exclude(id=user_id).exists():
            errors['email'] = 'Email already exists'

        # Password validation (only if user is trying to change password)
        password_change_attempt = new_password or confirm_password

        if password_change_attempt:
            # Admin users can change other users' passwords without current password
            # But users changing their own password need current password
            is_admin_changing_other_user = (
                request.user.is_superuser or
                (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin')
            ) and request.user.id != user.id

            if not is_admin_changing_other_user:
                if not current_password:
                    errors['current_password'] = 'Current password is required to change password'
                elif not user.check_password(current_password):
                    errors['current_password'] = 'Current password is incorrect'

            if not new_password:
                errors['new_password'] = 'New password is required'
            elif len(new_password) < 6:
                errors['new_password'] = 'Password must be at least 6 characters'

            if new_password != confirm_password:
                errors['confirm_password'] = 'Passwords do not match'

        if errors:
            for field, error in errors.items():
                messages.error(request, error)
        else:
            # Update user info
            user.username = username
            user.email = email

            # Update password if provided
            if password_change_attempt and new_password:
                user.set_password(new_password)
                messages.success(request, f'User "{username}" and password updated successfully!')
            else:
                messages.success(request, f'User "{username}" updated successfully!')

            user.save()

            # Update or create user profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.save()

            return redirect('manage_users')

    # Get user profile
    profile = getattr(user, 'userprofile', None)
    current_role = profile.role if profile else 'cashier'

    return render(request, 'nano/edit_user.html', {
        'user': user,
        'current_role': current_role
    })

@login_required


def delete_user(request, user_id):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    # Allow only superusers or users with admin role
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin')):
        return HttpResponseForbidden("You do not have permission to access this page.")

    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()

        if username != user.username:
            messages.error(request, 'Username does not match. User not deleted.')
        else:
            user.delete()
            messages.success(request, f'User "{username}" deleted successfully!')
            return redirect('manage_users')

    return render(request, 'nano/delete_user.html', {'user': user})

@login_required


def bulk_delete_users(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    # Allow only superusers or users with admin role
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin')):
        return HttpResponseForbidden("You do not have permission to access this page.")

    if request.method == 'POST':
        user_ids = request.POST.getlist('user_ids')

        if not user_ids:
            messages.error(request, 'No users selected for deletion.')
            return redirect('manage_users')

        deleted_count = 0
        for user_id in user_ids:
            try:
                user = User.objects.get(id=user_id)
                # Don't allow deletion of superusers or self
                if user.is_superuser or user.id == request.user.id:
                    continue
                user.delete()
                deleted_count += 1
            except User.DoesNotExist:
                continue

        if deleted_count > 0:
            messages.success(request, f'{deleted_count} users deleted successfully!')
        else:
            messages.warning(request, 'No users were deleted.')

        return redirect('manage_users')

    return redirect('manage_users')



@login_required


def check_role(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Check if user has specific role"""
    if request.method == 'GET':
        role = request.GET.get('role', '')

        if hasattr(request.user, 'userprofile'):
            user_role = request.user.userprofile.role
            has_role = user_role == role
        else:
            has_role = False

        return JsonResponse({'has_role': has_role, 'user_role': getattr(request.user.userprofile, 'role', None) if hasattr(request.user, 'userprofile') else None})

    return JsonResponse({'has_role': False})

@login_required


def get_user_by_username(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Get user by username"""
    if request.method == 'GET':
        username = request.GET.get('username', '').strip()

        if not username:
            return JsonResponse({'success': False, 'error': 'Username is required'})

        try:
            user = User.objects.get(username=username)
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': getattr(user.userprofile, 'role', None) if hasattr(user, 'userprofile') else None
            }
            return JsonResponse({'success': True, 'user': user_data})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
