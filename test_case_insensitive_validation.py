#!/usr/bin/env python3
"""
Test script to verify case-insensitive product name validation
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from nano.models import Product

def test_case_insensitive_validation():
    """Test case-insensitive product name validation"""
    
    print("Testing Case-Insensitive Product Name Validation")
    print("=" * 50)
    
    # Clear any existing test products
    Product.objects.filter(name__in=['Test', 'test', 'TEST', 'test2', 'Test2']).delete()
    
    # Test 1: Create first product "Test"
    print("\n1. Creating product 'Test'...")
    try:
        product1 = Product.objects.create(
            name='Test',
            price=10.00,
            category='basic_groceries',
            stock=50
        )
        print(f"   ✓ Successfully created: {product1.name}")
    except Exception as e:
        print(f"   ✗ Failed to create 'Test': {e}")
        return False
    
    # Test 2: Try to create "test" (should fail)
    print("\n2. Attempting to create 'test' (should fail)...")
    try:
        product2 = Product(name='test', price=15.00, category='basic_groceries', stock=30)
        product2.save()
        print(f"   ✗ ERROR: 'test' was created (should have been rejected)")
        return False
    except Exception as e:
        print(f"   ✓ Correctly rejected 'test': {e}")
    
    # Test 3: Try to create "TEST" (should fail)
    print("\n3. Attempting to create 'TEST' (should fail)...")
    try:
        product3 = Product(name='TEST', price=20.00, category='basic_groceries', stock=25)
        product3.save()
        print(f"   ✗ ERROR: 'TEST' was created (should have been rejected)")
        return False
    except Exception as e:
        print(f"   ✓ Correctly rejected 'TEST': {e}")
    
    # Test 4: Try to create "test2" (should succeed)
    print("\n4. Creating product 'test2' (should succeed)...")
    try:
        product4 = Product.objects.create(
            name='test2',
            price=12.00,
            category='basic_groceries',
            stock=40
        )
        print(f"   ✓ Successfully created: {product4.name}")
    except Exception as e:
        print(f"   ✗ Failed to create 'test2': {e}")
        return False
    
    # Test 5: Verify database state
    print("\n5. Verifying database state...")
    products = Product.objects.filter(name__in=['Test', 'test', 'TEST', 'test2'])
    print(f"   Found {products.count()} products:")
    for product in products:
        print(f"   - {product.name} (ID: {product.id})")
    
    # Test 6: Test case-insensitive query
    print("\n6. Testing case-insensitive query...")
    test_query = Product.objects.filter(name__iexact='test')
    print(f"   Query for name__iexact='test' found {test_query.count()} products:")
    for product in test_query:
        print(f"   - {product.name} (ID: {product.id})")
    
    print("\n" + "=" * 50)
    print("✓ All tests passed! Case-insensitive validation is working correctly.")
    
    # Clean up test data
    Product.objects.filter(name__in=['Test', 'test', 'TEST', 'test2']).delete()
    
    return True

if __name__ == '__main__':
    try:
        test_case_insensitive_validation()
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
