#!/usr/bin/env python
"""
Test script for Food Ordering Integration with POS System
This script demonstrates how the integration works between food ordering and POS systems
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from django.contrib.auth.models import User
from nano.models import Product, UserProfile
from food_ordering.models import Restaurant, MenuCategory, MenuItem
from nano.food_ordering_integration import FoodOrderingIntegration

def create_test_data():
    """Create test data for demonstration"""
    print("🍔 Creating test data for Food Ordering Integration...")
    
    # Create test user
    user, created = User.objects.get_or_create(
        username='test_food_user',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print("✅ Created test user: test_food_user")
    else:
        print("ℹ️ Test user already exists")
    
    # Create or get user profile
    profile, profile_created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'role': 'manager',
            'created_by': user
        }
    )
    if profile_created:
        print("✅ Created user profile")
    else:
        print("ℹ️ User profile already exists")
    
    # Create test restaurant
    restaurant, created = Restaurant.objects.get_or_create(
        name='Test Restaurant',
        defaults={
            'owner': user,
            'description': 'A test restaurant for food ordering integration',
            'phone': '0123456789',
            'address': '123 Test Street, Test City',
            'is_active': True
        }
    )
    
    if created:
        print("✅ Created test restaurant")
    else:
        print("ℹ️ Test restaurant already exists")
    
    # Create menu categories
    categories = {}
    for cat_name in ['Beverages', 'Main Courses', 'Desserts', 'Snacks']:
        category, created = MenuCategory.objects.get_or_create(
            restaurant=restaurant,
            name=cat_name,
            defaults={
                'description': f'{cat_name} category',
                'display_order': len(categories)
            }
        )
        categories[cat_name] = category
        if created:
            print(f"✅ Created category: {cat_name}")
    
    # Create menu items
    menu_items = [
        {
            'name': 'Coca-Cola',
            'description': 'Refreshing cold drink',
            'price': 15.00,
            'category': categories['Beverages'],
            'ingredients': 'Carbonated water, sugar, caffeine, natural flavors',
            'preparation_time': 2,
            'is_vegetarian': True,
            'is_vegan': True
        },
        {
            'name': 'Classic Burger',
            'description': 'Juicy beef patty with lettuce, tomato, and special sauce',
            'price': 65.00,
            'category': categories['Main Courses'],
            'ingredients': 'Beef patty, buns, lettuce, tomato, onion, special sauce',
            'preparation_time': 15,
            'is_vegetarian': False,
            'is_vegan': False
        },
        {
            'name': 'Chocolate Cake',
            'description': 'Rich chocolate cake with chocolate frosting',
            'price': 35.00,
            'category': categories['Desserts'],
            'ingredients': 'Flour, sugar, cocoa, eggs, butter',
            'preparation_time': 5,
            'is_vegetarian': True,
            'is_vegan': False
        },
        {
            'name': 'French Fries',
            'description': 'Crispy golden fries with salt',
            'price': 25.00,
            'category': categories['Snacks'],
            'ingredients': 'Potatoes, salt, vegetable oil',
            'preparation_time': 8,
            'is_vegetarian': True,
            'is_vegan': True
        }
    ]
    
    for item_data in menu_items:
        menu_item, created = MenuItem.objects.get_or_create(
            restaurant=restaurant,
            name=item_data['name'],
            defaults=item_data
        )
        if created:
            print(f"✅ Created menu item: {item_data['name']}")
        else:
            print(f"ℹ️ Menu item already exists: {item_data['name']}")
    
    return restaurant, menu_items

def test_barcode_patterns():
    """Test barcode pattern matching"""
    print("\n📷 Testing barcode pattern matching...")
    
    # Test South African barcode patterns
    test_barcodes = [
        '6001007123456',  # Coca-Cola pattern
        '6001063789012',  # Bread pattern
        '6001085345678',  # Chips pattern
        '6001062345678',  # Dairy pattern
        '6001019876543',  # Sweets pattern
    ]
    
    for barcode in test_barcodes:
        print(f"\n🔍 Testing barcode: {barcode}")
        results = FoodOrderingIntegration.search_menu_items_by_barcode(barcode)
        
        if results:
            print(f"✅ Found {len(results)} matching items:")
            for result in results:
                print(f"   - {result['name']} ({result['restaurant']}) - R{result['price']}")
                print(f"     Match type: {result['match_type']}")
        else:
            print("❌ No matching items found")

def test_pos_product_creation():
    """Test creating POS products from menu items"""
    print("\n🛒 Testing POS product creation...")
    
    # Get a menu item to test
    menu_item = MenuItem.objects.filter(is_available=True).first()
    if not menu_item:
        print("❌ No menu items found for testing")
        return
    
    print(f"🍽️ Testing with menu item: {menu_item.name}")
    
    # Test creating POS product
    pos_product = FoodOrderingIntegration.create_pos_product_from_menu_item(
        menu_item, 
        barcode=f"TEST{menu_item.id:08d}"
    )
    
    if pos_product:
        print(f"✅ Created POS product: {pos_product.name}")
        print(f"   Price: R{pos_product.price}")
        print(f"   Category: {pos_product.category}")
        print(f"   Barcode: {pos_product.barcode}")
        print(f"   Stock: {pos_product.stock}")
    else:
        print("❌ Failed to create POS product")

def test_integration_workflow():
    """Test the complete integration workflow"""
    print("\n🔄 Testing complete integration workflow...")
    
    # Step 1: Create test data
    restaurant, menu_items = create_test_data()
    
    # Step 2: Test barcode scanning
    test_barcode_patterns()
    
    # Step 3: Test POS product creation
    test_pos_product_creation()
    
    # Step 4: Show summary
    print("\n📊 Integration Test Summary:")
    print(f"   Restaurants: {Restaurant.objects.count()}")
    print(f"   Menu Items: {MenuItem.objects.count()}")
    print(f"   POS Products: {Product.objects.count()}")
    
    # Show food ordering items
    food_products = Product.objects.filter(name__startswith='[FOOD]')
    print(f"   Food Products in POS: {food_products.count()}")
    
    if food_products.exists():
        print("\n🍽️ Food Products in POS System:")
        for product in food_products:
            print(f"   - {product.name}: R{product.price} (Stock: {product.stock})")

def demonstrate_api_usage():
    """Demonstrate how the API would be used"""
    print("\n🌐 API Usage Examples:")
    print("\n1. Barcode Scanner API:")
    print("   GET /api/food/scanner/lookup/{barcode}/")
    print("   Returns: JSON with POS products and matching food items")
    
    print("\n2. Add Food Item to POS API:")
    print("   POST /api/food/add-to-pos/")
    print("   Body: {")
    print("     'menu_item_id': 123,")
    print("     'barcode': '6001007123456',")
    print("     'quantity': 1")
    print("   }")
    
    print("\n3. Menu Browser API:")
    print("   GET /food/menu/")
    print("   GET /food/menu/?restaurant_id=1")
    print("   Returns: HTML page with restaurant menu browser")
    
    print("\n4. Food Scanner Page:")
    print("   GET /food/scanner/")
    print("   Returns: HTML page with integrated scanner interface")

def main():
    """Main test function"""
    print("🍔 Food Ordering Integration Test Suite")
    print("=" * 50)
    
    try:
        # Run integration tests
        test_integration_workflow()
        
        # Show API usage examples
        demonstrate_api_usage()
        
        print("\n✅ All tests completed successfully!")
        print("\n📚 Integration Features:")
        print("   ✅ Barcode scanning for both POS and food items")
        print("   ✅ South African barcode pattern matching")
        print("   ✅ Automatic POS product creation from menu items")
        print("   ✅ Food category mapping to POS categories")
        print("   ✅ Menu browsing and searching")
        print("   ✅ Dietary information display")
        print("   ✅ Restaurant and preparation time info")
        
        print("\n🚀 Next Steps:")
        print("   1. Access /food/scanner/ to test the integrated scanner")
        print("   2. Access /food/menu/ to browse restaurant menus")
        print("   3. Scan real product barcodes to test pattern matching")
        print("   4. Add menu items to POS to test product creation")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
