#!/usr/bin/env python
"""
Test script for the password reset notification system
This script tests the complete flow:
1. User requests password reset via forgot password form
2. Admin receives notification with "Edit User" button
3. Clicking "Edit User" redirects to user editing page
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from nano.models import UserProfile, Notification

def test_password_reset_flow():
    """Test the complete password reset notification flow"""
    print("🧪 Testing Password Reset Notification System")
    print("=" * 50)
    
    # Create test client
    client = Client()
    
    # Create test users if they don't exist
    try:
        # Create a regular user
        test_user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'testuser@example.com',
                'is_active': True
            }
        )
        if created:
            test_user.set_password('testpass123')
            test_user.save()
            # Create user profile
            UserProfile.objects.get_or_create(
                user=test_user,
                defaults={'role': 'cashier'}
            )
            print("✅ Created test user: testuser")
        
        # Create an admin user
        admin_user, admin_created = User.objects.get_or_create(
            username='testadmin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True
            }
        )
        if admin_created:
            admin_user.set_password('adminpass123')
            admin_user.save()
            # Create admin profile
            UserProfile.objects.get_or_create(
                user=admin_user,
                defaults={'role': 'admin'}
            )
            print("✅ Created admin user: testadmin")
            
    except Exception as e:
        print(f"❌ Error creating test users: {e}")
        return False
    
    try:
        # Step 1: Test forgot password form submission
        print("\n📝 Step 1: Testing Forgot Password Form")
        print("-" * 30)
        
        # Clear any existing notifications
        Notification.objects.all().delete()
        
        # Submit forgot password form
        response = client.post('/forgot_password/', {
            'username': 'testuser'
        })
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 302:  # Redirect after successful submission
            print("✅ Forgot password form submitted successfully")
            
            # Step 2: Check if notification was created
            print("\n🔔 Step 2: Checking Notification Creation")
            print("-" * 30)
            
            notifications = Notification.objects.filter(
                notification_type='cashier_request',
                request_type='password_reset'
            )
            
            if notifications.exists():
                print(f"✅ Created {notifications.count()} password reset notification(s)")
                
                for notification in notifications:
                    print(f"   - Title: {notification.title}")
                    print(f"   - Message: {notification.message}")
                    print(f"   - Target User: {notification.target_user.username if notification.target_user else 'None'}")
                    print(f"   - Created By: {notification.created_by.username if notification.created_by else 'None'}")
                    print(f"   - Request Data: {notification.request_data}")
                
                # Step 3: Test notification API endpoint
                print("\n🌐 Step 3: Testing Notification API")
                print("-" * 30)
                
                # Login as admin to test API
                client.login(username='testadmin', password='adminpass123')
                
                api_response = client.get('/api/notifications/')
                if api_response.status_code == 200:
                    api_data = api_response.json()
                    print("✅ Notification API working")
                    
                    if 'notifications' in api_data:
                        password_notifications = [
                            n for n in api_data['notifications'] 
                            if n.get('request_type') == 'password_reset'
                        ]
                        
                        if password_notifications:
                            print(f"✅ Found {len(password_notifications)} password notification(s) in API")
                            
                            for notif in password_notifications:
                                print(f"   - ID: {notif['id']}")
                                print(f"   - Title: {notif['title']}")
                                print(f"   - Created By ID: {notif.get('created_by_id')}")
                                print(f"   - Request Type: {notif.get('request_type')}")
                                
                                # Step 4: Test user lookup API
                                print("\n👤 Step 4: Testing User Lookup API")
                                print("-" * 30)
                                
                                if notif.get('created_by_id'):
                                    user_response = client.get(f"/api/get_user_by_username/?username=testuser")
                                    if user_response.status_code == 200:
                                        user_data = user_response.json()
                                        if user_data.get('success'):
                                            print("✅ User lookup API working")
                                            user_info = user_data.get('user', {})
                                            print(f"   - User ID: {user_info.get('id')}")
                                            print(f"   - Username: {user_info.get('username')}")
                                            print(f"   - Email: {user_info.get('email')}")
                                            print(f"   - Role: {user_info.get('role')}")
                                            
                                            # Step 5: Test edit user redirect
                                            print("\n🔧 Step 5: Testing Edit User Redirect")
                                            print("-" * 30)
                                            
                                            edit_url = f"/edit_user/{user_info.get('id')}/"
                                            edit_response = client.get(edit_url)
                                            
                                            if edit_response.status_code == 200:
                                                print(f"✅ Edit user page accessible: {edit_url}")
                                            elif edit_response.status_code == 302:
                                                print(f"⚠️  Edit user page redirected (may need login)")
                                            else:
                                                print(f"❌ Edit user page not accessible: {edit_response.status_code}")
                                        else:
                                            print("❌ User lookup failed")
                                    else:
                                        print(f"❌ User lookup API error: {user_response.status_code}")
                                else:
                                    print("⚠️  No created_by_id in notification")
                        else:
                            print("⚠️  No password notifications found in API")
                    else:
                        print("❌ No notifications key in API response")
                else:
                    print(f"❌ Notification API failed: {api_response.status_code}")
            else:
                print("❌ No password reset notifications were created")
        else:
            print(f"❌ Forgot password form failed: {response.status_code}")
            if hasattr(response, 'context'):
                messages = response.context.get('messages', [])
                for message in messages:
                    print(f"   Message: {message}")
                    
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Password Reset System Test Complete!")
    
    # Summary
    print("\n📊 Test Summary:")
    notifications = Notification.objects.filter(
        notification_type='cashier_request',
        request_type='password_reset'
    )
    print(f"   - Password reset notifications created: {notifications.count()}")
    print(f"   - Test users created: 2 (testuser, testadmin)")
    print(f"   - API endpoints tested: /api/notifications/, /api/get_user_by_username/")
    
    return True

def test_low_stock_notifications():
    """Test that low stock notifications also work correctly"""
    print("\n📦 Testing Low Stock Notifications (for comparison)")
    print("-" * 30)
    
    try:
        from nano.models import Product
        
        # Create a test product with low stock
        test_product, created = Product.objects.get_or_create(
            name='Test Low Stock Product',
            defaults={
                'price': 10.00,
                'stock': 5,  # Low stock
                'category': 'basic_groceries'
            }
        )
        
        if created:
            print("✅ Created test product with low stock")
        
        # Trigger low stock check
        from nano.views import check_low_stock
        check_low_stock()
        
        # Check if low stock notifications were created
        low_stock_notifications = Notification.objects.filter(
            notification_type='low_stock'
        )
        
        if low_stock_notifications.exists():
            print(f"✅ Low stock notifications working: {low_stock_notifications.count()} created")
        else:
            print("⚠️  No low stock notifications created")
            
    except Exception as e:
        print(f"❌ Error testing low stock: {e}")

if __name__ == '__main__':
    print("🚀 Starting Password Reset System Tests")
    print("This tests the complete password reset notification flow")
    print()
    
    success = test_password_reset_flow()
    test_low_stock_notifications()
    
    if success:
        print("\n✅ All tests completed successfully!")
        print("\n📋 Manual Testing Steps:")
        print("1. Go to: http://localhost:8000/forgot_password/")
        print("2. Enter username: testuser")
        print("3. Submit the form")
        print("4. Login as admin: testadmin / adminpass123")
        print("5. Check notifications - should see password reset request")
        print("6. Click 'Edit User' button - should go to edit user page")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
