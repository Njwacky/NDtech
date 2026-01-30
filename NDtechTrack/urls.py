from django.urls import path
from . import views

app_name = 'NDtechTrack'

urlpatterns = [
    # Master Dashboard
    path('', views.master_dashboard, name='master_dashboard'),
    
    # Error Patterns
    path('patterns/', views.error_patterns, name='error_patterns'),
    
    # System Performance
    path('performance/', views.system_performance, name='system_performance'),
    
    # Automated Issues
    path('automated/', views.automated_issues, name='automated_issues'),
    
    # API Endpoints
    path('api/error-detector/', views.api_error_detector, name='api_error_detector'),
    path('api/resolve-issue/', views.resolve_issue, name='resolve_issue'),
    path('api/escalate-issue/', views.escalate_issue, name='escalate_issue'),
]
