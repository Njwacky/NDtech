#!/usr/bin/env python
"""
Test script to create notifications and verify the notification system
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from django.contrib.auth.models import User
from nano.models import Notification, UserProfile

def create_test_notifications():
    """Create test notifications for testing"""
    print("Creating test notifications...")
    
    # Get or create admin user
    try:
        admin_user = User.objects.get(username='admin')
        print(f"Found admin user: {admin_user.username}")
    except User.DoesNotExist:
        print("Admin user not found. Creating one...")
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        UserProfile.objects.create(user=admin_user, role='admin')
        print(f"Created admin user: {admin_user.username}")
    
    # Create test notifications
    notifications_created = []
    
    # Unread notification
    notification1 = Notification.objects.create(
        title="Test Unread Notification",
        message="This is a test unread notification for debugging",
        notification_type='system_alert',
        target_role='admin',
        target_user=admin_user,
        is_read=False
    )
    notifications_created.append(notification1)
    
    # Read notification
    notification2 = Notification.objects.create(
        title="Test Read Notification",
        message="This is a test read notification for debugging",
        notification_type='cashier_request',
        target_role='admin',
        target_user=admin_user,
        is_read=True
    )
    notifications_created.append(notification2)
    
    # Low stock notification
    notification3 = Notification.objects.create(
        title="Low Stock: Test Product",
        message="Test Product has only 5 units remaining",
        notification_type='low_stock',
        target_role='admin',
        target_user=admin_user,
        is_read=False
    )
    notifications_created.append(notification3)
    
    print(f"Created {len(notifications_created)} test notifications:")
    for notif in notifications_created:
        status = "Read" if notif.is_read else "Unread"
        print(f"  - {notif.title} ({notif.notification_type}) - {status}")
    
    return admin_user, notifications_created

def check_notification_data():
    """Check and display notification data"""
    print("\n" + "="*50)
    print("CHECKING NOTIFICATION DATA")
    print("="*50)
    
    # Get all users
    users = User.objects.all()
    print(f"Total users: {users.count()}")
    for user in users:
        print(f"  - {user.username} (Role: {getattr(user.userprofile, 'role', 'No profile') if hasattr(user, 'userprofile') else 'No profile'})")
    
    # Get all notifications
    notifications = Notification.objects.all()
    print(f"\nTotal notifications: {notifications.count()}")
    
    # Group by user
    for user in users:
        user_notifications = Notification.objects.filter(target_user=user)
        unread_count = user_notifications.filter(is_read=False).count()
        read_count = user_notifications.filter(is_read=True).count()
        
        print(f"\nNotifications for {user.username}:")
        print(f"  Total: {user_notifications.count()}")
        print(f"  Unread: {unread_count}")
        print(f"  Read: {read_count}")
        
        if user_notifications.exists():
            print("  Details:")
            for notif in user_notifications.order_by('-created_at'):
                status = "UNREAD" if not notif.is_read else "READ"
                print(f"    - {notif.title} ({notif.notification_type}) - {status} - {notif.created_at}")

def test_api_response_format():
    """Test the API response format"""
    print("\n" + "="*50)
    print("TESTING API RESPONSE FORMAT")
    print("="*50)
    
    # Get admin user
    try:
        admin_user = User.objects.get(username='admin')
    except User.DoesNotExist:
        print("No admin user found!")
        return
    
    # Simulate API response
    notifications = Notification.objects.filter(target_user=admin_user).order_by('-created_at')
    
    notification_data = []
    for notification in notifications:
        notification_data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'notification_type': notification.notification_type,
            'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_read': notification.is_read,
            'is_dismissed': notification.is_dismissed,
            'reminder_count': notification.reminder_count,
            'can_remind': notification.can_remind(),
            'created_by_id': notification.created_by.id if notification.created_by else None,
            'request_type': getattr(notification, 'request_type', '')
        })
    
    api_response = {'notifications': notification_data}
    
    print(f"API Response would contain {len(notification_data)} notifications")
    print("Sample notification data:")
    if notification_data:
        print(f"  First notification: {notification_data[0]}")
    
    # Calculate badge count
    unread_count = len([n for n in notification_data if not n['is_read']])
    print(f"Badge count should be: {unread_count}")

if __name__ == '__main__':
    print("NOTIFICATION SYSTEM TEST")
    print("="*50)
    
    # Create test data
    admin_user, notifications = create_test_notifications()
    
    # Check data
    check_notification_data()
    
    # Test API format
    test_api_response_format()
    
    print("\n" + "="*50)
    print("TEST COMPLETE")
    print("="*50)
    print("You can now:")
    print("1. Log in as admin/admin123")
    print("2. Visit http://127.0.0.1:8000/ to see notifications")
    print("3. Open test_notification_display.html for detailed testing")
