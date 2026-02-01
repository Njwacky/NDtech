"""
Developer Access Middleware
Restricts access to audit dashboard based on developer mode settings
"""

from django.conf import settings
from django.http import HttpResponseForbidden
from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)


class DeveloperAccessMiddleware:
    """
    Middleware to restrict access to audit dashboard based on developer mode
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Check if this is an audit dashboard request
        if self.is_audit_dashboard_request(request):
            if not self.can_access_audit_dashboard(request):
                logger.warning(
                    f"Audit dashboard access denied for user {request.user} "
                    f"from IP {self.get_client_ip(request)}. "
                    f"Developer mode: {getattr(settings, 'DEVELOPER_MODE', False)}, "
                    f"Audit dashboard dev only: {getattr(settings, 'AUDIT_DASHBOARD_DEV_ONLY', True)}"
                )
                
                if request.headers.get('Accept', '').startswith('application/json'):
                    return HttpResponseForbidden(
                        {
                            "error": "Audit dashboard access restricted to developer mode only",
                            "status": "error",
                            "developer_mode": getattr(settings, 'DEVELOPER_MODE', False),
                            "audit_dashboard_dev_only": getattr(settings, 'AUDIT_DASHBOARD_DEV_ONLY', True)
                        },
                        content_type="application/json"
                    )
                else:
                    return render(request, 'nano/audit_access_denied.html', {
                        'error_message': "Audit dashboard access is restricted to developer mode only.",
                        'developer_mode': getattr(settings, 'DEVELOPER_MODE', False),
                        'audit_dashboard_dev_only': getattr(settings, 'AUDIT_DASHBOARD_DEV_ONLY', True),
                        'current_user': request.user.username if request.user.is_authenticated else 'Anonymous',
                        'request_ip': self.get_client_ip(request)
                    }, status=403)
        
        return response
    
    def is_audit_dashboard_request(self, request):
        """Check if the request is for audit dashboard"""
        audit_paths = [
            '/audit/',
            '/audit/security-events/',
            '/audit/data-modifications/',
            '/audit/api-calls/',
            '/audit/sensitive-data/',
            '/audit/statistics/',
            '/audit/resolve/',
        ]
        
        return any(request.path.startswith(path) for path in audit_paths)
    
    def can_access_audit_dashboard(self, request):
        """Check if user can access audit dashboard"""
        # Get settings
        developer_mode = getattr(settings, 'DEVELOPER_MODE', False)
        audit_dashboard_dev_only = getattr(settings, 'AUDIT_DASHBOARD_DEV_ONLY', False)
        
        # If audit dashboard is not restricted to dev only, allow access
        if not audit_dashboard_dev_only:
            return True
        
        # If audit dashboard is dev only, check conditions
        if audit_dashboard_dev_only:
            # Allow access if in developer mode
            if developer_mode:
                return True
            
            # Allow access if user is superuser (even in production)
            if request.user.is_authenticated and request.user.is_superuser:
                logger.info(f"Superuser {request.user.username} accessing audit dashboard in production")
                return True
            
            # Allow access if user has admin role
            if (request.user.is_authenticated and 
                hasattr(request.user, 'userprofile') and 
                request.user.userprofile.role in ['admin', 'superuser']):
                logger.info(f"Admin user {request.user.username} accessing audit dashboard in production")
                return True
        
        return False
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
