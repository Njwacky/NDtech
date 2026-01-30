from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Count, Q, Avg, F
from django.utils import timezone
from datetime import timedelta
import json
from django.views.decorators.csrf import csrf_exempt

# Import models from both apps
from nano.models import ErrorLog, UserActivity, DeviceConnection, Notification
from NDtechTrack.models import SystemAlert, UserErrorPattern, SystemPerformance, AutomatedIssue, UserSession

@login_required
def master_dashboard(request):
    """Enhanced Master System Health Dashboard with real-time monitoring"""
    
    # Permission check - only superusers or admin/manager roles
    if not (request.user.is_superuser or 
            (hasattr(request.user, 'userprofile') and 
             request.user.userprofile.role in ['admin', 'manager'])):
        return HttpResponseForbidden("You do not have permission to access this page.")
    
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    
    # Enhanced Error Metrics
    total_errors = ErrorLog.objects.count()
    unresolved_errors = ErrorLog.objects.filter(is_resolved=False).count()
    critical_errors = ErrorLog.objects.filter(severity='critical', is_resolved=False).count()
    
    # System Alerts
    active_system_alerts = SystemAlert.objects.filter(is_active=True).count()
    critical_system_alerts = SystemAlert.objects.filter(
        is_active=True, 
        severity='critical'
    ).count()
    
    # User Activity Metrics
    active_users_24h = UserSession.objects.filter(
        end_time__gte=last_24h
    ).values('user').distinct().count()
    
    failed_logins_24h = UserActivity.objects.filter(
        activity_type='login',
        created_at__gte=last_24h
    ).filter(
        description__icontains='failed'
    ).count()
    
    # Device Metrics
    active_devices = DeviceConnection.objects.filter(is_active=True).count()
    total_devices = DeviceConnection.objects.count()
    
    # System Performance Metrics
    avg_response_time = SystemPerformance.objects.filter(
        metric_name='api_response_time'
    ).aggregate(avg_value=Avg('metric_value'))['avg_value'] or 0
    
    db_health_score = SystemPerformance.objects.filter(
        metric_name='db_health_score'
    ).aggregate(latest_score=Avg('metric_value'))['latest_score'] or 100
    
    # Recent Activity
    recent_errors = ErrorLog.objects.order_by('-created_at')[:10]
    recent_alerts = SystemAlert.objects.order_by('-created_at')[:5]
    recent_activities = UserActivity.objects.order_by('-created_at')[:10]
    
    context = {
        # Error Overview
        'total_errors': total_errors,
        'unresolved_errors': unresolved_errors,
        'critical_errors': critical_errors,
        'error_trend': 'increasing' if unresolved_errors > 10 else 'stable',
        
        # System Alerts
        'active_system_alerts': active_system_alerts,
        'critical_system_alerts': critical_system_alerts,
        'alert_trend': 'stable',
        
        # User Activity
        'active_users_24h': active_users_24h,
        'failed_logins_24h': failed_logins_24h,
        'user_activity_trend': 'active' if active_users_24h > 5 else 'low',
        
        # Device Metrics
        'active_devices': active_devices,
        'total_devices': total_devices,
        'device_utilization': 'high' if active_devices > total_devices * 0.8 else 'normal',
        
        # System Performance
        'avg_response_time': avg_response_time,
        'db_health_score': db_health_score,
        'system_health': 'optimal' if db_health_score > 90 else 'degraded',
        
        # Recent Data
        'recent_errors': recent_errors,
        'recent_alerts': recent_alerts,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'NDtechTrack/master_dashboard.html', context)

@login_required
def error_patterns(request):
    """Analyze user error patterns and recurring issues"""
    
    # Permission check
    if not (request.user.is_superuser or 
            (hasattr(request.user, 'userprofile') and 
             request.user.userprofile.role in ['admin', 'manager'])):
        return HttpResponseForbidden("You do not have permission to access this page.")
    
    # Get error patterns for all users or specific user
    user_id = request.GET.get('user_id')
    days = int(request.GET.get('days', 30))
    
    if user_id:
        patterns = UserErrorPattern.objects.filter(user_id=user_id)
        title = f"Error Patterns for User ID: {user_id}"
    else:
        patterns = UserErrorPattern.objects.all()
        title = "All User Error Patterns"
    
    # Calculate statistics
    total_patterns = patterns.count()
    active_patterns = patterns.filter(is_active=True).count()
    
    context = {
        'patterns': patterns,
        'total_patterns': total_patterns,
        'active_patterns': active_patterns,
        'days': days,
        'title': title,
    }
    
    return render(request, 'NDtechTrack/error_patterns.html', context)

@login_required
def system_performance(request):
    """Detailed system performance monitoring"""
    
    # Permission check
    if not (request.user.is_superuser or 
            (hasattr(request.user, 'userprofile') and 
             request.user.userprofile.role in ['admin', 'manager'])):
        return HttpResponseForbidden("You do not have permission to access this page.")
    
    # Get performance metrics
    performance_metrics = SystemPerformance.objects.all().order_by('-measured_at')
    
    # Calculate health indicators
    db_health = SystemPerformance.objects.filter(
        metric_name='db_health_score'
    ).aggregate(latest=Avg('metric_value'))['latest_score'] or 100
    
    api_response_time = SystemPerformance.objects.filter(
        metric_name='api_response_time'
    ).aggregate(average=Avg('metric_value'))['average'] or 0
    
    server_uptime = SystemPerformance.objects.filter(
        metric_name='server_uptime_percentage'
    ).aggregate(latest=Avg('metric_value'))['latest_score'] or 99.9
    
    context = {
        'performance_metrics': performance_metrics,
        'db_health': db_health,
        'api_response_time': api_response_time,
        'server_uptime': server_uptime,
        'system_overall_health': 'optimal' if db_health > 90 and api_response_time < 500 else 'needs_attention',
    }
    
    return render(request, 'NDtechTrack/system_performance.html', context)

@login_required
def automated_issues(request):
    """Manage automatically detected issues"""
    
    # Permission check
    if not (request.user.is_superuser or 
            (hasattr(request.user, 'userprofile') and 
             request.user.userprofile.role in ['admin', 'manager'])):
        return HttpResponseForbidden("You do not have permission to access this page.")
    
    if request.method == 'POST':
        action = request.POST.get('action')
        issue_id = request.POST.get('issue_id')
        
        if action == 'resolve' and issue_id:
            try:
                issue = AutomatedIssue.objects.get(id=issue_id)
                issue.auto_resolved = True
                issue.resolution_method = 'manual_admin'
                issue.resolved_at = timezone.now()
                issue.save()
                
                return JsonResponse({'success': True, 'message': 'Issue marked as resolved'})
            except AutomatedIssue.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Issue not found'})
        
        elif action == 'escalate' and issue_id:
            try:
                issue = AutomatedIssue.objects.get(id=issue_id)
                # Create a system alert for escalation
                SystemAlert.objects.create(
                    alert_type='high',
                    title=f"Escalated Issue: {issue.issue_type}",
                    message=issue.description,
                    severity='high',
                    auto_escalate=True
                )
                
                return JsonResponse({'success': True, 'message': 'Issue escalated to administrators'})
            except AutomatedIssue.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Issue not found'})
    
    # Get automated issues
    issues = AutomatedIssue.objects.filter(auto_resolved=False).order_by('-created_at')
    
    context = {
        'issues': issues,
        'total_issues': issues.count(),
        'unresolved_issues': issues.filter(auto_resolved=False).count(),
        'critical_issues': issues.filter(severity='critical').count(),
    }
    
    return render(request, 'NDtechTrack/automated_issues.html', context)

@csrf_exempt
def api_error_detector(request):
    """API endpoint for automatic error detection"""
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Detect 404 errors
            if data.get('status_code') == 404:
                AutomatedIssue.objects.create(
                    issue_type='system_error',
                    severity='medium',
                    description=f"404 Error: {data.get('path', 'Unknown path')}",
                    affected_url=data.get('url', ''),
                    detection_method='404_monitor',
                    detection_data={
                        'status_code': data.get('status_code'),
                        'path': data.get('path'),
                        'user_agent': data.get('user_agent'),
                        'ip_address': data.get('ip_address'),
                    }
                )
            
            # Detect AJAX failures
            elif data.get('error_type') == 'ajax_failure':
                AutomatedIssue.objects.create(
                    issue_type='api_error',
                    severity='high',
                    description=f"AJAX Failure: {data.get('error_message', 'Unknown error')}",
                    affected_url=data.get('url', ''),
                    detection_method='ajax_failure',
                    detection_data=data
                )
            
            # Detect JavaScript errors
            elif data.get('error_type') == 'javascript':
                AutomatedIssue.objects.create(
                    issue_type='javascript_error',
                    severity='medium',
                    description=f"JavaScript Error: {data.get('error_message', 'Unknown error')}",
                    affected_url=data.get('url', ''),
                    detection_method='javascript_monitor',
                    detection_data=data,
                    stack_trace=data.get('stack_trace', '')
                )
            
            return JsonResponse({'success': True, 'message': 'Error logged successfully'})
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Only POST method allowed'})

@login_required
def resolve_issue(request):
    """API endpoint to resolve an automated issue"""
    if request.method == 'POST':
        issue_id = request.POST.get('issue_id')
        resolution_notes = request.POST.get('resolution_notes', '')
        
        try:
            issue = AutomatedIssue.objects.get(id=issue_id)
            issue.auto_resolved = True
            issue.resolution_method = 'manual_admin'
            issue.resolution_notes = resolution_notes
            issue.resolved_at = timezone.now()
            issue.save()
            
            return JsonResponse({'success': True, 'message': 'Issue resolved successfully'})
        except AutomatedIssue.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Issue not found'})
    
    return JsonResponse({'success': False, 'error': 'Only POST method allowed'})

@login_required
def escalate_issue(request):
    """API endpoint to escalate an automated issue"""
    if request.method == 'POST':
        issue_id = request.POST.get('issue_id')
        
        try:
            issue = AutomatedIssue.objects.get(id=issue_id)
            
            # Create a system alert for escalation
            alert = SystemAlert.objects.create(
                alert_type='high',
                title=f"Escalated Issue: {issue.issue_type}",
                message=issue.description,
                severity='high',
                auto_escalate=True,
                escalation_threshold_minutes=15  # Escalate faster for manual escalations
            )
            
            # Add affected users if available
            if hasattr(issue, 'detection_data') and issue.detection_data.get('user_id'):
                from django.contrib.auth.models import User
                try:
                    user = User.objects.get(id=issue.detection_data['user_id'])
                    alert.affected_users.add(user)
                except User.DoesNotExist:
                    pass
            
            return JsonResponse({'success': True, 'message': 'Issue escalated successfully'})
        except AutomatedIssue.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Issue not found'})
    
    return JsonResponse({'success': False, 'error': 'Only POST method allowed'})
