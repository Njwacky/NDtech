"""
User Management Views for NDtech POS System
Handles user CRUD operations (Create, Read, Update, Delete).
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator
from ..models import UserProfile
from django.db.models import Q


@login_required
def create_user(request):
    """Create new user - Admin and Manager roles"""
    # Allow admins and managers to create users
    user_role = getattr(request.user.userprofile, 'role', 'cashier') if hasattr(request.user, 'userprofile') else 'cashier'
    
    if not (request.user.is_superuser or user_role in ['admin', 'manager']):
        return HttpResponseForbidden("You do not have permission to access this page.")

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        role = request.POST.get('role', '')
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

        if not password:
            errors['password'] = 'Password is required'
        elif len(password) < 6:
            errors['password'] = 'Password must be at least 6 characters'

        if password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match'

        if not role:
            errors['role'] = 'Role is required'
        
        # Validate role based on who is creating the user
        if user_role == 'manager':
            # Managers can only create cashiers and managers (not admins)
            if role not in ['manager', 'cashier']:
                errors['role'] = 'Managers can only create Manager or Cashier roles'
        elif user_role == 'admin':
            # Admins can create admin, manager, cashier (but not superuser)
            if role not in ['admin', 'manager', 'cashier']:
                errors['role'] = 'Admins can only create Admin, Manager, or Cashier roles'
        elif role not in ['superuser', 'admin', 'manager', 'cashier']:
            errors['role'] = 'Invalid role'

        # Check if trying to create superuser (only superusers can create superusers)
        if role == 'superuser' and not request.user.is_superuser:
            errors['role'] = 'Only superusers can create other superusers'

        if not company_name:
            errors['company_name'] = 'Company name is required'
        elif len(company_name) < 2:
            errors['company_name'] = 'Company name must be at least 2 characters'

        if errors:
            for field, error in errors.items():
                messages.error(request, error)
            return render(request, 'nano/create_user.html', {
                'user_role': user_role,
                'company_name': company_name
            })

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
        profile.company_name = company_name
        profile.save()

        messages.success(request, f'User "{username}" created successfully with role "{role}"!')
        return redirect('manage_users')

    return render(request, 'nano/create_user.html', {'user_role': user_role})


@login_required
def manage_users(request):
    """List users based on role - workspace separation"""
    # Allow admins and managers to view users
    user_role = getattr(request.user.userprofile, 'role', 'cashier') if hasattr(request.user, 'userprofile') else 'cashier'
    
    if not (request.user.is_superuser or user_role in ['admin', 'manager']):
        return HttpResponseForbidden("You do not have permission to access this page.")

    # Filter users based on who created them (workspace separation)
    if request.user.is_superuser:
        # Superusers can see all users
        users = User.objects.all().order_by('username')
    elif user_role == 'admin':
        # Admins can see all users
        users = User.objects.all().order_by('username')
    elif user_role == 'manager':
        # Managers can only see users they created + themselves
        users = User.objects.filter(
            Q(userprofile__created_by=request.user) | Q(id=request.user.id)
        ).distinct().order_by('username')
    else:
        users = User.objects.filter(id=request.user.id).order_by('username')

    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'nano/manage_users.html', {
        'users': page_obj,
        'user_role': user_role,
        'is_workspace_view': user_role == 'manager'
    })


@login_required
def edit_user(request, user_id):
    """Edit user details - Admin and Manager roles with workspace separation"""
    # Allow admins and managers to edit users
    user_role = getattr(request.user.userprofile, 'role', 'cashier') if hasattr(request.user, 'userprofile') else 'cashier'
    
    if not (request.user.is_superuser or user_role in ['admin', 'manager']):
        return HttpResponseForbidden("You do not have permission to access this page.")

    user = get_object_or_404(User, id=user_id)
    
    # Check workspace permissions
    if user_role == 'manager':
        # Managers can only edit users they created or themselves
        target_user_profile = getattr(user, 'userprofile', None)
        if not (user.id == request.user.id or 
                (target_user_profile and target_user_profile.created_by == request.user)):
            return HttpResponseForbidden("You can only edit users you created or yourself.")

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
    """Delete user - Admin and Manager roles with workspace separation"""
    # Allow admins and managers to delete users
    user_role = getattr(request.user.userprofile, 'role', 'cashier') if hasattr(request.user, 'userprofile') else 'cashier'
    
    if not (request.user.is_superuser or user_role in ['admin', 'manager']):
        return HttpResponseForbidden("You do not have permission to access this page.")

    user = get_object_or_404(User, id=user_id)
    
    # Check workspace permissions
    if user_role == 'manager':
        # Managers can only delete users they created
        target_user_profile = getattr(user, 'userprofile', None)
        if not (target_user_profile and target_user_profile.created_by == request.user):
            return HttpResponseForbidden("You can only delete users you created.")
    
    # Prevent users from deleting themselves
    if user.id == request.user.id:
        return HttpResponseForbidden("You cannot delete your own account.")

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
    """Bulk delete users - Admin and Manager roles with workspace separation"""
    # Allow admins and managers to delete users
    user_role = getattr(request.user.userprofile, 'role', 'cashier') if hasattr(request.user, 'userprofile') else 'cashier'
    
    if not (request.user.is_superuser or user_role in ['admin', 'manager']):
        return HttpResponseForbidden("You do not have permission to access this page.")

    if request.method == 'POST':
        user_ids = request.POST.getlist('user_ids')

        if not user_ids:
            messages.error(request, 'No users selected for deletion')
            return redirect('manage_users')

        # For managers, restrict to users they created
        if user_role == 'manager':
            # Get users they created
            deletable_users = User.objects.filter(
                id__in=user_ids,
                userprofile__created_by=request.user
            ).exclude(id=request.user.id)
        else:
            # Admins can delete any users except themselves
            deletable_users = User.objects.filter(id__in=user_ids).exclude(id=request.user.id)

        deleted_count = deletable_users.count()
        deletable_users.delete()
        
        if deleted_count > 0:
            messages.success(request, f'{deleted_count} user(s) deleted successfully!')
        else:
            messages.error(request, 'No users could be deleted. Check permissions.')

    return redirect('manage_users')
