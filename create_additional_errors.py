#!/usr/bin/env python
"""
Script to create additional test errors to cover all error types.
"""

import os
import django
from datetime import timedelta
import random

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from django.contrib.auth.models import User
from nano.models import ErrorLog, DeviceConnection
from django.utils import timezone

def create_additional_errors():
    """Create additional errors to cover all types"""
    
    # Get existing data
    users = User.objects.all()
    connections = DeviceConnection.objects.all()
    
    if not users.exists():
        print("No users found. Please run create_test_errors_fixed.py first.")
        return
    
    # Additional error scenarios to cover missing types
    additional_scenarios = [
        # User Errors (missing from previous run)
        {
            'error_type': 'user_error',
            'severity': 'low',
            'error_message': 'User entered invalid discount code',
            'url': '/checkout/apply-discount/',
            'request_method': 'POST',
            'user_action': 'Apply discount code',
            'form_data': {'discount_code': 'INVALID123', 'order_total': '150.00'},
            'file_name': 'checkout_views.py'
        },
        {
            'error_type': 'user_error',
            'severity': 'medium',
            'error_message': 'User attempted to checkout with empty cart',
            'url': '/checkout/process/',
            'request_method': 'POST',
            'user_action': 'Process empty checkout',
            'form_data': {'cart_items': [], 'customer_name': 'Test Customer'},
            'file_name': 'checkout_views.py'
        },
        
        # Validation Errors (missing from previous run)
        {
            'error_type': 'validation_error',
            'severity': 'medium',
            'error_message': 'Phone number format invalid for customer registration',
            'url': '/customers/register/',
            'request_method': 'POST',
            'user_action': 'Register new customer',
            'form_data': {'name': 'Test Customer', 'phone': 'invalid-phone', 'email': 'test@example.com'},
            'file_name': 'customer_views.py'
        },
        {
            'error_type': 'validation_error',
            'severity': 'low',
            'error_message': 'Product category selection required',
            'url': '/products/create/',
            'request_method': 'POST',
            'user_action': 'Create product without category',
            'form_data': {'name': 'Test Product', 'price': '50.00', 'category': ''},
            'file_name': 'product_views.py'
        },
        
        # Permission Errors (missing from previous run)
        {
            'error_type': 'permission_error',
            'severity': 'medium',
            'error_message': 'Cashier attempted to access financial reports',
            'url': '/reports/financial/',
            'request_method': 'GET',
            'user_action': 'Access restricted financial reports',
            'file_name': 'report_views.py'
        },
        
        # API Errors (missing from previous run)
        {
            'error_type': 'api_error',
            'severity': 'high',
            'error_message': 'Third-party inventory API returned 500 Internal Server Error',
            'url': '/api/inventory/sync/',
            'request_method': 'POST',
            'user_action': 'Sync inventory with external system',
            'form_data': {'sync_type': 'full', 'products': ['product1', 'product2']},
            'file_name': 'inventory_api.py'
        },
        
        # Network Errors (missing from previous run)
        {
            'error_type': 'network_error',
            'severity': 'medium',
            'error_message': 'Connection timeout to backup server',
            'url': '/system/backup/',
            'request_method': 'POST',
            'user_action': 'Perform system backup',
            'form_data': {'backup_type': 'full', 'destination': 'backup-server'},
            'file_name': 'backup_service.py'
        },
        {
            'error_type': 'network_error',
            'severity': 'low',
            'error_message': 'Slow response from CDN for static assets',
            'url': '/static/load/',
            'request_method': 'GET',
            'user_action': 'Load static assets from CDN',
            'file_name': 'static_views.py'
        },
        
        # Payment Errors (missing from previous run)
        {
            'error_type': 'payment_error',
            'severity': 'high',
            'error_message': 'Credit card expired',
            'url': '/payment/process-card/',
            'request_method': 'POST',
            'user_action': 'Process payment with expired card',
            'form_data': {'card_number': '****-****-****-1234', 'expiry': '12/20', 'amount': '250.00'},
            'file_name': 'payment_processor.py'
        },
        {
            'error_type': 'payment_error',
            'severity': 'medium',
            'error_message': 'Payment processor declined transaction - suspected fraud',
            'url': '/payment/verify/',
            'request_method': 'POST',
            'user_action': 'Verify suspicious transaction',
            'form_data': {'transaction_id': 'txn_123456', 'risk_score': '95'},
            'file_name': 'fraud_detection.py'
        }
    ]
    
    created_count = 0
    
    for scenario in additional_scenarios:
        try:
            user = random.choice(list(users))
            connection = random.choice(list(connections)) if connections.exists() else None
            
            # Create multiple instances
            for i in range(random.randint(1, 2)):
                created_at = timezone.now() - timedelta(
                    hours=random.randint(0, 72),
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
                    function_name=scenario.get('function_name', ''),
                    user_action=scenario.get('user_action', ''),
                    form_data=scenario.get('form_data', {}),
                    created_at=created_at
                )
                
                created_count += 1
                print(f"Created additional {scenario['error_type']} error for {user.username}")
                
        except Exception as e:
            print(f"Error creating additional test error: {e}")
    
    return created_count

def main():
    """Main function"""
    print("Creating additional test errors...")
    print("=" * 40)
    
    created_count = create_additional_errors()
    
    print("\n" + "=" * 40)
    print(f"ADDITIONAL ERRORS CREATED: {created_count}")
    print("=" * 40)
    
    # Show current error statistics
    print("\nCurrent error breakdown by type:")
    from django.db.models import Count
    error_stats = ErrorLog.objects.values('error_type').annotate(count=Count('id')).order_by('error_type')
    
    for stat in error_stats:
        print(f"  {stat['error_type']}: {stat['count']}")
    
    print("\nCurrent error breakdown by severity:")
    severity_stats = ErrorLog.objects.values('severity').annotate(count=Count('id')).order_by('severity')
    
    for stat in severity_stats:
        print(f"  {stat['severity']}: {stat['count']}")
    
    total_errors = ErrorLog.objects.count()
    print(f"\nTotal errors in system: {total_errors}")

if __name__ == '__main__':
    main()
