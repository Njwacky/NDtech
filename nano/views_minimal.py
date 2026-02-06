"""
Minimal Views for NDtech POS System
Essential views with minimal dependencies for quick startup.
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

# Import essential views from views_legacy
from .views_legacy import (
    add_stock,
    manage_sales,
    pending_orders,
    save_order,
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
)

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
    
    # Product & Stock management
    'add_stock',
    'manage_sales',
    
    # Order management
    'pending_orders',
    'save_order',
    'complete_order',
    'cancel_order',
    'checkout_order',
    'completed_orders',
    'order_details',
    'completed_order_details',
    
    # Notifications
    'get_notifications',
    'mark_notification_read',
    'dismiss_notification',
    'create_cashier_request',
    'check_role',
    'check_low_stock_api',
    'get_user_by_username',
    'get_product_by_barcode',
]
