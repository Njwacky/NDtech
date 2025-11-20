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
        """Get the current price (sale price if on sale, regular price otherwise)"""
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
