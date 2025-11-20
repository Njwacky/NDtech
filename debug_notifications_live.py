#!/usr/bin/env python
"""
Debug script to check current notification state
Run this to see what notifications exist and which users should receive them
"""

import os
import sys
import django

# Add project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from django.contrib.auth.models import User
from nano.models import UserProfile, Notification

def debug_notifications():
    print("🔍 Debugging Current Notification State")
    print("=" * 50)
    
    # Check all users
    print("\n👥 All Users:")
    users = User.objects.all()
    for user in users:
        profile = getattr(user, 'userprofile', None)
        role = profile.role if profile else 'no-profile'
        is_admin = user.is_superuser or (profile and profile.role in ['admin', 'manager'])
        print(f"   - {user.username} (Role: {role}, Admin: {is_admin})")
    
    # Check all notifications
    print("\n📬 All Notifications:")
    notifications = Notification.objects.all().order_by('-created_at')
    for notif in notifications:
        print(f"   - ID: {notif.id}")
        print(f"     Title: {notif.title}")
        print(f"     Type: {notif.notification_type}")
        print(f"     Request Type: {notif.request_type}")
        print(f"     Target User: {notif.target_user.username if notif.target_user else 'None'}")
        print(f"     Created By: {notif.created_by.username if notif.created_by else 'None'}")
        print(f"     Created At: {notif.created_at}")
        print(f"     Is Read: {notif.is_read}")
        print()
    
    # Check password reset notifications specifically
    print("\n🔐 Password Reset Notifications:")
    password_notifications = Notification.objects.filter(
        notification_type='cashier_request',
        request_type='password_reset'
    ).order_by('-created_at')
    
    if password_notifications.exists():
        print(f"   Found {password_notifications.count()} password reset notifications:")
        for notif in password_notifications:
            print(f"   - ID: {notif.id}")
            print(f"     Target: {notif.target_user.username if notif.target_user else 'None'}")
            print(f"     Created By: {notif.created_by.username if notif.created_by else 'None'}")
            print(f"     Message: {notif.message}")
    else:
        print("   No password reset notifications found")
    
    # Check for any admin users
    print("\n👑 Admin/Manager Users:")
    admin_users = User.objects.filter(
        Q(is_superuser=True) |
        Q(userprofile__role__in=['admin', 'manager'])
    ).distinct()
    
    for admin in admin_users:
        profile = getattr(admin, 'userprofile', None)
        role = profile.role if profile else 'no-profile'
        print(f"   - {admin.username} (Role: {role}, Superuser: {admin.is_superuser})")
    
    print("\n" + "=" * 50)
    print("📋 Manual Testing Instructions:")
    print("1. Start Django server: python manage.py runserver")
    print("2. Go to: http://localhost:8000/forgot_password/")
    print("3. Enter username: testuser")
    print("4. Submit the form")
    print("5. Login as admin with: testadmin / adminpass123")
    print("6. Click the notification bell (top right)")
    print("7. Look for password reset notification with orange key icon")
    print("8. Click 'Edit User' button")

if __name__ == '__main__':
    debug_notifications()
