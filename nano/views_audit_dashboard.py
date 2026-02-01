"""
Audit Dashboard Views for NDtech POS System
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q, Count, Avg, Max, Min
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import (
    SecurityAuditLog, DataModificationLog, AdminActionLog, 
    APICallLog, SensitiveDataAccessLog, UserProfile
)

def is_admin_or_manager(user):
    """Check if user is admin or manager"""
    if not user.is_authenticated:
        return False
    try:
        profile = user.userprofile
        return profile.role in ['admin', 'manager', 'superuser']
    except UserProfile.DoesNotExist:
        return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_admin_or_manager)
def audit_dashboard(request):
    """Main audit dashboard"""
    # Get time ranges
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)
    
    # Security Events Summary
    security_events_24h = SecurityAuditLog.objects.filter(created_at__gte=last_24h)
    security_events_7d = SecurityAuditLog.objects.filter(created_at__gte=last_7d)
    security_events_30d = SecurityAuditLog.objects.filter(created_at__gte=last_30d)
    
    security_summary = {
        'last_24h': {
            'total': security_events_24h.count(),
            'critical': security_events_24h.filter(severity='critical').count(),
            'failed_logins': security_events_24h.filter(event_type='login_failed').count(),
            'suspicious': security_events_24h.filter(event_type='suspicious_activity').count(),
        },
        'last_7d': {
            'total': security_events_7d.count(),
            'critical': security_events_7d.filter(severity='critical').count(),
            'failed_logins': security_events_7d.filter(event_type='login_failed').count(),
            'suspicious': security_events_7d.filter(event_type='suspicious_activity').count(),
        },
        'last_30d': {
            'total': security_events_30d.count(),
            'critical': security_events_30d.filter(severity='critical').count(),
            'failed_logins': security_events_30d.filter(event_type='login_failed').count(),
            'suspicious': security_events_30d.filter(event_type='suspicious_activity').count(),
        }
    }
    
    # Data Modifications Summary
    data_mods_24h = DataModificationLog.objects.filter(created_at__gte=last_24h)
    data_mods_7d = DataModificationLog.objects.filter(created_at__gte=last_7d)
    data_mods_30d = DataModificationLog.objects.filter(created_at__gte=last_30d)
    
    data_mod_summary = {
        'last_24h': {
            'total': data_mods_24h.count(),
            'critical': data_mods_24h.filter(sensitivity='critical').count(),
            'creates': data_mods_24h.filter(action_type='create').count(),
            'updates': data_mods_24h.filter(action_type='update').count(),
            'deletes': data_mods_24h.filter(action_type='delete').count(),
        },
        'last_7d': {
            'total': data_mods_7d.count(),
            'critical': data_mods_7d.filter(sensitivity='critical').count(),
            'creates': data_mods_7d.filter(action_type='create').count(),
            'updates': data_mods_7d.filter(action_type='update').count(),
            'deletes': data_mods_7d.filter(action_type='delete').count(),
        },
        'last_30d': {
            'total': data_mods_30d.count(),
            'critical': data_mods_30d.filter(sensitivity='critical').count(),
            'creates': data_mods_30d.filter(action_type='create').count(),
            'updates': data_mods_30d.filter(action_type='update').count(),
            'deletes': data_mods_30d.filter(action_type='delete').count(),
        }
    }
    
    # API Calls Summary
    api_calls_24h = APICallLog.objects.filter(created_at__gte=last_24h)
    api_calls_7d = APICallLog.objects.filter(created_at__gte=last_7d)
    api_calls_30d = APICallLog.objects.filter(created_at__gte=last_30d)
    
    api_summary = {
        'last_24h': {
            'total': api_calls_24h.count(),
            'suspicious': api_calls_24h.filter(is_suspicious=True).count(),
            'errors': api_calls_24h.filter(status='error').count(),
            'avg_duration': api_calls_24h.aggregate(avg=Avg('duration_ms'))['avg'] or 0,
        },
        'last_7d': {
            'total': api_calls_7d.count(),
            'suspicious': api_calls_7d.filter(is_suspicious=True).count(),
            'errors': api_calls_7d.filter(status='error').count(),
            'avg_duration': api_calls_7d.aggregate(avg=Avg('duration_ms'))['avg'] or 0,
        },
        'last_30d': {
            'total': api_calls_30d.count(),
            'suspicious': api_calls_30d.filter(is_suspicious=True).count(),
            'errors': api_calls_30d.filter(status='error').count(),
            'avg_duration': api_calls_30d.aggregate(avg=Avg('duration_ms'))['avg'] or 0,
        }
    }
    
    # Recent Security Events
    recent_security = SecurityAuditLog.objects.select_related('user').order_by('-created_at')[:10]
    
    # Recent Data Modifications
    recent_data_mods = DataModificationLog.objects.select_related('user').order_by('-created_at')[:10]
    
    # Top Failed Login IPs
    top_failed_ips = SecurityAuditLog.objects.filter(
        event_type='login_failed',
        created_at__gte=last_7d
    ).values('ip_address').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    context = {
        'security_summary': security_summary,
        'data_mod_summary': data_mod_summary,
        'api_summary': api_summary,
        'recent_security': recent_security,
        'recent_data_mods': recent_data_mods,
        'top_failed_ips': top_failed_ips,
        'page_title': 'Audit Dashboard',
    }
    
    return render(request, 'nano/audit_dashboard.html', context)

@login_required
@user_passes_test(is_admin_or_manager)
def security_events_view(request):
    """View security events with filtering"""
    page = request.GET.get('page', 1)
    event_type = request.GET.get('event_type', '')
    severity = request.GET.get('severity', '')
    search = request.GET.get('search', '')
    
    events = SecurityAuditLog.objects.select_related('user', 'resolved_by').order_by('-created_at')
    
    # Apply filters
    if event_type:
        events = events.filter(event_type=event_type)
    if severity:
        events = events.filter(severity=severity)
    if search:
        events = events.filter(
            Q(description__icontains=search) |
            Q(user__username__icontains=search) |
            Q(ip_address__icontains=search) |
            Q(username_attempted__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(events, 50)
    events_page = paginator.get_page(page)
    
    context = {
        'events': events_page,
        'event_types': SecurityAuditLog.EVENT_TYPES,
        'severity_levels': SecurityAuditLog.SEVERITY_LEVELS,
        'current_filters': {
            'event_type': event_type,
            'severity': severity,
            'search': search,
        },
        'page_title': 'Security Events',
    }
    
    return render(request, 'nano/security_events.html', context)

@login_required
@user_passes_test(is_admin_or_manager)
def data_modifications_view(request):
    """View data modifications with filtering"""
    page = request.GET.get('page', 1)
    action_type = request.GET.get('action_type', '')
    sensitivity = request.GET.get('sensitivity', '')
    search = request.GET.get('search', '')
    
    modifications = DataModificationLog.objects.select_related('user').order_by('-created_at')
    
    # Apply filters
    if action_type:
        modifications = modifications.filter(action_type=action_type)
    if sensitivity:
        modifications = modifications.filter(sensitivity=sensitivity)
    if search:
        modifications = modifications.filter(
            Q(object_repr__icontains=search) |
            Q(user__username__icontains=search) |
            Q(content_type__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(modifications, 50)
    mods_page = paginator.get_page(page)
    
    context = {
        'modifications': mods_page,
        'action_types': DataModificationLog.ACTION_TYPES,
        'sensitivity_levels': DataModificationLog.SENSITIVITY_LEVELS,
        'current_filters': {
            'action_type': action_type,
            'sensitivity': sensitivity,
            'search': search,
        },
        'page_title': 'Data Modifications',
    }
    
    return render(request, 'nano/data_modifications.html', context)

@login_required
@user_passes_test(is_admin_or_manager)
def api_calls_view(request):
    """View API calls with filtering"""
    page = request.GET.get('page', 1)
    status = request.GET.get('status', '')
    method = request.GET.get('method', '')
    search = request.GET.get('search', '')
    
    calls = APICallLog.objects.select_related('user').order_by('-created_at')
    
    # Apply filters
    if status:
        calls = calls.filter(status=status)
    if method:
        calls = calls.filter(method=method)
    if search:
        calls = calls.filter(
            Q(endpoint__icontains=search) |
            Q(user__username__icontains=search) |
            Q(view_name__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(calls, 50)
    calls_page = paginator.get_page(page)
    
    context = {
        'calls': calls_page,
        'status_choices': APICallLog.STATUS_CHOICES,
        'methods': ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
        'current_filters': {
            'status': status,
            'method': method,
            'search': search,
        },
        'page_title': 'API Calls',
    }
    
    return render(request, 'nano/api_calls.html', context)

@login_required
@user_passes_test(is_admin_or_manager)
def sensitive_data_access_view(request):
    """View sensitive data access logs"""
    page = request.GET.get('page', 1)
    data_type = request.GET.get('data_type', '')
    access_type = request.GET.get('access_type', '')
    search = request.GET.get('search', '')
    
    access_logs = SensitiveDataAccessLog.objects.select_related('user').order_by('-created_at')
    
    # Apply filters
    if data_type:
        access_logs = access_logs.filter(data_type=data_type)
    if access_type:
        access_logs = access_logs.filter(access_type=access_type)
    if search:
        access_logs = access_logs.filter(
            Q(object_repr__icontains=search) |
            Q(user__username__icontains=search) |
            Q(content_type__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(access_logs, 50)
    logs_page = paginator.get_page(page)
    
    context = {
        'access_logs': logs_page,
        'data_types': SensitiveDataAccessLog.DATA_TYPES,
        'access_types': SensitiveDataAccessLog.ACCESS_TYPES,
        'current_filters': {
            'data_type': data_type,
            'access_type': access_type,
            'search': search,
        },
        'page_title': 'Sensitive Data Access',
    }
    
    return render(request, 'nano/sensitive_data_access.html', context)

@login_required
@user_passes_test(is_admin_or_manager)
def resolve_security_event(request, log_id):
    """Resolve a security event"""
    log = get_object_or_404(SecurityAuditLog, id=log_id)
    
    if request.method == 'POST':
        resolution_notes = request.POST.get('resolution_notes', '')
        
        log.is_resolved = True
        log.resolved_by = request.user
        log.resolved_at = timezone.now()
        log.resolution_notes = resolution_notes
        log.save()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@user_passes_test(is_admin_or_manager)
def audit_statistics_api(request):
    """API endpoint for audit statistics"""
    days = int(request.GET.get('days', 7))
    start_date = timezone.now() - timedelta(days=days)
    
    # Security events over time
    security_events = SecurityAuditLog.objects.filter(created_at__gte=start_date)
    security_by_day = security_events.extra({
        'day': 'date(created_at)'
    }).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    # Data modifications by type
    data_mods = DataModificationLog.objects.filter(created_at__gte=start_date)
    mods_by_type = data_mods.values('action_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # API call status distribution
    api_calls = APICallLog.objects.filter(created_at__gte=start_date)
    api_by_status = api_calls.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    data = {
        'security_by_day': list(security_by_day),
        'mods_by_type': list(mods_by_type),
        'api_by_status': list(api_by_status),
        'summary': {
            'total_security': security_events.count(),
            'total_mods': data_mods.count(),
            'total_api': api_calls.count(),
            'critical_events': security_events.filter(severity='critical').count(),
            'suspicious_api': api_calls.filter(is_suspicious=True).count(),
        }
    }
    
    return JsonResponse(data)
