#!/usr/bin/env python
"""
Test script to verify the checkout functionality fix
"""
import os
import sys
import django
from django.test import Client, TestCase
from django.urls import reverse
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from django.contrib.auth.models import User
from nano.models import UserProfile, PendingOrder, CompletedOrder

def test_checkout_functionality():
    """Test the checkout functionality"""
    print("🧪 Testing checkout functionality...")
    
    # Create test client
    client = Client()
    
    # Create test user with cashier role
    try:
        user = User.objects.create_user(
            username='testcashier',
            email='test@example.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=user, role='cashier')
        print("✅ Created test cashier user")
    except:
        user = User.objects.get(username='testcashier')
        print("✅ Using existing test cashier user")
    
    # Login the user
    client.login(username='testcashier', password='testpass123')
    print("✅ User logged in")
    
    # Create a test pending order
    try:
        pending_order = PendingOrder.objects.create(
            customer_name='Test Customer',
            customer_phone='1234567890',
            items=[
                {'product': 'Test Product', 'quantity': 2, 'price': 10.00}
            ],
            total=20.00,
            status='pending'
        )
        print(f"✅ Created test pending order with ID: {pending_order.id}")
    except Exception as e:
        print(f"❌ Failed to create pending order: {e}")
        return False
    
    # Test the checkout endpoint
    try:
        url = reverse('checkout_order', kwargs={'order_id': pending_order.id})
        response = client.post(
            url,
            data=json.dumps({}),
            content_type='application/json'
        )
        
        print(f"📡 Response status: {response.status_code}")
        print(f"📡 Response content: {response.content.decode()}")
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('status') == 'success':
                print("✅ Checkout successful!")
                
                # Verify the order was moved to completed orders
                try:
                    completed_order = CompletedOrder.objects.get(
                        customer_name='Test Customer'
                    )
                    print(f"✅ Order found in completed orders with ID: {completed_order.id}")
                    
                    # Verify pending order status was updated
                    pending_order.refresh_from_db()
                    if pending_order.status == 'completed':
                        print("✅ Pending order status updated to 'completed'")
                        return True
                    else:
                        print(f"❌ Pending order status is: {pending_order.status}")
                        return False
                        
                except CompletedOrder.DoesNotExist:
                    print("❌ Order not found in completed orders")
                    return False
            else:
                print(f"❌ Checkout failed: {response_data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during checkout: {e}")
        return False

def test_urls():
    """Test that the URLs are properly configured"""
    print("\n🔗 Testing URL configuration...")
    
    try:
        from django.urls import reverse
        
        # Test the new checkout URL
        url = reverse('checkout_order', kwargs={'order_id': 1})
        expected_url = '/pending_orders/1/checkout/'
        
        if url == expected_url:
            print(f"✅ Checkout URL correctly configured: {url}")
            return True
        else:
            print(f"❌ URL mismatch. Expected: {expected_url}, Got: {url}")
            return False
            
    except Exception as e:
        print(f"❌ URL configuration error: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Testing FuturePOS Checkout Functionality Fix")
    print("=" * 60)
    
    # Test URL configuration
    urls_ok = test_urls()
    
    # Test checkout functionality
    checkout_ok = test_checkout_functionality()
    
    print("\n" + "=" * 60)
    if urls_ok and checkout_ok:
        print("🎉 All tests passed! Checkout functionality is working correctly.")
        print("✅ The 'failed to checkout the order' issue has been resolved.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    print("=" * 60)
