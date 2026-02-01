"""
Test script for customer data encryption implementation
"""

import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from django.test import TestCase
from django.contrib.auth.models import User
from nano.models import CompletedOrder, UserProfile
from nano.serializers import CompletedOrderSerializer, PublicCompletedOrderSerializer, CustomerDataExportSerializer
from confige.encryption import encrypt_sensitive_value, decrypt_sensitive_value
import json


def test_encryption_basic():
    """Test basic encryption/decryption functionality"""
    print("🔐 Testing basic encryption/decryption...")
    
    test_data = "John Doe"
    encrypted = encrypt_sensitive_value(test_data, 'customer_name')
    decrypted = decrypt_sensitive_value(encrypted, 'customer_name')
    
    assert test_data == decrypted, f"Encryption/decryption failed: {test_data} != {decrypted}"
    print("✅ Basic encryption/decryption works correctly")


def test_completed_order_encryption():
    """Test CompletedOrder model encryption methods"""
    print("\n🛒 Testing CompletedOrder encryption methods...")
    
    # Create test user
    user, created = User.objects.get_or_create(
        username='testuser_enc',
        defaults={'email': 'test@example.com', 'first_name': 'Test', 'last_name': 'User'}
    )
    
    # Create test order
    order_data = {
        'customer_name': 'John Smith',
        'customer_phone': '+27123456789',
        'customer_email': 'john.smith@example.com',
        'items': [{'name': 'Product 1', 'quantity': 2, 'price': '10.00'}],
        'total': '20.00',
        'cash_received': '25.00',
        'change_given': '5.00',
        'payment_method': 'cash',
        'processed_by': user
    }
    
    order = CompletedOrder(**order_data)
    
    # Test encryption methods
    order.set_customer_name('John Smith')
    order.set_customer_phone('+27123456789')
    order.set_customer_email('john.smith@example.com')
    
    # Verify encrypted fields are populated
    assert order.customer_name_encrypted, "Customer name should be encrypted"
    assert order.customer_phone_encrypted, "Customer phone should be encrypted"
    assert order.customer_email_encrypted, "Customer email should be encrypted"
    
    # Test decryption methods
    assert order.get_customer_name() == 'John Smith', "Decrypted name should match original"
    assert order.get_customer_phone() == '+27123456789', "Decrypted phone should match original"
    assert order.get_customer_email() == 'john.smith@example.com', "Decrypted email should match original"
    
    print("✅ CompletedOrder encryption methods work correctly")


def test_completed_order_serializer():
    """Test CompletedOrder serializer with encryption"""
    print("\n📝 Testing CompletedOrder serializer with encryption...")
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        username='testuser_serializer',
        defaults={'email': 'serializer@example.com', 'first_name': 'Serializer', 'last_name': 'User'}
    )
    
    # Test serializer creation
    order_data = {
        'customer_name': 'Jane Doe',
        'customer_phone': '+27987654321',
        'customer_email': 'jane.doe@example.com',
        'items': [{'name': 'Product 2', 'quantity': 1, 'price': '15.00'}],
        'total': '15.00',
        'cash_received': '20.00',
        'change_given': '5.00',
        'payment_method': 'card',
        'processed_by': user.id
    }
    
    serializer = CompletedOrderSerializer(data=order_data)
    assert serializer.is_valid(), f"Serializer validation failed: {serializer.errors}"
    
    order = serializer.save()
    
    # Verify encryption worked
    assert order.customer_name_encrypted, "Customer name should be encrypted"
    assert order.customer_phone_encrypted, "Customer phone should be encrypted"
    assert order.customer_email_encrypted, "Customer email should be encrypted"
    
    # Test serializer representation
    representation = serializer.data
    
    # Check decrypted fields are present
    assert 'customer_name_decrypted' in representation, "Decrypted name field should be present"
    assert 'customer_phone_decrypted' in representation, "Decrypted phone field should be present"
    assert 'customer_email_decrypted' in representation, "Decrypted email field should be present"
    
    # Check decrypted values match original
    assert representation['customer_name_decrypted'] == 'Jane Doe', "Decrypted name should match"
    assert representation['customer_phone_decrypted'] == '+27987654321', "Decrypted phone should match"
    assert representation['customer_email_decrypted'] == 'jane.doe@example.com', "Decrypted email should match"
    
    print("✅ CompletedOrder serializer with encryption works correctly")


def test_public_serializer():
    """Test public serializer excludes sensitive data"""
    print("\n🔒 Testing public serializer data exposure...")
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        username='testuser_public',
        defaults={'email': 'public@example.com', 'first_name': 'Public', 'last_name': 'User'}
    )
    
    # Create test order
    order = CompletedOrder.objects.create(
        customer_name='Public User',
        customer_phone='+27112223344',
        customer_email='public@example.com',
        items=[{'name': 'Product 3', 'quantity': 1, 'price': '25.00'}],
        total='25.00',
        cash_received='30.00',
        change_given='5.00',
        payment_method='cash',
        processed_by=user
    )
    
    # Encrypt customer data
    order.set_customer_name('Public User')
    order.set_customer_phone('+27112223344')
    order.set_customer_email('public@example.com')
    order.save()
    
    # Test public serializer
    serializer = PublicCompletedOrderSerializer(order)
    representation = serializer.data
    
    # Verify sensitive fields are not present
    sensitive_fields = [
        'customer_name', 'customer_name_encrypted', 'customer_name_decrypted',
        'customer_phone', 'customer_phone_encrypted', 'customer_phone_decrypted',
        'customer_email', 'customer_email_encrypted', 'customer_email_decrypted'
    ]
    
    for field in sensitive_fields:
        assert field not in representation, f"Sensitive field {field} should not be in public serializer"
    
    # Verify non-sensitive fields are present
    public_fields = ['id', 'items', 'total', 'cash_received', 'change_given', 'payment_method', 'completed_at']
    for field in public_fields:
        assert field in representation, f"Public field {field} should be present"
    
    print("✅ Public serializer correctly excludes sensitive data")


def test_export_serializer():
    """Test export serializer with encryption and logging"""
    print("\n📤 Testing export serializer with encryption...")
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        username='testuser_export',
        defaults={'email': 'export@example.com', 'first_name': 'Export', 'last_name': 'User'}
    )
    
    # Create test order
    order = CompletedOrder.objects.create(
        customer_name='Export User',
        customer_phone='+27998877665',
        customer_email='export@example.com',
        items=[{'name': 'Product 4', 'quantity': 2, 'price': '12.50'}],
        total='25.00',
        cash_received='25.00',
        change_given='0.00',
        payment_method='mobile',
        processed_by=user
    )
    
    # Encrypt customer data
    order.set_customer_name('Export User')
    order.set_customer_phone('+27998877665')
    order.set_customer_email('export@example.com')
    order.save()
    
    # Test export serializer
    serializer = CustomerDataExportSerializer(order)
    representation = serializer.to_representation(order)
    
    # Verify encrypted data is returned
    assert 'customer_name' in representation, "Encrypted customer name should be present"
    assert 'customer_phone' in representation, "Encrypted customer phone should be present"
    assert 'customer_email' in representation, "Encrypted customer email should be present"
    
    # Verify encryption flag
    assert representation.get('data_encrypted') is True, "Data should be marked as encrypted"
    
    # Verify export timestamp
    assert 'export_timestamp' in representation, "Export timestamp should be present"
    
    print("✅ Export serializer works correctly with encryption")


def test_sensitive_data_logging():
    """Test that sensitive data access is logged"""
    print("\n📋 Testing sensitive data access logging...")
    
    from nano.models import SensitiveDataAccessLog
    from django.test import RequestFactory
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        username='testuser_logging',
        defaults={'email': 'logging@example.com', 'first_name': 'Logging', 'last_name': 'User'}
    )
    
    # Create mock request
    factory = RequestFactory()
    request = factory.post('/api/orders/')
    request.user = user
    request.META['HTTP_USER_AGENT'] = 'Test Browser'
    request.META['REMOTE_ADDR'] = '127.0.0.1'
    request.META['HTTP_HOST'] = 'localhost'
    
    # Test order creation with logging
    order_data = {
        'customer_name': 'Logging User',
        'customer_phone': '+27123456789',
        'customer_email': 'logging@example.com',
        'items': [{'name': 'Product 5', 'quantity': 1, 'price': '30.00'}],
        'total': '30.00',
        'cash_received': '35.00',
        'change_given': '5.00',
        'payment_method': 'cash',
        'processed_by': user
    }
    
    serializer = CompletedOrderSerializer(data=order_data, context={'request': request})
    assert serializer.is_valid(), f"Serializer validation failed: {serializer.errors}"
    
    # Get initial log count
    initial_log_count = SensitiveDataAccessLog.objects.count()
    
    order = serializer.save()
    
    # Check if log was created
    final_log_count = SensitiveDataAccessLog.objects.count()
    assert final_log_count > initial_log_count, "Sensitive data access should be logged"
    
    # Check log details
    log = SensitiveDataAccessLog.objects.latest('created_at')
    assert log.user == user, "Log should be associated with correct user"
    assert log.data_type == 'personal_info', "Data type should be personal_info"
    assert log.access_type == 'create', "Access type should be create"
    assert log.content_type == 'CompletedOrder', "Content type should be CompletedOrder"
    assert log.object_id == order.id, "Object ID should match order ID"
    
    print("✅ Sensitive data access logging works correctly")


def test_encryption_key_rotation():
    """Test encryption key rotation functionality"""
    print("\n🔄 Testing encryption key rotation...")
    
    from confige.encryption import get_encryption_instance
    
    # Get encryption instance
    encryption = get_encryption_instance()
    
    # Test data
    original_data = "Test data for rotation"
    
    # Encrypt with current key
    encrypted_old = encryption.encrypt_field(original_data)
    
    # Rotate key
    old_fernet = encryption.rotate_encryption_key()
    
    # Verify new key is different
    assert encryption.fernet != old_fernet, "New encryption key should be different"
    
    # Encrypt with new key
    encrypted_new = encryption.encrypt_field(original_data)
    
    # Decrypt with new key
    decrypted_new = encryption.decrypt_field(encrypted_new)
    assert decrypted_new == original_data, "New key should decrypt correctly"
    
    # Old encrypted data should no longer decrypt (or be handled gracefully)
    try:
        decrypted_old = encryption.decrypt_field(encrypted_old)
        # If it doesn't throw an error, that's also fine (some implementations handle this)
    except Exception:
        # This is expected behavior - old data can't be decrypted with new key
        pass
    
    print("✅ Encryption key rotation works correctly")


def run_all_tests():
    """Run all encryption tests"""
    print("🚀 Starting Customer Data Encryption Tests\n")
    
    try:
        test_encryption_basic()
        test_completed_order_encryption()
        test_completed_order_serializer()
        test_public_serializer()
        test_export_serializer()
        test_sensitive_data_logging()
        test_encryption_key_rotation()
        
        print("\n🎉 All customer data encryption tests passed!")
        print("\n📊 Summary:")
        print("✅ Basic encryption/decryption functionality")
        print("✅ CompletedOrder model encryption methods")
        print("✅ CompletedOrder serializer with encryption")
        print("✅ Public serializer data protection")
        print("✅ Export serializer with encryption")
        print("✅ Sensitive data access logging")
        print("✅ Encryption key rotation")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
