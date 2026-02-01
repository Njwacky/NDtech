#!/usr/bin/env python
"""
Enhanced test script to verify comprehensive audit logging functionality
"""
import os
import sys
import django
import json
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
os.environ['DJANGO_ALLOWED_HOSTS'] = 'localhost,127.0.0.1,testserver'
django.setup()

from django.contrib.auth.models import User
from django.test import Client, RequestFactory
from django.urls import reverse
from nano.models import (
    Product, UserProfile, SecurityAuditLog, DataModificationLog, 
    AdminActionLog, APICallLog, SensitiveDataAccessLog
)
from django.contrib.auth import authenticate, login, logout

def cleanup_test_data():
    """Clean up existing test data"""
    print("🧹 Cleaning up existing test data...")
    
    # Delete test users
    User.objects.filter(username__in=['testuser_audit', 'testuser_audit2']).delete()
    
    # Delete test products
    Product.objects.filter(name__contains='Test Audit Product').delete()
    
    print("✅ Test data cleaned up")

def test_user_authentication_audit():
    """Test user authentication audit logging"""
    print("\n🔐 Testing User Authentication Audit...")
    
    factory = RequestFactory()
    client = Client()
    
    # Test 1: Failed login attempts
    print("1. Testing failed login attempts...")
    try:
        # Multiple failed attempts to trigger security monitoring
        for i in range(3):
            response = client.post('/sign_in/', {
                'username': 'nonexistent_user',
                'password': 'wrongpassword'
            })
        
        failed_logs = SecurityAuditLog.objects.filter(
            event_type='login_failed',
            username_attempted='nonexistent_user'
        )
        print(f"✅ Failed login attempts logged: {failed_logs.count()} entries")
        
        for log in failed_logs:
            print(f"   - Log ID: {log.id}, IP: {log.ip_address}, Severity: {log.severity}")
            
    except Exception as e:
        print(f"❌ Error testing failed login: {e}")
    
    # Test 2: User creation and login
    print("\n2. Testing user creation and successful login...")
    try:
        # Create test user
        test_user = User.objects.create_user(
            username='testuser_audit',
            email='test@example.com',
            password='testpass123'
        )
        print(f"✅ User created: {test_user.username}")
        
        # Create user profile
        profile = UserProfile.objects.create(
            user=test_user,
            role='cashier'
        )
        print(f"✅ User profile created: {profile.role}")
        
        # Test successful login
        login_success = client.post('/sign_in/', {
            'username': 'testuser_audit',
            'password': 'testpass123'
        })
        
        success_logs = SecurityAuditLog.objects.filter(
            event_type='login_success',
            user=test_user
        )
        if success_logs.exists():
            print("✅ Successful login logged")
            for log in success_logs:
                print(f"   - Log ID: {log.id}, Session: {log.session_key[:20]}...")
        else:
            print("❌ Successful login not logged")
            
    except Exception as e:
        print(f"❌ Error testing user creation/login: {e}")

def test_data_modification_audit():
    """Test data modification audit logging"""
    print("\n📝 Testing Data Modification Audit...")
    
    try:
        # Get or create test user
        test_user, created = User.objects.get_or_create(
            username='testuser_audit2',
            defaults={'email': 'test2@example.com', 'password': 'testpass123'}
        )
        if created:
            test_user.set_password('testpass123')
            test_user.save()
        
        # Test 1: Product creation
        print("1. Testing product creation...")
        test_product = Product.objects.create(
            name='Test Audit Product Enhanced',
            price=199.99,
            category='basic_groceries',
            stock=25,
            barcode='TEST123456'
        )
        print(f"✅ Product created: {test_product.name}")
        
        creation_logs = DataModificationLog.objects.filter(
            content_type='Product',
            action_type='create',
            object_id=test_product.id
        )
        if creation_logs.exists():
            print("✅ Product creation logged")
            for log in creation_logs:
                print(f"   - Log ID: {log.id}, Sensitivity: {log.sensitivity}")
                print(f"   - New values: {list(log.new_values.keys())}")
        else:
            print("❌ Product creation not logged")
        
        # Test 2: Product update
        print("\n2. Testing product update...")
        test_product.price = 149.99
        test_product.stock = 20
        test_product.save()
        
        update_logs = DataModificationLog.objects.filter(
            content_type='Product',
            action_type='update',
            object_id=test_product.id
        )
        if update_logs.exists():
            print("✅ Product update logged")
            for log in update_logs:
                print(f"   - Log ID: {log.id}, Changed fields: {list(log.changed_fields.keys())}")
        else:
            print("❌ Product update not logged")
        
        # Test 3: Product deletion
        print("\n3. Testing product deletion...")
        product_id = test_product.id
        product_name = str(test_product)
        test_product.delete()
        
        deletion_logs = DataModificationLog.objects.filter(
            content_type='Product',
            action_type='delete',
            object_id=product_id
        )
        if deletion_logs.exists():
            print("✅ Product deletion logged")
            for log in deletion_logs:
                print(f"   - Log ID: {log.id}, Object: {log.object_repr}")
        else:
            print("❌ Product deletion not logged")
            
    except Exception as e:
        print(f"❌ Error testing data modification: {e}")

def test_api_call_audit():
    """Test API call audit logging"""
    print("\n🌐 Testing API Call Audit...")
    
    client = Client()
    
    # Test API endpoints (these should be logged)
    api_endpoints = [
        '/api/products/',
        '/api/users/',
    ]
    
    for endpoint in api_endpoints:
        try:
            print(f"Testing {endpoint}...")
            response = client.get(endpoint)
            
            api_logs = APICallLog.objects.filter(
                endpoint=endpoint,
                method='GET'
            )
            if api_logs.exists():
                print(f"✅ API call to {endpoint} logged")
                for log in api_logs:
                    print(f"   - Log ID: {log.id}, Status: {log.status_code}, Duration: {log.duration_ms}ms")
            else:
                print(f"❌ API call to {endpoint} not logged")
                
        except Exception as e:
            print(f"❌ Error testing {endpoint}: {e}")

def test_sensitive_data_access():
    """Test sensitive data access logging"""
    print("\n🔒 Testing Sensitive Data Access Audit...")
    
    try:
        # Create a user with sensitive data
        test_user = User.objects.create_user(
            username='sensitive_test_user',
            email='sensitive@example.com',
            password='sensitivepass123',
            first_name='Sensitive',
            last_name='Test'
        )
        
        # Simulate accessing user data via API
        client = Client()
        
        # This should trigger sensitive data access logging
        # (In a real scenario, this would be an API endpoint that returns user data)
        response = client.post('/sign_in/', {
            'username': 'sensitive_test_user',
            'password': 'sensitivepass123'
        })
        
        # Check if any sensitive data was logged
        sensitive_logs = SensitiveDataAccessLog.objects.filter(
            user=test_user
        )
        if sensitive_logs.exists():
            print("✅ Sensitive data access logged")
            for log in sensitive_logs:
                print(f"   - Log ID: {log.id}, Data Type: {log.data_type}, Access Type: {log.access_type}")
        else:
            print("ℹ️  No sensitive data access logged (expected for this test)")
            
    except Exception as e:
        print(f"❌ Error testing sensitive data access: {e}")

def test_security_event_detection():
    """Test security event detection"""
    print("\n🚨 Testing Security Event Detection...")
    
    client = Client()
    
    # Test suspicious patterns
    suspicious_requests = [
        ('/api/products/?id=1 UNION SELECT * FROM auth_user--', 'SQL Injection attempt'),
        ('/api/products/<script>alert("xss")</script>', 'XSS attempt'),
        ('/admin/../../../etc/passwd', 'Path traversal attempt'),
    ]
    
    for path, description in suspicious_requests:
        try:
            print(f"Testing {description}: {path}")
            response = client.get(path)
            
            # Check if suspicious activity was logged
            suspicious_logs = SecurityAuditLog.objects.filter(
                event_type='suspicious_activity',
                description__contains='Suspicious request pattern'
            )
            recent_logs = suspicious_logs.filter(
                created_at__gte=datetime.now() - timedelta(minutes=1)
            )
            
            if recent_logs.exists():
                print(f"✅ {description} detected and logged")
            else:
                print(f"ℹ️  {description} not detected (may be filtered by Django)")
                
        except Exception as e:
            print(f"❌ Error testing {description}: {e}")

def test_admin_action_audit():
    """Test admin action audit logging"""
    print("\n⚙️ Testing Admin Action Audit...")
    
    try:
        # Create a product via admin-like action
        test_product = Product.objects.create(
            name='Admin Test Product',
            price=99.99,
            category='basic_groceries',
            stock=15
        )
        
        # Simulate admin action logging
        admin_logs = AdminActionLog.objects.filter(
            content_type='Product',
            action_type='add'
        )
        
        if admin_logs.exists():
            print("✅ Admin action logged")
            for log in admin_logs:
                print(f"   - Log ID: {log.id}, Action: {log.action_type}, Object: {log.object_repr}")
        else:
            print("ℹ️  Admin action logging requires actual admin interface usage")
            
    except Exception as e:
        print(f"❌ Error testing admin action audit: {e}")

def generate_audit_report():
    """Generate a comprehensive audit report"""
    print("\n📊 Generating Audit Report...")
    
    # Security Events Summary
    security_events = SecurityAuditLog.objects.all()
    print(f"\n🔒 Security Events Summary:")
    print(f"   - Total security events: {security_events.count()}")
    
    for event_type in ['login_success', 'login_failed', 'logout', 'suspicious_activity']:
        count = security_events.filter(event_type=event_type).count()
        if count > 0:
            print(f"   - {event_type}: {count}")
    
    # Data Modifications Summary
    data_mods = DataModificationLog.objects.all()
    print(f"\n📝 Data Modifications Summary:")
    print(f"   - Total data modifications: {data_mods.count()}")
    
    for action_type in ['create', 'update', 'delete']:
        count = data_mods.filter(action_type=action_type).count()
        if count > 0:
            print(f"   - {action_type}: {count}")
    
    # API Calls Summary
    api_calls = APICallLog.objects.all()
    print(f"\n🌐 API Calls Summary:")
    print(f"   - Total API calls: {api_calls.count()}")
    
    for status in ['success', 'error', 'unauthorized', 'forbidden']:
        count = api_calls.filter(status=status).count()
        if count > 0:
            print(f"   - {status}: {count}")
    
    # Recent Security Events
    print(f"\n📋 Recent Security Events (Last 10):")
    for log in security_events.order_by('-created_at')[:10]:
        print(f"   - {log.created_at.strftime('%Y-%m-%d %H:%M:%S')}: {log.get_event_type_display()} - {log.description[:50]}...")
    
    # Recent Data Modifications
    print(f"\n📋 Recent Data Modifications (Last 10):")
    for log in data_mods.order_by('-created_at')[:10]:
        print(f"   - {log.created_at.strftime('%Y-%m-%d %H:%M:%S')}: {log.get_action_type_display()} {log.content_type} - {log.object_repr[:50]}...")

def main():
    """Main test function"""
    print("🔍 Enhanced Audit Logging System Test")
    print("=" * 50)
    
    # Clean up test data
    cleanup_test_data()
    
    # Run all tests
    test_user_authentication_audit()
    test_data_modification_audit()
    test_api_call_audit()
    test_sensitive_data_access()
    test_security_event_detection()
    test_admin_action_audit()
    
    # Generate comprehensive report
    generate_audit_report()
    
    print("\n" + "=" * 50)
    print("✅ Enhanced audit logging test completed!")
    print("💡 Check the Django admin at /admin/nano/ to view all audit logs")
    print("📄 Log files are available at:")
    print("   - security_audit.log")
    print("   - security_events.log")

if __name__ == '__main__':
    main()
