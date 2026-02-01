"""
Enhanced Security Middleware for NDtech POS System
Provides additional data protection and privacy features
"""

import json
import logging
from django.utils import timezone
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from .models import SecurityAuditLog
from confige.security import SecurityUtils, SecurityHeaders, AuditSanitizer, DataProtection

logger = logging.getLogger('security_enhanced')

class EnhancedSecurityMiddleware(MiddlewareMixin):
    """
    Enhanced security middleware with data protection features
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
        
        # Sensitive patterns to detect in responses
        self.sensitive_patterns = [
            r'password["\s]*[:=]["\s]*[^"\\s]+',
            r'token["\s]*[:=]["\s]*[^"\\s]+',
            r'secret["\s]*[:=]["\s]*[^"\\s]+',
            r'key["\s]*[:=]["\s]*[^"\\s]+',
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card pattern
            r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',  # SSN pattern
        ]
    
    def process_response(self, request, response):
        """Apply security headers and sanitize response data"""
        try:
            # Add security headers
            self._add_security_headers(response)
            
            # Sanitize response content if it's JSON
            if self._is_json_response(response):
                self._sanitize_json_response(response)
            
            # Log suspicious response content
            self._check_for_sensitive_data_leakage(request, response)
            
        except Exception as e:
            logger.error(f"Error in EnhancedSecurityMiddleware: {str(e)}")
        
        return response
    
    def _add_security_headers(self, response):
        """Add security headers to response"""
        headers = SecurityHeaders.get_security_headers()
        
        for header, value in headers.items():
            response[header] = value
    
    def _is_json_response(self, response):
        """Check if response contains JSON data"""
        content_type = response.get('Content-Type', '')
        return 'application/json' in content_type
    
    def _sanitize_json_response(self, response):
        """Sanitize JSON response to remove sensitive data"""
        try:
            if hasattr(response, 'content'):
                content = response.content.decode('utf-8')
                data = json.loads(content)
                
                # Sanitize the data
                sanitized_data = AuditSanitizer.sanitize_response_data(data)
                
                # Update response content
                sanitized_content = json.dumps(sanitized_data)
                response.content = sanitized_content.encode('utf-8')
                
                # Update content length
                response['Content-Length'] = len(response.content)
        
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError) as e:
            logger.warning(f"Could not sanitize JSON response: {str(e)}")
    
    def _check_for_sensitive_data_leakage(self, request, response):
        """Check if response contains sensitive data that shouldn't be exposed"""
        try:
            if hasattr(response, 'content'):
                content = response.content.decode('utf-8', errors='ignore')
                
                import re
                for pattern in self.sensitive_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        # Log potential data leakage
                        SecurityAuditLog.objects.create(
                            user=request.user if request.user.is_authenticated else None,
                            event_type='suspicious_activity',
                            severity='warning',
                            description=f"Potential sensitive data leakage detected in response to {request.path}",
                            ip_address=self._get_client_ip(request),
                            user_agent=request.META.get('HTTP_USER_AGENT', ''),
                            request_data=AuditSanitizer.sanitize_request_data(dict(request.POST)),
                            detection_method='enhanced_middleware',
                        )
                        
                        logger.warning(f"Sensitive data pattern detected in response: {pattern}")
                        break
        
        except Exception as e:
            logger.error(f"Error checking for data leakage: {str(e)}")
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class DataRetentionMiddleware(MiddlewareMixin):
    """
    Middleware to handle data retention and cleanup
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
        
        # Run cleanup daily (check on each request but only run once per day)
        self.last_cleanup_date = None
    
    def process_response(self, request, response):
        """Check and perform data retention cleanup if needed"""
        try:
            today = timezone.now().date()
            
            # Only run cleanup once per day
            if self.last_cleanup_date != today:
                self._perform_data_cleanup()
                self.last_cleanup_date = today
        
        except Exception as e:
            logger.error(f"Error in data retention cleanup: {str(e)}")
        
        return response
    
    def _perform_data_cleanup(self):
        """Perform automated data cleanup based on retention policies"""
        from django.utils import timezone
        from nano.models import (
            SecurityAuditLog, DataModificationLog, 
            APICallLog, SensitiveDataAccessLog
        )
        
        logger.info("Starting automated data cleanup...")
        
        try:
            # Cleanup old security audit logs
            cutoff_date = timezone.now() - timezone.timedelta(
                days=DataProtection.get_data_retention_days()['security_logs']
            )
            deleted_count = SecurityAuditLog.objects.filter(
                created_at__lt=cutoff_date
            ).delete()[0]
            logger.info(f"Deleted {deleted_count} old security audit logs")
            
            # Cleanup old API call logs
            cutoff_date = timezone.now() - timezone.timedelta(
                days=DataProtection.get_data_retention_days()['api_logs']
            )
            deleted_count = APICallLog.objects.filter(
                created_at__lt=cutoff_date
            ).delete()[0]
            logger.info(f"Deleted {deleted_count} old API call logs")
            
            # Cleanup old sensitive data access logs
            cutoff_date = timezone.now() - timezone.timedelta(
                days=DataProtection.get_data_retention_days()['user_activity']
            )
            deleted_count = SensitiveDataAccessLog.objects.filter(
                created_at__lt=cutoff_date
            ).delete()[0]
            logger.info(f"Deleted {deleted_count} old sensitive data access logs")
            
            logger.info("Data cleanup completed successfully")
        
        except Exception as e:
            logger.error(f"Error during data cleanup: {str(e)}")


class PrivacyComplianceMiddleware(MiddlewareMixin):
    """
    Middleware to ensure privacy compliance in responses
    """
    
    def process_response(self, request, response):
        """Ensure privacy compliance in responses"""
        try:
            # Add privacy headers
            response['X-Privacy-Policy'] = 'https://ndtechpos.com/privacy'
            response['X-GDPR-Compliant'] = 'true'
            
            # Remove sensitive headers that might leak information
            sensitive_headers = [
                'Server',
                'X-Powered-By',
                'X-AspNet-Version',
                'X-AspNetMvc-Version',
            ]
            
            for header in sensitive_headers:
                if header in response:
                    del response[header]
            
            # Ensure no sensitive data in debug responses
            if settings.DEBUG and hasattr(response, 'content'):
                content = response.content.decode('utf-8', errors='ignore')
                if 'DEBUG' in content or 'settings' in content:
                    # Replace debug information with generic message
                    sanitized_content = json.dumps({
                        'error': 'Debug information not available in production',
                        'status': 'error'
                    })
                    response.content = sanitized_content.encode('utf-8')
                    response['Content-Length'] = len(response.content)
        
        except Exception as e:
            logger.error(f"Error in privacy compliance middleware: {str(e)}")
        
        return response


class SensitiveDataMaskingMiddleware(MiddlewareMixin):
    """
    Middleware to mask sensitive data in API responses
    """
    
    def process_response(self, request, response):
        """Mask sensitive data in responses"""
        try:
            # Only process JSON responses
            if not self._is_json_response(response):
                return response
            
            # Only process API endpoints
            if not request.path.startswith('/api/'):
                return response
            
            # Mask sensitive data in response
            self._mask_sensitive_response_data(response)
            
        except Exception as e:
            logger.error(f"Error in SensitiveDataMaskingMiddleware: {str(e)}")
        
        return response
    
    def _mask_sensitive_response_data(self, response):
        """Mask sensitive data in JSON response"""
        try:
            if hasattr(response, 'content'):
                content = response.content.decode('utf-8')
                data = json.loads(content)
                
                # Mask sensitive fields
                masked_data = self._mask_sensitive_fields(data)
                
                # Update response content
                masked_content = json.dumps(masked_data)
                response.content = masked_content.encode('utf-8')
                response['Content-Length'] = len(response.content)
        
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError) as e:
            logger.warning(f"Could not mask sensitive data in response: {str(e)}")
    
    def _mask_sensitive_fields(self, data, parent_key=''):
        """Recursively mask sensitive fields in data structure"""
        if isinstance(data, dict):
            masked = {}
            for key, value in data.items():
                if self._is_sensitive_field(key):
                    masked[key] = self._mask_value(key, value)
                else:
                    masked[key] = self._mask_sensitive_fields(value, key)
            return masked
        elif isinstance(data, list):
            return [self._mask_sensitive_fields(item, parent_key) for item in data]
        else:
            return data
    
    def _is_sensitive_field(self, field_name):
        """Check if field contains sensitive data"""
        sensitive_patterns = [
            'password', 'token', 'secret', 'key', 'credit_card',
            'ssn', 'social_security', 'bank_account', 'api_key',
            'private_key', 'access_token', 'refresh_token', 'csrf'
        ]
        
        field_lower = field_name.lower()
        return any(pattern in field_lower for pattern in sensitive_patterns)
    
    def _mask_value(self, field_name, value):
        """Mask a sensitive value based on field type"""
        if value is None:
            return None
        
        value_str = str(value)
        
        if 'email' in field_name.lower():
            return SecurityUtils.mask_email(value_str)
        elif 'phone' in field_name.lower():
            return SecurityUtils.mask_phone(value_str)
        elif 'card' in field_name.lower() or 'credit' in field_name.lower():
            return SecurityUtils.mask_credit_card(value_str)
        else:
            return '[MASKED]'
    
    def _is_json_response(self, response):
        """Check if response contains JSON data"""
        content_type = response.get('Content-Type', '')
        return 'application/json' in content_type
