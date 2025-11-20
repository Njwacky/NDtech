#!/usr/bin/env python
"""
Test script for OpenFoodFacts integration in futurePOS
This script tests OpenFoodFacts integration functionality
"""

import os
import sys
import django

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from nano.openfoodfacts_integration import (
    fetch_openfoodfacts_data,
    search_products_by_name,
    get_product_alternatives,
    map_openfoodfacts_category
)

def test_openfoodfacts_integration():
    """Test OpenFoodFacts integration functions"""
    
    print("🧪 Testing OpenFoodFacts Integration")
    print("=" * 50)
    
    # Test 1: Fetch a known product
    print("\n1. Testing fetch_openfoodfacts_data with a known barcode...")
    test_barcode = "7622210449283"  # Oreo cookies
    try:
        product_data = fetch_openfoodfacts_data(test_barcode)
        if product_data:
            print(f"✅ Successfully fetched product: {product_data['name']}")
            print(f"   Brand: {product_data['brand']}")
            print(f"   Category: {product_data['category']}")
            print(f"   Source: {product_data['source']}")
        else:
            print("❌ No product found for test barcode")
    except Exception as e:
        print(f"❌ Error fetching product: {str(e)}")
    
    # Test 2: Search products by name
    print("\n2. Testing search_products_by_name...")
    try:
        search_results = search_products_by_name("chocolate", limit=5)
        print(f"✅ Found {len(search_results)} products matching 'chocolate'")
        for i, product in enumerate(search_results[:3], 1):
            print(f"   {i}. {product['name']} ({product['brand']})")
    except Exception as e:
        print(f"❌ Error searching products: {str(e)}")
    
    # Test 3: Category mapping
    print("\n3. Testing category mapping...")
    test_categories = [
        {"categories": "Beverages, Sodas", "expected": "cold_drinks"},
        {"categories": "Snacks, Chips", "expected": "snacks_chips"},
        {"categories": "Dairy, Yogurts", "expected": "dairy_eggs"}
    ]
    
    for test in test_categories:
        mapped = map_openfoodfacts_category({"categories": test["categories"]})
        status = "✅" if mapped == test["expected"] else "❌"
        print(f"   {status} '{test['categories']}' -> '{mapped}' (expected: '{test['expected']}')")
    
    # Test 4: Product alternatives
    print("\n4. Testing get_product_alternatives...")
    try:
        alternatives = get_product_alternatives(test_barcode, limit=3)
        print(f"✅ Found {len(alternatives)} alternatives for test product")
        for i, alt in enumerate(alternatives[:2], 1):
            print(f"   {i}. {alt['name']} ({alt['brand']})")
    except Exception as e:
        print(f"❌ Error finding alternatives: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🏁 OpenFoodFacts Integration Test Complete")

def test_upc_integration():
    """Test integrated UPC lookup functionality"""
    
    print("\n🧪 Testing Integrated UPC Lookup")
    print("=" * 50)
    
    from nano.upc_views import fetch_upc_data
    
    # Test with a barcode that should be in OpenFoodFacts
    test_barcodes = [
        "7622210449283",  # Oreo cookies
        "5449000214911",  # Coca-Cola
        "4008400402228"   # Nutella
    ]
    
    for barcode in test_barcodes:
        print(f"\nTesting barcode: {barcode}")
        try:
            result = fetch_upc_data(barcode)
            if result:
                print(f"✅ Found: {result['name']}")
                print(f"   Source: {result['source']}")
                print(f"   Brand: {result.get('brand', 'N/A')}")
                print(f"   Category: {result['category']}")
            else:
                print("❌ No product found")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    # Check if OpenFoodFacts library is available
    try:
        import openfoodfacts
        print("✅ OpenFoodFacts library is available")
        
        # Run tests
        test_openfoodfacts_integration()
        test_upc_integration()
        
    except ImportError:
        print("❌ OpenFoodFacts library is not installed")
        print("Please install it with: pip install openfoodfacts")
    except Exception as e:
        print(f"❌ Error running tests: {str(e)}")
