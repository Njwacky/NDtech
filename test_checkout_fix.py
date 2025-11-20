#!/usr/bin/env python3
"""
Test script to verify checkout functionality fix
"""

import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from nano.models import Product, PendingOrder, CompletedOrder, UserProfile
import json

def test_checkout_functionality():
    """Test that checkout properly moves orders from pending to completed"""
    
    print("🧪 Testing Checkout Functionality Fix")
    print("=" * 50)
    
    # Create test client
    client = Client()
    
    # Create test user if not exists
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(username='testuser', password='testpass123')
        UserProfile.objects.create(user=user, role='admin')
    
    # Log in the test user
    login_success = client.login(username='testuser', password='testpass123')
    print(f"   Login successful: {login_success}")
    
    # Create test product if not exists
    try:
        product = Product.objects.get(name='Test Product')
    except Product.DoesNotExist:
        product = Product.objects.create(
            name='Test Product',
            price=10.00,
            stock=100,
            category='basic_groceries'
        )
    
    # Create a test pending order
    order_items = [
        {
            'product': 'Test Product',
            'product_id': product.id,
            'quantity': 2,
            'price': 10.00
        }
    ]
    
    pending_order = PendingOrder.objects.create(
        user=user,
        customer_name='Test Customer',
        customer_phone='1234567890',
        items=order_items,
        total=20.00,
        status='pending'
    )
    
    print(f"✅ Created pending order #{pending_order.id}")
    print(f"   Customer: {pending_order.customer_name}")
    print(f"   Phone: {pending_order.customer_phone}")
    print(f"   Total: R{pending_order.total}")
    print(f"   Status: {pending_order.status}")
    
    # Test checkout endpoint
    print(f"\n🔄 Testing checkout for order #{pending_order.id}...")
    
    checkout_data = {
        'cash_received': '20.00',
        'payment_method': 'cash'
    }
    
    response = client.post(
        f'/pending_orders/{pending_order.id}/checkout/',
        data=json.dumps(checkout_data),
        content_type='application/json'
    )
    
    print(f"   Response status: {response.status_code}")
    
    if response.status_code == 200:
        response_data = response.json()
        print(f"   Response: {response_data}")
        
        if response_data.get('success'):
            print("✅ Checkout successful!")
            
            # Verify pending order status changed
            pending_order.refresh_from_db()
            print(f"   Pending order status: {pending_order.status}")
            
            # Verify completed order was created
            completed_orders = CompletedOrder.objects.all()
            if completed_orders.exists():
                completed_order = completed_orders.first()
                print(f"✅ Completed order created: #{completed_order.id}")
                print(f"   Customer: {completed_order.customer_name}")
                print(f"   Phone: {completed_order.customer_phone}")
                print(f"   Total: R{completed_order.total}")
                print(f"   Cash Received: R{completed_order.cash_received}")
                print(f"   Change Given: R{completed_order.change_given}")
                print(f"   Payment Method: {completed_order.payment_method}")
                print(f"   Processed By: {completed_order.processed_by.username}")
                
                # Verify customer info is preserved
                if (completed_order.customer_name == 'Test Customer' and 
                    completed_order.customer_phone == '1234567890'):
                    print("✅ Customer information correctly preserved!")
                else:
                    print("❌ Customer information not preserved correctly")
            else:
                print("❌ No completed order found")
        else:
            print(f"❌ Checkout failed: {response_data.get('error')}")
    else:
        print(f"❌ Checkout request failed with status {response.status_code}")
        print(f"   Response: {response.content.decode()}")
    
    # Test pending orders list
    print(f"\n📋 Testing pending orders list...")
    response = client.get('/pending_orders/')
    if response.status_code == 200:
        orders = PendingOrder.objects.filter(status='pending')
        print(f"   Pending orders count: {orders.count()}")
        if orders.count() == 0:
            print("✅ No pending orders found (order moved to completed)")
        else:
            print("❌ Pending orders still found")
    else:
        print(f"❌ Failed to get pending orders: {response.status_code}")
    
    # Test completed orders list
    print(f"\n📋 Testing completed orders list...")
    response = client.get('/completed_orders/')
    if response.status_code == 200:
        completed_orders = CompletedOrder.objects.all()
        print(f"   Completed orders count: {completed_orders.count()}")
        if completed_orders.count() > 0:
            print("✅ Completed orders found")
        else:
            print("❌ No completed orders found")
    else:
        print(f"❌ Failed to get completed orders: {response.status_code}")
    
    # Cleanup
    print(f"\n🧹 Cleaning up test data...")
    PendingOrder.objects.all().delete()
    CompletedOrder.objects.all().delete()
    print("✅ Test data cleaned up")
    
    print(f"\n🎉 Checkout functionality test completed!")
    print("=" * 50)

if __name__ == '__main__':
    test_checkout_functionality()
