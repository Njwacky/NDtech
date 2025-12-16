from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# Create your models here.

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('superuser', 'Superuser'),
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('cashier', 'Cashier'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='cashier')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_users')
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

    def can_create_users(self):
        """Check if this user can create other users"""
        return self.role in ['superuser', 'admin']
    
    def can_manage_users(self):
        """Check if this user can manage (edit/delete) other users"""
        return self.role in ['superuser', 'admin']
    
    def can_create_products(self):
        """Check if this user can create products"""
        return self.role in ['superuser', 'admin', 'manager']
    
    def can_manage_sales(self):
        """Check if this user can manage sales"""
        return self.role in ['superuser', 'admin', 'manager']

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('staple_foods', 'Staple Foods'),
        ('snacks_chips', 'Snacks & Chips'),
        ('cold_drinks', 'Cold Drinks'),
        ('sweets_treats', 'Sweets & Treats'),
        ('basic_groceries', 'Basic Groceries'),
        ('dairy_eggs', 'Dairy & Eggs'),
        ('bread_baked', 'Bread & Baked Goods'),
        ('canned_goods', 'Canned Goods'),
        ('personal_care', 'Personal Care'),
        ('household_items', 'Household Items'),
        ('airtime_data', 'Airtime & Data'),
        ('frozen_goods', 'Frozen Goods'),
        ('tuckshop_packs', 'Tuckshop Packs'),
        ('stationery', 'Stationery'),
        ('baby_products', 'Baby Products'),
        ('seasonal_items', 'Seasonal Items'),
    ]
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='basic_groceries')
    expiry_date = models.DateField(null=True, blank=True)
    stock = models.IntegerField(default=0)  # Add stock field
    barcode = models.CharField(max_length=50, unique=True, null=True, blank=True)  # Add barcode field
    date_added = models.DateTimeField(default=timezone.now)
    
    # Sale fields
    is_on_sale = models.BooleanField(default=False)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sale_start_date = models.DateTimeField(null=True, blank=True)
    sale_end_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name
    
    def is_currently_on_sale(self):
        """Check if product is currently on sale"""
        if not self.is_on_sale or not self.sale_price:
            return False
        
        now = timezone.now()
        
        # Check if sale has started
        if self.sale_start_date and now < self.sale_start_date:
            return False
        
        # Check if sale has ended
        if self.sale_end_date and now > self.sale_end_date:
            return False
        
        return True
    
    def get_current_price(self):
        """Get current price (sale price if on sale, regular price otherwise)"""
        if self.is_currently_on_sale():
            return self.sale_price
        return self.price
    
    def get_discount_percentage(self):
        """Calculate discount percentage"""
        if not self.is_currently_on_sale() or not self.sale_price:
            return 0
        
        discount = ((self.price - self.sale_price) / self.price) * 100
        return round(discount, 1)
    
    def get_discount_amount(self):
        """Calculate discount amount"""
        if not self.is_currently_on_sale() or not self.sale_price:
            return 0
        
        return self.price - self.sale_price
    
    def is_expired(self):
        """Check if product is expired"""
        if not self.expiry_date:
            return False
        return self.expiry_date < timezone.now().date()

class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.quantity} units"

class PendingOrder(models.Model):
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=15)
    items = models.JSONField()  # Store cart items as JSON
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='pending')  # pending, completed, cancelled
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Order for {self.customer_name} - {self.total}"

class CompletedOrder(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('mobile', 'Mobile Payment'),
    ]
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=15)
    items = models.JSONField()  # Store cart items as JSON
    total = models.DecimalField(max_digits=10, decimal_places=2)
    cash_received = models.DecimalField(max_digits=10, decimal_places=2)
    change_given = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='cash')
    completed_at = models.DateTimeField(auto_now_add=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Completed Order for {self.customer_name} - R{self.total}"

class WarehousePrice(models.Model):
    """Store warehouse price data for comparison"""
    product_name = models.CharField(max_length=200)
    warehouse_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    barcode = models.CharField(max_length=50, null=True, blank=True)
    category = models.CharField(max_length=50, null=True, blank=True)
    stock_quantity = models.IntegerField(null=True, blank=True)
    unit_size = models.CharField(max_length=50, null=True, blank=True)
    date_imported = models.DateTimeField(auto_now_add=True)
    imported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        ordering = ['-date_imported']
        indexes = [
            models.Index(fields=['product_name', 'warehouse_name']),
            models.Index(fields=['barcode']),
        ]
    
    def __str__(self):
        return f"{self.product_name} - {self.warehouse_name} - R{self.price}"

class PriceComparison(models.Model):
    """Store automated price comparison results"""
    product_name = models.CharField(max_length=200)
    barcode = models.CharField(max_length=50, null=True, blank=True)
    lowest_price = models.DecimalField(max_digits=10, decimal_places=2)
    lowest_warehouse = models.CharField(max_length=100)
    price_difference = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    compared_warehouses = models.JSONField(default=list)  # List of warehouse names compared
    all_prices = models.JSONField(default=dict)  # Dictionary of warehouse: price pairs
    comparison_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-comparison_date']
        indexes = [
            models.Index(fields=['product_name']),
            models.Index(fields=['barcode']),
            models.Index(fields=['lowest_price']),
        ]
    
    def __str__(self):
        return f"{self.product_name} - Best: {self.lowest_warehouse} @ R{self.lowest_price}"
    
    def get_savings_percentage(self):
        """Calculate percentage savings compared to average price"""
        if not self.all_prices or len(self.all_prices) < 2:
            return 0
        
        prices = list(self.all_prices.values())
        avg_price = sum(prices) / len(prices)
        if avg_price == 0:
            return 0
        
        savings = ((avg_price - self.lowest_price) / avg_price) * 100
        return round(savings, 1)

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('low_stock', 'Low Stock Alert'),
        ('cashier_request', 'Cashier Request'),
        ('system_alert', 'System Alert'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    target_role = models.CharField(max_length=10, choices=UserProfile.ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    last_reminded = models.DateTimeField(null=True, blank=True)
    reminder_count = models.IntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_notifications')
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='received_notifications')
    
    # For low stock notifications
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    
    # For cashier requests
    request_type = models.CharField(max_length=50, blank=True)
    request_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.get_notification_type_display()}"

    def can_remind(self):
        """Check if notification can be reminded (every 15 minutes)"""
        from django.utils import timezone
        import datetime
        
        if self.is_dismissed:
            return False
            
        now = timezone.now()
        if self.last_reminded:
            time_diff = now - self.last_reminded
            return time_diff >= datetime.timedelta(minutes=15)
        return True
    
    def update_reminder(self):
        """Update reminder timestamp and count"""
        from django.utils import timezone
        self.last_reminded = timezone.now()
        self.reminder_count += 1
        self.save()

class FCMToken(models.Model):
    """Store FCM tokens for push notifications"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fcm_tokens')
    token = models.CharField(max_length=255, unique=True)
    device_id = models.CharField(max_length=100, blank=True, null=True)
    device_type = models.CharField(max_length=20, choices=[
        ('web', 'Web'),
        ('android', 'Android'),
        ('ios', 'iOS'),
    ], default='web')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_used']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['token']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.device_type} - {self.token[:20]}..."

class DeviceConnection(models.Model):
    """Track device connections and usage"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device_connections')
    device_id = models.CharField(max_length=100)
    device_type = models.CharField(max_length=20, choices=[
        ('web', 'Web'),
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('tablet', 'Tablet'),
        ('desktop', 'Desktop'),
    ])
    
    # Location information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    location_country = models.CharField(max_length=100, blank=True)
    location_city = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    
    # Session tracking
    session_start = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    session_duration_seconds = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Usage statistics
    page_views = models.PositiveIntegerField(default=0)
    actions_performed = models.PositiveIntegerField(default=0)
    data_transferred_mb = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['device_id']),
            models.Index(fields=['session_start']),
            models.Index(fields=['last_activity']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.device_type} ({self.device_id})"
    
    def get_session_duration_display(self):
        """Get human-readable session duration"""
        if self.session_duration_seconds < 60:
            return f"{self.session_duration_seconds}s"
        elif self.session_duration_seconds < 3600:
            minutes = self.session_duration_seconds // 60
            return f"{minutes}m"
        else:
            hours = self.session_duration_seconds // 3600
            minutes = (self.session_duration_seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    def update_activity(self):
        """Update last activity and recalculate session duration"""
        from django.utils import timezone
        self.last_activity = timezone.now()
        if self.session_start:
            duration = self.last_activity - self.session_start
            self.session_duration_seconds = int(duration.total_seconds())
        self.save()

class ErrorLog(models.Model):
    """Track application errors and user mistakes"""
    ERROR_TYPES = [
        ('user_error', 'User Error'),
        ('system_error', 'System Error'),
        ('validation_error', 'Validation Error'),
        ('permission_error', 'Permission Error'),
        ('api_error', 'API Error'),
        ('database_error', 'Database Error'),
        ('network_error', 'Network Error'),
        ('payment_error', 'Payment Error'),
    ]
    
    ERROR_SEVERITY = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # Error information
    error_type = models.CharField(max_length=20, choices=ERROR_TYPES)
    severity = models.CharField(max_length=10, choices=ERROR_SEVERITY, default='medium')
    error_message = models.TextField()
    error_code = models.CharField(max_length=50, blank=True)
    
    # Context information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='errors')
    device_connection = models.ForeignKey(DeviceConnection, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Request information
    url = models.URLField()
    request_method = models.CharField(max_length=10)
    request_data = models.JSONField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Stack trace and debugging
    stack_trace = models.TextField(blank=True)
    line_number = models.PositiveIntegerField(null=True, blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    function_name = models.CharField(max_length=100, blank=True)
    
    # User action context
    user_action = models.CharField(max_length=100, blank=True, help_text="What the user was trying to do")
    form_data = models.JSONField(null=True, blank=True, help_text="Form data that caused the error")
    
    # Resolution tracking
    is_resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_errors')
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['error_type', 'severity']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['is_resolved']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_error_type_display()} - {self.error_message[:50]}..."
    
    def get_occurrence_count(self):
        """Get how many times this error has occurred"""
        return ErrorLog.objects.filter(
            error_message=self.error_message,
            error_type=self.error_type,
            url=self.url
        ).count()
    
    def mark_resolved(self, resolved_by_user, notes=""):
        """Mark error as resolved"""
        from django.utils import timezone
        self.is_resolved = True
        self.resolved_by = resolved_by_user
        self.resolved_at = timezone.now()
        self.resolution_notes = notes
        self.save()

class UserActivity(models.Model):
    """Track user activities for analytics"""
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('page_view', 'Page View'),
        ('product_view', 'Product View'),
        ('add_to_cart', 'Add to Cart'),
        ('remove_from_cart', 'Remove from Cart'),
        ('checkout', 'Checkout'),
        ('payment', 'Payment'),
        ('search', 'Search'),
        ('filter', 'Filter'),
        ('sort', 'Sort'),
        ('error', 'Error'),
        ('form_submit', 'Form Submit'),
        ('api_call', 'API Call'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    
    # Activity details
    description = models.TextField(blank=True)
    page_url = models.URLField(blank=True)
    object_type = models.CharField(max_length=50, blank=True, help_text="Type of object acted upon")
    object_id = models.PositiveIntegerField(null=True, blank=True, help_text="ID of object acted upon")
    
    # Request context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_connection = models.ForeignKey(DeviceConnection, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Additional data
    metadata = models.JSONField(default=dict, help_text="Additional activity data")
    duration_ms = models.PositiveIntegerField(null=True, blank=True, help_text="Activity duration in milliseconds")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'activity_type', 'created_at']),
            models.Index(fields=['activity_type', 'created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.created_at}"

class AirtimeProduct(models.Model):
    """Separate model for airtime products"""
    NETWORK_CHOICES = [
        ('vodacom', 'Vodacom'),
        ('mtn', 'MTN'),
        ('telkom', 'Telkom'),
        ('cell_c', 'Cell C'),
        ('rain', 'Rain'),
        ('blu', 'BLU'),
    ]
    
    TYPE_CHOICES = [
        ('airtime', 'Airtime'),
        ('data', 'Data'),
        ('sms_bundle', 'SMS Bundle'),
        ('combo', 'Combo'),
    ]
    
    name = models.CharField(max_length=100)
    network = models.CharField(max_length=10, choices=NETWORK_CHOICES)
    airtime_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Value in Rands")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Selling price")
    description = models.TextField(blank=True)
    stock = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    date_added = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_network_display()} {self.get_airtime_type_display()} R{self.value}"
    
    def get_display_name(self):
        """Get formatted display name"""
        return f"{self.get_network_display()} {self.get_airtime_type_display()} - R{self.value}"

class AirtimeSale(models.Model):
    """Track airtime sales"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    airtime_product = models.ForeignKey(AirtimeProduct, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    customer_phone = models.CharField(max_length=15)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Approval tracking
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='airtime_requests')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_airtime')
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    
    # Completion tracking
    completed_at = models.DateTimeField(null=True, blank=True)
    voucher_code = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.airtime_product.name} - {self.customer_phone} ({self.get_status_display()})"
    
    def requires_approval(self):
        """Check if this sale requires approval"""
        user_role = getattr(self.requested_by.userprofile, 'role', 'cashier') if hasattr(self.requested_by, 'userprofile') else 'cashier'
        return user_role == 'cashier' and self.status == 'pending'

class AirtimeRequest(models.Model):
    """Model for cashier airtime requests that need manager approval"""
    REQUEST_TYPE_CHOICES = [
        ('add_airtime', 'Add Airtime Product'),
        ('update_stock', 'Update Airtime Stock'),
        ('bulk_airtime', 'Bulk Airtime Operation'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPE_CHOICES)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='airtime_management_requests')
    target_role = models.CharField(max_length=10, choices=UserProfile.ROLE_CHOICES, default='manager')
    
    # Request details
    title = models.CharField(max_length=200)
    message = models.TextField()
    request_data = models.JSONField(default=dict)
    
    # Approval tracking
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_airtime_requests')
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.requested_by.username} ({self.get_status_display()})"
