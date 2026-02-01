"""
Security configuration and utilities for NDtech POS System
This module contains security-related functions and configurations
that should not contain sensitive information.
"""

import hashlib
import secrets
import re
from datetime import datetime, timedelta
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
import logging

logger = logging.getLogger('security')

class SecurityUtils:
    """Utility class for security operations"""
    
    @staticmethod
    def hash_sensitive_data(data, salt=None):
        """
        Hash sensitive data for logging purposes
        Returns a consistent hash that can't be reversed but allows tracking
        """
        if salt is None:
            salt = settings.SECRET_KEY[:16]  # Use part of SECRET_KEY as salt
        
        # Create a consistent hash for the data
        hash_object = hashlib.sha256(f"{salt}{str(data)}".encode())
        return hash_object.hexdigest()[:16]  # Return first 16 chars
    
    @staticmethod
    def mask_email(email):
        """Mask email address for logging"""
        if not email or '@' not in email:
            return 'invalid_email'
        
        local, domain = email.split('@', 1)
        if len(local) <= 2:
            masked_local = '*' * len(local)
        else:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        
        return f"{masked_local}@{domain}"
    
    @staticmethod
    def mask_phone(phone):
        """Mask phone number for logging"""
        if not phone:
            return 'invalid_phone'
        
        # Remove non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        if len(digits) <= 4:
            return '*' * len(digits)
        
        # Show first 2 and last 2 digits
        return digits[:2] + '*' * (len(digits) - 4) + digits[-2:]
    
    @staticmethod
    def mask_credit_card(card_number):
        """Mask credit card number"""
        if not card_number:
            return 'invalid_card'
        
        # Remove non-digit characters
        digits = re.sub(r'\D', '', card_number)
        
        if len(digits) <= 4:
            return '*' * len(digits)
        
        # Show last 4 digits only
        return '*' * (len(digits) - 4) + digits[-4:]
    
    @staticmethod
    def generate_secure_token(length=32):
        """Generate a cryptographically secure token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def sanitize_for_logging(data):
        """
        Sanitize data for logging by removing sensitive fields
        """
        if isinstance(data, dict):
            sanitized = {}
            sensitive_fields = [
                'password', 'token', 'secret', 'key', 'csrfmiddlewaretoken',
                'credit_card', 'ssn', 'social_security', 'bank_account',
                'api_key', 'private_key', 'access_token', 'refresh_token'
            ]
            
            for key, value in data.items():
                # Check if key contains sensitive patterns
                if any(sensitive in key.lower() for sensitive in sensitive_fields):
                    sanitized[key] = '[REDACTED]'
                elif 'email' in key.lower():
                    sanitized[key] = SecurityUtils.mask_email(str(value))
                elif 'phone' in key.lower():
                    sanitized[key] = SecurityUtils.mask_phone(str(value))
                elif 'card' in key.lower() or 'credit' in key.lower():
                    sanitized[key] = SecurityUtils.mask_credit_card(str(value))
                else:
                    sanitized[key] = value
            
            return sanitized
        
        return data

class DataProtection:
    """Data protection utilities"""
    
    @staticmethod
    def get_data_retention_days():
        """Get data retention period from settings or use defaults"""
        return getattr(settings, 'DATA_RETENTION_DAYS', {
            'security_logs': 365,  # 1 year
            'audit_logs': 2555,    # 7 years
            'api_logs': 90,        # 3 months
            'user_activity': 365,  # 1 year
            'error_logs': 180,     # 6 months
        })
    
    @staticmethod
    def should_purge_data(log_type, created_at):
        """Check if data should be purged based on retention policy"""
        retention_days = DataProtection.get_data_retention_days()
        
        if log_type not in retention_days:
            return False
        
        cutoff_date = timezone.now() - timedelta(days=retention_days[log_type])
        return created_at < cutoff_date
    
    @staticmethod
    def anonymize_user_data(user):
        """Anonymize user data for GDPR compliance"""
        if not user:
            return None
        
        # Create anonymized representation
        anonymized = {
            'id': user.id,
            'username_hash': SecurityUtils.hash_sensitive_data(user.username),
            'email_hash': SecurityUtils.hash_sensitive_data(user.email),
            'is_active': user.is_active,
            'date_joined': user.date_joined,
            'last_login': user.last_login,
        }
        
        return anonymized

class SecurityHeaders:
    """Security headers configuration"""
    
    @staticmethod
    def get_security_headers():
        """Get security headers for responses"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https://fcm.googleapis.com; "
                "frame-ancestors 'none';"
            ),
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': (
                'geolocation=(), microphone=(), camera=(), '
                'payment=(), usb=(), magnetometer=(), gyroscope=()'
            ),
        }

class EncryptionHelper:
    """Helper class for encryption operations"""
    
    @staticmethod
    def encrypt_sensitive_field(value):
        """
        Encrypt a sensitive field for storage
        Note: This is a placeholder - implement proper encryption in production
        """
        if not value:
            return None
        
        # In production, use proper encryption like Fernet or AES
        # For now, we'll just hash the value to demonstrate the concept
        return SecurityUtils.hash_sensitive_data(value)
    
    @staticmethod
    def decrypt_sensitive_field(encrypted_value):
        """
        Decrypt a sensitive field
        Note: This is a placeholder - implement proper decryption in production
        """
        if not encrypted_value:
            return None
        
        # In production, use proper decryption
        # For now, we can't reverse the hash, so return masked version
        return '[ENCRYPTED]'

class AuditSanitizer:
    """Sanitize audit logs to remove sensitive information"""
    
    @staticmethod
    def sanitize_request_data(request_data):
        """Sanitize request data for audit logging"""
        if not request_data:
            return {}
        
        return SecurityUtils.sanitize_for_logging(request_data)
    
    @staticmethod
    def sanitize_response_data(response_data):
        """Sanitize response data for audit logging"""
        if not response_data:
            return {}
        
        # Convert to dict if it's not already
        if isinstance(response_data, str):
            try:
                import json
                response_data = json.loads(response_data)
            except:
                return {'response': '[NON-JSON DATA]'}
        
        return SecurityUtils.sanitize_for_logging(response_data)
    
    @staticmethod
    def sanitize_user_object(user):
        """Sanitize user object for audit logging"""
        if not user:
            return None
        
        return {
            'id': user.id,
            'username': SecurityUtils.hash_sensitive_data(user.username),
            'email': SecurityUtils.mask_email(user.email),
            'is_active': user.is_active,
            'role': getattr(user.userprofile, 'role', 'unknown') if hasattr(user, 'userprofile') else 'unknown',
        }

class PrivacySettings:
    """Privacy and GDPR compliance settings"""
    
    @staticmethod
    def get_anonymization_fields():
        """Get fields that should be anonymized for GDPR"""
        return {
            'User': ['email', 'first_name', 'last_name', 'username'],
            'UserProfile': ['role', 'is_active'],
            'CompletedOrder': ['customer_name', 'customer_phone'],
            'AirtimeSale': ['customer_phone'],
            'FCMToken': ['token', 'device_id'],
        }
    
    @staticmethod
    def get_consent_purposes():
        """Get data processing purposes for consent"""
        return [
            'essential',      # Essential for service operation
            'analytics',      # Analytics and improvement
            'marketing',      # Marketing communications
            'personalization', # Personalization
            'security',       # Security and fraud prevention
        ]
