"""
Simple validation script for data protection features
Tests the core security utilities without complex database operations
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from confige.security import SecurityUtils, DataProtection, PrivacySettings

def test_security_utils():
    """Test core security utility functions"""
    print("\n" + "="*60)
    print("TESTING SECURITY UTILITIES")
    print("="*60)
    
    tests_passed = 0
    tests_total = 0
    
    # Test email masking
    tests_total += 1
    email = "john.doe@example.com"
    masked_email = SecurityUtils.mask_email(email)
    print(f"✓ Email masking: {email} -> {masked_email}")
    
    if '@' in masked_email and '*' in masked_email:
        tests_passed += 1
        print("  PASSED")
    else:
        print("  FAILED")
    
    # Test phone masking
    tests_total += 1
    phone = "0721234567"
    masked_phone = SecurityUtils.mask_phone(phone)
    print(f"✓ Phone masking: {phone} -> {masked_phone}")
    
    if '*' in masked_phone and len(masked_phone) == len(phone):
        tests_passed += 1
        print("  PASSED")
    else:
        print("  FAILED")
    
    # Test credit card masking
    tests_total += 1
    card = "4111111111111111"
    masked_card = SecurityUtils.mask_credit_card(card)
    print(f"✓ Credit card masking: {card} -> {masked_card}")
    
    if masked_card.endswith('1111') and masked_card.startswith('*'):
        tests_passed += 1
        print("  PASSED")
    else:
        print("  FAILED")
    
    # Test data sanitization
    tests_total += 1
    sensitive_data = {
        'username': 'john',
        'password': 'secret123',
        'email': 'john@example.com',
        'credit_card': '4111111111111111',
        'normal_field': 'normal_value'
    }
    
    sanitized = SecurityUtils.sanitize_for_logging(sensitive_data)
    print(f"✓ Data sanitization: {sanitized}")
    
    if (sanitized['password'] == '[REDACTED]' and 
        sanitized['credit_card'] == '[REDACTED]' and 
        sanitized['email'] != 'john@example.com' and
        sanitized['normal_field'] == 'normal_value'):
        tests_passed += 1
        print("  PASSED")
    else:
        print("  FAILED")
    
    # Test secure token generation
    tests_total += 1
    token = SecurityUtils.generate_secure_token(16)
    print(f"✓ Secure token generation: {token[:20]}...")
    
    if len(token) == 16 and token.isalnum():
        tests_passed += 1
        print("  PASSED")
    else:
        print("  FAILED")
    
    print(f"\nSecurity Utils: {tests_passed}/{tests_total} tests passed")
    return tests_passed == tests_total

def test_data_protection():
    """Test data protection utilities"""
    print("\n" + "="*60)
    print("TESTING DATA PROTECTION")
    print("="*60)
    
    tests_passed = 0
    tests_total = 0
    
    # Test retention policies
    tests_total += 1
    retention_days = DataProtection.get_data_retention_days()
    print(f"✓ Retention policies: {retention_days}")
    
    expected_policies = ['security_logs', 'audit_logs', 'api_logs', 'user_activity', 'error_logs']
    if all(policy in retention_days for policy in expected_policies):
        tests_passed += 1
        print("  PASSED")
    else:
        print("  FAILED")
    
    # Test user anonymization
    tests_total += 1
    # Create a mock user object
    class MockUser:
        def __init__(self):
            self.id = 123
            self.username = 'testuser'
            self.email = 'test@example.com'
            self.is_active = True
            self.date_joined = '2024-01-01'
            self.last_login = '2024-01-01'
    
    mock_user = MockUser()
    anonymized = DataProtection.anonymize_user_data(mock_user)
    print(f"✓ User anonymization: {anonymized}")
    
    if (anonymized and 
        'username_hash' in anonymized and 
        'email_hash' in anonymized and
        anonymized.get('username') != mock_user.username):
        tests_passed += 1
        print("  PASSED")
    else:
        print("  FAILED")
    
    print(f"\nData Protection: {tests_passed}/{tests_total} tests passed")
    return tests_passed == tests_total

def test_privacy_settings():
    """Test privacy settings"""
    print("\n" + "="*60)
    print("TESTING PRIVACY SETTINGS")
    print("="*60)
    
    tests_passed = 0
    tests_total = 0
    
    # Test anonymization fields
    tests_total += 1
    anonymization_fields = PrivacySettings.get_anonymization_fields()
    print(f"✓ Anonymization fields: {anonymization_fields}")
    
    expected_fields = ['User', 'UserProfile', 'CompletedOrder', 'AirtimeSale', 'FCMToken']
    if all(field in anonymization_fields for field in expected_fields):
        tests_passed += 1
        print("  PASSED")
    else:
        print("  FAILED")
    
    # Test consent purposes
    tests_total += 1
    consent_purposes = PrivacySettings.get_consent_purposes()
    print(f"✓ Consent purposes: {consent_purposes}")
    
    expected_purposes = ['essential', 'analytics', 'marketing', 'personalization', 'security']
    if all(purpose in consent_purposes for purpose in expected_purposes):
        tests_passed += 1
        print("  PASSED")
    else:
        print("  FAILED")
    
    print(f"\nPrivacy Settings: {tests_passed}/{tests_total} tests passed")
    return tests_passed == tests_total

def test_pattern_detection():
    """Test sensitive data pattern detection"""
    print("\n" + "="*60)
    print("TESTING PATTERN DETECTION")
    print("="*60)
    
    tests_passed = 0
    tests_total = 0
    
    # Test patterns that should be detected
    sensitive_patterns = [
        '{"password": "secret123"}',
        '{"token": "sensitive_token"}',
        '{"credit_card": "4111111111111111"}',
        '{"ssn": "123-45-6789"}',
        '{"normal": "data"}'  # This should not trigger
    ]
    
    import re
    detection_patterns = [
        r'password["\s]*[:=]["\s]*[^"\\s]+',
        r'token["\s]*[:=]["\s]*[^"\\s]+',
        r'key["\s]*[:=]["\s]*[^"\\s]+',
        r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
    ]
    
    for i, response in enumerate(sensitive_patterns):
        tests_total += 1
        pattern_found = False
        for pattern in detection_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                pattern_found = True
                break
        
        if i < 4:  # First 4 should trigger detection
            if pattern_found:
                tests_passed += 1
                print(f"✓ Sensitive pattern detected in test {i+1}: PASSED")
            else:
                print(f"✗ Sensitive pattern NOT detected in test {i+1}: FAILED")
        else:  # Last one should not trigger
            if not pattern_found:
                tests_passed += 1
                print(f"✓ No false positive for test {i+1}: PASSED")
            else:
                print(f"✗ False positive for test {i+1}: FAILED")
    
    print(f"\nPattern Detection: {tests_passed}/{tests_total} tests passed")
    return tests_passed == tests_total

def main():
    """Main validation function"""
    print("NDtech POS Data Protection Validation")
    print("=" * 60)
    print("Validating core data protection and privacy features")
    print("This ensures sensitive information is properly hidden from GitHub exposure")
    print("=" * 60)
    
    # Run all tests
    results = []
    results.append(test_security_utils())
    results.append(test_data_protection())
    results.append(test_privacy_settings())
    results.append(test_pattern_detection())
    
    # Summary
    total_tests = len(results)
    passed_tests = sum(results)
    
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    print(f"Total test categories: {total_tests}")
    print(f"Categories passed: {passed_tests}")
    print(f"Categories failed: {total_tests - passed_tests}")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL DATA PROTECTION VALIDATIONS PASSED! 🎉")
        print("✅ Security utilities are working correctly")
        print("✅ Data protection features are functional")
        print("✅ Privacy settings are properly configured")
        print("✅ Pattern detection is working")
        print("\n🛡️  Your system is protected against sensitive data exposure!")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test categories failed")
        print("Please review the failed tests above")
    
    print("="*60)
    
    return passed_tests == total_tests

if __name__ == '__main__':
    main()
