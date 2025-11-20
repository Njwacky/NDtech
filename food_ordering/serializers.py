from rest_framework import serializers
from .models import (
    Restaurant, MenuCategory, MenuItem, Order, Customer,
    DeliveryDriver, DeliveryZone, OrderItem, PlatformIntegration,
    CustomerReview
)

class RestaurantSerializer(serializers.ModelSerializer):
    """Serializer for Restaurant model"""
    owner = serializers.ReadOnlyField(source='owner.get_full_name')
    
    class Meta:
        model = Restaurant
        fields = [
            'id', 'name', 'description', 'phone', 'email', 'address',
            'latitude', 'longitude', 'delivery_zones', 'operating_hours',
            'commission_rate', 'is_active', 'is_featured', 'logo',
            'delivery_time_minutes', 'min_order_amount', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class MenuCategorySerializer(serializers.ModelSerializer):
    """Serializer for MenuCategory model"""
    class Meta:
        model = MenuCategory
        fields = [
            'id', 'restaurant', 'name', 'description', 'display_order',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class MenuItemSerializer(serializers.ModelSerializer):
    """Serializer for MenuItem model"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    
    class Meta:
        model = MenuItem
        fields = [
            'id', 'restaurant', 'category', 'category_name', 'name', 'description',
            'price', 'image', 'ingredients', 'allergens', 'preparation_time',
            'spice_level', 'is_available', 'is_vegetarian', 'is_vegan',
            'is_gluten_free', 'order_count', 'rating', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for OrderItem model"""
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    menu_item_price = serializers.DecimalField(source='menu_item.price', read_only=True, max_digits=10, decimal_places=2)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'order', 'menu_item', 'menu_item_name', 'quantity',
            'unit_price', 'subtotal', 'special_instructions', 'additions',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model"""
    customer_name = serializers.CharField(source='customer.user.get_full_name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    items = OrderItemSerializer(source='orderitem_set', many=True, read_only=True)
    
    # Calculate totals
    subtotal = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    delivery_fee = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    service_fee = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    total_amount = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    
    # Status and timestamps
    status_display = serializers.CharField(read_only=True)
    estimated_delivery_time = serializers.DateTimeField(read_only=True)
    actual_delivery_time = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'tracking_code', 'customer', 'customer_name',
            'customer_phone', 'restaurant', 'restaurant_name', 'items',
            'subtotal', 'delivery_fee', 'service_fee', 'total_amount',
            'delivery_address', 'delivery_instructions', 'payment_method',
            'payment_status', 'estimated_delivery_time', 'actual_delivery_time',
            'status', 'status_display', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for Customer model"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    total_orders = serializers.IntegerField(read_only=True)
    total_spent = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    
    class Meta:
        model = Customer
        fields = [
            'id', 'user', 'user_name', 'user_email', 'phone', 'email',
            'default_address', 'delivery_notes', 'favorite_items',
            'dietary_preferences', 'total_orders', 'total_spent',
            'is_verified', 'verification_code', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class DeliveryDriverSerializer(serializers.ModelSerializer):
    """Serializer for DeliveryDriver model"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    current_location = serializers.JSONField(read_only=True)
    last_location_update = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = DeliveryDriver
        fields = [
            'id', 'user', 'user_name', 'phone', 'vehicle_type',
            'license_plate', 'is_available', 'current_location',
            'last_location_update', 'rating', 'total_deliveries',
            'total_earnings', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class DeliveryZoneSerializer(serializers.ModelSerializer):
    """Serializer for DeliveryZone model"""
    class Meta:
        model = DeliveryZone
        fields = [
            'id', 'restaurant', 'name', 'coordinates', 'center_point',
            'base_fee', 'per_km_fee', 'free_delivery_threshold',
            'estimated_time_minutes', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class PlatformIntegrationSerializer(serializers.ModelSerializer):
    """Serializer for PlatformIntegration model"""
    class Meta:
        model = PlatformIntegration
        fields = [
            'id', 'restaurant', 'platform', 'is_active', 'api_key',
            'api_secret', 'webhook_url', 'last_sync_at', 'sync_status',
            'sync_errors', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class CustomerReviewSerializer(serializers.ModelSerializer):
    """Serializer for CustomerReview model"""
    customer_name = serializers.CharField(source='customer.user.get_full_name', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    
    class Meta:
        model = CustomerReview
        fields = [
            'id', 'customer', 'customer_name', 'restaurant', 'restaurant_name',
            'menu_item', 'menu_item_name', 'rating', 'comment',
            'is_approved', 'moderation_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

# Specialized serializers for API responses

class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating new orders"""
    items = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        error_messages={"required": "At least one item is required"}
    )
    
    delivery_address = serializers.CharField(max_length=500, required=True)
    delivery_instructions = serializers.CharField(
        allow_blank=True,
        max_length=500,
        required=False
    )
    payment_method = serializers.ChoiceField(
        choices=Order.PAYMENT_METHOD_CHOICES,
        required=True
    )
    
    def validate_items(self, value):
        """Validate order items"""
        if not value:
            raise serializers.ValidationError("At least one item is required")
        
        for item in value:
            if 'menu_item_id' not in item:
                raise serializers.ValidationError("Each item must have a menu_item_id")
            if 'quantity' not in item:
                raise serializers.ValidationError("Each item must have a quantity")
            try:
                quantity = int(item['quantity'])
                if quantity <= 0:
                    raise serializers.ValidationError("Quantity must be greater than 0")
            except (ValueError, TypeError):
                raise serializers.ValidationError("Quantity must be a valid number")
        
        return value

class OrderUpdateSerializer(serializers.Serializer):
    """Serializer for updating order status"""
    status = serializers.ChoiceField(choices=Order.ORDER_STATUS_CHOICES)
    notes = serializers.CharField(allow_blank=True, required=False)
    actual_delivery_time = serializers.DateTimeField(allow_null=True, required=False)
    
    def validate_status(self, value):
        """Validate status transitions"""
        # Add business logic for valid status transitions
        return value

class MenuItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new menu items"""
    class Meta:
        model = MenuItem
        fields = [
            'restaurant', 'category', 'name', 'description', 'price',
            'image', 'ingredients', 'allergens', 'preparation_time',
            'spice_level', 'is_available', 'is_vegetarian', 'is_vegan',
            'is_gluten_free'
        ]
    
    def validate_price(self, value):
        """Validate price is positive"""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value

class RestaurantCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new restaurants"""
    operating_hours = serializers.JSONField(required=True)
    delivery_zones = serializers.JSONField(required=True)
    
    class Meta:
        model = Restaurant
        fields = [
            'name', 'description', 'phone', 'email', 'address',
            'latitude', 'longitude', 'operating_hours', 'delivery_zones',
            'commission_rate', 'delivery_time_minutes', 'min_order_amount'
        ]
    
    def validate_operating_hours(self, value):
        """Validate operating hours format"""
        required_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        for day in required_days:
            if day not in value:
                raise serializers.ValidationError(f"{day.title()} hours are required")
        
        for day, hours in value.items():
            if not isinstance(hours, dict):
                raise serializers.ValidationError(f"{day.title()} hours must be a dictionary")
            
            if 'open' not in hours or 'close' not in hours:
                raise serializers.ValidationError(f"{day.title()} must have 'open' and 'close' times")
        
        return value

class CustomerCreateSerializer(serializers.Serializer):
    """Serializer for creating customer profiles"""
    phone = serializers.CharField(max_length=20, required=True)
    email = serializers.EmailField(required=False)
    default_address = serializers.CharField(max_length=500, required=False)
    delivery_notes = serializers.CharField(allow_blank=True, required=False)
    dietary_preferences = serializers.JSONField(required=False)
    favorite_items = serializers.JSONField(required=False)
    
    def validate_phone(self, value):
        """Validate phone number"""
        if len(value) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits")
        return value

class QuickOrderSerializer(serializers.Serializer):
    """Serializer for quick ordering from menu"""
    menu_item_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(min_value=1, required=True)
    special_instructions = serializers.CharField(allow_blank=True, required=False)
    
    def validate_menu_item_id(self, value):
        """Validate menu item exists and is available"""
        try:
            menu_item = MenuItem.objects.get(id=value, is_available=True)
        except MenuItem.DoesNotExist:
            raise serializers.ValidationError("Menu item not found or not available")
        return value
