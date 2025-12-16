#!/usr/bin/env python
import os
import django
import json

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from nano.models import PendingOrder, Product

def debug_checkout_issue():
    print("=== DEBUG CHECKOUT ISSUE ===")
    
    # Check for pending orders
    orders = PendingOrder.objects.all()
    print(f"Total pending orders: {orders.count()}")
    
    if orders.exists():
        order = orders.first()
        print(f"\nOrder ID: {order.id}")
        print(f"Customer: {order.customer_name}")
        print(f"Total: R{order.total}")
        print(f"Items: {order.items}")
        
        if order.items:
            print(f"\nItems type: {type(order.items)}")
            
            if isinstance(order.items, list):
                print(f"Number of items: {len(order.items)}")
                for i, item in enumerate(order.items):
                    print(f"Item {i}: {item}")
                    print(f"  Keys: {list(item.keys()) if isinstance(item, dict) else 'Not a dict'}")
                    
                    # Try to find product by different methods
                    if isinstance(item, dict):
                        product_id = item.get('product_id')
                        product_name = item.get('product')
                        
                        print(f"  Product ID: {product_id}")
                        print(f"  Product Name: {product_name}")
                        
                        if product_id:
                            try:
                                product = Product.objects.get(id=product_id)
                                print(f"  ✓ Found product by ID: {product.name}")
                            except Product.DoesNotExist:
                                print(f"  ✗ Product not found by ID: {product_id}")
                        
                        if product_name:
                            try:
                                product = Product.objects.get(name=product_name)
                                print(f"  ✓ Found product by name: {product.name}")
                            except Product.DoesNotExist:
                                print(f"  ✗ Product not found by name: {product_name}")
            else:
                print("Items is not a list")
    
    # Check all products
    print(f"\n=== ALL PRODUCTS ===")
    products = Product.objects.all()[:5]  # First 5 products
    for product in products:
        print(f"ID: {product.id}, Name: {product.name}")

if __name__ == '__main__':
    debug_checkout_issue()
