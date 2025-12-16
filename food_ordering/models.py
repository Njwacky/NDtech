from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json
import uuid

# Import tracking models from nano app for integration
from nano.models import ErrorLog, UserActivity, DeviceConnection

class Restaurant(models.Model):
    """Restaurant/Shop model for food ordering system"""
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='restaurants')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField()
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    
    # Delivery zones are handled by DeliveryZone model
    
    # Operating hours as JSON - e.g., {"monday": {"open": "08:00", "close": "22:00"}}
    operating_hours = models.JSONField(default=dict)
    
    # Commission settings
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.15, help_text="Commission rate (0.15 = 15%)")
    
    # Platform settings
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Featured on platform homepage")
    logo = models.ImageField(upload_to='restaurant_logos/', blank=True)
    
    # Delivery settings
    delivery_time_minutes = models.PositiveIntegerField(default=30, help_text="Average delivery time in minutes")
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=50.00, help_text="Minimum order amount")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Restaurant"
        verbose_name_plural = "Restaurants"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class MenuCategory(models.Model):
    """Menu categories for organizing items"""
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menu_categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0, help_text="Order in which this category appears")
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Menu Category"
        verbose_name_plural = "Menu Categories"
        ordering = ['display_order', 'name']

    def __str__(self):
        return f"{self.restaurant.name} - {self.name}"

class MenuItem(models.Model):
    """Individual menu items"""
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menu_items')
    category = models.ForeignKey(MenuCategory, on_delete=models.CASCADE, related_name='menu_items')
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Media
    image = models.ImageField(upload_to='menu_items/', blank=True)
    
    # Inventory and preparation
    ingredients = models.TextField(help_text="List of ingredients")
    allergens = models.JSONField(default=list, help_text="List of allergens")
    preparation_time = models.PositiveIntegerField(default=15, help_text="Preparation time in minutes")
    spice_level = models.CharField(max_length=20, choices=[
        ('mild', 'Mild'),
        ('medium', 'Medium'),
        ('hot', 'Hot'),
        ('extra_hot', 'Extra Hot')
    ], default='medium')
    
    # Availability
    is_available = models.BooleanField(default=True)
    is_vegetarian = models.BooleanField(default=False)
    is_vegan = models.BooleanField(default=False)
    is_gluten_free = models.BooleanField(default=False)
    
    # Popularity tracking
    order_count = models.PositiveIntegerField(default=0, help_text="Number of times ordered")
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Menu Item"
        verbose_name_plural = "Menu Items"
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.restaurant.name} - {self.name}"

class Customer(models.Model):
    """Customer model for ordering system"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)
    
    # Addresses
    default_address = models.TextField()
    delivery_notes = models.TextField(blank=True, help_text="Special delivery instructions")
    
    # Preferences
    favorite_items = models.JSONField(default=list, help_text="List of favorite item IDs")
    dietary_preferences = models.JSONField(default=list, help_text="Dietary restrictions")
    
    # Order history
    total_orders = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.phone})"

class Order(models.Model):
    """Order model for food ordering system"""
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded')
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('cash', 'Cash'),
        ('eft', 'EFT'),
        ('yoco', 'Yoco'),
        ('snapscan', 'SnapScan'),
        ('ozow', 'Ozow'),
        ('mobile_money', 'Mobile Money')
    ]
    
    # Unique identifiers
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=50, unique=True)
    tracking_code = models.CharField(max_length=20, unique=True, blank=True)
    
    # Relationships
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='orders')
    
    # Order details
    items = models.JSONField(default=list, help_text="List of ordered items with quantities")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Delivery information
    delivery_address = models.TextField()
    delivery_instructions = models.TextField(blank=True)
    estimated_delivery_time = models.DateTimeField(null=True, blank=True)
    actual_delivery_time = models.DateTimeField(null=True, blank=True)
    
    # Payment information
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, blank=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_reference = models.CharField(max_length=100, blank=True)
    
    # Status and timestamps
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_number} - {self.customer.user.get_full_name()}"

class DeliveryDriver(models.Model):
    """Delivery driver model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver_profile')
    phone = models.CharField(max_length=20)
    
    # Vehicle information
    vehicle_type = models.CharField(max_length=50, choices=[
        ('motorcycle', 'Motorcycle'),
        ('car', 'Car'),
        ('bicycle', 'Bicycle'),
        ('van', 'Van')
    ])
    license_plate = models.CharField(max_length=20)
    
    # Availability and location
    is_available = models.BooleanField(default=True)
    current_location = models.JSONField(default=dict, help_text="Current GPS location")
    last_location_update = models.DateTimeField(null=True, blank=True)
    
    # Performance metrics
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.0)
    total_deliveries = models.PositiveIntegerField(default=0)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Delivery Driver"
        verbose_name_plural = "Delivery Drivers"

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.phone})"

class DeliveryZone(models.Model):
    """Delivery zones for calculating delivery fees"""
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='delivery_zones')
    name = models.CharField(max_length=100)
    
    # Geographic boundaries (stored as JSON coordinates)
    coordinates = models.JSONField(default=dict, help_text="Delivery area coordinates as JSON")
    center_latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True, help_text="Center point latitude")
    center_longitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True, help_text="Center point longitude")
    
    # Fee structure
    base_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    per_km_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    free_delivery_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Time estimates
    estimated_time_minutes = models.PositiveIntegerField(default=30)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Delivery Zone"
        verbose_name_plural = "Delivery Zones"

    def __str__(self):
        return f"{self.restaurant.name} - {self.name}"

class OrderItem(models.Model):
    """Individual items within an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='order_items')
    
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Customizations
    special_instructions = models.TextField(blank=True)
    additions = models.JSONField(default=list, help_text="Extra additions or modifications")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name} (Order {self.order.order_number})"

class PlatformIntegration(models.Model):
    """Track integrations with external platforms"""
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='integrations')
    
    PLATFORM_CHOICES = [
        ('mr_d_food', 'Mr D Food'),
        ('uber_eats', 'Uber Eats'),
        ('whatsapp', 'WhatsApp Ordering'),
        ('website', 'Self-hosted Website')
    ]
    
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES)
    is_active = models.BooleanField(default=True)
    
    # API credentials (encrypted)
    api_key = models.TextField(blank=True, help_text="Encrypted API key")
    api_secret = models.TextField(blank=True, help_text="Encrypted API secret")
    webhook_url = models.URLField(blank=True, help_text="Webhook URL for platform")
    
    # Sync settings
    last_sync_at = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(max_length=50, default='pending')
    sync_errors = models.JSONField(default=list, help_text="Recent sync errors")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Platform Integration"
        verbose_name_plural = "Platform Integrations"

    def __str__(self):
        return f"{self.restaurant.name} - {self.get_platform_display()}"

class CustomerReview(models.Model):
    """Customer reviews for restaurants and items"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='reviews')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='reviews')
    menu_item = models.ForeignKey(MenuItem, null=True, blank=True, on_delete=models.CASCADE, related_name='reviews')
    
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    
    # Moderation
    is_approved = models.BooleanField(default=False)
    moderation_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Customer Review"
        verbose_name_plural = "Customer Reviews"

    def __str__(self):
        return f"Review by {self.customer} for {self.restaurant}"

# Food Ordering Specific Tracking Models

class FoodOrderingActivity(models.Model):
    """Track food ordering specific activities"""
    ACTIVITY_TYPES = [
        ('restaurant_view', 'Restaurant View'),
        ('menu_browse', 'Menu Browse'),
        ('item_view', 'Menu Item View'),
        ('add_to_cart', 'Add to Cart'),
        ('remove_from_cart', 'Remove from Cart'),
        ('checkout', 'Checkout'),
        ('payment', 'Payment'),
        ('order_placed', 'Order Placed'),
        ('order_cancelled', 'Order Cancelled'),
        ('delivery_tracking', 'Delivery Tracking'),
        ('review_left', 'Review Left'),
        ('search_restaurant', 'Search Restaurant'),
        ('filter_menu', 'Filter Menu'),
        ('barcode_scan', 'Barcode Scan'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='food_activities')
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    
    # Activity details
    description = models.TextField(blank=True)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs')
    
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
            models.Index(fields=['restaurant', 'created_at']),
            models.Index(fields=['order', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.created_at}"

class FoodOrderingError(models.Model):
    """Track food ordering specific errors"""
    ERROR_TYPES = [
        ('order_error', 'Order Error'),
        ('payment_error', 'Payment Error'),
        ('inventory_error', 'Inventory Error'),
        ('delivery_error', 'Delivery Error'),
        ('menu_error', 'Menu Error'),
        ('restaurant_error', 'Restaurant Error'),
        ('customer_error', 'Customer Error'),
        ('integration_error', 'Integration Error'),
        ('validation_error', 'Validation Error'),
        ('api_error', 'API Error'),
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
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='food_errors')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.SET_NULL, null=True, blank=True, related_name='error_logs')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='error_logs')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='error_logs')
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
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_food_errors')
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['error_type', 'severity']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['restaurant', 'created_at']),
            models.Index(fields=['is_resolved']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_error_type_display()} - {self.error_message[:50]}..."
    
    def get_occurrence_count(self):
        """Get how many times this error has occurred"""
        return FoodOrderingError.objects.filter(
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

class FoodOrderingDeviceTracking(models.Model):
    """Track device usage for food ordering app"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='food_device_sessions')
    device_id = models.CharField(max_length=100)
    device_type = models.CharField(max_length=20, choices=[
        ('web', 'Web'),
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('tablet', 'Tablet'),
        ('mobile', 'Mobile'),
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
    
    # Food ordering specific metrics
    restaurants_viewed = models.PositiveIntegerField(default=0)
    menu_items_viewed = models.PositiveIntegerField(default=0)
    orders_placed = models.PositiveIntegerField(default=0)
    cart_additions = models.PositiveIntegerField(default=0)
    checkout_attempts = models.PositiveIntegerField(default=0)
    payments_completed = models.PositiveIntegerField(default=0)
    
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
