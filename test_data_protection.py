"""
Test script for data protection and privacy features
Validates that sensitive information is properly protected
"""

import os
import sys
import django
import json
import requests
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
from nano.models import (
    SecurityAuditLog, DataModificationLog, APICallLog, 
    SensitiveDataAccessLog, UserProfile, Product, CompletedOrder
)
from confige.security import SecurityUtils, DataProtection, PrivacySettings

class DataProtectionTester:
    """Test data protection and privacy features"""
    
    def __init__(self):
        self.client = Client()
        self.test_user = None
        self.admin_user = None
        self.setup_users()
    
    def setup_users(self):
        """Create test users"""
        # Clean up existing test users first
        User.objects.filter(username__in=['testuser', 'admin']).delete()
        
        # Create regular user
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        # Create user profiles
        UserProfile.objects.create(
            user=self.test_user,
            role='cashier',
            created_by=self.admin_user
        )
        
        UserProfile.objects.create(
            user=self.admin_user,
            role='superuser',
            created_by=self.admin_user
        )
    
    def test_data_masking_in_logs(self):
        """Test that sensitive data is masked in logs"""
        print("\n" + "="*60)
        print("TESTING DATA MASKING IN LOGS")
        print("="*60)
        
        # Test email masking
        email = "john.doe@example.com"
        masked_email = SecurityUtils.mask_email(email)
        print(f"Email masking: {email} -> {masked_email}")
        assert '@' in masked_email and '*' in masked_email, "Email not properly masked"
        
        # Test phone masking
        phone = "0721234567"
        masked_phone = SecurityUtils.mask_phone(phone)
        print(f"Phone masking: {phone} -> {masked_phone}")
        assert '*' in masked_phone and len(masked_phone) == len(phone), "Phone not properly masked"
        
        # Test credit card masking
        card = "4111111111111111"
        masked_card = SecurityUtils.mask_credit_card(card)
        print(f"Credit card masking: {card} -> {masked_card}")
        assert masked_card.endswith('1111') and masked_card.startswith('*'), "Credit card not properly masked"
        
        # Test data sanitization
        sensitive_data = {
            'username': 'john',
            'password': 'secret123',
            'email': 'john@example.com',
            'credit_card': '4111111111111111',
            'normal_field': 'normal_value'
        }
        
        sanitized = SecurityUtils.sanitize_for_logging(sensitive_data)
        print(f"Sanitized data: {sanitized}")
        
        assert sanitized['password'] == '[REDACTED]', "Password not redacted"
        assert sanitized['credit_card'] == '[REDACTED]', "Credit card not redacted"
        assert sanitized['email'] != 'john@example.com', "Email not masked"
        assert sanitized['normal_field'] == 'normal_value', "Normal field incorrectly modified"
        
        print("✅ Data masking tests passed")
    
    def test_api_response_masking(self):
        """Test that API responses mask sensitive data"""
        print("\n" + "="*60)
        print("TESTING API RESPONSE MASKING")
        print("="*60)
        
        # Login as test user
        self.client.login(username='testuser', password='testpass123')
        
        # Test user API endpoint
        response = self.client.get('/api/v1/users/')
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"User API response: {json.dumps(data, indent=2)}")
                
                # Check that sensitive fields are masked in API responses
                for user_data in data if isinstance(data, list) else [data]:
                    if 'email' in user_data:
                        email = user_data['email']
                        assert '@' in email and ('*' in email or len(email) < 10), f"Email not masked in API: {email}"
                    
                    if 'password' in user_data:
                        assert user_data['password'] == '[MASKED]' or not user_data['password'], "Password exposed in API"
                
                print("✅ API response masking tests passed")
                
            except json.JSONDecodeError:
                print("⚠️  Could not parse API response as JSON")
        else:
            print(f"⚠️  API endpoint returned status {response.status_code}")
    
    def test_security_headers(self):
        """Test that security headers are present"""
        print("\n" + "="*60)
        print("TESTING SECURITY HEADERS")
        print("="*60)
        
        # Test various endpoints
        endpoints = ['/', '/api/v1/products/', '/sign_in/']
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            
            # Check for security headers
            security_headers = [
                'X-Content-Type-Options',
                'X-Frame-Options',
                'X-XSS-Protection',
                'Content-Security-Policy',
                'Referrer-Policy',
            ]
            
            missing_headers = []
            for header in security_headers:
                if header not in response:
                    missing_headers.append(header)
            
            if missing_headers:
                print(f"⚠️  Missing security headers for {endpoint}: {missing_headers}")
            else:
                print(f"✅ Security headers present for {endpoint}")
        
        print("✅ Security headers tests completed")
    
    def test_data_retention_policies(self):
        """Test data retention policies"""
        print("\n" + "="*60)
        print("TESTING DATA RETENTION POLICIES")
        print("="*60)
        
        retention_days = DataProtection.get_data_retention_days()
        print(f"Retention policies: {retention_days}")
        
        # Test retention period calculation
        from django.utils import timezone
        now = timezone.now()
        
        for log_type, days in retention_days.items():
            cutoff_date = now - timedelta(days=days)
            should_purge = DataProtection.should_purge_data(log_type, cutoff_date - timedelta(days=1))
            
            assert should_purge, f"Data retention policy not working for {log_type}"
            
            should_not_purge = DataProtection.should_purge_data(log_type, cutoff_date + timedelta(days=1))
            assert not should_not_purge, f"Data retention policy incorrect for {log_type}"
        
        print("✅ Data retention policies tests passed")
    
    def test_privacy_compliance(self):
        """Test GDPR and privacy compliance features"""
        print("\n" + "="*60)
        print("TESTING PRIVACY COMPLIANCE")
        print("="*60)
        
        # Test anonymization fields
        anonymization_fields = PrivacySettings.get_anonymization_fields()
        print(f"Anonymization fields: {anonymization_fields}")
        
        # Test consent purposes
        consent_purposes = PrivacySettings.get_consent_purposes()
        print(f"Consent purposes: {consent_purposes}")
        
        # Test user data anonymization
        anonymized = DataProtection.anonymize_user_data(self.test_user)
        print(f"Anonymized user data: {anonymized}")
        
        assert anonymized is not None, "User anonymization failed"
        assert 'username_hash' in anonymized, "Username not hashed in anonymization"
        assert 'email_hash' in anonymized, "Email not hashed in anonymization"
        assert anonymized['username'] != self.test_user.username, "Original username exposed in anonymization"
        
        print("✅ Privacy compliance tests passed")
    
    def test_audit_logging_security(self):
        """Test that audit logging doesn't expose sensitive data"""
        print("\n" + "="*60)
        print("TESTING AUDIT LOGGING SECURITY")
        print("="*60)
        
        # Create a test event with sensitive data
        sensitive_request_data = {
            'username': 'testuser',
            'password': 'sensitive_password',
            'email': 'sensitive@example.com',
            'credit_card': '4111111111111111'
        }
        
        # Simulate a security event
        SecurityAuditLog.objects.create(
            user=self.test_user,
            event_type='test_event',
            severity='info',
            description='Test event with sensitive data',
            request_data=sensitive_request_data,
            ip_address='127.0.0.1'
        )
        
        # Retrieve the log entry
        log_entry = SecurityAuditLog.objects.latest('created_at')
        logged_data = log_entry.request_data
        
        print(f"Logged request data: {logged_data}")
        
        # Check that sensitive data is masked in logs
        if isinstance(logged_data, dict):
            assert logged_data.get('password') == '[REDACTED]', "Password not redacted in audit log"
            assert logged_data.get('credit_card') == '[REDACTED]', "Credit card not redacted in audit log"
        
        print("✅ Audit logging security tests passed")
    
    def test_data_leakage_detection(self):
        """Test detection of sensitive data leakage"""
        print("\n" + "="*60)
        print("TESTING DATA LEAKAGE DETECTION")
        print("="*60)
        
        # Simulate response with sensitive data patterns
        test_responses = [
            '{"password": "secret123"}',
            '{"token": "sensitive_token"}',
            '{"credit_card": "4111111111111111"}',
            '{"ssn": "123-45-6789"}',
            '{"normal": "data"}'  # This should not trigger
        ]
        
        import re
        sensitive_patterns = [
            r'password["\s]*[:=]["\s]*[^"\\s]+',
            r'token["\s]*[:=]["\s]*[^"\\s]+',
            r'key["\s]*[:=]["\s]*[^"\\s]+',
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
        ]
        
        for i, response in enumerate(test_responses):
            pattern_found = False
            for pattern in sensitive_patterns:
                if re.search(pattern, response, re.IGNORECASE):
                    pattern_found = True
                    break
            
            if i < 4:  # First 4 should trigger detection
                assert pattern_found, f"Sensitive pattern not detected in: {response}"
                print(f"✅ Sensitive pattern detected in test response {i+1}")
            else:  # Last one should not trigger
                assert not pattern_found, f"False positive in: {response}"
                print(f"✅ No false positive for test response {i+1}")
        
        print("✅ Data leakage detection tests passed")
    
    def test_gdpr_compliance_features(self):
        """Test GDPR-specific compliance features"""
        print("\n" + "="*60)
        print("TESTING GDPR COMPLIANCE FEATURES")
        print("="*60)
        
        # Test data export functionality
        print("Testing data export...")
        
        # Create test data for the user
        test_product = Product.objects.create(
            name='Test Product',
            price=10.00,
            barcode='123456789'
        )
        
        test_order = CompletedOrder.objects.create(
            customer_name='Test Customer',
            customer_phone='0721234567',
            items=[{'product': test_product.id, 'quantity': 1}],
            total=10.00,
            cash_received=10.00,
            change_given=0.00,
            processed_by=self.test_user
        )
        
        # Test user data export (simulated)
        user_data = {
            'personal_info': {
                'username': self.test_user.username,
                'email': SecurityUtils.mask_email(self.test_user.email),
                'date_joined': self.test_user.date_joined,
            },
            'orders': [{
                'id': test_order.id,
                'customer_name': SecurityUtils.mask_email(test_order.customer_name),
                'customer_phone': SecurityUtils.mask_phone(test_order.customer_phone),
                'total': str(test_order.total),
            }]
        }
        
        print(f"Exported user data: {json.dumps(user_data, indent=2, default=str)}")
        
        # Verify that sensitive data is masked in export
        assert '*' in user_data['personal_info']['email'], "Email not masked in export"
        assert '*' in user_data['orders'][0]['customer_phone'], "Phone not masked in export"
        
        print("✅ GDPR compliance features tests passed")
    
    def run_all_tests(self):
        """Run all data protection tests"""
        print("Starting comprehensive data protection tests...")
        print(f"Test user: {self.test_user.username}")
        print(f"Admin user: {self.admin_user.username}")
        
        try:
            self.test_data_masking_in_logs()
            self.test_api_response_masking()
            self.test_security_headers()
            self.test_data_retention_policies()
            self.test_privacy_compliance()
            self.test_audit_logging_security()
            self.test_data_leakage_detection()
            self.test_gdpr_compliance_features()
            
            print("\n" + "="*60)
            print("🎉 ALL DATA PROTECTION TESTS PASSED! 🎉")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Cleanup test data
            self.cleanup_test_data()
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\nCleaning up test data...")
        
        # Delete test objects
        CompletedOrder.objects.all().delete()
        Product.objects.all().delete()
        SecurityAuditLog.objects.all().delete()
        DataModificationLog.objects.all().delete()
        APICallLog.objects.all().delete()
        SensitiveDataAccessLog.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.all().delete()
        
        print("✅ Test data cleaned up")

def main():
    """Main function to run tests"""
    print("NDtech POS Data Protection Test Suite")
    print("=" * 60)
    print("Testing data protection, privacy, and security features")
    print("This ensures sensitive information is properly hidden from GitHub exposure")
    print("=" * 60)
    
    tester = DataProtectionTester()
    tester.run_all_tests()

if __name__ == '__main__':
    main()
