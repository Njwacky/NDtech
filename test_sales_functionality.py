#!/usr/bin/env python3
"""
Test script to check sales functionality in the futurePOS system
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from nano.models import Product, UserProfile, Sale

class SalesFunctionalityTest(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create user profile with admin role
        self.profile = UserProfile.objects.create(
            user=self.user,
            role='admin',
            created_by=self.user
        )
        
        # Create test products
        self.product1 = Product.objects.create(
            name='Test Product 1',
            price=Decimal('100.00'),
            category='basic_groceries',
            stock=50
        )
        
        self.product2 = Product.objects.create(
            name='Test Product 2',
            price=Decimal('50.00'),
            category='snacks_chips',
            stock=30
        )
        
        # Create product with sale
        self.product3 = Product.objects.create(
            name='Test Product 3',
            price=Decimal('200.00'),
            category='cold_drinks',
            stock=20,
            is_on_sale=True,
            sale_price=Decimal('150.00'),
            sale_start_date=timezone.now() - timezone.timedelta(days=1),
            sale_end_date=timezone.now() + timezone.timedelta(days=7)
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_manage_sales_page_access(self):
        """Test if manage sales page is accessible"""
        print("\n=== Testing Manage Sales Page Access ===")
        response = self.client.get('/manage_sales/')
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✅ Manage sales page accessible")
        else:
            print("❌ Manage sales page not accessible")
            
        return response.status_code == 200
    
    def test_add_sale_functionality(self):
        """Test adding a sale to a product"""
        print("\n=== Testing Add Sale Functionality ===")
        
        # Test adding sale to product1
        sale_data = {
            'product_id': self.product1.id,
            'action': 'add_sale',
            'sale_price': '75.00',
            'sale_start_date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'sale_end_date': (timezone.now() + timezone.timedelta(days=5)).strftime('%Y-%m-%dT%H:%M')
        }
        
        response = self.client.post('/manage_sales/', data=sale_data)
        
        print(f"Response Status: {response.status_code}")
        print(f"Redirect: {response.status_code == 302}")
        
        # Check if product was updated
        updated_product = Product.objects.get(id=self.product1.id)
        print(f"Product is_on_sale: {updated_product.is_on_sale}")
        print(f"Product sale_price: {updated_product.sale_price}")
        
        if (updated_product.is_on_sale and 
            updated_product.sale_price == Decimal('75.00')):
            print("✅ Sale added successfully")
            return True
        else:
            print("❌ Failed to add sale")
            return False
    
    def test_remove_sale_functionality(self):
        """Test removing a sale from a product"""
        print("\n=== Testing Remove Sale Functionality ===")
        
        # Remove sale from product3
        sale_data = {
            'product_id': self.product3.id,
            'action': 'remove_sale'
        }
        
        response = self.client.post('/manage_sales/', data=sale_data)
        
        print(f"Response Status: {response.status_code}")
        
        # Check if product was updated
        updated_product = Product.objects.get(id=self.product3.id)
        print(f"Product is_on_sale: {updated_product.is_on_sale}")
        print(f"Product sale_price: {updated_product.sale_price}")
        
        if (not updated_product.is_on_sale and 
            updated_product.sale_price is None):
            print("✅ Sale removed successfully")
            return True
        else:
            print("❌ Failed to remove sale")
            return False
    
    def test_sale_validation(self):
        """Test sale price validation"""
        print("\n=== Testing Sale Price Validation ===")
        
        # Test sale price higher than regular price
        invalid_sale_data = {
            'product_id': self.product2.id,
            'action': 'add_sale',
            'sale_price': '75.00',  # Higher than regular price of 50.00
            'sale_start_date': timezone.now().strftime('%Y-%m-%dT%H:%M')
        }
        
        response = self.client.post('/manage_sales/', data=invalid_sale_data)
        
        # Check that product was not updated
        updated_product = Product.objects.get(id=self.product2.id)
        print(f"Product is_on_sale: {updated_product.is_on_sale}")
        
        if not updated_product.is_on_sale:
            print("✅ Sale validation working correctly")
            return True
        else:
            print("❌ Sale validation failed")
            return False
    
    def test_product_sale_methods(self):
        """Test Product model methods for sales"""
        print("\n=== Testing Product Sale Methods ===")
        
        # Test product with active sale
        print(f"Product3 is_currently_on_sale(): {self.product3.is_currently_on_sale()}")
        print(f"Product3 get_current_price(): {self.product3.get_current_price()}")
        print(f"Product3 get_discount_percentage(): {self.product3.get_discount_percentage()}")
        print(f"Product3 get_discount_amount(): {self.product3.get_discount_amount()}")
        
        # Test product without sale
        print(f"Product1 is_currently_on_sale(): {self.product1.is_currently_on_sale()}")
        print(f"Product1 get_current_price(): {self.product1.get_current_price()}")
        print(f"Product1 get_discount_percentage(): {self.product1.get_discount_percentage()}")
        print(f"Product1 get_discount_amount(): {self.product1.get_discount_amount()}")
        
        if (self.product3.is_currently_on_sale() and 
            self.product3.get_current_price() == Decimal('150.00') and
            self.product3.get_discount_percentage() == 25.0 and
            not self.product1.is_currently_on_sale()):
            print("✅ Product sale methods working correctly")
            return True
        else:
            print("❌ Product sale methods not working correctly")
            return False
    
    def test_home_page_sale_display(self):
        """Test if sales are displayed correctly on home page"""
        print("\n=== Testing Home Page Sale Display ===")
        
        response = self.client.get('/')
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check if sale badge is present for product3
            if 'SALE' in content and 'Test Product 3' in content:
                print("✅ Sale badge displayed on home page")
            else:
                print("❌ Sale badge not displayed on home page")
                print("Content preview:", content[:500])
            
            # Check if sale price is displayed
            if 'R150.00' in content:
                print("✅ Sale price displayed correctly")
            else:
                print("❌ Sale price not displayed correctly")
            
            return True
        else:
            print("❌ Home page not accessible")
            return False
    
    def test_checkout_with_sale_items(self):
        """Test checkout functionality with sale items"""
        print("\n=== Testing Checkout with Sale Items ===")
        
        checkout_data = {
            'customerName': 'Test Customer',
            'customerPhone': '1234567890',
            'items': [
                {
                    'product': 'Test Product 3',
                    'price': '150.00',
                    'regularPrice': '200.00',
                    'salePrice': '150.00',
                    'isOnSale': True,
                    'quantity': 2
                }
            ],
            'total': '300.00',
            'cashReceived': '350.00',
            'changeGiven': '50.00'
        }
        
        response = self.client.post(
            '/checkout_order/',
            data=json.dumps(checkout_data),
            content_type='application/json'
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"Response Data: {response_data}")
            
            if response_data.get('status') == 'success':
                print("✅ Checkout with sale items successful")
                return True
            else:
                print(f"❌ Checkout failed: {response_data.get('message', 'Unknown error')}")
                return False
        else:
            print("❌ Checkout request failed")
            return False

def run_all_tests():
    """Run all sales functionality tests"""
    print("=" * 60)
    print("SALES FUNCTIONALITY TEST REPORT")
    print("=" * 60)
    
    test_instance = SalesFunctionalityTest()
    test_instance.setUp()
    
    results = {
        'manage_sales_access': test_instance.test_manage_sales_page_access(),
        'add_sale': test_instance.test_add_sale_functionality(),
        'remove_sale': test_instance.test_remove_sale_functionality(),
        'sale_validation': test_instance.test_sale_validation(),
        'product_methods': test_instance.test_product_sale_methods(),
        'home_display': test_instance.test_home_page_sale_display(),
        'checkout_sales': test_instance.test_checkout_with_sale_items()
    }
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All sales functionality tests passed!")
    else:
        print("⚠️  Some tests failed. Check the details above.")
    
    return results

if __name__ == '__main__':
    run_all_tests()
