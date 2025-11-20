#!/usr/bin/env python
"""
Test script to verify that the notifications API fix is working correctly.
This script tests the /api/notifications/ endpoint to ensure it no longer
throws the FieldError about 'user' field.
"""

import os
import sys
import django

# Setup Django FIRST
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

# Now import Django modules
from django.test import RequestFactory
from django.contrib.auth.models import User
from nano.models import Notification, UserProfile
from nano.views import get_notifications

def test_notifications_api():
    """Test the notifications API endpoint"""
    print("Testing notifications API fix...")
    
    # Create a test user if it doesn't exist
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Get or create user profile
    profile, profile_created = UserProfile.objects.get_or_create(
        user=user,
        defaults={'role': 'admin'}
    )
    
    # Create a test notification for this user
    notification = Notification.objects.create(
        title="Test Notification",
        message="This is a test notification",
        notification_type='system_alert',
        target_role='admin',
        target_user=user
    )
    
    # Create a request factory and mock request
    factory = RequestFactory()
    request = factory.get('/api/notifications/')
    request.user = user
    
    try:
        # Call the get_notifications view
        response = get_notifications(request)
        
        # Check if response is successful
        if response.status_code == 200:
            print("✅ SUCCESS: Notifications API is working correctly!")
            print(f"Response status: {response.status_code}")
            
            # Parse response content
            import json
            data = json.loads(response.content)
            notifications = data.get('notifications', [])
            print(f"Found {len(notifications)} notifications")
            
            for notif in notifications:
                print(f"  - {notif['message']}")
            
            return True
        else:
            print(f"❌ ERROR: Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False
    
    finally:
        # Clean up test data
        notification.delete()
        if created:
            user.userprofile.delete()
            user.delete()

if __name__ == '__main__':
    success = test_notifications_api()
    if success:
        print("\n🎉 The notifications API fix is working correctly!")
        print("The FieldError 'Cannot resolve keyword user into field' has been resolved.")
    else:
        print("\n💥 There are still issues with the notifications API.")
    
    sys.exit(0 if success else 1)
