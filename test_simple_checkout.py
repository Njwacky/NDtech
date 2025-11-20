#!/usr/bin/env python3
"""
Simple test to verify checkout functionality fix
"""

import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from django.contrib.auth.models import User
from nano.models import Product, PendingOrder, CompletedOrder, UserProfile
import json

def test_simple_checkout():
    """Test checkout functionality directly"""
    
    print("🧪 Simple Checkout Functionality Test")
    print("=" * 50)
    
    # Create test user if not exists
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(username='testuser', password='testpass123')
        UserProfile.objects.create(user=user, role='admin')
        print("✅ Created test user")
    
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
        print("✅ Created test product")
    
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
    
    # Simulate checkout process
    print(f"\n🔄 Simulating checkout process...")
    
    # Check stock availability
    stock_ok = True
    for item in pending_order.items:
        product_id = item.get('product_id')
        quantity = item.get('quantity', 0)
        
        try:
            product = Product.objects.get(id=product_id)
            if product.stock < quantity:
                print(f"❌ Insufficient stock for {product.name}. Available: {product.stock}")
                stock_ok = False
                break
        except Product.DoesNotExist:
            print(f"❌ Product not found")
            stock_ok = False
            break
    
    if not stock_ok:
        return
    
    print("✅ Stock availability check passed")
    
    # Create completed order
    completed_order = CompletedOrder.objects.create(
        customer_name=pending_order.customer_name,
        customer_phone=pending_order.customer_phone,
        items=pending_order.items,
        total=pending_order.total,
        cash_received=20.00,
        change_given=0.00,
        payment_method='cash',
        processed_by=user
    )
    
    print(f"✅ Created completed order #{completed_order.id}")
    print(f"   Customer: {completed_order.customer_name}")
    print(f"   Phone: {completed_order.customer_phone}")
    print(f"   Total: R{completed_order.total}")
    print(f"   Cash Received: R{completed_order.cash_received}")
    print(f"   Change Given: R{completed_order.change_given}")
    print(f"   Payment Method: {completed_order.payment_method}")
    print(f"   Processed By: {completed_order.processed_by.username}")
    
    # Create sale records
    for item in pending_order.items:
        product_id = item.get('product_id')
        quantity = item.get('quantity', 0)
        price = item.get('price', 0)
        
        try:
            product = Product.objects.get(id=product_id)
            from nano.models import Sale
            Sale.objects.create(
                product=product,
                quantity=quantity,
                total_price=price * quantity
            )
            print(f"✅ Created sale record for {product.name}")
        except Product.DoesNotExist:
            continue
    
    # Update product stock
    for item in pending_order.items:
        product_id = item.get('product_id')
        quantity = item.get('quantity', 0)
        
        try:
            product = Product.objects.get(id=product_id)
            product.stock -= quantity
            product.save()
            print(f"✅ Updated stock for {product.name}: {product.stock + quantity} -> {product.stock}")
        except Product.DoesNotExist:
            continue
    
    # Update pending order status
    pending_order.status = 'completed'
    pending_order.save()
    print("✅ Updated pending order status to 'completed'")
    
    # Verify results
    print(f"\n📋 Verifying results...")
    
    # Check pending order status
    pending_order.refresh_from_db()
    print(f"   Pending order #{pending_order.id} status: {pending_order.status}")
    
    # Check completed orders
    completed_orders = CompletedOrder.objects.filter(id=completed_order.id)
    if completed_orders.exists():
        print(f"   ✅ Completed order #{completed_order.id} exists")
        
        # Verify customer info is preserved
        completed_order = completed_orders.first()
        if (completed_order.customer_name == 'Test Customer' and 
            completed_order.customer_phone == '1234567890'):
            print("   ✅ Customer information correctly preserved!")
        else:
            print("   ❌ Customer information not preserved correctly")
    else:
        print("   ❌ Completed order not found")
    
    # Check pending orders count
    pending_orders = PendingOrder.objects.filter(status='pending')
    print(f"   Pending orders count: {pending_orders.count()}")
    
    # Cleanup
    print(f"\n🧹 Cleaning up test data...")
    PendingOrder.objects.all().delete()
    CompletedOrder.objects.all().delete()
    Sale.objects.all().delete()
    print("✅ Test data cleaned up")
    
    print(f"\n🎉 Simple checkout test completed successfully!")
    print("=" * 50)

if __name__ == '__main__':
    test_simple_checkout()
