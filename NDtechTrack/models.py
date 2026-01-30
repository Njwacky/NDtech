from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class SystemAlert(models.Model):
    """System-wide alerts that affect multiple users"""
    ALERT_TYPES = [
        ('critical', 'Critical System Issue'),
        ('high', 'High Priority Issue'),
        ('medium', 'Medium Priority Issue'),
        ('low', 'Low Priority Issue'),
        ('info', 'Informational'),
    ]
    
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    severity = models.CharField(max_length=20, choices=ALERT_TYPES)
    
    # Affected systems and users
    affected_users = models.ManyToManyField(User, related_name='affected_alerts', blank=True)
    affected_systems = models.JSONField(default=list)  # List of system names affected
    
    # Resolution tracking
    resolved_by = models.ForeignKey(User, null=True, blank=True, related_name='resolved_alerts', on_delete=models.SET_NULL)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Auto-escalation
    auto_escalate = models.BooleanField(default=False)
    escalation_threshold_minutes = models.IntegerField(default=30)  # Auto-escalate after 30 minutes
    escalated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['alert_type', 'severity', 'created_at']),
            models.Index(fields=['is_active', 'resolved_at']),
            models.Index(fields=['auto_escalate', 'escalated_at']),
        ]
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.title}"
    
    def get_affected_user_count(self):
        """Get count of affected users"""
        return self.affected_users.count()
    
    def requires_immediate_action(self):
        """Check if alert requires immediate action"""
        return self.severity in ['critical', 'high']
    
    def is_overdue(self):
        """Check if alert is overdue for resolution"""
        if self.auto_escalate and not self.escalated_at:
            threshold_time = self.created_at + timezone.timedelta(minutes=self.escalation_threshold_minutes)
            return timezone.now() > threshold_time
        return False

class UserErrorPattern(models.Model):
    """Track recurring error patterns per user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='error_patterns')
    error_type = models.CharField(max_length=50)
    pattern_description = models.TextField()
    occurrence_count = models.IntegerField(default=1)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-occurrence_count', '-last_seen']
        indexes = [
            models.Index(fields=['user', 'error_type']),
            models.Index(fields=['occurrence_count', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.error_type} ({self.occurrence_count} occurrences)"

class SystemPerformance(models.Model):
    """Track system performance metrics"""
    metric_name = models.CharField(max_length=100)
    metric_value = models.DecimalField(max_digits=10, decimal_places=2)
    threshold_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    threshold_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=20, default='count')
    status = models.CharField(max_length=20, choices=[
        ('optimal', 'Optimal'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ])
    measured_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-measured_at']
        indexes = [
            models.Index(fields=['metric_name', 'status']),
            models.Index(fields=['status', 'measured_at']),
        ]
    
    def __str__(self):
        return f"{self.metric_name}: {self.metric_value} {self.unit}"
    
    def is_healthy(self):
        """Check if metric is within healthy range"""
        if self.threshold_min and self.threshold_max:
            return self.threshold_min <= self.metric_value <= self.threshold_max
        return self.status == 'optimal'

class AutomatedIssue(models.Model):
    """Automatically detected issues that need resolution"""
    issue_type = models.CharField(max_length=50)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SystemAlert.ALERT_TYPES)
    affected_url = models.URLField()
    error_details = models.JSONField(default=dict)
    stack_trace = models.TextField(blank=True)
    
    # Detection metadata
    detection_method = models.CharField(max_length=50)  # '404_monitor', 'ajax_failure', etc.
    detection_data = models.JSONField(default=dict)
    
    # Resolution tracking
    auto_resolved = models.BooleanField(default=False)
    resolution_method = models.CharField(max_length=100, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Notification
    notification_sent = models.BooleanField(default=False)
    notification_channels = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['issue_type', 'severity', 'created_at']),
            models.Index(fields=['auto_resolved', 'resolved_at']),
        ]
    
    def __str__(self):
        return f"{self.issue_type} - {self.description[:50]}"

class UserSession(models.Model):
    """Track user sessions for behavior analysis"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_sessions')
    session_id = models.CharField(max_length=100)
    
    # Session metadata
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    
    # Session details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=50, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    
    # Activity tracking
    page_views = models.IntegerField(default=0)
    errors_encountered = models.IntegerField(default=0)
    actions_completed = models.IntegerField(default=0)
    
    # Session status
    is_active = models.BooleanField(default=True)
    ended_naturally = models.BooleanField(default=True)  # False if crashed/timed out
    
    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['user', 'start_time']),
            models.Index(fields=['is_active', 'end_time']),
            models.Index(fields=['device_type', 'start_time']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    def calculate_duration(self):
        """Calculate session duration in minutes"""
        if self.end_time and self.start_time:
            duration = self.end_time - self.start_time
            self.duration_minutes = int(duration.total_seconds() / 60)
            self.save()
        return self.duration_minutes
    
    def is_long_session(self):
        """Check if session is unusually long (> 2 hours)"""
        return self.duration_minutes and self.duration_minutes > 120

class ErrorTrend(models.Model):
    """Track error trends over time for predictive analysis"""
    error_type = models.CharField(max_length=100)
    error_count = models.IntegerField()
    unique_users_affected = models.IntegerField()
    
    # Time period
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    period_type = models.CharField(max_length=20, choices=[
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ])
    
    # Trend analysis
    trend_direction = models.CharField(max_length=20, choices=[
        ('increasing', 'Increasing'),
        ('decreasing', 'Decreasing'),
        ('stable', 'Stable'),
        ('spike', 'Spike'),
    ])
    
    # Predictive metrics
    predicted_next_period = models.IntegerField(null=True, blank=True)
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-period_start']
        indexes = [
            models.Index(fields=['error_type', 'period_start']),
            models.Index(fields=['period_type', 'period_start']),
            models.Index(fields=['trend_direction', 'period_start']),
        ]
    
    def __str__(self):
        return f"{self.error_type} - {self.period_type} ({self.period_start.strftime('%Y-%m-%d')})"

class SystemHealthScore(models.Model):
    """Overall system health score calculation"""
    score = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Component scores
    error_score = models.DecimalField(max_digits=5, decimal_places=2)
    performance_score = models.DecimalField(max_digits=5, decimal_places=2)
    user_activity_score = models.DecimalField(max_digits=5, decimal_places=2)
    system_resource_score = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Health status
    health_status = models.CharField(max_length=20, choices=[
        ('excellent', 'Excellent (>90)'),
        ('good', 'Good (75-90)'),
        ('fair', 'Fair (60-75)'),
        ('poor', 'Poor (<60)'),
    ])
    
    # Recommendations
    recommendations = models.JSONField(default=list)
    critical_issues = models.JSONField(default=list)
    
    calculated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-calculated_at']
        indexes = [
            models.Index(fields=['health_status', 'calculated_at']),
            models.Index(fields=['score', 'calculated_at']),
        ]
    
    def __str__(self):
        return f"Health Score: {self.score} ({self.get_health_status_display()})"
    
    def get_recommendations(self):
        """Get prioritized recommendations based on score"""
        if self.score >= 90:
            return ["System is performing optimally. Continue monitoring."]
        elif self.score >= 75:
            return ["Monitor performance metrics closely.", "Address minor issues before they escalate."]
        elif self.score >= 60:
            return ["Immediate attention required for performance issues.", "Review error patterns and user feedback."]
        else:
            return ["Critical issues require immediate resolution.", "Consider emergency maintenance window."]
