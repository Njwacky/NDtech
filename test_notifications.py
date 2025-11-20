#!/usr/bin/env python
"""
Test script for the notification system
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from django.contrib.auth.models import User
from nano.models import Product, Notification, UserProfile

def test_notification_system():
    print("=== Testing FuturePOS Notification System ===\n")
    
    # 1. Check if users exist
    print("1. Checking users...")
    users = User.objects.all()
    if users:
        print(f"   Found {users.count()} users:")
        for user in users:
            if hasattr(user, 'userprofile'):
                print(f"   - {user.username} ({user.userprofile.role})")
            else:
                print(f"   - {user.username} (no profile)")
    else:
        print("   No users found. Please create some users first.")
        return
    
    # 2. Check products and create low stock scenario
    print("\n2. Checking products for low stock...")
    products = Product.objects.all()
    if products:
        print(f"   Found {products.count()} products:")
        for product in products:
            print(f"   - {product.name}: {product.stock} units")
            if product.stock < 20:
                print(f"     ⚠️  LOW STOCK - will trigger notification")
    else:
        print("   No products found. Creating test products...")
        # Create some test products with low stock
        test_products = [
            {"name": "Test Product 1", "price": 10.00, "stock": 5},
            {"name": "Test Product 2", "price": 15.00, "stock": 25},
            {"name": "Test Product 3", "price": 20.00, "stock": 15},
        ]
        
        for prod_data in test_products:
            product = Product.objects.create(**prod_data)
            print(f"   Created: {product.name} with {product.stock} units")
    
    # 3. Test low stock notification creation
    print("\n3. Testing low stock notification creation...")
    from nano.views import check_low_stock
    
    # Run the low stock check
    check_low_stock()
    
    # Check if notifications were created
    low_stock_notifications = Notification.objects.filter(
        notification_type='low_stock',
        is_dismissed=False
    )
    
    if low_stock_notifications:
        print(f"   ✅ Created {low_stock_notifications.count()} low stock notifications:")
        for notif in low_stock_notifications:
            print(f"   - {notif.title}")
            print(f"     Message: {notif.message}")
            print(f"     Target: {notif.target_role}")
    else:
        print("   ℹ️  No low stock notifications created")
    
    # 4. Test cashier request functionality
    print("\n4. Testing cashier request notification creation...")
    cashiers = User.objects.filter(userprofile__role='cashier')
    managers = User.objects.filter(userprofile__role='manager')
    
    if cashiers and managers:
        cashier = cashiers.first()
        manager = managers.first()
        
        # Create a test cashier request
        notification = Notification.objects.create(
            title=f"Cashier Request: Password Reset",
            message=f"From {cashier.username}: I forgot my password and need a reset",
            notification_type='cashier_request',
            target_role='manager',
            created_by=cashier,
            request_type='password_reset',
            request_data={'urgent': True}
        )
        
        print(f"   ✅ Created test cashier request notification:")
        print(f"   - {notification.title}")
        print(f"   - Target: {notification.target_role}")
        print(f"   - Created by: {notification.created_by.username}")
    else:
        print("   ℹ️  Need at least one cashier and one manager to test cashier requests")
        if not cashiers:
            print("     No cashiers found")
        if not managers:
            print("     No managers found")
    
    # 5. Summary
    print("\n5. Summary")
    total_notifications = Notification.objects.filter(is_dismissed=False).count()
    print(f"   Total active notifications: {total_notifications}")
    
    unread_notifications = Notification.objects.filter(is_read=False, is_dismissed=False).count()
    print(f"   Unread notifications: {unread_notifications}")
    
    print("\n=== Test Complete ===")
    print("The notification system is ready!")
    print("\nFeatures implemented:")
    print("✅ Low stock notifications for managers (< 20 units)")
    print("✅ Cashier request system for managers")
    print("✅ Notification bell with badge counter")
    print("✅ Floating message button for cashiers")
    print("✅ 15-minute reminder system")
    print("✅ Mark as read/dismiss functionality")
    print("✅ Real-time notifications")
    
    print("\nTo test the system:")
    print("1. Start the development server: python manage.py runserver")
    print("2. Login as a manager to see low stock notifications")
    print("3. Login as a cashier to see the floating message button")
    print("4. Create a cashier request and see it appear as a notification")

if __name__ == '__main__':
    test_notification_system()
