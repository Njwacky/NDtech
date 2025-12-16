#!/usr/bin/env python
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from django.utils import timezone
from nano.models import ErrorLog, User, UserActivity, DeviceConnection
from django.contrib.auth import get_user_model

def create_test_data():
    """Create test data for error tracking system"""
    
    print("Creating test data for error tracking system...")
    
    # Get or create a test user
    User = get_user_model()
    try:
        test_user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        print(f"Created test user: {test_user.username}")
    
    # Create sample error logs
    error_types = ['system_error', 'user_error', 'validation_error', 'api_error']
    severities = ['low', 'medium', 'high', 'critical']
    
    sample_errors = [
        {
            'error_type': 'system_error',
            'severity': 'critical',
            'error_message': 'Database connection failed: Unable to connect to PostgreSQL server',
            'url': '/api/products/',
            'request_method': 'GET',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'ip_address': '192.168.1.100',
            'stack_trace': 'Traceback (most recent call last):\n  File "views.py", line 123, in get_products\n    connection = get_db_connection()\nDatabaseError: Connection failed',
            'file_name': 'views.py',
            'function_name': 'get_products',
            'line_number': 123,
            'user_action': 'Loading product list',
            'user': test_user
        },
        {
            'error_type': 'user_error',
            'severity': 'medium',
            'error_message': 'Invalid product ID provided: Product not found',
            'url': '/api/products/99999/',
            'request_method': 'GET',
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'ip_address': '192.168.1.101',
            'user_action': 'Viewing product details',
            'user': test_user
        },
        {
            'error_type': 'validation_error',
            'severity': 'low',
            'error_message': 'Form validation failed: Required field missing',
            'url': '/checkout/',
            'request_method': 'POST',
            'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'ip_address': '192.168.1.102',
            'form_data': {'product_id': '', 'quantity': '0'},
            'user_action': 'Completing checkout',
            'user': test_user
        },
        {
            'error_type': 'api_error',
            'severity': 'high',
            'error_message': 'External API timeout: Warehouse service unreachable',
            'url': '/api/sync-warehouse/',
            'request_method': 'POST',
            'user_agent': 'curl/7.68.0',
            'ip_address': '192.168.1.103',
            'stack_trace': 'TimeoutError: Request timed out after 30 seconds',
            'user_action': 'Syncing warehouse data',
            'user': test_user
        }
    ]
    
    # Create error logs
    for i, error_data in enumerate(sample_errors):
        error, created = ErrorLog.objects.get_or_create(
            error_message=error_data['error_message'],
            error_type=error_data['error_type'],
            url=error_data['url'],
            defaults={
                **error_data,
                'created_at': timezone.now() - timezone.timedelta(hours=i*2)  # Stagger creation times
            }
        )
        if created:
            print(f"Created error log: {error.error_message[:50]}...")
        else:
            print(f"Error log already exists: {error.error_message[:50]}...")
    
    # Create some resolved errors
    unresolved_errors = ErrorLog.objects.filter(is_resolved=False)[:2]
    for error in unresolved_errors:
        error.is_resolved = True
        error.resolved_by = test_user
        error.resolved_at = timezone.now() - timezone.timedelta(hours=1)
        error.resolution_notes = "Fixed by updating database connection string and adding retry logic"
        error.save()
        print(f"Marked error #{error.id} as resolved")
    
    # Create sample device connections
    device_connections = [
        {
            'device_id': 'web_browser_001',
            'device_type': 'web',
            'ip_address': '192.168.1.100',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'location_country': 'South Africa',
            'location_city': 'Johannesburg',
            'latitude': -26.2041,
            'longitude': 28.0473,
            'user': test_user
        },
        {
            'device_id': 'mobile_app_001',
            'device_type': 'android',
            'ip_address': '192.168.1.101',
            'user_agent': 'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36',
            'location_country': 'South Africa',
            'location_city': 'Cape Town',
            'latitude': -33.9249,
            'longitude': 18.4241,
            'user': test_user
        }
    ]
    
    for device_data in device_connections:
        device, created = DeviceConnection.objects.get_or_create(
            user=device_data['user'],
            device_id=device_data['device_id'],
            defaults=device_data
        )
        if created:
            print(f"Created device connection: {device.device_type} - {device.device_id}")
        else:
            print(f"Device connection already exists: {device.device_type} - {device.device_id}")
    
    # Create sample user activities
    activities = [
        {
            'activity_type': 'login',
            'description': 'User logged in successfully',
            'page_url': '/login/',
            'user': test_user,
            'ip_address': '192.168.1.100'
        },
        {
            'activity_type': 'page_view',
            'description': 'Viewed dashboard',
            'page_url': '/',
            'user': test_user,
            'ip_address': '192.168.1.100'
        },
        {
            'activity_type': 'api_call',
            'description': 'Called product API endpoint',
            'page_url': '/api/products/',
            'user': test_user,
            'ip_address': '192.168.1.100',
            'duration_ms': 250
        },
        {
            'activity_type': 'form_submit',
            'description': 'Submitted checkout form',
            'page_url': '/checkout/',
            'user': test_user,
            'ip_address': '192.168.1.100'
        },
        {
            'activity_type': 'error',
            'description': 'Encountered validation error',
            'page_url': '/checkout/',
            'user': test_user,
            'ip_address': '192.168.1.100'
        }
    ]
    
    for i, activity_data in enumerate(activities):
        activity, created = UserActivity.objects.get_or_create(
            user=activity_data['user'],
            activity_type=activity_data['activity_type'],
            description=activity_data['description'],
            defaults={
                **activity_data,
                'created_at': timezone.now() - timezone.timedelta(minutes=i*10)  # Stagger creation times
            }
        )
        if created:
            print(f"Created user activity: {activity.activity_type} - {activity.description}")
        else:
            print(f"User activity already exists: {activity.activity_type} - {activity.description}")
    
    print("\n✅ Test data creation completed!")
    print(f"📊 Summary:")
    print(f"   - Error Logs: {ErrorLog.objects.count()}")
    print(f"   - Resolved Errors: {ErrorLog.objects.filter(is_resolved=True).count()}")
    print(f"   - Unresolved Errors: {ErrorLog.objects.filter(is_resolved=False).count()}")
    print(f"   - Device Connections: {DeviceConnection.objects.count()}")
    print(f"   - User Activities: {UserActivity.objects.count()}")
    
    print(f"\n🌐 You can now access the tracking dashboards at:")
    print(f"   - Main Dashboard: http://127.0.0.1:8000/tracking/")
    print(f"   - Error Tracking: http://127.0.0.1:8000/tracking/errors/")
    print(f"   - Device Tracking: http://127.0.0.1:8000/tracking/devices/")
    print(f"   - User Activity: http://127.0.0.1:8000/tracking/activities/")

if __name__ == '__main__':
    create_test_data()
