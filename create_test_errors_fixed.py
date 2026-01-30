#!/usr/bin/env python
"""
Script to create test errors for NDtechTrack error tracking system.
This script generates various types of errors to test error monitoring capabilities.
"""

import os
import sys
import django
from datetime import datetime, timedelta
import random

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import models
from nano.models import ErrorLog, DeviceConnection, UserActivity, Notification
from django.utils import timezone

def create_test_users():
    """Create test users if they don't exist"""
    users_created = []
    
    test_users = [
        {'username': 'test_admin', 'email': 'admin@test.com', 'role': 'admin'},
        {'username': 'test_manager', 'email': 'manager@test.com', 'role': 'manager'},
        {'username': 'test_cashier', 'email': 'cashier@test.com', 'role': 'cashier'},
        {'username': 'test_user1', 'email': 'user1@test.com', 'role': 'cashier'},
        {'username': 'test_user2', 'email': 'user2@test.com', 'role': 'cashier'},
    ]
    
    for user_data in test_users:
        try:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={'email': user_data['email']}
            )
            if created:
                user.set_password('test123')
                user.save()
                
                # Create user profile
                from nano.models import UserProfile
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.role = user_data['role']
                profile.save()
                
                users_created.append(user)
                print(f"Created user: {user.username} ({user_data['role']})")
            else:
                users_created.append(user)
                print(f"User already exists: {user.username}")
        except Exception as e:
            print(f"Error creating user {user_data['username']}: {e}")
    
    return users_created

def create_test_device_connections(users):
    """Create test device connections"""
    connections = []
    
    device_types = ['web', 'android', 'ios', 'tablet', 'desktop']
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
        'Mozilla/5.0 (Android 11; Mobile; rv:68.0) Gecko/68.0 Firefox/88.0',
    ]
    
    for user in users:
        for i in range(random.randint(1, 3)):
            try:
                connection = DeviceConnection.objects.create(
                    user=user,
                    device_id=f"device_{user.id}_{i}",
                    device_type=random.choice(device_types),
                    ip_address=f"192.168.1.{random.randint(100, 255)}",
                    user_agent=random.choice(user_agents),
                    location_country='South Africa',
                    location_city=random.choice(['Johannesburg', 'Cape Town', 'Durban', 'Pretoria']),
                    latitude=random.uniform(-35, -22),
                    longitude=random.uniform(18, 33),
                    is_active=random.choice([True, False]),
                    page_views=random.randint(10, 1000),
                    actions_performed=random.randint(5, 500),
                    data_transferred_mb=random.uniform(1, 100)
                )
                connections.append(connection)
                print(f"Created device connection for {user.username}")
            except Exception as e:
                print(f"Error creating device connection: {e}")
    
    return connections

def create_test_errors(users, connections):
    """Create various types of test errors"""
    
    error_scenarios = [
        # User Errors
        {
            'error_type': 'user_error',
            'severity': 'low',
            'error_message': 'User entered invalid product barcode',
            'url': '/home/',
            'request_method': 'POST',
            'user_action': 'Product lookup via barcode scanner',
            'form_data': {'barcode': 'INVALID123', 'action': 'lookup'},
            'file_name': 'views.py'
        },
        {
            'error_type': 'user_error',
            'severity': 'medium',
            'error_message': 'User attempted to process sale with insufficient stock',
            'url': '/checkout/',
            'request_method': 'POST',
            'user_action': 'Complete sale transaction',
            'form_data': {'product_id': 1, 'quantity': 999, 'customer_name': 'Test Customer'},
            'file_name': 'views.py'
        },
        {
            'error_type': 'user_error',
            'severity': 'high',
            'error_message': 'User attempted to delete critical product without permissions',
            'url': '/products/delete/123/',
            'request_method': 'POST',
            'user_action': 'Delete product',
            'form_data': {'product_id': 123, 'confirm_delete': 'true'},
            'file_name': 'views.py'
        },
        
        # System Errors
        {
            'error_type': 'system_error',
            'severity': 'critical',
            'error_message': 'Database connection timeout during order processing',
            'url': '/checkout/process/',
            'request_method': 'POST',
            'stack_trace': 'Traceback (most recent call last):\n  File "views.py", line 1234, in process_checkout\n    db_connection.execute(query)\nOperationalError: connection timeout',
            'line_number': 1234,
            'file_name': 'views.py',
            'function_name': 'process_checkout'
        },
        {
            'error_type': 'system_error',
            'severity': 'high',
            'error_message': 'Memory exhaustion during large product import',
            'url': '/warehouse/import/',
            'request_method': 'POST',
            'user_action': 'Import warehouse prices',
            'stack_trace': 'Traceback (most recent call last):\n  File "views.py", line 567, in import_warehouse_data\n    df = pd.read_excel(file)\nMemoryError: Unable to allocate array',
            'line_number': 567,
            'file_name': 'views.py',
            'function_name': 'import_warehouse_data'
        },
        
        # Validation Errors
        {
            'error_type': 'validation_error',
            'severity': 'medium',
            'error_message': 'Invalid email format in user registration',
            'url': '/users/create/',
            'request_method': 'POST',
            'user_action': 'Create new user',
            'form_data': {'username': 'testuser', 'email': 'invalid-email', 'password': 'test123'},
            'file_name': 'views.py'
        },
        {
            'error_type': 'validation_error',
            'severity': 'low',
            'error_message': 'Product price must be greater than zero',
            'url': '/products/add/',
            'request_method': 'POST',
            'user_action': 'Add new product',
            'form_data': {'name': 'Test Product', 'price': '-10', 'category': 'basic_groceries'},
            'file_name': 'views.py'
        },
        
        # Permission Errors
        {
            'error_type': 'permission_error',
            'severity': 'medium',
            'error_message': 'Cashier attempted to access admin dashboard without permissions',
            'url': '/admin/dashboard/',
            'request_method': 'GET',
            'user_action': 'Access admin dashboard',
            'file_name': 'views.py'
        },
        {
            'error_type': 'permission_error',
            'severity': 'high',
            'error_message': 'Unauthorized attempt to delete user accounts',
            'url': '/users/delete/456/',
            'request_method': 'POST',
            'user_action': 'Delete user account',
            'form_data': {'user_id': 456},
            'file_name': 'views.py'
        },
        
        # API Errors
        {
            'error_type': 'api_error',
            'severity': 'high',
            'error_message': 'External payment gateway API returned 503 Service Unavailable',
            'url': '/api/payment/process/',
            'request_method': 'POST',
            'user_action': 'Process payment via external API',
            'form_data': {'amount': 150.00, 'payment_method': 'card', 'card_token': 'tok_123456'},
            'file_name': 'api_views.py'
        },
        {
            'error_type': 'api_error',
            'severity': 'medium',
            'error_message': 'Rate limit exceeded for third-party price comparison API',
            'url': '/api/price-comparison/',
            'request_method': 'GET',
            'user_action': 'Fetch price comparison data',
            'file_name': 'api_views.py'
        },
        
        # Database Errors
        {
            'error_type': 'database_error',
            'severity': 'critical',
            'error_message': 'Deadlock detected during concurrent order processing',
            'url': '/orders/complete/',
            'request_method': 'POST',
            'user_action': 'Complete pending order',
            'stack_trace': 'Traceback (most recent call last):\n  File "views.py", line 789, in complete_order\n    order.save()\nIntegrityError: deadlock detected',
            'line_number': 789,
            'file_name': 'views.py',
            'function_name': 'complete_order'
        },
        
        # Network Errors
        {
            'error_type': 'network_error',
            'severity': 'medium',
            'error_message': 'Failed to connect to email server for receipt delivery',
            'url': '/orders/send-receipt/',
            'request_method': 'POST',
            'user_action': 'Email receipt to customer',
            'form_data': {'order_id': 789, 'customer_email': 'customer@example.com'},
            'file_name': 'email_service.py'
        },
        {
            'error_type': 'network_error',
            'severity': 'low',
            'error_message': 'Timeout while fetching product images from CDN',
            'url': '/products/load-images/',
            'request_method': 'GET',
            'user_action': 'Load product images',
            'file_name': 'image_service.py'
        },
        
        # Payment Errors
        {
            'error_type': 'payment_error',
            'severity': 'high',
            'error_message': 'Payment declined: Insufficient funds',
            'url': '/payment/process/',
            'request_method': 'POST',
            'user_action': 'Process card payment',
            'form_data': {'amount': 500.00, 'card_number': '****-****-****-1234'},
            'file_name': 'payment_views.py'
        },
        {
            'error_type': 'payment_error',
            'severity': 'critical',
            'error_message': 'Payment gateway configuration error: Invalid API keys',
            'url': '/payment/setup/',
            'request_method': 'POST',
            'user_action': 'Configure payment gateway',
            'form_data': {'gateway': 'stripe', 'api_key': 'invalid_key'},
            'file_name': 'payment_views.py'
        }
    ]
    
    created_errors = []
    
    for scenario in error_scenarios:
        # Create multiple instances of each error with variations
        for i in range(random.randint(1, 3)):
            try:
                user = random.choice(users)
                connection = random.choice(connections) if connections else None
                
                # Vary timestamp
                created_at = timezone.now() - timedelta(
                    hours=random.randint(0, 168),  # Up to 1 week ago
                    minutes=random.randint(0, 60)
                )
                
                error = ErrorLog.objects.create(
                    error_type=scenario['error_type'],
                    severity=scenario['severity'],
                    error_message=scenario['error_message'],
                    user=user,
                    device_connection=connection,
                    url=scenario['url'],
                    request_method=scenario['request_method'],
                    user_agent=random.choice([
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
                        'Mozilla/5.0 (Android 11; Mobile; rv:68.0) Gecko/68.0 Firefox/88.0',
                    ]),
                    ip_address=f"192.168.1.{random.randint(100, 255)}",
                    stack_trace=scenario.get('stack_trace', ''),
                    line_number=scenario.get('line_number'),
                    file_name=scenario.get('file_name', 'unknown.py'),
                    function_name=scenario.get('function_name'),
                    user_action=scenario.get('user_action', ''),
                    form_data=scenario.get('form_data', {}),
                    created_at=created_at
                )
                
                created_errors.append(error)
                print(f"Created {scenario['error_type']} error for {user.username}")
                
            except Exception as e:
                print(f"Error creating test error: {e}")
    
    return created_errors

def create_test_user_activities(users, connections):
    """Create test user activities"""
    activity_types = [choice[0] for choice in UserActivity.ACTIVITY_TYPES]
    
    activities = []
    
    for user in users:
        for _ in range(random.randint(5, 20)):
            try:
                connection = random.choice(connections) if connections else None
                
                activity = UserActivity.objects.create(
                    user=user,
                    activity_type=random.choice(activity_types),
                    description=f"Test activity for {user.username}",
                    page_url=random.choice([
                        '/home/', '/products/', '/checkout/', '/orders/', '/reports/',
                        '/users/', '/settings/', '/dashboard/', '/warehouse/', '/airtime/'
                    ]),
                    object_type=random.choice(['product', 'order', 'user', 'sale', '']),
                    object_id=random.randint(1, 1000) if random.random() > 0.5 else None,
                    ip_address=f"192.168.1.{random.randint(100, 255)}",
                    user_agent=random.choice([
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
                    ]),
                    device_connection=connection,
                    metadata={'test_data': True, 'generated_by': 'create_test_errors_fixed.py'},
                    duration_ms=random.randint(100, 5000),
                    created_at=timezone.now() - timedelta(
                        hours=random.randint(0, 72),
                        minutes=random.randint(0, 60)
                    )
                )
                
                activities.append(activity)
                print(f"Created activity for {user.username}: {activity.activity_type}")
                
            except Exception as e:
                print(f"Error creating user activity: {e}")
    
    return activities

def create_automated_issues():
    """Create automated issue scenarios"""
    
    issue_scenarios = [
        {
            'title': 'Critical Database Connection Pool Exhausted',
            'message': 'Database connection pool has reached maximum capacity. New connections are being queued, causing significant slowdown in order processing.',
            'notification_type': 'system_alert',
            'request_type': 'database_issue',
            'request_data': {
                'metric': 'connection_pool_usage',
                'current_value': '95%',
                'threshold': '80%',
                'affected_systems': ['orders', 'payments', 'inventory']
            }
        },
        {
            'title': 'High Memory Usage on Application Server',
            'message': 'Application server memory usage has exceeded 90% for the past 30 minutes. Performance degradation detected.',
            'notification_type': 'system_alert',
            'request_type': 'performance_issue',
            'request_data': {
                'metric': 'memory_usage',
                'current_value': '92%',
                'threshold': '85%',
                'server': 'app-server-01'
            }
        },
        {
            'title': 'Payment Gateway API Response Time Degraded',
            'message': 'External payment gateway API response times have increased by 300%. Average response time: 8.5 seconds.',
            'notification_type': 'system_alert',
            'request_type': 'api_performance',
            'request_data': {
                'api_endpoint': 'payment-gateway.com/process',
                'avg_response_time': '8.5s',
                'threshold': '3s',
                'impact': 'checkout_processing'
            }
        },
        {
            'title': 'Disk Space Running Low on Database Server',
            'message': 'Database server disk space is at 88% capacity. Estimated time to full: 48 hours.',
            'notification_type': 'system_alert',
            'request_type': 'infrastructure_issue',
            'request_data': {
                'server': 'db-server-01',
                'disk_usage': '88%',
                'available_space': '120GB',
                'threshold': '85%'
            }
        },
        {
            'title': 'Unusual Spike in Failed Login Attempts',
            'message': 'Detected 500 failed login attempts in the last hour from 50 unique IP addresses. Possible brute force attack.',
            'notification_type': 'system_alert',
            'request_type': 'security_issue',
            'request_data': {
                'failed_attempts': '500',
                'time_window': '1 hour',
                'unique_ips': '50',
                'top_source_ips': ['192.168.1.100', '10.0.0.1', '172.16.0.1']
            }
        }
    ]
    
    created_issues = []
    
    for scenario in issue_scenarios:
        try:
            # Create for admin users
            admin_users = User.objects.filter(
                models.Q(is_superuser=True) | 
                models.Q(userprofile__role__in=['admin', 'manager'])
            ).distinct()
            
            for admin_user in admin_users:
                notification = Notification.objects.create(
                    title=scenario['title'],
                    message=scenario['message'],
                    notification_type=scenario['notification_type'],
                    target_role='admin',
                    target_user=admin_user,
                    request_type=scenario['request_type'],
                    request_data=scenario['request_data'],
                    created_at=timezone.now() - timedelta(
                        hours=random.randint(0, 24),
                        minutes=random.randint(0, 60)
                    )
                )
                created_issues.append(notification)
                
            print(f"Created automated issue: {scenario['title']}")
            
        except Exception as e:
            print(f"Error creating automated issue: {e}")
    
    return created_issues

def main():
    """Main function to create all test data"""
    print("Creating test errors for NDtechTrack...")
    print("=" * 50)
    
    # Create test users
    print("\n1. Creating test users...")
    users = create_test_users()
    
    # Create device connections
    print("\n2. Creating device connections...")
    connections = create_test_device_connections(users)
    
    # Create test errors
    print("\n3. Creating test errors...")
    errors = create_test_errors(users, connections)
    
    # Create user activities
    print("\n4. Creating user activities...")
    activities = create_test_user_activities(users, connections)
    
    # Create automated issues
    print("\n5. Creating automated issues...")
    issues = create_automated_issues()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST DATA CREATION COMPLETE")
    print("=" * 50)
    print(f"Users created: {len(users)}")
    print(f"Device connections: {len(connections)}")
    print(f"Test errors: {len(errors)}")
    print(f"User activities: {len(activities)}")
    print(f"Automated issues: {len(issues)}")
    
    print("\nError breakdown by type:")
    error_types = {}
    for error in errors:
        error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
    
    for error_type, count in sorted(error_types.items()):
        print(f"  {error_type}: {count}")
    
    print("\nError breakdown by severity:")
    severity_counts = {}
    for error in errors:
        severity_counts[error.severity] = severity_counts.get(error.severity, 0) + 1
    
    for severity, count in sorted(severity_counts.items()):
        print(f"  {severity}: {count}")
    
    print("\nYou can now test the error tracking system at:")
    print("- Error Tracking: /error-tracking/")
    print("- Device Tracking: /device-tracking/")
    print("- User Activity: /user-activity-tracking/")
    print("- Automated Issues: /automated-issues/")
    print("- Error Patterns: /error-patterns/")
    print("- System Performance: /system-performance/")

if __name__ == '__main__':
    main()
