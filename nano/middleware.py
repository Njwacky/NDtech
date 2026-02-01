"""
Security and Audit Logging Middleware for NDtech POS System
"""
import time
import json
import logging
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
from django.db import connection
from django.contrib.auth.models import User
from .models import (
    SecurityAuditLog, DataModificationLog, AdminActionLog, 
    APICallLog, SensitiveDataAccessLog, UserProfile
)

logger = logging.getLogger('security_audit')

class SecurityAuditMiddleware(MiddlewareMixin):
    """
    Middleware to log security events and API calls
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
        
        # Define sensitive endpoints that require extra logging
        self.sensitive_endpoints = [
            '/admin/', '/api/auth/', '/login/', '/logout/', 
            '/password/', '/register/', '/change-password/'
        ]
        
        # Define sensitive data fields
        self.sensitive_fields = {
            'User': ['password', 'email', 'first_name', 'last_name', 'is_superuser', 'is_staff'],
            'UserProfile': ['role', 'is_active'],
            'CompletedOrder': ['customer_name', 'customer_phone', 'total'],
            'AirtimeSale': ['customer_phone', 'total_price'],
            'FCMToken': ['token', 'device_id'],
        }

    def process_request(self, request):
        """Store request start time and initial data"""
        request._audit_start_time = time.time()
        request._audit_db_queries = len(connection.queries)
        return None

    def process_response(self, request, response):
        """Log API calls and security events"""
        try:
            # Skip logging for static files and admin media
            if self._should_skip_logging(request):
                return response

            # Calculate duration
            duration_ms = None
            if hasattr(request, '_audit_start_time'):
                duration_ms = int((time.time() - request._audit_start_time) * 1000)

            # Get request context
            context = self._get_request_context(request)
            
            # Log API calls
            if self._is_api_call(request):
                self._log_api_call(request, response, duration_ms, context)
            
            # Log security events
            self._log_security_events(request, response, context)
            
            # Log sensitive data access
            self._log_sensitive_data_access(request, response, context)
            
        except Exception as e:
            logger.error(f"Error in SecurityAuditMiddleware: {str(e)}")
        
        return response

    def process_exception(self, request, exception):
        """Log security-related exceptions"""
        try:
            context = self._get_request_context(request)
            
            # Log permission denied exceptions
            if isinstance(exception, PermissionDenied):
                SecurityAuditLog.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    event_type='suspicious_activity',
                    severity='warning',
                    description=f"Permission denied: {str(exception)}",
                    ip_address=context['ip_address'],
                    user_agent=context['user_agent'],
                    request_data=self._sanitize_request_data(request),
                    detection_method='middleware_exception',
                )
        except Exception as e:
            logger.error(f"Error logging exception: {str(e)}")
        
        return None

    def _should_skip_logging(self, request):
        """Determine if request should be skipped from logging"""
        skip_patterns = [
            '/static/', '/media/', '/favicon.ico', '/robots.txt',
            '/admin/jsi18n/', '/__debug__/'
        ]
        
        path = request.path.lower()
        return any(pattern in path for pattern in skip_patterns)

    def _is_api_call(self, request):
        """Check if request is an API call"""
        return (
            request.path.startswith('/api/') or
            request.content_type == 'application/json' or
            'application/json' in request.META.get('HTTP_ACCEPT', '')
        )

    def _get_request_context(self, request):
        """Extract common request context"""
        # Get IP address (handle proxies)
        ip_address = request.META.get('REMOTE_ADDR')
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()

        return {
            'ip_address': ip_address,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'method': request.method,
            'path': request.path,
            'user': request.user if request.user.is_authenticated else None,
        }

    def _sanitize_request_data(self, request):
        """Remove sensitive data from request data"""
        data = {}
        
        if hasattr(request, 'POST') and request.POST:
            data.update(dict(request.POST))
        
        if hasattr(request, 'GET') and request.GET:
            data.update(dict(request.GET))
        
        # Remove sensitive fields
        sensitive_keys = ['password', 'token', 'secret', 'key', 'csrfmiddlewaretoken']
        for key in sensitive_keys:
            data.pop(key, None)
        
        return data

    def _log_api_call(self, request, response, duration_ms, context):
        """Log API call details"""
        try:
            # Determine status based on response
            status_code = getattr(response, 'status_code', 200)
            if status_code < 400:
                status = 'success'
            elif status_code == 401:
                status = 'unauthorized'
            elif status_code == 403:
                status = 'forbidden'
            elif status_code == 429:
                status = 'rate_limited'
            elif status_code >= 500:
                status = 'error'
            else:
                status = 'error'

            # Check for security concerns
            security_flags = []
            is_suspicious = False
            
            if status_code == 401 or status_code == 403:
                security_flags.append('authentication_failure')
                is_suspicious = True
            
            if duration_ms and duration_ms > 5000:  # Very slow requests
                security_flags.append('slow_request')
                is_suspicious = True
            
            # Get endpoint type
            endpoint_type = 'rest'
            if 'graphql' in request.path:
                endpoint_type = 'graphql'
            elif 'internal' in request.path:
                endpoint_type = 'internal'
            elif 'third-party' in request.path:
                endpoint_type = 'third_party'

            # Safely get request and response data
            request_body = ''
            try:
                if hasattr(request, 'body') and request.body:
                    request_body = request.body.decode('utf-8', errors='ignore')[:1000]
            except Exception:
                request_body = '[Body not accessible]'

            response_body = ''
            try:
                if hasattr(response, 'content') and response.content:
                    response_body = response.content.decode('utf-8', errors='ignore')[:500]
            except Exception:
                response_body = '[Response body not accessible]'

            APICallLog.objects.create(
                user=context['user'],
                endpoint_type=endpoint_type,
                method=context['method'],
                endpoint=request.get_full_path(),
                view_name=getattr(request.resolver_match, 'view_name', '') if hasattr(request, 'resolver_match') else '',
                request_headers=self._get_headers(request),
                request_body=request_body,
                query_params=dict(request.GET),
                status_code=status_code,
                status=status,
                response_headers=dict(response.items()) if hasattr(response, 'items') else {},
                response_body=response_body,
                duration_ms=duration_ms,
                db_query_count=len(connection.queries) - getattr(request, '_audit_db_queries', 0),
                ip_address=context['ip_address'],
                user_agent=context['user_agent'],
                authentication_method=self._get_auth_method(request) or 'unknown',
                is_suspicious=is_suspicious,
                security_flags=security_flags,
            )

        except Exception as e:
            logger.error(f"Error logging API call: {str(e)}")

    def _log_security_events(self, request, response, context):
        """Log security-related events"""
        try:
            # Check for failed authentication
            if (response.status_code == 401 or response.status_code == 403) and not request.user.is_authenticated:
                SecurityAuditLog.objects.create(
                    user=None,
                    event_type='login_failed',
                    severity='warning',
                    description=f"Failed authentication attempt to {request.path}",
                    ip_address=context['ip_address'],
                    user_agent=context['user_agent'],
                    username_attempted=request.POST.get('username', request.GET.get('username', '')),
                    request_data=self._sanitize_request_data(request),
                    detection_method='middleware_response',
                )

            # Check for suspicious patterns
            if self._is_suspicious_request(request, response):
                SecurityAuditLog.objects.create(
                    user=context['user'],
                    event_type='suspicious_activity',
                    severity='warning',
                    description=f"Suspicious request pattern detected: {request.method} {request.path}",
                    ip_address=context['ip_address'],
                    user_agent=context['user_agent'],
                    request_data=self._sanitize_request_data(request),
                    detection_method='pattern_detection',
                )

        except Exception as e:
            logger.error(f"Error logging security event: {str(e)}")

    def _log_sensitive_data_access(self, request, response, context):
        """Log access to sensitive data"""
        try:
            if not context['user']:
                return

            # Check if response contains sensitive data
            if hasattr(response, 'content'):
                content = response.content.decode('utf-8', errors='ignore').lower()
                
                for model_name, fields in self.sensitive_fields.items():
                    for field in fields:
                        if field in content and request.path.startswith('/api/'):
                            SensitiveDataAccessLog.objects.create(
                                user=context['user'],
                                data_type=self._get_data_type_for_field(field),
                                access_type='view',
                                content_type=model_name,
                                object_repr=f"API endpoint: {request.path}",
                                sensitive_fields=[field],
                                ip_address=context['ip_address'],
                                user_agent=context['user_agent'],
                                request_url=request.get_full_path(),
                                session_key=request.session.session_key if hasattr(request, 'session') else '',
                            )
                            break

        except Exception as e:
            logger.error(f"Error logging sensitive data access: {str(e)}")

    def _is_suspicious_request(self, request, response):
        """Check if request has suspicious patterns"""
        suspicious_patterns = [
            # SQL injection patterns
            lambda r: any(pattern in r.path.lower() for pattern in ['union select', 'drop table', 'insert into']),
            # XSS patterns
            lambda r: any(pattern in r.path.lower() for pattern in ['<script', 'javascript:', 'onload=']),
            # Path traversal
            lambda r: '../' in r.path,
            # Unusual user agents
            lambda r: any(pattern in r.META.get('HTTP_USER_AGENT', '').lower() for pattern in ['sqlmap', 'nmap', 'nikto']),
            # Large request bodies
            lambda r: hasattr(r, 'body') and len(r.body) > 10000000,  # 10MB
        ]
        
        return any(pattern(request) for pattern in suspicious_patterns)

    def _get_headers(self, request):
        """Extract relevant headers"""
        relevant_headers = [
            'CONTENT_TYPE', 'HTTP_ACCEPT', 'HTTP_USER_AGENT', 
            'HTTP_X_REQUESTED_WITH', 'HTTP_AUTHORIZATION',
            'HTTP_X_API_KEY', 'HTTP_REFERER'
        ]
        
        headers = {}
        for header in relevant_headers:
            value = request.META.get(header)
            if value:
                # Sanitize sensitive headers
                if 'AUTH' in header.upper() or 'KEY' in header.upper():
                    value = '[REDACTED]'
                headers[header] = value
        
        return headers

    def _get_auth_method(self, request):
        """Determine authentication method"""
        if request.user.is_authenticated:
            if 'HTTP_AUTHORIZATION' in request.META:
                return 'token'
            elif hasattr(request, 'session') and request.session.get('_auth_user_id'):
                return 'session'
            else:
                return 'unknown'
        return None

    def _get_data_type_for_field(self, field):
        """Map field names to data types"""
        field_mapping = {
            'password': 'authentication_data',
            'email': 'contact_info',
            'first_name': 'personal_info',
            'last_name': 'personal_info',
            'customer_phone': 'contact_info',
            'customer_name': 'personal_info',
            'token': 'authentication_data',
        }
        return field_mapping.get(field, 'personal_info')


class DataModificationMiddleware(MiddlewareMixin):
    """
    Middleware to track data modifications
    """
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """Store view information for later use"""
        request._view_name = f"{view_func.__module__}.{view_func.__name__}"
        return None


# Signal handlers for audit logging

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log successful user login"""
    try:
        ip_address = request.META.get('REMOTE_ADDR')
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()

        SecurityAuditLog.objects.create(
            user=user,
            event_type='login_success',
            severity='info',
            description=f"User {user.username} logged in successfully",
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            session_key=request.session.session_key if hasattr(request, 'session') else '',
            detection_method='django_signal',
        )
    except Exception as e:
        logger.error(f"Error logging user login: {str(e)}")


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout"""
    try:
        ip_address = request.META.get('REMOTE_ADDR')
        
        SecurityAuditLog.objects.create(
            user=user,
            event_type='logout',
            severity='info',
            description=f"User {user.username} logged out",
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            session_key=request.session.session_key if hasattr(request, 'session') else '',
            detection_method='django_signal',
        )
    except Exception as e:
        logger.error(f"Error logging user logout: {str(e)}")


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """Log failed login attempt"""
    try:
        ip_address = request.META.get('REMOTE_ADDR')
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()

        SecurityAuditLog.objects.create(
            user=None,
            event_type='login_failed',
            severity='warning',
            description=f"Failed login attempt for username: {credentials.get('username', 'unknown')}",
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            username_attempted=credentials.get('username', ''),
            request_data={'username': credentials.get('username', '')},
            detection_method='django_signal',
        )
    except Exception as e:
        logger.error(f"Error logging failed login: {str(e)}")


@receiver(pre_save)
def log_data_modification(sender, instance, **kwargs):
    """Log data modifications before save"""
    try:
        # Skip logging for audit models themselves to avoid infinite loops
        if sender.__name__ in ['SecurityAuditLog', 'DataModificationLog', 'AdminActionLog', 'APICallLog', 'SensitiveDataAccessLog']:
            return

        # Skip if instance doesn't have an ID yet (new object)
        if not instance.pk:
            return

        # Get the old object from database
        try:
            old_instance = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            return

        # Compare fields and log changes
        changed_fields = {}
        for field in instance._meta.fields:
            old_value = getattr(old_instance, field.name)
            new_value = getattr(instance, field.name)
            
            if old_value != new_value:
                changed_fields[field.name] = {
                    'old': str(old_value),
                    'new': str(new_value)
                }

        if changed_fields:
            # Get current request
            from django.http import HttpRequest
            # Try to get current request from thread local
            try:
                from threading import current_thread
                request = getattr(current_thread(), 'request', None)
            except:
                request = None
            
            # Determine sensitivity level
            sensitivity = 'medium'
            if sender.__name__ in ['User', 'UserProfile']:
                sensitivity = 'high'
            elif 'password' in changed_fields or 'role' in changed_fields:
                sensitivity = 'critical'

            # Get user from request
            user = None
            ip_address = None
            user_agent = None
            request_method = None
            request_url = None
            
            if request:
                user = request.user if request.user.is_authenticated else None
                ip_address = request.META.get('REMOTE_ADDR')
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                request_method = request.method
                request_url = request.get_full_path()

            # Handle case where instance.pk might be a string (for session objects)
            object_id = None
            if instance.pk:
                try:
                    object_id = int(instance.pk)
                except (ValueError, TypeError):
                    # For non-integer primary keys (like session IDs), store as None
                    # and include the actual ID in object_repr
                    object_id = None

            DataModificationLog.objects.create(
                user=user,
                action_type='update',
                sensitivity=sensitivity,
                content_type=sender.__name__,
                object_id=object_id,
                object_repr=str(instance)[:200],
                changed_fields=changed_fields,
                ip_address=ip_address,
                user_agent=user_agent or '',
                request_method=request_method or '',
                request_url=request_url or '',
                old_values={field: data['old'] for field, data in changed_fields.items()},
                new_values={field: data['new'] for field, data in changed_fields.items()},
            )

    except Exception as e:
        logger.error(f"Error logging data modification: {str(e)}")


@receiver(post_save)
def log_data_creation(sender, instance, created, **kwargs):
    """Log data creation"""
    try:
        # Skip logging for audit models themselves
        if sender.__name__ in ['SecurityAuditLog', 'DataModificationLog', 'AdminActionLog', 'APICallLog', 'SensitiveDataAccessLog']:
            return

        if not created:
            return

        # Skip during migrations
        from django.core.management import execute_from_command_line
        import sys
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
            return

        # Get current request
        try:
            from threading import current_thread
            request = getattr(current_thread(), 'request', None)
        except:
            request = None

        # Determine sensitivity level
        sensitivity = 'medium'
        if sender.__name__ in ['User', 'UserProfile']:
            sensitivity = 'high'

        # Get user from request
        user = None
        ip_address = None
        user_agent = None
        request_method = None
        request_url = None
        
        if request:
            user = request.user if request.user.is_authenticated else None
            ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            request_method = request.method or ''
            request_url = request.get_full_path() or ''

        # Handle case where instance.pk might be a string (for session objects)
        object_id = None
        if instance.pk:
            try:
                object_id = int(instance.pk)
            except (ValueError, TypeError):
                # For non-integer primary keys (like session IDs), store as None
                # and include the actual ID in object_repr
                object_id = None

        DataModificationLog.objects.create(
            user=user,
            action_type='create',
            sensitivity=sensitivity,
            content_type=sender.__name__,
            object_id=object_id,
            object_repr=str(instance)[:200],
            ip_address=ip_address,
            user_agent=user_agent or '',
            request_method=request_method or '',
            request_url=request_url or '',
            new_values={
                field.name: str(getattr(instance, field.name))
                for field in instance._meta.fields
            },
        )

    except Exception as e:
        logger.error(f"Error logging data creation: {str(e)}")


@receiver(post_delete)
def log_data_deletion(sender, instance, **kwargs):
    """Log data deletion"""
    try:
        # Skip logging for audit models themselves
        if sender.__name__ in ['SecurityAuditLog', 'DataModificationLog', 'AdminActionLog', 'APICallLog', 'SensitiveDataAccessLog']:
            return

        # Get current request
        try:
            from threading import current_thread
            request = getattr(current_thread(), 'request', None)
        except:
            request = None

        # Determine sensitivity level
        sensitivity = 'medium'
        if sender.__name__ in ['User', 'UserProfile']:
            sensitivity = 'high'

        # Get user from request
        user = None
        ip_address = None
        user_agent = None
        request_method = None
        request_url = None
        
        if request:
            user = request.user if request.user.is_authenticated else None
            ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            request_method = request.method
            request_url = request.get_full_path()

        # Handle case where instance.pk might be a string (for session objects)
        object_id = None
        if instance.pk:
            try:
                object_id = int(instance.pk)
            except (ValueError, TypeError):
                # For non-integer primary keys (like session IDs), store as None
                # and include the actual ID in object_repr
                object_id = None

        DataModificationLog.objects.create(
            user=user,
            action_type='delete',
            sensitivity=sensitivity,
            content_type=sender.__name__,
            object_id=object_id,
            object_repr=str(instance)[:200],
            ip_address=ip_address,
            user_agent=user_agent or '',
            request_method=request_method or '',
            request_url=request_url or '',
            old_values={
                field.name: str(getattr(instance, field.name))
                for field in instance._meta.fields
            },
        )

    except Exception as e:
        logger.error(f"Error logging data deletion: {str(e)}")


# Store request in thread local for signal handlers
class ThreadLocalMiddleware(MiddlewareMixin):
    """Store request in thread local for signal handlers"""
    
    def process_request(self, request):
        try:
            from threading import current_thread
            current_thread().request = request
        except Exception as e:
            logger.error(f"Error in ThreadLocalMiddleware: {str(e)}")
        return None

    def process_response(self, request, response):
        try:
            from threading import current_thread
            if hasattr(current_thread(), 'request'):
                delattr(current_thread(), 'request')
        except Exception as e:
            logger.error(f"Error in ThreadLocalMiddleware cleanup: {str(e)}")
        return response
