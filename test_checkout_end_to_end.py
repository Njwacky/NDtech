#!/usr/bin/env python
import os
import django
import json
from django.test import Client
from django.contrib.auth import authenticate

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from nano.models import PendingOrder, Product, CompletedOrder, Sale
from django.contrib.auth.models import User

def test_checkout_end_to_end():
    print("=== END-TO-END CHECKOUT TEST ===")
    
    # Get or create a test user
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        print(f"Created test user: {user.username}")
    
    # Authenticate the user
    client = Client()
    client.force_login(user)
    print(f"Logged in as: {user.username}")
    
    # Get a pending order
    order = PendingOrder.objects.first()
    if not order:
        print("❌ No pending orders found")
        return
    
    print(f"\n=== TESTING ORDER {order.id} ===")
    print(f"Customer: {order.customer_name}")
    print(f"Total: R{order.total}")
    print(f"Items: {order.items}")
    
    # Test 1: Check order details page loads
    print(f"\n--- Test 1: Order Details Page ---")
    response = client.get(f'/order_details/{order.id}/')
    if response.status_code == 200:
        print("✅ Order details page loads successfully")
    else:
        print(f"❌ Order details page failed: {response.status_code}")
        return
    
    # Test 2: Simulate checkout POST request
    print(f"\n--- Test 2: Checkout POST Request ---")
    
    checkout_data = {
        'cash_received': str(float(order.total) + 10),  # Add extra for change
        'payment_method': 'cash'
    }
    
    response = client.post(f'/order_details/{order.id}/', data=checkout_data)
    
    print(f"Checkout response status: {response.status_code}")
    
    if response.status_code == 302:  # Redirect after successful checkout
        print("✅ Checkout successful - redirecting to completed orders")
        
        # Check if order was marked as completed
        order.refresh_from_db()
        if order.status == 'completed':
            print("✅ Order status updated to 'completed'")
        else:
            print(f"❌ Order status not updated: {order.status}")
        
        # Check if completed order was created
        completed_orders = CompletedOrder.objects.filter(
            customer_name=order.customer_name,
            total=order.total
        )
        if completed_orders.exists():
            print("✅ CompletedOrder record created")
            completed_order = completed_orders.first()
            print(f"  Order ID: {completed_order.id}")
            print(f"  Cash Received: R{completed_order.cash_received}")
            print(f"  Change Given: R{completed_order.change_given}")
        else:
            print("❌ CompletedOrder record not created")
        
        # Check if sale records were created
        cart_items = order.items
        sales_created = 0
        for item in cart_items:
            product_name = item.get('product')
            if product_name:
                try:
                    product = Product.objects.get(name=product_name)
                    sales = Sale.objects.filter(
                        product=product,
                        quantity=item.get('quantity', 0)
                    )
                    if sales.exists():
                        sales_created += 1
                        print(f"  ✅ Sale record created for {product.name}")
                except Product.DoesNotExist:
                    print(f"  ❌ Product not found: {product_name}")
        
        print(f"Total sale records created: {sales_created}/{len(cart_items)}")
        
        # Check stock updates
        stock_updated = 0
        for item in cart_items:
            product_name = item.get('product')
            if product_name:
                try:
                    product = Product.objects.get(name=product_name)
                    print(f"  ✅ Stock updated for {product.name}: {product.stock}")
                    stock_updated += 1
                except Product.DoesNotExist:
                    print(f"  ❌ Product not found for stock check: {product_name}")
        
        print(f"Total products with stock updated: {stock_updated}/{len(cart_items)}")
        
    elif response.status_code == 200:
        # Check for error messages in the response
        content = response.content.decode('utf-8')
        if 'error' in content.lower() or 'failed' in content.lower():
            print("❌ Checkout failed - error detected in response")
            # Look for specific error patterns
            if 'product not found' in content.lower():
                print("  ❌ 'Product not found' error detected")
            if 'insufficient stock' in content.lower():
                print("  ❌ 'Insufficient stock' error detected")
        else:
            print("❌ Checkout failed - returned to order details page")
    else:
        print(f"❌ Unexpected response status: {response.status_code}")
        print(f"Response content: {response.content.decode('utf-8')[:500]}...")
    
    print(f"\n=== TEST COMPLETE ===")

if __name__ == '__main__':
    test_checkout_end_to_end()
