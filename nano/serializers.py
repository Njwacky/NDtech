"""
API serializers for NDtech POS system
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    UserProfile, Product, Notification, ErrorLog, SecurityAuditLog,
    FCMToken, AirtimeProduct, AirtimeSale, WarehousePrice, PriceComparison,
    DataModificationLog, AdminActionLog, APICallLog, SensitiveDataAccessLog
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    role = serializers.CharField(source='userprofile.role', read_only=True)
    is_active_profile = serializers.BooleanField(source='userprofile.is_active', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'is_staff', 'is_active', 'date_joined', 'role', 'is_active_profile']
        read_only_fields = ['id', 'date_joined', 'is_staff', 'is_active']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'username', 'email', 'role', 'is_active', 
                 'date_created', 'created_by', 'created_by_username']
        read_only_fields = ['id', 'date_created', 'created_by']


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model"""
    current_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_percentage = serializers.FloatField(read_only=True)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_currently_on_sale = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'description', 'category', 'expiry_date',
                 'stock', 'barcode', 'date_added', 'is_on_sale', 'sale_price',
                 'sale_start_date', 'sale_end_date', 'current_price',
                 'discount_percentage', 'discount_amount', 'is_currently_on_sale',
                 'is_expired']
        read_only_fields = ['id', 'date_added']


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    target_user_username = serializers.CharField(source='target_user.username', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'notification_type', 'target_role',
                 'created_at', 'is_read', 'is_dismissed', 'last_reminded',
                 'reminder_count', 'created_by', 'created_by_username',
                 'target_user', 'target_user_username', 'product', 'product_name',
                 'request_type', 'request_data']
        read_only_fields = ['id', 'created_at', 'last_reminded', 'reminder_count',
                          'created_by']


class ErrorLogSerializer(serializers.ModelSerializer):
    """Serializer for ErrorLog model"""
    username = serializers.CharField(source='user.username', read_only=True)
    resolved_by_username = serializers.CharField(source='resolved_by.username', read_only=True)
    occurrence_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ErrorLog
        fields = ['id', 'error_type', 'severity', 'error_message', 'error_code',
                 'user', 'username', 'device_connection', 'url', 'request_method',
                 'request_data', 'user_agent', 'ip_address', 'stack_trace',
                 'line_number', 'file_name', 'function_name', 'user_action',
                 'form_data', 'is_resolved', 'resolution_notes', 'resolved_by',
                 'resolved_by_username', 'resolved_at', 'created_at', 'updated_at',
                 'occurrence_count']
        read_only_fields = ['id', 'created_at', 'updated_at', 'resolved_at',
                          'resolved_by', 'occurrence_count']


class SecurityAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for SecurityAuditLog model"""
    username = serializers.CharField(source='user.username', read_only=True)
    resolved_by_username = serializers.CharField(source='resolved_by.username', read_only=True)
    
    class Meta:
        model = SecurityAuditLog
        fields = ['id', 'user', 'username', 'event_type', 'severity', 'description',
                 'ip_address', 'user_agent', 'username_attempted', 'country', 'city',
                 'session_key', 'request_data', 'response_data', 'detection_method',
                 'confidence_score', 'is_resolved', 'resolved_by', 'resolved_by_username',
                 'resolved_at', 'resolution_notes', 'created_at']
        read_only_fields = ['id', 'created_at', 'resolved_at', 'resolved_by']


class FCMTokenSerializer(serializers.ModelSerializer):
    """Serializer for FCMToken model"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = FCMToken
        fields = ['id', 'user', 'username', 'token', 'device_id', 'device_type',
                 'is_active', 'created_at', 'last_used']
        read_only_fields = ['id', 'created_at', 'last_used']


class AirtimeProductSerializer(serializers.ModelSerializer):
    """Serializer for AirtimeProduct model"""
    display_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = AirtimeProduct
        fields = ['id', 'name', 'network', 'airtime_type', 'value', 'price',
                 'description', 'stock', 'is_active', 'date_added', 'display_name']
        read_only_fields = ['id', 'date_added', 'display_name']


class AirtimeSaleSerializer(serializers.ModelSerializer):
    """Serializer for AirtimeSale model"""
    airtime_product_name = serializers.CharField(source='airtime_product.name', read_only=True)
    requested_by_username = serializers.CharField(source='requested_by.username', read_only=True)
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True)
    
    class Meta:
        model = AirtimeSale
        fields = ['id', 'airtime_product', 'airtime_product_name', 'quantity',
                 'total_price', 'customer_phone', 'status', 'requested_by',
                 'requested_by_username', 'approved_by', 'approved_by_username',
                 'approved_at', 'approval_notes', 'completed_at', 'voucher_code',
                 'created_at']
        read_only_fields = ['id', 'created_at', 'approved_at', 'completed_at',
                          'approved_by', 'approved_by_username', 'voucher_code']


class WarehousePriceSerializer(serializers.ModelSerializer):
    """Serializer for WarehousePrice model"""
    imported_by_username = serializers.CharField(source='imported_by.username', read_only=True)
    
    class Meta:
        model = WarehousePrice
        fields = ['id', 'product_name', 'warehouse_name', 'price', 'barcode',
                 'category', 'stock_quantity', 'unit_size', 'date_imported',
                 'imported_by', 'imported_by_username', 'file_name']
        read_only_fields = ['id', 'date_imported', 'imported_by', 'imported_by_username']


class PriceComparisonSerializer(serializers.ModelSerializer):
    """Serializer for PriceComparison model"""
    savings_percentage = serializers.FloatField(read_only=True)
    
    class Meta:
        model = PriceComparison
        fields = ['id', 'product_name', 'barcode', 'lowest_price', 'lowest_warehouse',
                 'price_difference', 'compared_warehouses', 'all_prices',
                 'comparison_date', 'savings_percentage']
        read_only_fields = ['id', 'comparison_date', 'savings_percentage']


class DataModificationLogSerializer(serializers.ModelSerializer):
    """Serializer for DataModificationLog model"""
    username = serializers.CharField(source='user.username', read_only=True)
    changed_fields_list = serializers.ListField(source='get_changed_fields_display', read_only=True)
    
    class Meta:
        model = DataModificationLog
        fields = ['id', 'user', 'username', 'action_type', 'sensitivity',
                 'content_type', 'object_id', 'object_repr', 'changed_fields',
                 'changed_fields_list', 'ip_address', 'user_agent', 'request_method',
                 'request_url', 'old_values', 'new_values', 'reason', 'batch_id',
                 'created_at']
        read_only_fields = ['id', 'created_at']


class AdminActionLogSerializer(serializers.ModelSerializer):
    """Serializer for AdminActionLog model"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = AdminActionLog
        fields = ['id', 'user', 'username', 'action_type', 'content_type',
                 'object_id', 'object_repr', 'action_message', 'change_message',
                 'ip_address', 'user_agent', 'affected_objects', 'total_affected',
                 'request_data', 'created_at']
        read_only_fields = ['id', 'created_at']


class APICallLogSerializer(serializers.ModelSerializer):
    """Serializer for APICallLog model"""
    username = serializers.CharField(source='user.username', read_only=True)
    is_slow_request = serializers.BooleanField(read_only=True)
    has_security_concerns = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = APICallLog
        fields = ['id', 'user', 'username', 'endpoint_type', 'method', 'endpoint',
                 'view_name', 'request_headers', 'request_body', 'query_params',
                 'status_code', 'status', 'response_headers', 'response_body',
                 'duration_ms', 'db_query_count', 'memory_usage_mb', 'ip_address',
                 'user_agent', 'api_key_used', 'authentication_method',
                 'is_suspicious', 'security_flags', 'is_slow_request',
                 'has_security_concerns', 'created_at']
        read_only_fields = ['id', 'created_at', 'is_slow_request', 'has_security_concerns']


class SensitiveDataAccessLogSerializer(serializers.ModelSerializer):
    """Serializer for SensitiveDataAccessLog model"""
    username = serializers.CharField(source='user.username', read_only=True)
    requires_review = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = SensitiveDataAccessLog
        fields = ['id', 'user', 'username', 'data_type', 'access_type',
                 'content_type', 'object_id', 'object_repr', 'sensitive_fields',
                 'ip_address', 'user_agent', 'request_url', 'session_key',
                 'access_reason', 'legal_basis', 'is_bulk_access', 'total_records',
                 'expires_at', 'requires_review', 'created_at']
        read_only_fields = ['id', 'created_at', 'requires_review']
