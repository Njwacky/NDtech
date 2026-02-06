"""
NDtech POS System - Views Package
Organizes all view functions into logical modules for better maintainability.

This package consolidates views from multiple sources:
- Core views (auth, dashboard, users, products, orders)
- Specialized views (cashier, warehouse, UPC, audit, export, API)
"""

# ============================================================================
# AUTHENTICATION VIEWS
# ============================================================================
from .auth_views import (
    register,
    sign_up,
    sign_in,
    logout_view,
    forgot_password,
)

# ============================================================================
# DASHBOARD & UTILITIES
# ============================================================================
from .dashboard_views import (
    home,
    check_low_stock,
)

# ============================================================================
# USER MANAGEMENT VIEWS
# ============================================================================
from .user_views import (
    create_user,
    manage_users,
    edit_user,
    delete_user,
    bulk_delete_users,
)

# ============================================================================
# PRODUCT & STOCK MANAGEMENT (from views_legacy.py)
# ============================================================================
from ..views_legacy import (
    add_stock,
    manage_sales,
    save_order,
    pending_orders,
    complete_order,
    cancel_order,
    checkout_order,
    completed_orders,
    order_details,
    completed_order_details,
    get_notifications,
    mark_notification_read,
    dismiss_notification,
    create_cashier_request,
    check_role,
    check_low_stock_api,
    get_user_by_username,
    get_product_by_barcode,
    register_fcm_token,
    send_test_notification,
    test_fcm_connection,
    get_user_fcm_tokens,
    send_price_change_notification,
    warehouse_import,
    warehouse_prices,
    price_comparisons,
    price_comparisons_marketing,
    run_price_comparison_view,
    price_comparison_details,
    sync_warehouse_data,
    export_warehouse_prices,
    export_price_comparisons,
    export_marketing_report,
    marketing_analytics_data,
    warehouse_api_prices,
    test_notifications_complete,
    notifications_page,
    fcm_test_page,
    tracking_dashboard,
    device_tracking,
    error_tracking,
    error_details,
    resolve_error,
    user_activity_tracking,
    track_device_connection,
    track_user_activity,
    log_error,
    service_worker,
    manifest,
    offline,
    airtime_dashboard,
    airtime_management,
    airtime_sales,
    process_airtime_sale,
    approve_airtime_sale,
    reject_airtime_sale,
    airtime_requests_management,
    approve_airtime_request,
    reject_airtime_request,
    process_quick_airtime_sale,
    cashier_airtime_quick_sell,
    airtime_history_review,
    verify_airtime_phone,
    process_cashier_airtime_sale,
)


# ============================================================================
# ORDER MANAGEMENT (from main views.py)
# ============================================================================
# These will be imported from the main views.py as they're extracted
# from ..views import (order_views_here)


# ============================================================================
# SPECIALIZED VIEWS (existing separate files)
# ============================================================================
# These are imported directly in urls.py to avoid circular imports
# Cashier-specific views - from ..cashier_views import *
# Warehouse price comparison views - from ..warehouse_views import *
# UPC/Barcode scanning views - from ..upc_views import *
# Audit dashboard views - from ..views_audit_dashboard import *
# Export/reporting views - from ..views_export import *
# API views (v1) - from ..views_api_v1 import *


# ============================================================================
# EXPORTS - All views available for import
# ============================================================================
__all__ = [
    # Auth
    'register',
    'sign_up',
    'sign_in',
    'logout_view',
    'forgot_password',
    
    # Dashboard
    'home',
    'check_low_stock',
    
    # User Management
    'create_user',
    'manage_users',
    'edit_user',
    'delete_user',
    'bulk_delete_users',
    
    # Product & Stock (still in main views.py)
    'add_stock',
    'manage_sales',
    
    # Note: Specialized views from other modules are also available
    # but not explicitly listed here to avoid duplication
]
