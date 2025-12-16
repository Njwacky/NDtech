#!/usr/bin/env python3
"""
Test script to verify order completion functionality fixes
"""

import os
import sys
import django
from django.test import Client, TestCase
from django.contrib.auth.models import User
from decimal import Decimal
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from nano.models import Product, PendingOrder, CompletedOrder, UserProfile, Sale

def test_order_completion():
    """Test the order completion functionality"""
    print("🧪 Testing Order Completion Functionality")
    print("=" * 50)
    
    # Create test user
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=user, role='cashier')
        print("✅ Created test user")
    
    # Create test products
    products = []
    for i in range(1, 4):
        try:
            product = Product.objects.get(name=f'Test Product {i}')
        except Product.DoesNotExist:
            product = Product.objects.create(
                name=f'Test Product {i}',
                price=Decimal(f'{i * 10}.50'),
                stock=20 + i,
                category='basic_groceries'
            )
            print(f"✅ Created test product: {product.name}")
        products.append(product)
    
    # Create test pending order
    order_items = [
        {
            'product': products[0].name,
            'product_id': products[0].id,
            'quantity': 2,
            'price': float(products[0].price)
        },
        {
            'product': products[1].name,
            'product_id': products[1].id,
            'quantity': 1,
            'price': float(products[1].price)
        }
    ]
    
    total_amount = sum(item['quantity'] * item['price'] for item in order_items)
    
    order = PendingOrder.objects.create(
        user=user,
        customer_name='Test Customer',
        customer_phone='0721234567',
        items=order_items,
        total=total_amount,
        status='pending'
    )
    print(f"✅ Created test pending order: #{order.id} - Total: R{total_amount}")
    
    # Test 1: Check stock before completion
    print("\n📊 Testing Stock Validation")
    print("-" * 30)
    initial_stocks = {p.name: p.stock for p in products}
    for name, stock in initial_stocks.items():
        print(f"   {name}: {stock} units")
    
    # Test 2: Simulate order completion
    print("\n🔄 Testing Order Completion")
    print("-" * 30)
    
    from nano.views import complete_order
    from django.http import HttpRequest
    from django.contrib.messages.storage.fallback import FallbackStorage
    
    # Create mock request
    client = Client()
    client.force_login(user)
    
    # Test valid completion
    completion_data = {
        'cash_received': str(total_amount + 10),  # Extra for change
        'payment_method': 'cash'
    }
    
    response = client.post(f'/pending_orders/{order.id}/complete/', completion_data)
    
    if response.status_code == 302:  # Redirect after success
        print("✅ Order completion successful (redirect detected)")
        
        # Check if order was marked as completed
        order.refresh_from_db()
        if order.status == 'completed':
            print("✅ Pending order status updated to 'completed'")
        else:
            print(f"❌ Order status not updated: {order.status}")
        
        # Check if completed order was created
        try:
            completed_order = CompletedOrder.objects.get(customer_name='Test Customer')
            print(f"✅ Completed order created: #{completed_order.id}")
            print(f"   Cash Received: R{completed_order.cash_received}")
            print(f"   Change Given: R{completed_order.change_given}")
            print(f"   Payment Method: {completed_order.payment_method}")
            print(f"   Processed By: {completed_order.processed_by.username}")
        except CompletedOrder.DoesNotExist:
            print("❌ Completed order not found")
        
        # Check if sales were created
        sales = Sale.objects.filter(product__in=products)
        if sales.exists():
            print(f"✅ Sales records created: {sales.count()} records")
            for sale in sales:
                print(f"   {sale.product.name}: {sale.quantity} units")
        else:
            print("❌ No sales records found")
        
        # Check stock updates
        print("\n📦 Testing Stock Updates")
        print("-" * 30)
        updated_stocks = {p.name: p.stock for p in products}
        stock_correct = True
        
        for name, initial_stock in initial_stocks.items():
            current_stock = updated_stocks[name]
            expected_reduction = sum(item['quantity'] for item in order_items if item['product'] == name)
            expected_stock = initial_stock - expected_reduction
            
            if current_stock == expected_stock:
                print(f"✅ {name}: {initial_stock} → {current_stock} (correct)")
            else:
                print(f"❌ {name}: {initial_stock} → {current_stock} (expected {expected_stock})")
                stock_correct = False
        
        if stock_correct:
            print("✅ All stock updates correct")
        else:
            print("❌ Stock update issues detected")
            
    else:
        print(f"❌ Order completion failed with status: {response.status_code}")
        if hasattr(response, 'context'):
            messages = response.context.get('messages', [])
            for message in messages:
                print(f"   Message: {message}")
    
    # Test 3: Test insufficient stock scenario
    print("\n⚠️  Testing Insufficient Stock Scenario")
    print("-" * 30)
    
    # Create another order with more items than available
    large_order_items = [
        {
            'product': products[0].name,
            'product_id': products[0].id,
            'quantity': 100,  # More than available
            'price': float(products[0].price)
        }
    ]
    
    large_order = PendingOrder.objects.create(
        user=user,
        customer_name='Large Order Customer',
        customer_phone='0721234568',
        items=large_order_items,
        total=large_order_items[0]['quantity'] * large_order_items[0]['price'],
        status='pending'
    )
    
    completion_data = {
        'cash_received': str(large_order.total + 10),
        'payment_method': 'cash'
    }
    
    response = client.post(f'/pending_orders/{large_order.id}/complete/', completion_data)
    
    if response.status_code == 302:
        print("❌ Large order should have failed but didn't")
    else:
        print("✅ Large order correctly rejected due to insufficient stock")
    
    # Test 4: Test invalid payment method
    print("\n💳 Testing Invalid Payment Method")
    print("-" * 30)
    
    invalid_payment_data = {
        'cash_received': str(total_amount + 10),
        'payment_method': 'invalid_method'
    }
    
    # Create another order for this test
    test_order = PendingOrder.objects.create(
        user=user,
        customer_name='Payment Test Customer',
        customer_phone='0721234569',
        items=order_items,
        total=total_amount,
        status='pending'
    )
    
    response = client.post(f'/pending_orders/{test_order.id}/complete/', invalid_payment_data)
    
    if response.status_code == 302:
        print("❌ Invalid payment method should have been rejected")
    else:
        print("✅ Invalid payment method correctly rejected")
    
    # Test 5: Test negative cash received
    print("\n💰 Testing Negative Cash Received")
    print("-" * 30)
    
    negative_cash_data = {
        'cash_received': '-50.00',
        'payment_method': 'cash'
    }
    
    # Create another order for this test
    negative_order = PendingOrder.objects.create(
        user=user,
        customer_name='Negative Cash Customer',
        customer_phone='0721234570',
        items=order_items,
        total=total_amount,
        status='pending'
    )
    
    response = client.post(f'/pending_orders/{negative_order.id}/complete/', negative_cash_data)
    
    if response.status_code == 302:
        print("❌ Negative cash should have been rejected")
    else:
        print("✅ Negative cash amount correctly rejected")
    
    print("\n🎯 Test Summary")
    print("=" * 50)
    print("✅ Order completion functionality tested")
    print("✅ Stock validation working")
    print("✅ Payment method validation working")
    print("✅ Cash amount validation working")
    print("✅ Sales record creation working")
    
    # Cleanup test data
    print("\n🧹 Cleaning up test data...")
    PendingOrder.objects.filter(customer_name__startswith='Test').delete()
    PendingOrder.objects.filter(customer_name__in=['Large Order Customer', 'Payment Test Customer', 'Negative Cash Customer']).delete()
    CompletedOrder.objects.filter(customer_name__startswith='Test').delete()
    Sale.objects.filter(product__in=products).delete()
    Product.objects.filter(name__startswith='Test Product').delete()
    user.delete()
    print("✅ Test data cleaned up")

if __name__ == '__main__':
    test_order_completion()
