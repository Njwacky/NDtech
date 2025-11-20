#!/usr/bin/env python
"""
Test script for UPC API integration
Tests the UPC lookup functionality and API integration
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from nano.upc_views import fetch_upc_data, map_category
from nano.models import Product
from django.test import TestCase, Client
from django.contrib.auth.models import User
from nano.models import UserProfile

def test_upc_api_direct():
    """Test direct UPC API call"""
    print("=" * 60)
    print("Testing UPC API Direct Call")
    print("=" * 60)
    
    # Test with a sample UPC code (this is a common test barcode)
    test_upc = "042100005264"  # This is a valid UPC for a test product
    
    try:
        print(f"Testing UPC: {test_upc}")
        result = fetch_upc_data(test_upc)
        
        if result:
            print("✅ SUCCESS: UPC data retrieved successfully!")
            print(f"Product Name: {result.get('name', 'N/A')}")
            print(f"Price: R{result.get('price', 'N/A')}")
            print(f"Category: {result.get('category', 'N/A')}")
            print(f"Brand: {result.get('brand', 'N/A')}")
            print(f"Description: {result.get('description', 'N/A')[:100]}...")
            print(f"Barcode: {result.get('barcode', 'N/A')}")
            return True
        else:
            print("❌ FAILED: No data returned for UPC")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_category_mapping():
    """Test category mapping function"""
    print("\n" + "=" * 60)
    print("Testing Category Mapping")
    print("=" * 60)
    
    test_cases = [
        ("Food & Beverages", "basic_groceries"),
        ("Snacks", "snacks_chips"),
        ("Soda", "cold_drinks"),
        ("Candy", "sweets_treats"),
        ("Milk", "dairy_eggs"),
        ("Bread", "bread_baked"),
        ("Canned Goods", "canned_goods"),
        ("Soap", "personal_care"),
        ("Cleaning", "household_items"),
        ("Stationery", "stationery"),
        ("Baby", "baby_products"),
        ("Frozen", "frozen_goods"),
        ("Airtime", "airtime_data"),
        ("Unknown Category", "basic_groceries"),
        ("", "basic_groceries"),
    ]
    
    all_passed = True
    
    for input_category, expected in test_cases:
        result = map_category(input_category)
        if result == expected:
            print(f"✅ '{input_category}' -> '{result}'")
        else:
            print(f"❌ '{input_category}' -> '{result}' (expected '{expected}')")
            all_passed = False
    
    return all_passed

def test_upc_views():
    """Test UPC views with Django test client"""
    print("\n" + "=" * 60)
    print("Testing UPC Views")
    print("=" * 60)
    
    # Create test user
    try:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        profile = UserProfile.objects.create(
            user=user,
            role='manager'
        )
        print("✅ Test user created")
    except Exception as e:
        print(f"⚠️  Test user might already exist: {e}")
        user = User.objects.filter(username='testuser').first()
        if not user:
            print("❌ Could not create or find test user")
            return False
    
    client = Client()
    client.login(username='testuser', password='testpass123')
    
    # Test UPC lookup page
    try:
        response = client.get('/upc/lookup/')
        if response.status_code == 200:
            print("✅ UPC lookup page accessible")
        else:
            print(f"❌ UPC lookup page returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing UPC lookup page: {e}")
        return False
    
    # Test UPC history page
    try:
        response = client.get('/upc/history/')
        if response.status_code == 200:
            print("✅ UPC history page accessible")
        else:
            print(f"❌ UPC history page returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing UPC history page: {e}")
        return False
    
    # Test API endpoint
    try:
        response = client.post('/api/upc/lookup/', 
                            data='{"upc_code": "042100005264"}',
                            content_type='application/json')
        if response.status_code == 200:
            print("✅ UPC API endpoint responds")
            data = response.json()
            if data.get('success'):
                print("✅ API returns success response")
            else:
                print(f"⚠️  API returns error: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ UPC API endpoint returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing UPC API endpoint: {e}")
        return False
    
    return True

def test_product_creation():
    """Test product creation with UPC data"""
    print("\n" + "=" * 60)
    print("Testing Product Creation with UPC Data")
    print("=" * 60)
    
    # Sample UPC data
    upc_data = {
        'barcode': '042100005264',
        'name': 'Test Product from UPC',
        'price': '10.99',
        'category': 'basic_groceries',
        'description': 'This is a test product created from UPC data',
        'brand': 'Test Brand',
        'size': '500ml'
    }
    
    try:
        # Check if product already exists
        existing_product = Product.objects.filter(barcode=upc_data['barcode']).first()
        if existing_product:
            print(f"⚠️  Product with barcode {upc_data['barcode']} already exists")
            print(f"   Existing product: {existing_product.name}")
            return True
        
        # Create product
        product = Product.objects.create(
            name=upc_data['name'],
            price=float(upc_data['price']),
            category=upc_data['category'],
            description=upc_data['description'],
            barcode=upc_data['barcode'],
            stock=10
        )
        
        print(f"✅ Product created successfully: {product.name}")
        print(f"   ID: {product.id}")
        print(f"   Barcode: {product.barcode}")
        print(f"   Price: R{product.price}")
        print(f"   Stock: {product.stock}")
        
        # Clean up - delete the test product
        product.delete()
        print("✅ Test product cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating product: {e}")
        return False

def test_permissions():
    """Test user permissions for UPC functionality"""
    print("\n" + "=" * 60)
    print("Testing User Permissions")
    print("=" * 60)
    
    client = Client()
    
    # Test without login
    response = client.get('/upc/lookup/')
    if response.status_code == 302:  # Redirect to login
        print("✅ Unauthenticated users redirected from UPC lookup")
    else:
        print(f"❌ Unauthenticated users should be redirected, got {response.status_code}")
        return False
    
    # Create users with different roles
    roles_to_test = ['admin', 'manager', 'cashier']
    
    for role in roles_to_test:
        try:
            # Create user with specific role
            username = f'test_{role}'
            user = User.objects.create_user(
                username=username,
                email=f'{username}@example.com',
                password='testpass123'
            )
            UserProfile.objects.create(user=user, role=role)
            
            # Test access
            client.login(username=username, password='testpass123')
            response = client.get('/upc/lookup/')
            
            if response.status_code == 200:
                print(f"✅ {role} can access UPC lookup")
            else:
                print(f"❌ {role} cannot access UPC lookup (status: {response.status_code})")
                return False
            
            # Clean up
            user.delete()
            
        except Exception as e:
            print(f"❌ Error testing {role} permissions: {e}")
            return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 Starting UPC Integration Tests")
    print("API Key: 0EF8A07BB103C1A35F6CAF9B64535DD5")
    print()
    
    tests = [
        ("Direct UPC API Call", test_upc_api_direct),
        ("Category Mapping", test_category_mapping),
        ("UPC Views", test_upc_views),
        ("Product Creation", test_product_creation),
        ("User Permissions", test_permissions),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! UPC integration is ready to use.")
        print("\nNext steps:")
        print("1. Start your Django server: python manage.py runserver")
        print("2. Navigate to: http://127.0.0.1:8000/upc/lookup/")
        print("3. Test with real UPC codes from your products")
        print("4. Check the UPC history page: http://127.0.0.1:8000/upc/history/")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
