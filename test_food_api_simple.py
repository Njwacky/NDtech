#!/usr/bin/env python
"""
Simple test for food ordering API without authentication
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from nano.food_ordering_integration import FoodOrderingIntegration

def test_api_directly():
    """Test the API function directly without HTTP"""
    print("🔌 Testing Food Ordering API Directly...")
    
    try:
        # Test barcode lookup
        test_barcode = "6001007123456"
        results = FoodOrderingIntegration.search_menu_items_by_barcode(test_barcode)
        
        print(f"✅ API function working for barcode: {test_barcode}")
        print(f"   Found {len(results)} food items:")
        
        for result in results:
            print(f"   - {result['name']} ({result['restaurant']}) - R{result['price']}")
            print(f"     Match type: {result['match_type']}")
        
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ Error testing API directly: {str(e)}")
        return False

def test_pos_product_creation():
    """Test POS product creation directly"""
    print("\n🛒 Testing POS Product Creation...")
    
    try:
        from food_ordering.models import MenuItem
        
        # Get a menu item
        menu_item = MenuItem.objects.filter(is_available=True).first()
        if not menu_item:
            print("❌ No menu items found")
            return False
        
        print(f"🍽️ Testing with menu item: {menu_item.name}")
        
        # Create POS product
        pos_product = FoodOrderingIntegration.create_pos_product_from_menu_item(
            menu_item, 
            barcode=f"TEST{menu_item.id:08d}"
        )
        
        if pos_product:
            print(f"✅ Created POS product: {pos_product.name}")
            print(f"   Price: R{pos_product.price}")
            print(f"   Category: {pos_product.category}")
            print(f"   Barcode: {pos_product.barcode}")
            return True
        else:
            print("❌ Failed to create POS product")
            return False
            
    except Exception as e:
        print(f"❌ Error testing POS product creation: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🍔 Food Ordering API Direct Test")
    print("=" * 40)
    
    tests = [
        ("API Function", test_api_directly),
        ("POS Product Creation", test_pos_product_creation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {str(e)}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All API tests passed! Core functionality is working.")
        print("\n💡 Note: The HTTP API requires authentication, which is why the web test failed.")
        print("   The core functionality is working correctly when accessed directly.")
    else:
        print("⚠️ Some tests failed.")
    
    return passed == total

if __name__ == '__main__':
    main()
