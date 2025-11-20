#!/usr/bin/env python3
"""
Test script to verify password notification redirect functionality.
This script tests the backend API endpoints that support the password notification redirect feature.
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
import json

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from nano.models import UserProfile, Notification

class PasswordNotificationRedirectTest(TestCase):
    """Test cases for password notification redirect functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.manager_user = User.objects.create_user(
            username='testmanager',
            email='manager@test.com',
            password='testpass123'
        )
        self.manager_profile, created = UserProfile.objects.get_or_create(
            user=self.manager_user,
            defaults={'role': 'manager'}
        )
        if not created:
            self.manager_profile.role = 'manager'
            self.manager_profile.save()
        
        self.cashier_user = User.objects.create_user(
            username='testcashier',
            email='cashier@test.com',
            password='testpass123'
        )
        self.cashier_profile, created = UserProfile.objects.get_or_create(
            user=self.cashier_user,
            defaults={'role': 'cashier'}
        )
        if not created:
            self.cashier_profile.role = 'cashier'
            self.cashier_profile.save()
        
        # Create test password notification
        self.password_notification = Notification.objects.create(
            title='Cashier Request: password_reset',
            message='From testcashier: Please reset my password',
            notification_type='cashier_request',
            target_role='manager',
            created_by=self.cashier_user,
            request_type='password_reset'
        )
        
        self.client = Client()
    
    def test_get_user_by_username_api(self):
        """Test the get_user_by_username API endpoint"""
        # Login as manager
        self.client.login(username='testmanager', password='testpass123')
        
        # Test successful user lookup
        response = self.client.get(
            reverse('get_user_by_username') + '?username=testcashier'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['user_id'], self.cashier_user.id)
        
        # Test non-existent user
        response = self.client.get(
            reverse('get_user_by_username') + '?username=nonexistent'
        )
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')
        
        # Test missing username parameter
        response = self.client.get(reverse('get_user_by_username'))
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')
    
    def test_notifications_api_includes_password_fields(self):
        """Test that notifications API includes password-related fields"""
        # Login as manager
        self.client.login(username='testmanager', password='testpass123')
        
        response = self.client.get(reverse('get_notifications'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Find the password notification
        password_notif = None
        for notif in data['notifications']:
            if notif['id'] == self.password_notification.id:
                password_notif = notif
                break
        
        self.assertIsNotNone(password_notif)
        self.assertEqual(password_notif['request_type'], 'password_reset')
        self.assertEqual(password_notif['created_by_id'], self.cashier_user.id)
    
    def test_password_notification_detection(self):
        """Test that password notifications are correctly identified"""
        # Create various notification types
        notifications_data = [
            {
                'type': 'cashier_request',
                'request_type': 'password_reset',
                'title': 'Password Reset Request',
                'message': 'From user1: Please reset my password'
            },
            {
                'type': 'cashier_request',
                'request_type': 'order_issue',
                'title': 'Order Issue',
                'message': 'From user2: Problem with order'
            },
            {
                'type': 'system_alert',
                'request_type': '',
                'title': 'Password Change Required',
                'message': 'System requires password change'
            },
            {
                'type': 'low_stock',
                'request_type': '',
                'title': 'Low Stock Alert',
                'message': 'Product is low on stock'
            }
        ]
        
        # Simulate the JavaScript detection logic
        def is_password_related_notification(notification):
            # Check if notification is related to password change
            if notification.get('type') == 'cashier_request' and notification.get('request_type') == 'password_reset':
                return True
            
            # Also check title and message for password-related keywords
            password_keywords = ['password', 'pwd', 'reset', 'change password']
            title = notification.get('title', '').lower()
            message = notification.get('message', '').lower()
            
            return any(keyword in title or keyword in message for keyword in password_keywords)
        
        # Test detection
        password_related_count = 0
        for notif in notifications_data:
            if is_password_related_notification(notif):
                password_related_count += 1
        
        # Should detect 2 password-related notifications
        self.assertEqual(password_related_count, 2)
    
    def test_edit_user_access(self):
        """Test that managers can access edit user page"""
        # Login as manager
        self.client.login(username='testmanager', password='testpass123')
        
        # Test access to edit user page
        response = self.client.get(
            reverse('edit_user', kwargs={'user_id': self.cashier_user.id})
        )
        self.assertEqual(response.status_code, 200)
        
        # Test that cashier cannot access edit user page
        self.client.login(username='testcashier', password='testpass123')
        response = self.client.get(
            reverse('edit_user', kwargs={'user_id': self.manager_user.id})
        )
        self.assertEqual(response.status_code, 403)

def run_tests():
    """Run all tests"""
    print("🧪 Running Password Notification Redirect Tests...")
    print("=" * 50)
    
    # Create test case instance
    test_case = PasswordNotificationRedirectTest()
    test_case.setUp()
    
    tests = [
        ("Get User by Username API", test_case.test_get_user_by_username_api),
        ("Notifications API Includes Password Fields", test_case.test_notifications_api_includes_password_fields),
        ("Password Notification Detection", test_case.test_password_notification_detection),
        ("Edit User Access", test_case.test_edit_user_access),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"📝 Running: {test_name}")
            test_func()
            print(f"✅ PASSED: {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {test_name}")
            print(f"   Error: {str(e)}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Password notification redirect functionality is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    return failed == 0

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
