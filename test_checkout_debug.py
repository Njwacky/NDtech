#!/usr/bin/env python
"""
Debug script to test checkout functionality and identify product lookup issues
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from nano.models import Product, CompletedOrder

def debug_product_lookup():
    """Debug product lookup issues in completed orders"""
    print("=== DEBUGGING PRODUCT LOOKUP ISSUES ===\n")
    
    # Check all products
    products = Product.objects.all()
    print(f"Total products in database: {products.count()}")
    
    print("\nAll products:")
    for product in products:
        print(f"  ID: {product.id}, Name: '{product.name}', Price: {product.price}")
    
    # Check completed orders
    completed_orders = CompletedOrder.objects.all()
    print(f"\nTotal completed orders: {completed_orders.count()}")
    
    for order in completed_orders:
        print(f"\n--- Order #{order.id} ---")
        print(f"Customer: {order.customer_name}")
        print(f"Items: {order.items}")
        
        if order.items:
            for item in order.items:
                product_name = item.get('product', '')
                product_id = item.get('product_id')
                
                print(f"  Item: '{product_name}' (ID: {product_id})")
                
                # Try to find by name (like home.js does)
                if product_name:
                    try:
                        product_by_name = Product.objects.get(name=product_name)
                        print(f"    ✓ Found by name: ID {product_by_name.id}")
                    except Product.DoesNotExist:
                        print(f"    ✗ NOT FOUND by name: '{product_name}'")
                        
                        # Try case-insensitive search
                        similar_products = Product.objects.filter(name__iexact=product_name)
                        if similar_products.exists():
                            print(f"    → Similar products found: {[p.name for p in similar_products]}")
                        else:
                            # Try partial match
                            partial_matches = Product.objects.filter(name__icontains=product_name)
                            if partial_matches.exists():
                                print(f"    → Partial matches found: {[p.name for p in partial_matches]}")
                
                # Try to find by ID (like pending orders do)
                if product_id:
                    try:
                        product_by_id = Product.objects.get(id=product_id)
                        print(f"    ✓ Found by ID: {product_by_id.name}")
                    except Product.DoesNotExist:
                        print(f"    ✗ NOT FOUND by ID: {product_id}")

def test_checkout_scenarios():
    """Test different checkout scenarios"""
    print("\n=== TESTING CHECKOUT SCENARIOS ===\n")
    
    # Test home.js checkout scenario (using product names)
    print("1. Testing home.js checkout scenario (using product names):")
    
    # Get a sample product
    sample_product = Product.objects.first()
    if sample_product:
        print(f"   Sample product: '{sample_product.name}' (ID: {sample_product.id})")
        
        # Test exact match
        try:
            found = Product.objects.get(name=sample_product.name)
            print(f"   ✓ Exact name match works: {found.name}")
        except Product.DoesNotExist:
            print(f"   ✗ Exact name match failed for: '{sample_product.name}'")
        
        # Test with slight variations
        variations = [
            sample_product.name.lower(),
            sample_product.name.upper(),
            sample_product.name + " ",
            " " + sample_product.name,
            sample_product.name.replace(" ", ""),
        ]
        
        for variation in variations:
            try:
                found = Product.objects.get(name=variation)
                print(f"   ✓ Variation '{variation}' works: {found.name}")
            except Product.DoesNotExist:
                print(f"   ✗ Variation '{variation}' not found")

if __name__ == "__main__":
    debug_product_lookup()
    test_checkout_scenarios()
