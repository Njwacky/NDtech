from django.http import JsonResponse
from django.utils import timezone
from django.db import connection
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
import traceback

def health_check(request):
    """
    Health check endpoint to verify database and application status
    """
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "healthy"
        
        # Test User model (this will fail if auth_user table doesn't exist)
        user_count = User.objects.count()
        
        # Check if security audit tables exist
        from nano.models import SecurityAuditLog
        audit_log_count = SecurityAuditLog.objects.count()
        
        return JsonResponse({
            'status': 'healthy',
            'database': db_status,
            'user_count': user_count,
            'audit_log_count': audit_log_count,
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0'
        })
        
    except ImproperlyConfigured as e:
        return JsonResponse({
            'status': 'misconfigured',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=503)
        
    except Exception as e:
        # Log the full error for debugging
        error_details = {
            'error': str(e),
            'traceback': traceback.format_exc(),
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)

def database_status(request):
    """
    Detailed database status endpoint
    """
    try:
        from django.db.migrations.recorder import MigrationRecorder
        from django.contrib.auth.models import User
        from nano.models import SecurityAuditLog
        
        # Get migration status
        recorder = MigrationRecorder(connection)
        applied_migrations = recorder.applied_migrations()
        
        # Check key tables
        tables_exist = {
            'auth_user': User.objects.exists(),
            'security_audit_log': SecurityAuditLog.objects.exists(),
        }
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'applied_migrations': len(applied_migrations),
            'tables_exist': tables_exist,
            'user_count': User.objects.count() if tables_exist['auth_user'] else 0,
            'audit_log_count': SecurityAuditLog.objects.count() if tables_exist['security_audit_log'] else 0,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)
