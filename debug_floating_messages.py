#!/usr/bin/env python
"""
Debug script to test floating message notifications
"""

import os
import sys
import django
from django.conf import settings
from django.db import models
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from django.contrib.auth.models import User
from nano.models import Notification, UserProfile

def test_notification_creation():
    """Test creating a notification like the floating button does"""
    print("=== Testing Notification Creation ===")
    
    # Get admin users
    admin_users = User.objects.filter(
        models.Q(is_superuser=True) |
        models.Q(userprofile__role__in=['admin', 'manager'])
    ).distinct()
    
    print(f"Found {admin_users.count()} admin/manager users:")
    for user in admin_users:
        print(f"  - {user.username} (superuser: {user.is_superuser}, role: {getattr(user.userprofile, 'role', 'None')})")
    
    if not admin_users.exists():
        print("No admin users found! This is the problem.")
        # Create a test admin user
        admin_user = User.objects.create_user(
            username='test_admin',
            email='admin@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=admin_user, role='admin')
        admin_user.is_superuser = True
        admin_user.save()
        print(f"Created test admin user: {admin_user.username}")
        admin_users = User.objects.filter(id=admin_user.id)
    
    # Get a test user (sender)
    test_user = User.objects.first()
    if not test_user:
        print("No users found in the system!")
        return
    
    print(f"\nUsing test user: {test_user.username}")
    
    # Create a notification like the floating button does
    notifications_created = []
    for admin_user in admin_users:
        notification = Notification.objects.create(
            title=f"Cashier Request: Test Message",
            message=f"Request from {test_user.username}: This is a test floating message",
            notification_type='cashier_request',
            target_role='admin',
            target_user=admin_user,
            created_by=test_user,
            request_type='other',
            request_data={
                'message': 'This is a test floating message',
                'urgent': False,
                'sender': test_user.username,
                'sender_id': test_user.id,
                'timestamp': django.utils.timezone.now().isoformat()
            }
        )
        notifications_created.append(notification.id)
        print(f"Created notification {notification.id} for {admin_user.username}")
    
    print(f"\nTotal notifications created: {len(notifications_created)}")
    return notifications_created

def test_notification_retrieval():
    """Test retrieving notifications for admin users"""
    print("\n=== Testing Notification Retrieval ===")
    
    # Get admin users
    admin_users = User.objects.filter(
        models.Q(is_superuser=True) |
        models.Q(userprofile__role__in=['admin', 'manager'])
    ).distinct()
    
    for admin_user in admin_users:
        print(f"\nChecking notifications for {admin_user.username}:")
        
        # Get unread notifications (like the get_notifications view does)
        notifications = Notification.objects.filter(
            target_user=admin_user,
            is_read=False
        ).order_by('-created_at')
        
        print(f"  Total unread notifications: {notifications.count()}")
        
        for notification in notifications:
            print(f"    - ID: {notification.id}")
            print(f"      Title: {notification.title}")
            print(f"      Message: {notification.message}")
            print(f"      Type: {notification.notification_type}")
            print(f"      Target Role: {notification.target_role}")
            print(f"      Target User: {notification.target_user.username if notification.target_user else 'None'}")
            print(f"      Created By: {notification.created_by.username if notification.created_by else 'None'}")
            print(f"      Created At: {notification.created_at}")
            print(f"      Request Type: {notification.request_type}")
            print()

def check_all_notifications():
    """Check all notifications in the system"""
    print("\n=== All Notifications in System ===")
    
    all_notifications = Notification.objects.all().order_by('-created_at')
    print(f"Total notifications: {all_notifications.count()}")
    
    for notification in all_notifications:
        print(f"\nNotification {notification.id}:")
        print(f"  Title: {notification.title}")
        print(f"  Message: {notification.message}")
        print(f"  Type: {notification.notification_type}")
        print(f"  Target Role: {notification.target_role}")
        print(f"  Target User: {notification.target_user.username if notification.target_user else 'None'}")
        print(f"  Created By: {notification.created_by.username if notification.created_by else 'None'}")
        print(f"  Is Read: {notification.is_read}")
        print(f"  Created At: {notification.created_at}")

def simulate_api_call():
    """Simulate the API call made by the floating button"""
    print("\n=== Simulating API Call ===")
    
    # This simulates what happens when the floating button sends a request
    from django.test import Client
    from django.contrib.auth import authenticate
    
    # Get or create a test user
    test_user, created = User.objects.get_or_create(
        username='test_cashier',
        defaults={
            'email': 'cashier@test.com',
            'password': 'testpass123'
        }
    )
    
    if created:
        UserProfile.objects.create(user=test_user, role='cashier')
        test_user.set_password('testpass123')
        test_user.save()
        print(f"Created test cashier user: {test_user.username}")
    
    # Create client and login
    client = Client()
    
    # Authenticate the user
    client.login(username='test_cashier', password='testpass123')
    
    # Simulate the POST request to create_cashier_request
    response = client.post('/api/cashier_request/', 
        data=json.dumps({
            'request_type': 'other',
            'message': 'Test floating message from API simulation',
            'urgent': False
        }),
        content_type='application/json'
    )
    
    print(f"API Response Status: {response.status_code}")
    print(f"API Response Content: {response.content.decode()}")
    
    return response

def main():
    """Main test function"""
    print("Debugging Floating Message Notifications")
    print("=" * 50)
    
    # Check current users
    print("Current Users:")
    users = User.objects.all()
    for user in users:
        role = getattr(user.userprofile, 'role', 'None') if hasattr(user, 'userprofile') else 'No Profile'
        print(f"  - {user.username} (superuser: {user.is_superuser}, role: {role})")
    
    # Test notification creation
    notification_ids = test_notification_creation()
    
    # Test notification retrieval
    test_notification_retrieval()
    
    # Check all notifications
    check_all_notifications()
    
    # Simulate API call
    simulate_api_call()
    
    print("\n" + "=" * 50)
    print("Debug complete!")

if __name__ == '__main__':
    main()
