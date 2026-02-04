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
from ..models import UserProfile, Notification
from ..fcm_service import send_fcm_notification_to_user


def register(request):
    """Initial registration redirect - checks if users exist"""
    # Check if any users already exist
    existing_users = User.objects.exists()

    if existing_users:
        # If users exist, show the sign_up page which will display "registration closed"
        return redirect('sign_up')
    else:
        # If no users exist, show the sign_up page for first user registration
        return redirect('sign_up')


def sign_up(request):
    """User registration form - only allows first user creation"""
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
    """User logout handler"""
    logout(request)
    return redirect('register')


def forgot_password(request):
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
                )
                notifications_created.append(notification.id)

                # Send FCM notification
                send_fcm_notification_to_user(admin_user, notification.title, notification.message)

            return redirect('sign_in')

        except User.DoesNotExist:
            # Don't reveal if user exists or not for security
            messages.success(request, 'If the username exists, a password reset request has been sent to the administrators.')
            return redirect('sign_in')

    return render(request, 'nano/forgot_password.html')
