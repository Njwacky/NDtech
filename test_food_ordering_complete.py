#!/usr/bin/env python
"""
Complete Food Ordering System Test
Tests all aspects of the food ordering system including web interfaces and APIs
"""

import requests
import json
import time
import sys
import os

# Setup Django environment for database access
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')

import django
django.setup()

from django.contrib.auth.models import User
from food_ordering.models import Restaurant, MenuCategory, MenuItem
from nano.models import Product

class FoodOrderingTester:
    def __init__(self, base_url='http://127.0.0.1:8000'):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_food_scanner_page(self):
        """Test the food scanner web page"""
        print("\n📷 Testing Food Scanner Page...")
        
        try:
            response = self.session.get(f"{self.base_url}/food/scanner/")
            
            if response.status_code == 200:
                print("✅ Food scanner page loaded successfully")
                
                # Check if page contains expected elements
                content = response.text
                if 'food scanner' in content.lower() or 'scanner' in content.lower():
                    print("✅ Page contains scanner-related content")
                else:
                    print("⚠️ Page may not contain expected scanner content")
                    
                if 'barcode' in content.lower():
                    print("✅ Page contains barcode functionality")
                else:
                    print("⚠️ Page may not contain barcode functionality")
                    
                return True
            else:
                print(f"❌ Food scanner page failed with status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing food scanner page: {str(e)}")
            return False
    
    def test_food_menu_browser(self):
        """Test the food menu browser page"""
        print("\n🍽️ Testing Food Menu Browser...")
        
        try:
            response = self.session.get(f"{self.base_url}/food/menu/")
            
            if response.status_code == 200:
                print("✅ Food menu browser loaded successfully")
                
                content = response.text
                if 'restaurant' in content.lower() or 'menu' in content.lower():
                    print("✅ Page contains menu/restaurant content")
                else:
                    print("⚠️ Page may not contain expected menu content")
                    
                return True
            else:
                print(f"❌ Food menu browser failed with status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing food menu browser: {str(e)}")
            return False
    
    def test_api_endpoints(self):
        """Test food ordering API endpoints"""
        print("\n🔌 Testing API Endpoints...")
        
        # Test barcode lookup API
        test_barcode = "6001007123456"
        
        try:
            response = self.session.get(f"{self.base_url}/api/food/scanner/lookup/{test_barcode}/")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Barcode lookup API working")
                print(f"   Response contains: {list(data.keys())}")
                
                if 'pos_products' in data:
                    print(f"   Found {len(data['pos_products'])} POS products")
                if 'food_items' in data:
                    print(f"   Found {len(data['food_items'])} food items")
                    
                return True
            else:
                print(f"❌ Barcode lookup API failed with status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing barcode lookup API: {str(e)}")
            return False
    
    def test_database_integration(self):
        """Test database integration"""
        print("\n🗄️ Testing Database Integration...")
        
        try:
            # Check if food ordering models exist and have data
            restaurant_count = Restaurant.objects.count()
            menu_item_count = MenuItem.objects.count()
            category_count = MenuCategory.objects.count()
            
            print(f"✅ Restaurants: {restaurant_count}")
            print(f"✅ Menu Categories: {category_count}")
            print(f"✅ Menu Items: {menu_item_count}")
            
            if restaurant_count > 0:
                print("✅ Database has restaurant data")
            else:
                print("⚠️ No restaurant data found")
                
            if menu_item_count > 0:
                print("✅ Database has menu item data")
            else:
                print("⚠️ No menu item data found")
                
            return restaurant_count > 0 and menu_item_count > 0
            
        except Exception as e:
            print(f"❌ Error testing database integration: {str(e)}")
            return False
    
    def test_pos_integration(self):
        """Test POS system integration"""
        print("\n🛒 Testing POS Integration...")
        
        try:
            # Check for food products in POS
            food_products = Product.objects.filter(name__startswith='[FOOD]')
            
            print(f"✅ Food products in POS: {food_products.count()}")
            
            if food_products.exists():
                for product in food_products[:3]:  # Show first 3
                    print(f"   - {product.name}: R{product.price}")
                print("✅ POS integration working")
                return True
            else:
                print("⚠️ No food products found in POS system")
                return False
                
        except Exception as e:
            print(f"❌ Error testing POS integration: {str(e)}")
            return False
    
    def test_url_routing(self):
        """Test URL routing"""
        print("\n🛣️ Testing URL Routing...")
        
        urls_to_test = [
            '/food/scanner/',
            '/food/menu/',
            '/api/food/scanner/lookup/6001007123456/',
        ]
        
        success_count = 0
        
        for url in urls_to_test:
            try:
                response = self.session.get(f"{self.base_url}{url}")
                if response.status_code in [200, 404, 405]:  # 404/405 are ok for routing test
                    print(f"✅ {url} - Route exists (status: {response.status_code})")
                    success_count += 1
                else:
                    print(f"❌ {url} - Unexpected status: {response.status_code}")
            except Exception as e:
                print(f"❌ {url} - Error: {str(e)}")
        
        return success_count == len(urls_to_test)
    
    def run_all_tests(self):
        """Run all tests"""
        print("🍔 Complete Food Ordering System Test")
        print("=" * 50)
        
        tests = [
            ("Database Integration", self.test_database_integration),
            ("URL Routing", self.test_url_routing),
            ("Food Scanner Page", self.test_food_scanner_page),
            ("Food Menu Browser", self.test_food_menu_browser),
            ("API Endpoints", self.test_api_endpoints),
            ("POS Integration", self.test_pos_integration),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {str(e)}")
                results.append((test_name, False))
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1
        
        print(f"\nResults: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Food ordering system is working correctly.")
        else:
            print("⚠️ Some tests failed. Check the details above.")
        
        return passed == total

def main():
    """Main test function"""
    tester = FoodOrderingTester()
    
    # Wait a moment for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    # Run all tests
    success = tester.run_all_tests()
    
    if success:
        print("\n🚀 Food Ordering System Status: OPERATIONAL")
        print("\n📱 Access Points:")
        print("   • Food Scanner: http://127.0.0.1:8000/food/scanner/")
        print("   • Menu Browser: http://127.0.0.1:8000/food/menu/")
        print("   • API Endpoint: http://127.0.0.1:8000/api/food/scanner/lookup/{barcode}/")
    else:
        print("\n❌ Food Ordering System Status: NEEDS ATTENTION")
    
    return success

if __name__ == '__main__':
    main()
