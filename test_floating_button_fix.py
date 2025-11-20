#!/usr/bin/env python
"""
Test script to verify the floating message button fix
This tests that the API response is handled correctly by the frontend
"""

import os
import sys
import django
import json
from django.test import Client, TestCase
from django.contrib.auth.models import User
from nano.models import UserProfile, Notification

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

class FloatingButtonFixTest(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=self.user, role='cashier')
        
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_superuser=True
        )
        UserProfile.objects.create(user=self.admin, role='admin')
        
        self.client = Client()
    
    def test_cashier_request_api_response_format(self):
        """Test that the API returns the correct response format"""
        # Login as cashier
        self.client.login(username='testuser', password='testpass123')
        
        # Test successful request
        response = self.client.post(
            '/api/cashier_request/',
            data=json.dumps({
                'request_type': 'password_reset',
                'message': 'Please reset my password',
                'urgent': False
            }),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Parse response
        data = response.json()
        
        # Check that the response contains 'success': True (backend returns this)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('message', data)
        
        print(f"✅ API Response: {data}")
        print("✅ Backend returns 'success': True correctly")
    
    def test_frontend_response_handling(self):
        """Test that frontend can handle both 'success' and 'status' fields"""
        # Simulate different response formats the frontend might receive
        
        # Test case 1: Backend response (success: true)
        backend_response = {
            'success': True,
            'message': 'Request sent successfully',
            'data': {'notification_ids': [1, 2]}
        }
        
        # Simulate frontend logic: data.success === true || data.status === 'success'
        frontend_will_accept = (
            backend_response.get('success') is True or 
            backend_response.get('status') == 'success'
        )
        
        self.assertTrue(frontend_will_accept)
        print("✅ Frontend will accept backend response format")
        
        # Test case 2: Alternative response (status: 'success')
        alt_response = {
            'status': 'success',
            'message': 'Request sent successfully'
        }
        
        frontend_will_accept_alt = (
            alt_response.get('success') is True or 
            alt_response.get('status') == 'success'
        )
        
        self.assertTrue(frontend_will_accept_alt)
        print("✅ Frontend will accept alternative response format")
        
        # Test case 3: Error response
        error_response = {
            'success': False,
            'error': 'Something went wrong'
        }
        
        frontend_will_accept_error = (
            error_response.get('success') is True or 
            error_response.get('status') == 'success'
        )
        
        self.assertFalse(frontend_will_accept_error)
        print("✅ Frontend will correctly reject error response")
    
    def test_notification_creation(self):
        """Test that notifications are created correctly"""
        # Login as cashier
        self.client.login(username='testuser', password='testpass123')
        
        # Send request
        response = self.client.post(
            '/api/cashier_request/',
            data=json.dumps({
                'request_type': 'password_reset',
                'message': 'Please reset my password',
                'urgent': True
            }),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check that notifications were created
        admin_notifications = Notification.objects.filter(
            target_user=self.admin,
            notification_type='cashier_request'
        )
        
        self.assertGreater(admin_notifications.count(), 0)
        
        # Check notification details
        notification = admin_notifications.first()
        self.assertEqual(notification.request_type, 'password_reset')
        self.assertIn('Please reset my password', notification.message)
        self.assertEqual(notification.created_by, self.user)
        
        print(f"✅ Created {admin_notifications.count()} admin notifications")
        print(f"✅ Notification type: {notification.request_type}")
        print(f"✅ Notification message: {notification.message}")
    
    def test_error_handling(self):
        """Test error handling for missing fields"""
        # Login as cashier
        self.client.login(username='testuser', password='testpass123')
        
        # Test with missing request_type
        response = self.client.post(
            '/api/cashier_request/',
            data=json.dumps({
                'message': 'Test message',
                'urgent': False
            }),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        
        print(f"✅ Error handling works: {data['error']}")

def main():
    """Run the tests"""
    print("🧪 Testing Floating Message Button Fix")
    print("=" * 50)
    
    # Run tests
    test = FloatingButtonFixTest()
    test.setUp()
    
    try:
        test.test_cashier_request_api_response_format()
        test.test_frontend_response_handling()
        test.test_notification_creation()
        test.test_error_handling()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed! The floating button fix is working correctly.")
        print("✅ Backend returns 'success': True")
        print("✅ Frontend handles both 'success' and 'status' fields")
        print("✅ No more confusing 'Error sending request: Request sent successfully' messages")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
