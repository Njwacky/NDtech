#!/usr/bin/env python
"""
Script to create error patterns and test resolution workflow.
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

def create_error_patterns():
    """Create recurring error patterns for testing"""
    
    users = User.objects.all()
    connections = DeviceConnection.objects.all()
    
    if not users.exists():
        print("No users found. Please run create_test_errors_fixed.py first.")
        return
    
    # Create recurring error patterns
    error_patterns = [
        # Pattern 1: Barcode scanner issues (repeated user_error)
        {
            'base_message': 'Barcode scanner failed to read product',
            'error_type': 'user_error',
            'severity': 'low',
            'url': '/home/',
            'request_method': 'POST',
            'user_action': 'Scan product barcode',
            'file_name': 'scanner_service.py',
            'variations': [
                'Barcode scanner failed to read product',
                'Unable to read damaged barcode',
                'Barcode scanner timeout error',
                'Invalid barcode format detected'
            ]
        },
        
        # Pattern 2: Payment processing timeouts (repeated api_error)
        {
            'base_message': 'Payment gateway timeout during transaction',
            'error_type': 'api_error',
            'severity': 'high',
            'url': '/payment/process/',
            'request_method': 'POST',
            'user_action': 'Process payment transaction',
            'file_name': 'payment_gateway.py',
            'variations': [
                'Payment gateway timeout during transaction',
                'External payment API response timeout',
                'Payment processor connection timeout',
                'Gateway response exceeded 30 second limit'
            ]
        },
        
        # Pattern 3: Database connection issues (repeated system_error)
        {
            'base_message': 'Database connection lost during operation',
            'error_type': 'system_error',
            'severity': 'critical',
            'url': '/orders/process/',
            'request_method': 'POST',
            'user_action': 'Process customer order',
            'file_name': 'database_service.py',
            'function_name': 'execute_query',
            'variations': [
                'Database connection lost during operation',
                'Connection to database server failed',
                'Database server not responding',
                'Connection pool exhausted'
            ]
        },
        
        # Pattern 4: Inventory sync failures (repeated network_error)
        {
            'base_message': 'Failed to sync inventory with external system',
            'error_type': 'network_error',
            'severity': 'medium',
            'url': '/inventory/sync/',
            'request_method': 'POST',
            'user_action': 'Sync inventory data',
            'file_name': 'inventory_sync.py',
            'variations': [
                'Failed to sync inventory with external system',
                'External inventory API unavailable',
                'Inventory sync network timeout',
                'Third-party warehouse connection failed'
            ]
        }
    ]
    
    created_patterns = []
    
    for pattern in error_patterns:
        # Create 3-5 instances of each pattern to simulate recurrence
        pattern_count = random.randint(3, 5)
        
        for i in range(pattern_count):
            try:
                user = random.choice(list(users))
                connection = random.choice(list(connections)) if connections.exists() else None
                
                # Use variation or base message
                if random.random() > 0.3:  # 70% chance of using variation
                    error_message = random.choice(pattern['variations'])
                else:
                    error_message = pattern['base_message']
                
                # Spread occurrences over time
                created_at = timezone.now() - timedelta(
                    hours=random.randint(1, 48),  # Within last 2 days
                    minutes=random.randint(0, 60)
                )
                
                error = ErrorLog.objects.create(
                    error_type=pattern['error_type'],
                    severity=pattern['severity'],
                    error_message=error_message,
                    user=user,
                    device_connection=connection,
                    url=pattern['url'],
                    request_method=pattern['request_method'],
                    user_agent=random.choice([
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
                        'Mozilla/5.0 (Android 11; Mobile; rv:68.0) Gecko/68.0 Firefox/88.0',
                    ]),
                    ip_address=f"192.168.1.{random.randint(100, 255)}",
                    stack_trace=f"Pattern error - occurred at line {random.randint(100, 999)}",
                    line_number=random.randint(100, 999),
                    file_name=pattern['file_name'],
                    function_name=pattern.get('function_name', ''),
                    user_action=pattern['user_action'],
                    form_data={'pattern_id': len(created_patterns), 'occurrence': i + 1},
                    created_at=created_at
                )
                
                created_patterns.append(error)
                print(f"Created pattern error: {pattern['error_type']} - {error_message[:50]}...")
                
            except Exception as e:
                print(f"Error creating pattern: {e}")
    
    return created_patterns

def create_resolved_errors():
    """Create some resolved errors to test resolution workflow"""
    
    users = User.objects.filter(userprofile__role__in=['admin', 'manager'])
    
    if not users.exists():
        print("No admin/manager users found.")
        return []
    
    # Get some existing errors to mark as resolved
    unresolved_errors = ErrorLog.objects.filter(is_resolved=False)[:10]
    
    resolved_count = 0
    for error in unresolved_errors:
        try:
            resolver = random.choice(list(users))
            
            # Create resolution notes
            resolution_notes = random.choice([
                "Fixed by restarting the affected service",
                "Resolved by updating database connection pool settings",
                "Fixed by implementing proper error handling",
                "Resolved by updating API timeout configuration",
                "Fixed by clearing application cache and restarting services"
            ])
            
            error.mark_resolved(resolver, resolution_notes)
            resolved_count += 1
            print(f"Resolved error #{error.id}: {error.error_message[:40]}...")
            
        except Exception as e:
            print(f"Error resolving error: {e}")
    
    return resolved_count

def create_critical_errors():
    """Create some critical errors for testing escalation"""
    
    users = User.objects.all()
    connections = DeviceConnection.objects.all()
    
    critical_scenarios = [
        {
            'error_type': 'system_error',
            'severity': 'critical',
            'error_message': 'Application server crashed - out of memory',
            'url': '/system/status/',
            'request_method': 'GET',
            'user_action': 'Check system status',
            'file_name': 'system_monitor.py',
            'function_name': 'check_system_health'
        },
        {
            'error_type': 'database_error',
            'severity': 'critical',
            'error_message': 'Primary database server is down',
            'url': '/orders/list/',
            'request_method': 'GET',
            'user_action': 'Load orders list',
            'file_name': 'database_connection.py',
            'function_name': 'connect_primary_db'
        },
        {
            'error_type': 'payment_error',
            'severity': 'critical',
            'error_message': 'Payment gateway security breach detected',
            'url': '/payment/process/',
            'request_method': 'POST',
            'user_action': 'Process payment transaction',
            'file_name': 'payment_security.py',
            'function_name': 'validate_transaction'
        }
    ]
    
    created_critical = 0
    
    for scenario in critical_scenarios:
        try:
            user = random.choice(list(users))
            connection = random.choice(list(connections)) if connections.exists() else None
            
            error = ErrorLog.objects.create(
                error_type=scenario['error_type'],
                severity=scenario['severity'],
                error_message=scenario['error_message'],
                user=user,
                device_connection=connection,
                url=scenario['url'],
                request_method=scenario['request_method'],
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                ip_address=f"192.168.1.{random.randint(100, 255)}",
                stack_trace=f"Critical error at {scenario['file_name']} line {random.randint(1, 1000)}",
                line_number=random.randint(1, 1000),
                file_name=scenario['file_name'],
                function_name=scenario.get('function_name', ''),
                user_action=scenario['user_action'],
                form_data={'critical': True, 'escalation_required': True},
                created_at=timezone.now() - timedelta(minutes=random.randint(5, 60))
            )
            
            created_critical += 1
            print(f"Created critical error: {scenario['error_type']} - {scenario['error_message'][:40]}...")
            
        except Exception as e:
            print(f"Error creating critical error: {e}")
    
    return created_critical

def main():
    """Main function"""
    print("Creating error patterns and test data...")
    print("=" * 50)
    
    # Create error patterns
    print("\n1. Creating error patterns...")
    patterns = create_error_patterns()
    
    # Create resolved errors
    print("\n2. Creating resolved errors...")
    resolved = create_resolved_errors()
    
    # Create critical errors
    print("\n3. Creating critical errors...")
    critical = create_critical_errors()
    
    print("\n" + "=" * 50)
    print("ERROR PATTERN CREATION COMPLETE")
    print("=" * 50)
    print(f"Error patterns created: {len(patterns)}")
    print(f"Errors resolved: {resolved}")
    print(f"Critical errors created: {critical}")
    
    # Show final statistics
    from django.db.models import Count
    total_errors = ErrorLog.objects.count()
    unresolved_errors = ErrorLog.objects.filter(is_resolved=False).count()
    resolved_errors = ErrorLog.objects.filter(is_resolved=True).count()
    
    print(f"\nFinal Statistics:")
    print(f"Total errors in system: {total_errors}")
    print(f"Unresolved errors: {unresolved_errors}")
    print(f"Resolved errors: {resolved_errors}")
    
    print("\nError breakdown by type:")
    error_stats = ErrorLog.objects.values('error_type').annotate(count=Count('id')).order_by('-count')
    
    for stat in error_stats[:10]:  # Top 10
        print(f"  {stat['error_type']}: {stat['count']}")
    
    print("\nError breakdown by severity:")
    severity_stats = ErrorLog.objects.values('severity').annotate(count=Count('id')).order_by('severity')
    
    for stat in severity_stats:
        print(f"  {stat['severity']}: {stat['count']}")
    
    print("\nYou can now test the following features:")
    print("- Error Patterns: /error-patterns/ (shows recurring errors)")
    print("- Error Resolution: /error-tracking/ (resolve/unresolve errors)")
    print("- Critical Error Escalation: /automated-issues/ (shows critical issues)")

if __name__ == '__main__':
    main()
