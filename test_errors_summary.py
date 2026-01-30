#!/usr/bin/env python
"""
Summary script for NDtechTrack test errors.
This script provides a comprehensive overview of all test errors created
and generates a testing guide for the error tracking system.
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from django.contrib.auth.models import User
from nano.models import ErrorLog, DeviceConnection, UserActivity, Notification
from django.db.models import Count, Q
from django.utils import timezone

def generate_test_summary():
    """Generate comprehensive test summary"""
    
    print("NDTECHTRACK ERROR TRACKING TEST SUMMARY")
    print("=" * 60)
    
    # User Statistics
    total_users = User.objects.count()
    admin_users = User.objects.filter(Q(is_superuser=True) | Q(userprofile__role__in=['admin', 'manager'])).count()
    
    print(f"\n👥 USERS:")
    print(f"   Total Users: {total_users}")
    print(f"   Admin/Manager Users: {admin_users}")
    print(f"   Test Users Created: test_admin, test_manager, test_cashier, test_user1, test_user2")
    
    # Device Connections
    total_connections = DeviceConnection.objects.count()
    active_connections = DeviceConnection.objects.filter(is_active=True).count()
    
    print(f"\n📱 DEVICE CONNECTIONS:")
    print(f"   Total Connections: {total_connections}")
    print(f"   Active Connections: {active_connections}")
    
    # Error Statistics
    total_errors = ErrorLog.objects.count()
    unresolved_errors = ErrorLog.objects.filter(is_resolved=False).count()
    resolved_errors = ErrorLog.objects.filter(is_resolved=True).count()
    
    print(f"\n🚨 ERROR LOGS:")
    print(f"   Total Errors: {total_errors}")
    print(f"   Unresolved Errors: {unresolved_errors}")
    print(f"   Resolved Errors: {resolved_errors}")
    print(f"   Resolution Rate: {(resolved_errors/total_errors*100):.1f}%")
    
    # Error Breakdown by Type
    print(f"\n📊 ERROR BREAKDOWN BY TYPE:")
    error_types = ErrorLog.objects.values('error_type').annotate(
        count=Count('id'),
        unresolved=Count('id', filter=Q(is_resolved=False))
    ).order_by('-count')
    
    for stat in error_types:
        percentage = (stat['count'] / total_errors) * 100
        print(f"   {stat['error_type']:15} {stat['count']:3} ({percentage:5.1f}%) - Unresolved: {stat['unresolved']}")
    
    # Error Breakdown by Severity
    print(f"\n⚠️  ERROR BREAKDOWN BY SEVERITY:")
    severity_stats = ErrorLog.objects.values('severity').annotate(
        count=Count('id'),
        unresolved=Count('id', filter=Q(is_resolved=False))
    ).order_by('-count')
    
    for stat in severity_stats:
        percentage = (stat['count'] / total_errors) * 100
        print(f"   {stat['severity']:8} {stat['count']:3} ({percentage:5.1f}%) - Unresolved: {stat['unresolved']}")
    
    # User Activities
    total_activities = UserActivity.objects.count()
    
    print(f"\n📈 USER ACTIVITIES:")
    print(f"   Total Activities: {total_activities}")
    
    # Automated Issues
    total_issues = Notification.objects.filter(notification_type='system_alert').count()
    
    print(f"\n🔔 AUTOMATED ISSUES:")
    print(f"   Total System Alerts: {total_issues}")
    
    # Recent Critical Errors (last 24 hours)
    recent_critical = ErrorLog.objects.filter(
        severity='critical',
        created_at__gte=timezone.now() - timezone.timedelta(hours=24)
    ).count()
    
    print(f"\n🚨 CRITICAL ERRORS (Last 24 Hours): {recent_critical}")
    
    # Top Error Sources
    print(f"\n🌐 TOP ERROR SOURCES (URLs):")
    url_errors = ErrorLog.objects.values('url').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    for stat in url_errors:
        print(f"   {stat['url']:40} {stat['count']}")
    
    # Top Users with Errors
    print(f"\n👥 USERS WITH MOST ERRORS:")
    user_errors = ErrorLog.objects.values('user__username').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    for stat in user_errors:
        print(f"   {stat['user__username']:15} {stat['count']} errors")

def generate_testing_guide():
    """Generate testing guide for the error tracking system"""
    
    print(f"\n" + "=" * 60)
    print("🧪 TESTING GUIDE FOR NDTECHTRACK ERROR TRACKING")
    print("=" * 60)
    
    print(f"\n📋 TEST SCENARIOS CREATED:")
    print("1. USER ERRORS:")
    print("   • Invalid barcode scanning attempts")
    print("   • Checkout with insufficient stock")
    print("   • Unauthorized access attempts")
    print("   • Invalid discount codes")
    print("   • Empty cart checkout attempts")
    
    print("\n2. SYSTEM ERRORS:")
    print("   • Database connection timeouts")
    print("   • Memory exhaustion during imports")
    print("   • Application server crashes")
    print("   • Database deadlocks")
    
    print("\n3. VALIDATION ERRORS:")
    print("   • Invalid email formats")
    print("   • Negative product prices")
    print("   • Invalid phone numbers")
    print("   • Missing required fields")
    
    print("\n4. PERMISSION ERRORS:")
    print("   • Cashier accessing admin features")
    print("   • Unauthorized user deletion attempts")
    print("   • Access to restricted financial reports")
    
    print("\n5. API ERRORS:")
    print("   • Payment gateway timeouts")
    print("   • Third-party service failures")
    print("   • Rate limit exceeded")
    print("   • Inventory sync failures")
    
    print("\n6. NETWORK ERRORS:")
    print("   • Email server connection failures")
    print("   • CDN timeout issues")
    print("   • Backup server failures")
    print("   • External service timeouts")
    
    print("\n7. PAYMENT ERRORS:")
    print("   • Insufficient funds declines")
    print("   • Expired credit cards")
    print("   • Fraud detection triggers")
    print("   • Gateway configuration errors")
    
    print("\n8. DATABASE ERRORS:")
    print("   • Connection pool exhaustion")
    print("   • Deadlock situations")
    print("   • Server unavailability")
    
    print(f"\n🔍 TESTING FEATURES:")
    print("\n1. ERROR TRACKING (/error-tracking/):")
    print("   • Filter by error type (user_error, system_error, etc.)")
    print("   • Filter by severity (low, medium, high, critical)")
    print("   • Search by error message or URL")
    print("   • Date range filtering")
    print("   • Resolve/unresolve errors")
    print("   • View error details and stack traces")
    
    print("\n2. DEVICE TRACKING (/device-tracking/):")
    print("   • View active/inactive device connections")
    print("   • Filter by device type (web, mobile, etc.)")
    print("   • Search by user or IP address")
    print("   • View session durations and activity")
    print("   • Geographic location tracking")
    
    print("\n3. USER ACTIVITY TRACKING (/user-activity-tracking/):")
    print("   • Track user actions (login, checkout, etc.)")
    print("   • Filter by activity type")
    print("   • Monitor page views and navigation patterns")
    print("   • Track session durations and user engagement")
    
    print("\n4. AUTOMATED ISSUES (/automated-issues/):")
    print("   • View system-generated alerts")
    print("   • Monitor critical infrastructure issues")
    print("   • Track security alerts and performance warnings")
    print("   • Escalate and resolve automated issues")
    
    print("\n5. ERROR PATTERNS (/error-patterns/):")
    print("   • Identify recurring error patterns")
    print("   • Track error frequency by user/system")
    print("   • Monitor error trends over time")
    print("   • Activate/deactivate error pattern tracking")
    
    print("\n6. SYSTEM PERFORMANCE (/system-performance/):")
    print("   • Monitor database health metrics")
    print("   • Track API response times")
    print("   • View server uptime statistics")
    print("   • Analyze system resource utilization")
    
    print(f"\n🔧 TEST INSTRUCTIONS:")
    print("\n1. LOGIN AS TEST USER:")
    print("   • Username: test_admin (password: test123)")
    print("   • Username: test_manager (password: test123)")
    print("   • Username: test_cashier (password: test123)")
    
    print("\n2. NAVIGATE TO ERROR TRACKING PAGES:")
    print("   • Access the URLs listed above")
    print("   • Test filtering and search functionality")
    print("   • Try resolving and unresolving errors")
    print("   • Test error pattern detection")
    
    print("\n3. GENERATE NEW ERRORS:")
    print("   • Use invalid barcodes, negative prices, etc.")
    print("   • Attempt unauthorized actions")
    print("   • Test form validation with invalid data")
    print("   • Simulate network timeouts and failures")
    
    print("\n4. TEST RESOLUTION WORKFLOW:")
    print("   • Mark errors as resolved/unresolved")
    print("   • Add resolution notes")
    print("   • Test error pattern detection")
    print("   • Verify automated issue creation")

def main():
    """Main function to generate summary and guide"""
    generate_test_summary()
    generate_testing_guide()
    
    print(f"\n" + "=" * 60)
    print("✅ TEST ENVIRONMENT READY")
    print("=" * 60)
    print("The NDtechTrack error tracking system now has comprehensive test data.")
    print("Use the guide above to test all features and functionality.")

if __name__ == '__main__':
    main()
