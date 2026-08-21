"""
Authentication Views for NDtech POS System
Handles user login, logout, registration, and password reset requests.
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from ..models import UserProfile, Notification
from ..fcm_service import send_fcm_notification_to_user
from confige.security import rate_limit


def register(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Initial registration redirect - always allows registration"""
    return redirect('sign_up')


def sign_up(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """User registration form - allows multiple users to create their own workspaces"""
    # Check if any users already exist to determine if this is first user
    existing_users = User.objects.exists()
    is_first_user = not existing_users

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        company_name = request.POST.get('company_name', '').strip()

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

        if not company_name:
            errors['company_name'] = 'Company name is required'
        elif len(company_name) < 2:
            errors['company_name'] = 'Company name must be at least 2 characters'

        if not password:
            errors['password'] = 'Password is required'
        elif len(password) < 6:
            errors['password'] = 'Password must be at least 6 characters'

        if password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match'

        if errors:
            for field, error in errors.items():
                messages.error(request, error)
            return render(request, 'nano/sign_up.html', {'is_first_user': is_first_user})

        try:
            with transaction.atomic():
                user = User.objects.create_user(username=username, email=email, password=password)

                # Determine role based on whether this is the first user
                if is_first_user:
                    # First user gets admin privileges
                    user.is_staff = True
                    user.is_superuser = True
                    role = 'admin'
                    created_by = None
                    success_message = 'Admin account created successfully! You can now manage other users.'
                else:
                    # New users get manager role so they can create their own team
                    user.is_staff = False
                    user.is_superuser = False
                    role = 'manager'
                    created_by = None  # Self-registered
                    success_message = 'Account created successfully! You can now create and manage your own team.'

                user.save()

                # Create user profile
                profile = UserProfile.objects.create(
                    user=user,
                    role=role,
                    created_by=created_by,
                    company_name=company_name
                )
                profile.save()

                messages.success(request, success_message)
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return redirect('sign_up')

        return redirect('sign_in')

    return render(request, 'nano/sign_up.html', {'is_first_user': is_first_user})


@rate_limit('login', limit=10, window=300)
def sign_in(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """User login view"""
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
    """User logout handler"""
    logout(request)
    return redirect('register')


def forgot_password(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Handle forgot password requests - creates notification for admins"""
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
def verify_admin_password(request):
    """Verify admin password for secret NDtechTrack access"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    try:
        data = json.loads(request.body)
        password = data.get('password', '')

        if not password:
            return JsonResponse({'success': False, 'error': 'Password required'})

        # Verify the password against the current user
        user = authenticate(request, username=request.user.username, password=password)

        if user is not None:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Incorrect password'})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid request'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'Server error'})