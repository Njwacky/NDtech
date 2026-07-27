#!/usr/bin/env python3
"""
Script to split views_legacy.py into 3 logical sections:
1. views_core.py - Authentication, Users, Dashboard
2. views_pos.py - POS, Sales, Orders, Inventory
3. views_communications.py - Notifications, FCM, Airtime, Tracking
"""

import re

# Read the original file
with open('views.py', 'r') as f:
    content = f.read()

# Find all function definitions
func_pattern = r'^def (\w+)\(.*\):$'
functions = [(m.group(1), m.start()) for m in re.finditer(func_pattern, content, re.MULTILINE)]

# Define which functions go in which file
core_functions = [
    'check_low_stock', 'home', 'register', 'sign_up', 'sign_in', 'logout_view',
    'forgot_password', 'create_user', 'manage_users', 'edit_user', 'delete_user',
    'bulk_delete_users', 'check_role', 'get_user_by_username'
]

pos_functions = [
    'add_stock', 'manage_sales', 'spaza_pos', 'spaza_pos_complete_sale',
    'pending_orders', 'save_order', 'order_details', 'complete_order',
    'completed_orders', 'completed_order_details', 'checkout', 'cancel_order',
    'checkout_order', 'get_product_by_barcode', 'check_low_stock_api',
    'warehouse_import', 'warehouse_prices', 'price_comparisons',
    'run_price_comparison', 'run_price_comparison_view', 'price_comparison_details',
    'price_comparisons_marketing', 'marketing_analytics_data', 'warehouse_api_prices',
    'sync_warehouse_data', 'export_warehouse_prices', 'export_price_comparisons',
    'export_marketing_report'
]

comm_functions = [
    'get_notifications', 'mark_notification_read', 'mark_all_notifications_read',
    'dismiss_notification', 'create_cashier_request', 'register_fcm_token',
    'send_test_notification', 'test_fcm_connection', 'get_user_fcm_tokens',
    'send_price_change_notification', 'send_fcm_for_notification', 'fcm_test_page',
    'cashier_airtime_quick_sell', 'airtime_history_review', 'verify_airtime_phone',
    'process_cashier_airtime_sale', 'airtime_dashboard', 'airtime_management',
    'airtime_sales', 'process_airtime_sale', 'process_quick_airtime_sale',
    'approve_airtime_sale', 'reject_airtime_sale', 'airtime_requests_management',
    'approve_airtime_request', 'reject_airtime_request', 'airtime_product_status_api',
    'notifications_page', 'test_notifications_complete', 'export_products_excel',
    'service_worker', 'manifest', 'offline', 'tracking_dashboard', 'device_tracking',
    'error_tracking', 'error_details', 'resolve_error', 'user_activity_tracking',
    'track_device_connection', 'track_user_activity', 'log_error'
]

# Categorize functions
core_funcs = set(core_functions)
pos_funcs = set(pos_functions)
comm_funcs = set(comm_functions)

# Find function boundaries
func_boundaries = []
for i, (func_name, start_pos) in enumerate(functions):
    end_pos = functions[i+1][1] if i+1 < len(functions) else len(content)
    func_boundaries.append((func_name, start_pos, end_pos))

# Split content
core_content = []
pos_content = []
comm_content = []

for func_name, start, end in func_boundaries:
    func_content = content[start:end]
    if func_name in core_funcs:
        core_content.append(func_content)
    elif func_name in pos_funcs:
        pos_content.append(func_content)
    elif func_name in comm_funcs:
        comm_content.append(func_content)

# Get the imports (first part of file before first function)
first_func_pos = functions[0][1]
imports = content[:first_func_pos]

# Write the files
import_block = '''"""
{category} Views
"""

{imports}

'''

# Write views_core.py
with open('views_core.py', 'w') as f:
    f.write(import_block.format(
        category='Core/Authentication',
        imports=imports
    ))
    f.write('\n\n'.join(core_content))

print(f"Created views_core.py with {len(core_content)} functions")

# Write views_pos.py
with open('views_pos.py', 'w') as f:
    f.write(import_block.format(
        category='POS/Inventory',
        imports=imports
    ))
    f.write('\n\n'.join(pos_content))

print(f"Created views_pos.py with {len(pos_content)} functions")

# Write views_communications.py
with open('views_communications.py', 'w') as f:
    f.write(import_block.format(
        category='Communications/Tracking',
        imports=imports
    ))
    f.write('\n\n'.join(comm_content))

print(f"Created views_communications.py with {len(comm_content)} functions")

print("\nDone! Now update views.py to import from these modules.")
