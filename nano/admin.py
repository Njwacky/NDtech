from django.contrib import admin
from .models import (
    UserProfile, Product, Sale, PendingOrder, CompletedOrder, WarehousePrice, 
    PriceComparison, Notification, FCMToken, DeviceConnection, ErrorLog, UserActivity, 
    AirtimeProduct, AirtimeSale, AirtimeRequest,
    # Audit models
    SecurityAuditLog, DataModificationLog, AdminActionLog, APICallLog, SensitiveDataAccessLog
)

# Original models
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'is_active', 'date_created']
    list_filter = ['role', 'is_active', 'date_created']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['date_created']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'date_added']
    list_filter = ['category', 'date_added']
    search_fields = ['name', 'description']
    readonly_fields = ['date_added']

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity', 'total_price', 'sale_date']
    list_filter = ['sale_date']
    search_fields = ['product__name']

@admin.register(PendingOrder)
class PendingOrderAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'customer_phone', 'total', 'status', 'created_at', 'user']
    list_filter = ['status', 'created_at']
    search_fields = ['customer_name', 'customer_phone']

@admin.register(CompletedOrder)
class CompletedOrderAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'customer_phone', 'total', 'payment_method', 'completed_at', 'processed_by']
    list_filter = ['payment_method', 'completed_at']
    search_fields = ['customer_name', 'customer_phone']

@admin.register(WarehousePrice)
class WarehousePriceAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'warehouse_name', 'price', 'date_imported', 'imported_by']
    list_filter = ['warehouse_name', 'date_imported']
    search_fields = ['product_name', 'warehouse_name']

@admin.register(PriceComparison)
class PriceComparisonAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'lowest_price', 'lowest_warehouse', 'price_difference', 'comparison_date']
    list_filter = ['comparison_date']
    search_fields = ['product_name', 'lowest_warehouse']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'notification_type', 'target_role', 'is_read', 'is_dismissed', 'created_at']
    list_filter = ['notification_type', 'target_role', 'is_read', 'is_dismissed', 'created_at']
    search_fields = ['title', 'message']

@admin.register(FCMToken)
class FCMTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'device_type', 'is_active', 'last_used']
    list_filter = ['device_type', 'is_active', 'last_used']
    search_fields = ['user__username']

@admin.register(DeviceConnection)
class DeviceConnectionAdmin(admin.ModelAdmin):
    list_display = ['user', 'device_type', 'ip_address', 'session_start', 'last_activity', 'is_active']
    list_filter = ['device_type', 'is_active', 'session_start', 'last_activity']
    search_fields = ['user__username', 'ip_address']

@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ['error_type', 'severity', 'error_message', 'user', 'created_at', 'is_resolved']
    list_filter = ['error_type', 'severity', 'created_at', 'is_resolved']
    search_fields = ['error_message', 'url']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type', 'description', 'page_url', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['user__username', 'description']

@admin.register(AirtimeProduct)
class AirtimeProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'network', 'airtime_type', 'value', 'price', 'stock', 'is_active']
    list_filter = ['network', 'airtime_type', 'is_active']
    search_fields = ['name', 'description']

@admin.register(AirtimeSale)
class AirtimeSaleAdmin(admin.ModelAdmin):
    list_display = ['airtime_product', 'quantity', 'total_price', 'customer_phone', 'status', 'requested_by']
    list_filter = ['status', 'created_at']
    search_fields = ['customer_phone', 'airtime_product__name']

@admin.register(AirtimeRequest)
class AirtimeRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'request_type', 'requested_by', 'target_role', 'status', 'created_at']
    list_filter = ['request_type', 'target_role', 'status', 'created_at']
    search_fields = ['title', 'message']

# Audit Logging Models

@admin.register(SecurityAuditLog)
class SecurityAuditLogAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'severity', 'user', 'ip_address', 'created_at', 'is_resolved']
    list_filter = ['event_type', 'severity', 'created_at', 'is_resolved']
    search_fields = ['user__username', 'username_attempted', 'description']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'resolved_by')

@admin.register(DataModificationLog)
class DataModificationLogAdmin(admin.ModelAdmin):
    list_display = ['action_type', 'sensitivity', 'content_type', 'user', 'created_at']
    list_filter = ['action_type', 'sensitivity', 'content_type', 'created_at']
    search_fields = ['user__username', 'object_repr', 'content_type']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')

@admin.register(AdminActionLog)
class AdminActionLogAdmin(admin.ModelAdmin):
    list_display = ['action_type', 'content_type', 'user', 'total_affected', 'created_at']
    list_filter = ['action_type', 'content_type', 'created_at']
    search_fields = ['user__username', 'object_repr', 'content_type']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')

@admin.register(APICallLog)
class APICallLogAdmin(admin.ModelAdmin):
    list_display = ['method', 'endpoint', 'status_code', 'duration_ms', 'user', 'created_at']
    list_filter = ['method', 'status_code', 'endpoint_type', 'created_at', 'is_suspicious']
    search_fields = ['user__username', 'endpoint', 'view_name']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')

@admin.register(SensitiveDataAccessLog)
class SensitiveDataAccessLogAdmin(admin.ModelAdmin):
    list_display = ['data_type', 'access_type', 'user', 'total_records', 'created_at']
    list_filter = ['data_type', 'access_type', 'created_at', 'is_bulk_access']
    search_fields = ['user__username', 'object_repr', 'content_type']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')
