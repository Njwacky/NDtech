#!/usr/bin/env python
"""
Test script to verify audit logging is working
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
os.environ['DJANGO_ALLOWED_HOSTS'] = 'localhost,127.0.0.1,testserver'
django.setup()

from django.contrib.auth.models import User
from nano.models import Product, SecurityAuditLog, DataModificationLog
from django.test import Client

def test_audit_logging():
    """Test that audit logging is working"""
    print("🔍 Testing Audit Logging System...")
    
    # Test 1: Create a test user
    print("\n1. Testing user creation...")
    try:
        test_user = User.objects.create_user(
            username='testuser_audit',
            email='test@example.com',
            password='testpass123'
        )
        print(f"✅ User created: {test_user.username}")
        
        # Check if creation was logged
        logs = DataModificationLog.objects.filter(
            content_type='User',
            action_type='create',
            user=test_user
        )
        if logs.exists():
            print("✅ User creation logged successfully")
            for log in logs:
                print(f"   - Log ID: {log.id}, Action: {log.action_type}, Sensitivity: {log.sensitivity}")
        else:
            print("❌ User creation not logged")
            
    except Exception as e:
        print(f"❌ Error creating user: {e}")
    
    # Test 2: Update the user
    print("\n2. Testing user update...")
    try:
        test_user.email = 'updated@example.com'
        test_user.save()
        print(f"✅ User updated: {test_user.email}")
        
        # Check if update was logged
        logs = DataModificationLog.objects.filter(
            content_type='User',
            action_type='update',
            user=test_user
        )
        if logs.exists():
            print("✅ User update logged successfully")
            for log in logs:
                print(f"   - Log ID: {log.id}, Changed fields: {list(log.changed_fields.keys())}")
        else:
            print("❌ User update not logged")
            
    except Exception as e:
        print(f"❌ Error updating user: {e}")
    
    # Test 3: Create a product
    print("\n3. Testing product creation...")
    try:
        test_product = Product.objects.create(
            name='Test Audit Product',
            price=99.99,
            category='basic_groceries',
            stock=10
        )
        print(f"✅ Product created: {test_product.name}")
        
        # Check if creation was logged
        logs = DataModificationLog.objects.filter(
            content_type='Product',
            action_type='create'
        )
        if logs.exists():
            print("✅ Product creation logged successfully")
            for log in logs:
                print(f"   - Log ID: {log.id}, Object: {log.object_repr}")
        else:
            print("❌ Product creation not logged")
            
    except Exception as e:
        print(f"❌ Error creating product: {e}")
    
    # Test 4: Test security event via HTTP request
    print("\n4. Testing security event logging...")
    try:
        client = Client()
        
        # Test failed login
        response = client.post('/sign_in/', {
            'username': 'nonexistent_user',
            'password': 'wrongpassword'
        })
        
        # Check if failed login was logged
        security_logs = SecurityAuditLog.objects.filter(
            event_type='login_failed'
        )
        if security_logs.exists():
            print("✅ Failed login logged successfully")
            for log in security_logs:
                print(f"   - Log ID: {log.id}, Username attempted: {log.username_attempted}")
        else:
            print("❌ Failed login not logged")
            
    except Exception as e:
        print(f"❌ Error testing security event: {e}")
    
    # Summary
    print("\n📊 Audit Logging Summary:")
    print(f"   - Total Security Logs: {SecurityAuditLog.objects.count()}")
    print(f"   - Total Data Modification Logs: {DataModificationLog.objects.count()}")
    
    # Show recent logs
    print("\n📋 Recent Security Logs:")
    for log in SecurityAuditLog.objects.all()[:5]:
        print(f"   - {log.created_at}: {log.get_event_type_display()} - {log.description[:50]}...")
    
    print("\n📋 Recent Data Modification Logs:")
    for log in DataModificationLog.objects.all()[:5]:
        print(f"   - {log.created_at}: {log.get_action_type_display()} {log.content_type}")
    
    print("\n✅ Audit logging test completed!")
    print("💡 Check the Django admin at /admin/nano/ to view all audit logs")

if __name__ == '__main__':
    test_audit_logging()
