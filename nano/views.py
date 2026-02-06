"""
NDtech POS System - Main Views Module
Consolidates all view functions from the split modules for backward compatibility.
"""

# ============================================================================
# IMPORTS FROM SPLIT VIEW MODULES
# ============================================================================

# Authentication Views
from .views.auth_views import (
    register,
    sign_up,
    sign_in,
    logout_view,
    forgot_password,
)

# Dashboard Views
from .views.dashboard_views import (
    home,
    check_low_stock,
)

# User Management Views
from .views.user_views import (
    create_user,
    manage_users,
    edit_user,
    delete_user,
    bulk_delete_users,
)

# Import all other views from views_legacy (these need to be further split)
from .views_legacy import *

# ============================================================================
# EXPORT ALL VIEWS FOR URL IMPORTS
# ============================================================================

__all__ = [
    # Auth views
    'register',
    'sign_up',
    'sign_in',
    'logout_view',
    'forgot_password',
    
    # Dashboard views
    'home',
    'check_low_stock',
    
    # User management views
    'create_user',
    'manage_users',
    'edit_user',
    'delete_user',
    'bulk_delete_users',
    
    # Product & Stock management (from views_legacy)
    'add_stock',
    'manage_sales',
    
    # Order management (from views_legacy)
    'pending_orders',
    'save_order',
    'complete_order',
    'cancel_order',
    'checkout_order',
    'completed_orders',
    'order_details',
    'completed_order_details',
    
    # Notifications (from views_legacy)
    'get_notifications',
    'mark_notification_read',
    'dismiss_notification',
    'create_cashier_request',
    'check_role',
    'check_low_stock_api',
    'get_user_by_username',
    'get_product_by_barcode',
    
    # FCM (from views_legacy)
    'register_fcm_token',
    'send_test_notification',
    'test_fcm_connection',
    'get_user_fcm_tokens',
    'send_price_change_notification',
    
    # Warehouse management (from views_legacy)
    'warehouse_import',
    'warehouse_prices',
    'price_comparisons',
    'price_comparisons_marketing',
    'run_price_comparison_view',
    'price_comparison_details',
    'sync_warehouse_data',
    'export_warehouse_prices',
    'export_price_comparisons',
    'export_marketing_report',
    'marketing_analytics_data',
    'warehouse_api_prices',
    
    # Test pages (from views_legacy)
    'test_notifications_complete',
    'notifications_page',
    'fcm_test_page',
    
    # Tracking (from views_legacy)
    'tracking_dashboard',
    'device_tracking',
    'error_tracking',
    'error_details',
    'resolve_error',
    'user_activity_tracking',
    'track_device_connection',
    'track_user_activity',
    'log_error',
    
    # PWA (from views_legacy)
    'service_worker',
    'manifest',
    'offline',
    
    # Airtime (from views_legacy)
    'airtime_dashboard',
    'airtime_management',
    'airtime_sales',
    'process_airtime_sale',
    'approve_airtime_sale',
    'reject_airtime_sale',
    'airtime_requests_management',
    'approve_airtime_request',
    'reject_airtime_request',
    'process_quick_airtime_sale',
    'cashier_airtime_quick_sell',
    'airtime_history_review',
    'verify_airtime_phone',
    'process_cashier_airtime_sale',
]
