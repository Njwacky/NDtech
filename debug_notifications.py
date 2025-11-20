#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from django.contrib.auth.models import User
from nano.models import Notification, UserProfile

def check_notification_system():
    print("🔍 Debugging Notification System")
    print("=" * 50)
    
    # Check users and their roles
    print("\n📋 Users and Roles:")
    users = User.objects.all()
    for user in users:
        try:
            profile = user.userprofile
            print(f"  - {user.username} ({user.email}) - Role: {profile.role}")
        except UserProfile.DoesNotExist:
            print(f"  - {user.username} ({user.email}) - No profile found")
    
    # Check all notifications
    print("\n📢 All Notifications in Database:")
    notifications = Notification.objects.all().order_by('-created_at')
    if notifications:
        for notification in notifications:
            print(f"  ID: {notification.id}")
            print(f"    Title: {notification.title}")
            print(f"    Message: {notification.message}")
            print(f"    Type: {notification.notification_type}")
            print(f"    Target User: {notification.target_user.username if notification.target_user else 'None'}")
            print(f"    Target Role: {notification.target_role}")
            print(f"    Is Read: {notification.is_read}")
            print(f"    Created: {notification.created_at}")
            print(f"    ---")
    else:
        print("  ❌ No notifications found in database")
    
    # Check unread notifications for each admin/manager user
    print("\n🔔 Unread Notifications by Admin/Manager Users:")
    admin_users = User.objects.filter(
        models.Q(is_superuser=True) |
        models.Q(userprofile__role__in=['admin', 'manager'])
    ).distinct()
    
    for user in admin_users:
        unread_notifications = Notification.objects.filter(
            target_user=user,
            is_read=False
        )
        print(f"  {user.username}: {unread_notifications.count()} unread notifications")
        for notif in unread_notifications:
            print(f"    - {notif.title}: {notif.message[:50]}...")
    
    # Test notification creation
    print("\n🧪 Testing Notification Creation:")
    try:
        # Get first admin user
        admin_user = admin_users.first()
        if admin_user:
            test_notification = Notification.objects.create(
                title="Test Notification",
                message="This is a test notification to verify the system is working.",
                notification_type='system_alert',
                target_role='admin',
                target_user=admin_user
            )
            print(f"  ✅ Test notification created with ID: {test_notification.id}")
            
            # Test retrieval
            retrieved_notifications = Notification.objects.filter(
                target_user=admin_user,
                is_read=False
            )
            print(f"  ✅ Retrieved {retrieved_notifications.count()} unread notifications for {admin_user.username}")
        else:
            print("  ❌ No admin user found to test with")
            
    except Exception as e:
        print(f"  ❌ Error creating test notification: {e}")
    
    print("\n🌐 API Endpoint Test:")
    print("  To test the API endpoint manually:")
    print("  1. Login as an admin user")
    print("  2. Visit: /api/notifications/")
    print("  3. Check browser console for any errors")
    print("  4. Check Network tab for API response")

if __name__ == '__main__':
    from django.db import models
    check_notification_system()
