"""
API serializers for NDtech POS system
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from .models import (
    UserProfile, Product, Notification, ErrorLog, SecurityAuditLog,
    FCMToken, AirtimeProduct, AirtimeSale, WarehousePrice, PriceComparison,
    DataModificationLog, AdminActionLog, APICallLog, SensitiveDataAccessLog, 
    PendingOrder, CompletedOrder
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

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('Price must be greater than zero.')
        return value

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError('Stock cannot be negative.')
        return value

    def validate(self, attrs):
        sale_price = attrs.get('sale_price')
        price = attrs.get('price', getattr(self.instance, 'price', None))
        if sale_price is not None and price is not None and sale_price <= 0:
            raise serializers.ValidationError({'sale_price': 'Sale price must be greater than zero.'})
        if sale_price is not None and price is not None and sale_price >= price:
            raise serializers.ValidationError({'sale_price': 'Sale price must be lower than the regular price.'})
        return attrs


class OrderItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)


class PendingOrderCreateSerializer(serializers.Serializer):
    items = OrderItemSerializer(many=True, allow_empty=False)
    customer_name = serializers.CharField(max_length=100, allow_blank=False)
    customer_phone = serializers.RegexField(r'^[0-9]{10,15}$')
    idempotency_key = serializers.CharField(max_length=64, required=False, allow_blank=True)


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
    # 5-Whys (accept relative URLs):
    # 1. Why override? Model URLField rejects '/pos/checkout/' style paths with 400.
    # 2. Why do clients send paths? Browser error reporters send window.location.pathname.
    # 3. Why not change the model? A serializer override avoids a schema migration for a validation rule.
    # 4. Why CharField(max_length=200)? Matches URLField's DB column, so no truncation risk.
    url = serializers.CharField(max_length=200)
    
    class Meta:
        model = ErrorLog
        fields = ['id', 'error_type', 'severity', 'error_message', 'error_code',
                 'user', 'username', 'device_connection', 'url', 'request_method',
                 'request_data', 'user_agent', 'ip_address', 'stack_trace',
                 'line_number', 'file_name', 'function_name', 'user_action',
                 'form_data', 'is_resolved', 'resolution_notes', 'resolved_by',
                 'resolved_by_username', 'resolved_at', 'created_at', 'updated_at',
                 'occurrence_count']
        # 5-Whys ('user' made read-only):
        # 1. Why read-only? A writable 'user' let any client attribute errors to any account.
        # 2. Why does that matter? Audit/error trails must be tamper-proof to be trustworthy.
        # 3. Why was it required before? ModelSerializer auto-exposed the FK, breaking POSTs with a 400.
        # 4. Why is the server authoritative? perform_create() stamps request.user - identity comes from the session, never the payload.
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'resolved_at',
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
        # 5-Whys ('user' made read-only):
        # 1. Why read-only? A writable 'user' let a client register a push token under another account.
        # 2. Why is that dangerous? The attacker's device would then receive that user's notifications.
        # 3. Why was registration also broken? The auto-generated required 'user' field 400'd every normal POST.
        # 4. Why fix in the serializer? Token ownership is derived from the session (perform_create), never client input.
        read_only_fields = ['id', 'user', 'created_at', 'last_used']


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
        # 5-Whys ('requested_by' and 'status' made read-only):
        # 1. Why 'requested_by' read-only? Writable, it both 400'd honest clients (required field)
        #    and let dishonest ones book sales against other cashiers.
        # 2. Why 'status' read-only? A cashier could PATCH {'status': 'approved'} on their own
        #    sale, silently bypassing the approve/reject workflow (verified exploitable).
        # 3. Why route transitions through actions? approve()/reject() enforce role checks and
        #    stamp approved_by/approved_at - a bare field write records no accountability.
        # 4. Why keep both in 'fields'? Clients still need to READ who requested and the current
        #    state; read-only removes the write path without breaking API consumers.
        read_only_fields = ['id', 'status', 'requested_by', 'created_at', 'approved_at',
                          'completed_at', 'approved_by', 'approved_by_username', 'voucher_code']


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
    changed_fields_display = serializers.ListField(read_only=True)
    
    class Meta:
        model = DataModificationLog
        fields = ['id', 'user', 'username', 'action_type', 'sensitivity',
                 'content_type', 'object_id', 'object_repr', 'changed_fields',
                 'changed_fields_display', 'ip_address', 'user_agent',
                 'request_method', 'request_url', 'old_values', 'new_values',
                 'reason', 'batch_id', 'created_at']
        read_only_fields = ['id', 'created_at', 'changed_fields_display']


class AdminActionLogSerializer(serializers.ModelSerializer):
    """Serializer for AdminActionLog model"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = AdminActionLog
        fields = ['id', 'user', 'username', 'action_type', 'content_type',
                 'object_id', 'object_repr', 'action_message', 'change_message',
                 'ip_address', 'user_agent', 'affected_objects', 'total_affected',
                 'request_data', 'created_at']
        read_only_fields = ['id', 'created_at', 'total_affected']


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
                 'duration_ms', 'db_query_count', 'memory_usage_mb',
                 'ip_address', 'user_agent', 'api_key_used', 'authentication_method',
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


class PendingOrderSerializer(serializers.ModelSerializer):
    """Serializer for PendingOrder model"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = PendingOrder
        fields = ['id', 'customer_name', 'customer_phone', 'items', 'total',
                 'created_at', 'status', 'user', 'username']
        read_only_fields = ['id', 'created_at', 'user', 'username']


class CompletedOrderSerializer(serializers.ModelSerializer):
    """Serializer for CompletedOrder model with field-level encryption for customer PII"""
    processed_by_username = serializers.CharField(source='processed_by.username', read_only=True)
    
    # Encrypted fields - these will handle decryption automatically
    customer_name_decrypted = serializers.SerializerMethodField()
    customer_phone_decrypted = serializers.SerializerMethodField()
    customer_email_decrypted = serializers.SerializerMethodField()
    
    class Meta:
        model = CompletedOrder
        fields = ['id', 'customer_name', 'customer_name_encrypted', 'customer_name_decrypted',
                 'customer_phone', 'customer_phone_encrypted', 'customer_phone_decrypted',
                 'customer_email', 'customer_email_encrypted', 'customer_email_decrypted',
                 'items', 'total', 'cash_received', 'change_given', 'payment_method',
                 'completed_at', 'processed_by', 'processed_by_username']
        read_only_fields = ['id', 'completed_at', 'processed_by', 'processed_by_username',
                          'customer_name_encrypted', 'customer_phone_encrypted', 
                          'customer_email_encrypted']
    
    def get_customer_name_decrypted(self, obj):
        """Get decrypted customer name"""
        try:
            return obj.get_customer_name()
        except Exception:
            return '[Encrypted]'
    
    def get_customer_phone_decrypted(self, obj):
        """Get decrypted customer phone"""
        try:
            return obj.get_customer_phone()
        except Exception:
            return '[Encrypted]'
    
    def get_customer_email_decrypted(self, obj):
        """Get decrypted customer email"""
        try:
            return obj.get_customer_email()
        except Exception:
            return '[Encrypted]'
    
    def create(self, validated_data):
        """Create completed order with encrypted customer data"""
        # Extract customer data for encryption
        customer_name = validated_data.pop('customer_name', '')
        customer_phone = validated_data.pop('customer_phone', '')
        customer_email = validated_data.pop('customer_email', '')
        
        # Create the order instance
        order = CompletedOrder(**validated_data)
        
        # Set and encrypt customer PII
        order.set_customer_name(customer_name)
        order.set_customer_phone(customer_phone)
        order.set_customer_email(customer_email)
        
        order.save()
        
        # Log sensitive data access
        self._log_sensitive_data_access(order, 'create')
        
        return order
    
    def update(self, instance, validated_data):
        """Update completed order with encrypted customer data"""
        # Handle customer data updates with encryption
        if 'customer_name' in validated_data:
            instance.set_customer_name(validated_data.pop('customer_name'))
        
        if 'customer_phone' in validated_data:
            instance.set_customer_phone(validated_data.pop('customer_phone'))
        
        if 'customer_email' in validated_data:
            instance.set_customer_email(validated_data.pop('customer_email'))
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        # Log sensitive data access
        self._log_sensitive_data_access(instance, 'update')
        
        return instance
    
    def _log_sensitive_data_access(self, order, action_type):
        """Log access to sensitive customer data"""
        try:
            from django.contrib.auth.models import AnonymousUser
            request = self.context.get('request')
            if not request or not hasattr(request, 'user'):
                return
            
            user = request.user
            if user.is_anonymous:
                return
            
            # Log the access
            SensitiveDataAccessLog.objects.create(
                user=user,
                data_type='personal_info',
                access_type=action_type,
                content_type='CompletedOrder',
                object_id=order.id,
                object_repr=str(order),
                sensitive_fields=['customer_name', 'customer_phone', 'customer_email'],
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                request_url=request.build_absolute_uri(),
                access_reason=f'Order {action_type} operation',
                legal_basis='legitimate_interest'
            , workspace=workspace)
        except Exception as e:
            # Don't let logging errors break the main functionality
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to log sensitive data access: {e}")
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# Public-facing serializers with limited data exposure
class PublicCompletedOrderSerializer(serializers.ModelSerializer):
    """Public serializer for CompletedOrder with limited data exposure"""
    
    class Meta:
        model = CompletedOrder
        fields = ['id', 'items', 'total', 'cash_received', 'change_given',
                 'payment_method', 'completed_at']
        read_only_fields = ['id', 'completed_at']


class CustomerDataExportSerializer(serializers.Serializer):
    """Serializer for secure customer data export with encryption"""
    
    def to_representation(self, instance):
        """Export customer data with encryption and audit logging"""
        if not isinstance(instance, CompletedOrder):
            return {}
        
        try:
            # Log the export
            request = self.context.get('request')
            if request and hasattr(request, 'user') and not request.user.is_anonymous:
                SensitiveDataAccessLog.objects.create(
                    user=request.user,
                    data_type='personal_info',
                    access_type='export',
                    content_type='CompletedOrder',
                    object_id=instance.id,
                    object_repr=str(instance),
                    sensitive_fields=['customer_name', 'customer_phone', 'customer_email'],
                    ip_address=self._get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    request_url=request.build_absolute_uri(),
                    access_reason='Customer data export',
                    legal_basis='legitimate_interest'
                , workspace=workspace)
            
            # Return encrypted data
            return {
                'id': instance.id,
                'customer_name': instance.customer_name_encrypted or '[No Data]',
                'customer_phone': instance.customer_phone_encrypted or '[No Data]',
                'customer_email': instance.customer_email_encrypted or '[No Data]',
                'items': instance.items,
                'total': str(instance.total),
                'payment_method': instance.payment_method,
                'completed_at': instance.completed_at.isoformat() if instance.completed_at else None,
                'export_timestamp': timezone.now().isoformat(),
                'data_encrypted': True
            }
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to export customer data: {e}")
            return {'error': 'Export failed', 'id': instance.id}
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
