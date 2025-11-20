#!/usr/bin/env python3
"""
Demo script to demonstrate the password notification redirect feature.
This script creates test data and shows how the feature works.
"""

import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from django.contrib.auth.models import User
from nano.models import UserProfile, Notification

def create_demo_data():
    """Create demo users and notifications"""
    print("🎬 Creating demo data for password notification redirect feature...")
    print("=" * 60)
    
    # Create or get manager user
    manager, created = User.objects.get_or_create(
        username='demo_manager',
        defaults={
            'email': 'manager@demo.com',
            'first_name': 'Demo',
            'last_name': 'Manager'
        }
    )
    if created:
        manager.set_password('manager123')
        manager.save()
        print("✅ Created manager user: demo_manager / manager123")
    else:
        print("ℹ️  Manager user already exists: demo_manager")
    
    # Create or get manager profile
    manager_profile, created = UserProfile.objects.get_or_create(
        user=manager,
        defaults={'role': 'manager'}
    )
    if not created:
        manager_profile.role = 'manager'
        manager_profile.save()
    
    # Create or get cashier users
    cashiers = [
        ('demo_cashier1', 'Alice', 'Smith'),
        ('demo_cashier2', 'Bob', 'Johnson'),
        ('demo_cashier3', 'Carol', 'Williams')
    ]
    
    for username, first_name, last_name in cashiers:
        cashier, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@demo.com',
                'first_name': first_name,
                'last_name': last_name
            }
        )
        if created:
            cashier.set_password('cashier123')
            cashier.save()
            print(f"✅ Created cashier user: {username} / cashier123")
        else:
            print(f"ℹ️  Cashier user already exists: {username}")
        
        # Create or get cashier profile
        cashier_profile, created = UserProfile.objects.get_or_create(
            user=cashier,
            defaults={'role': 'cashier'}
        )
        if not created:
            cashier_profile.role = 'cashier'
            cashier_profile.save()
    
    # Clear existing password notifications
    Notification.objects.filter(
        notification_type='cashier_request',
        request_type='password_reset'
    ).delete()
    
    # Create password reset notifications
    password_notifications = [
        {
            'user': User.objects.get(username='demo_cashier1'),
            'message': 'I forgot my password and need to reset it for my shift today.'
        },
        {
            'user': User.objects.get(username='demo_cashier2'),
            'message': 'Please help me change my password, I think someone might know my current one.'
        },
        {
            'user': User.objects.get(username='demo_cashier3'),
            'message': 'Having trouble logging in, can you reset my password please?'
        }
    ]
    
    for notif_data in password_notifications:
        notification = Notification.objects.create(
            title=f"Cashier Request: password_reset",
            message=f"From {notif_data['user'].username}: {notif_data['message']}",
            notification_type='cashier_request',
            target_role='manager',
            created_by=notif_data['user'],
            request_type='password_reset'
        )
        print(f"✅ Created password notification from {notif_data['user'].username}")
    
    # Create some other notifications for comparison
    other_notifications = [
        {
            'user': User.objects.get(username='demo_cashier1'),
            'request_type': 'order_issue',
            'message': 'Customer is asking for a refund on order #1234'
        },
        {
            'user': User.objects.get(username='demo_cashier2'),
            'request_type': 'stock_issue',
            'message': 'We are running low on coffee beans'
        }
    ]
    
    for notif_data in other_notifications:
        notification = Notification.objects.create(
            title=f"Cashier Request: {notif_data['request_type']}",
            message=f"From {notif_data['user'].username}: {notif_data['message']}",
            notification_type='cashier_request',
            target_role='manager',
            created_by=notif_data['user'],
            request_type=notif_data['request_type']
        )
        print(f"✅ Created {notif_data['request_type']} notification from {notif_data['user'].username}")
    
    print("\n" + "=" * 60)
    print("🎯 Demo Data Created Successfully!")
    print("=" * 60)

def show_notification_summary():
    """Show summary of created notifications"""
    print("\n📊 Notification Summary:")
    print("-" * 30)
    
    password_notifications = Notification.objects.filter(
        notification_type='cashier_request',
        request_type='password_reset'
    )
    
    other_notifications = Notification.objects.filter(
        notification_type='cashier_request'
    ).exclude(request_type='password_reset')
    
    print(f"🔐 Password Reset Notifications: {password_notifications.count()}")
    for notif in password_notifications:
        print(f"   • From {notif.created_by.username}: {notif.message[:50]}...")
    
    print(f"\n📋 Other Notifications: {other_notifications.count()}")
    for notif in other_notifications:
        print(f"   • From {notif.created_by.username}: {notif.message[:50]}...")

def show_test_instructions():
    """Show instructions for testing the feature"""
    print("\n🧪 Testing Instructions:")
    print("=" * 60)
    print("1. Start the Django development server:")
    print("   python manage.py runserver")
    print()
    print("2. Open your browser and go to: http://127.0.0.1:8000/")
    print()
    print("3. Login as manager:")
    print("   Username: demo_manager")
    print("   Password: manager123")
    print()
    print("4. Look for the notification bell icon in the navigation")
    print("   - It should show a badge with number '3' (password notifications)")
    print()
    print("5. Click the notification bell to see the dropdown")
    print("   - Password notifications will have orange color and key icon")
    print("   - Each password notification will have an 'Edit User' button")
    print()
    print("6. Click 'Edit User' on any password notification")
    print("   - You should be redirected directly to the user edit page")
    print("   - The user's password fields will be available for editing")
    print()
    print("7. Test the fallback mechanism:")
    print("   - Other notifications (order issue, stock issue) won't have 'Edit User' button")
    print("   - They will only have 'Mark as read' and 'Dismiss' buttons")
    print()
    print("8. Test as cashier (optional):")
    print("   - Login as demo_cashier1 / cashier123")
    print("   - Use the floating message button to send new password requests")
    print()
    print("🎉 Expected Behavior:")
    print("   • Password notifications are visually distinct (orange color)")
    print("   • 'Edit User' button appears only for password-related notifications")
    print("   • Clicking 'Edit User' redirects to the correct user edit page")
    print("   • Manager can reset passwords and save changes")
    print("   • System gracefully handles any errors during redirect")

def cleanup_demo_data():
    """Clean up demo data"""
    print("\n🧹 Cleaning up demo data...")
    
    # Delete demo notifications
    deleted_notifications = Notification.objects.filter(
        created_by__username__in=['demo_cashier1', 'demo_cashier2', 'demo_cashier3']
    ).delete()
    print(f"✅ Deleted {deleted_notifications[0]} notifications")
    
    # Delete demo users
    deleted_users = User.objects.filter(
        username__in=['demo_manager', 'demo_cashier1', 'demo_cashier2', 'demo_cashier3']
    ).delete()
    print(f"✅ Deleted {deleted_users[0]} users")
    
    print("🧹 Cleanup completed!")

def main():
    """Main demo function"""
    print("🚀 Password Notification Redirect Feature Demo")
    print("=" * 60)
    
    while True:
        print("\n📋 Choose an option:")
        print("1. Create demo data")
        print("2. Show notification summary")
        print("3. Show testing instructions")
        print("4. Clean up demo data")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            create_demo_data()
            show_notification_summary()
        elif choice == '2':
            show_notification_summary()
        elif choice == '3':
            show_test_instructions()
        elif choice == '4':
            cleanup_demo_data()
        elif choice == '5':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-5.")

if __name__ == '__main__':
    main()
