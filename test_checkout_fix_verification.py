#!/usr/bin/env python
"""
Test script to verify the checkout fix works for various product name variations
"""

import os
import sys
import django
import json

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from nano.models import Product

def test_product_lookup_fallbacks():
    """Test the improved product lookup with fallbacks"""
    print("=== TESTING IMPROVED PRODUCT LOOKUP ===\n")
    
    # Get all products for testing
    products = Product.objects.all()
    test_cases = []
    
    for product in products:
        # Create test cases with variations
        test_cases.extend([
            f"  Testing '{product.name}' (exact match)",
            f"  Testing '{product.name.lower()}' (lowercase)",
            f"  Testing '{product.name.upper()}' (uppercase)",
            f"  Testing '{product.name.strip()}' (with extra spaces)",
            f"  Testing '{product.name.replace(' ', '')}' (no spaces)",
        ])
    
    print("Product lookup test cases:")
    for case in test_cases:
        print(case)
    
    print("\n=== TESTING LOOKUP LOGIC ===\n")
    
    # Test the lookup logic from the fixed checkout_order function
    for product in products[:3]:  # Test first 3 products
        print(f"Testing product: '{product.name}' (ID: {product.id})")
        
        # Test variations
        variations = [
            product.name,  # Exact match
            product.name.lower(),  # Lowercase
            product.name.upper(),  # Uppercase
            product.name + " ",  # Extra space
            " " + product.name,  # Leading space
        ]
        
        for variation in variations:
            print(f"  Looking up: '{variation}'")
            
            try:
                # Try exact match first (for performance)
                found_product = Product.objects.get(name=variation)
                print(f"    ✓ Exact match found: {found_product.name} (ID: {found_product.id})")
            except Product.DoesNotExist:
                try:
                    # Try case-insensitive match
                    found_product = Product.objects.get(name__iexact=variation.strip())
                    print(f"    ✓ Case-insensitive match found: {found_product.name} (ID: {found_product.id})")
                except Product.DoesNotExist:
                    # Try to find closest match
                    possible_products = Product.objects.filter(name__icontains=variation.strip())
                    if possible_products.exists():
                        found_product = possible_products.first()
                        print(f"    ✓ Partial match found: {found_product.name} (ID: {found_product.id})")
                    else:
                        print(f"    ✗ Not found: '{variation}'")
        
        print()

def simulate_checkout_request():
    """Simulate a checkout request with variations"""
    print("=== SIMULATING CHECKOUT REQUEST ===\n")
    
    # Get a sample product
    sample_product = Product.objects.first()
    if not sample_product:
        print("No products found in database")
        return
    
    print(f"Original product: '{sample_product.name}' (ID: {sample_product.id})")
    
    # Simulate cart items with variations
    cart_items = [
        {
            'product': sample_product.name,  # Exact match
            'price': float(sample_product.price),
            'quantity': 1
        },
        {
            'product': sample_product.name.lower(),  # Lowercase
            'price': float(sample_product.price),
            'quantity': 1
        },
        {
            'product': sample_product.name.upper(),  # Uppercase
            'price': float(sample_product.price),
            'quantity': 1
        }
    ]
    
    print(f"\nSimulated cart items:")
    for i, item in enumerate(cart_items, 1):
        print(f"  {i}. '{item['product']}' - R{item['price']} - Qty: {item['quantity']}")
    
    print("\nTesting lookup for each cart item:")
    
    for i, item in enumerate(cart_items, 1):
        product_name = item.get('product')
        print(f"\n{i}. Looking up: '{product_name}'")
        
        try:
            # Try exact match first (for performance)
            product = Product.objects.get(name=product_name)
            print(f"   ✓ Found by exact match: {product.name} (ID: {product.id})")
            print(f"   ✓ Stock available: {product.stock}")
        except Product.DoesNotExist:
            try:
                # Try case-insensitive match
                product = Product.objects.get(name__iexact=product_name.strip())
                print(f"   ✓ Found by case-insensitive match: {product.name} (ID: {product.id})")
                print(f"   ✓ Stock available: {product.stock}")
            except Product.DoesNotExist:
                # Try to find closest match
                possible_products = Product.objects.filter(name__icontains=product_name.strip())
                if possible_products.exists():
                    product = possible_products.first()
                    print(f"   ✓ Found by partial match: {product.name} (ID: {product.id})")
                    print(f"   ✓ Stock available: {product.stock}")
                else:
                    print(f"   ✗ Product not found: {product_name}")

if __name__ == "__main__":
    test_product_lookup_fallbacks()
    simulate_checkout_request()
