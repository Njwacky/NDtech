from django.urls import path
from . import views
from . import views_export
from . import upc_views
from . import food_ordering_integration
from . import views_audit_dashboard

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('sign_in/', views.sign_in, name='sign_in'),
    path('sign_up/', views.sign_up, name='sign_up'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('add_stock/', views.add_stock, name='add_stock'),
    path('manage_sales/', views.manage_sales, name='manage_sales'),
    path('create_user/', views.create_user, name='create_user'),
    path('manage_users/', views.manage_users, name='manage_users'),
    path('edit_user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('bulk_delete_users/', views.bulk_delete_users, name='bulk_delete_users'),
    path('pending_orders/', views.pending_orders, name='pending_orders'),
    path('save_order/', views.save_order, name='save_order'),
    path('pending_orders/<int:order_id>/complete/', views.complete_order, name='complete_order'),
    path('pending_orders/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('pending_orders/<int:order_id>/checkout/', views.checkout_order, name='checkout_order'),
    path('completed_orders/', views.completed_orders, name='completed_orders'),
    path('checkout_order/', views.checkout_order, name='checkout_order_generic'),
    path('order_details/<int:order_id>/', views.order_details, name='order_details'),
    path('completed_order_details/<int:order_id>/', views.completed_order_details, name='completed_order_details'),
    
    # Notification URLs
    path('api/notifications/', views.get_notifications, name='get_notifications'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/<int:notification_id>/dismiss/', views.dismiss_notification, name='dismiss_notification'),
    path('api/cashier_request/', views.create_cashier_request, name='create_cashier_request'),
    path('api/check_role/', views.check_role, name='check_role'),
    path('api/check_low_stock/', views.check_low_stock_api, name='check_low_stock_api'),
    path('api/get_user_by_username/', views.get_user_by_username, name='get_user_by_username'),
    path('api/get_product_by_barcode/', views.get_product_by_barcode, name='get_product_by_barcode'),
    
    # FCM (Firebase Cloud Messaging) URLs
    path('api/fcm/register/', views.register_fcm_token, name='register_fcm_token'),
    path('api/fcm/test/', views.send_test_notification, name='send_test_notification'),
    path('api/fcm/test-connection/', views.test_fcm_connection, name='test_fcm_connection'),
    path('api/fcm/tokens/', views.get_user_fcm_tokens, name='get_user_fcm_tokens'),
    path('api/fcm/price-change/', views.send_price_change_notification, name='send_price_change_notification'),
    
    # Warehouse URLs
    path('warehouse/import/', views.warehouse_import, name='warehouse_import'),
    path('warehouse/prices/', views.warehouse_prices, name='warehouse_prices'),
    path('warehouse/comparisons/', views.price_comparisons, name='price_comparisons'),
    path('warehouse/comparisons/marketing/', views.price_comparisons_marketing, name='price_comparisons_marketing'),
    path('warehouse/run-comparison/', views.run_price_comparison_view, name='run_price_comparison'),
    path('warehouse/price-comparison-details/<int:comparison_id>/', views.price_comparison_details, name='price_comparison_details'),
    path('warehouse/sync/', views.sync_warehouse_data, name='sync_warehouse_data'),
    path('warehouse/export/prices/', views.export_warehouse_prices, name='export_warehouse_prices'),
    path('warehouse/export/comparisons/', views.export_price_comparisons, name='export_price_comparisons'),
    path('warehouse/export/marketing-report/', views.export_marketing_report, name='export_marketing_report'),
    path('warehouse/marketing-analytics-data/', views.marketing_analytics_data, name='marketing_analytics_data'),
    path('api/warehouse/prices/', views.warehouse_api_prices, name='warehouse_api_prices'),
    
    # UPC Lookup URLs
    path('upc/lookup/', upc_views.upc_lookup, name='upc_lookup'),
    path('upc/lookup/<str:barcode>/', upc_views.upc_lookup_detail, name='upc_lookup_detail'),
    path('upc/history/', upc_views.upc_history, name='upc_history'),
    path('upc/scanner/', upc_views.barcode_scanner, name='barcode_scanner'),
    path('api/upc/lookup/', upc_views.api_upc_lookup, name='api_upc_lookup'),
    path('api/upc/lookup/<str:barcode>/', upc_views.api_upc_lookup_detail, name='api_upc_lookup_detail'),
    
    # Food Ordering Integration URLs
    path('food/scanner/', food_ordering_integration.food_scanner_integration, name='food_scanner'),
    path('food/menu/', food_ordering_integration.food_menu_browser, name='food_menu_browser'),
    path('api/food/scanner/lookup/<str:barcode>/', food_ordering_integration.api_food_scanner_lookup, name='api_food_scanner_lookup'),
    path('api/food/add-to-pos/', food_ordering_integration.api_add_food_item_to_pos, name='api_add_food_item_to_pos'),
    
    # Test URLs
    path('test/notifications/', views.test_notifications_complete, name='test_notifications_complete'),
    path('notifications/', views.notifications_page, name='notifications_page'),
    path('test/fcm/', views.fcm_test_page, name='fcm_test_page'),
    
    # Tracking URLs
    path('tracking/', views.tracking_dashboard, name='tracking_dashboard'),
    path('tracking/devices/', views.device_tracking, name='device_tracking'),
    path('tracking/errors/', views.error_tracking, name='error_tracking'),
    path('tracking/errors/<int:error_id>/', views.error_details, name='error_details'),
    path('tracking/errors/<int:error_id>/resolve/', views.resolve_error, name='resolve_error'),
    path('tracking/activities/', views.user_activity_tracking, name='user_activity_tracking'),
    
    # Tracking API URLs
    path('api/tracking/device/', views.track_device_connection, name='track_device_connection'),
    path('api/tracking/activity/', views.track_user_activity, name='track_user_activity'),
    path('api/tracking/error/', views.log_error, name='log_error'),
    
    # PWA URLs
    path('sw.js', views.service_worker, name='service_worker'),
    path('manifest.json', views.manifest, name='manifest'),
    path('offline/', views.offline, name='offline'),
    
    # Export URLs
    path('export/products/excel/', views_export.export_products_excel, name='export_products_excel'),
    
    # Airtime URLs
    path('airtime/', views.airtime_dashboard, name='airtime_dashboard'),
    path('airtime/management/', views.airtime_management, name='airtime_management'),
    path('airtime/sales/', views.airtime_sales, name='airtime_sales'),
    path('airtime/process/', views.process_airtime_sale, name='process_airtime_sale'),
    path('airtime/sales/<int:sale_id>/approve/', views.approve_airtime_sale, name='approve_airtime_sale'),
    path('airtime/sales/<int:sale_id>/reject/', views.reject_airtime_sale, name='reject_airtime_sale'),
    path('airtime/requests/', views.airtime_requests_management, name='airtime_requests_management'),
    path('airtime/requests/<int:request_id>/approve/', views.approve_airtime_request, name='approve_airtime_request'),
    path('airtime/requests/<int:request_id>/reject/', views.reject_airtime_request, name='reject_airtime_request'),
    path('airtime/process-quick/', views.process_quick_airtime_sale, name='process_quick_airtime_sale'),
    path('airtime/cashier-quick-sell/', views.cashier_airtime_quick_sell, name='cashier_airtime_quick_sell'),
    path('airtime/history-review/', views.airtime_history_review, name='airtime_history_review'),
    path('airtime/verify-phone/<int:sale_id>/', views.verify_airtime_phone, name='verify_airtime_phone'),
    path('api/airtime/cashier-process/', views.process_cashier_airtime_sale, name='process_cashier_airtime_sale'),
    
    # Audit Dashboard URLs
    path('audit/', views_audit_dashboard.audit_dashboard, name='audit_dashboard'),
    path('audit/security-events/', views_audit_dashboard.security_events_view, name='security_events'),
    path('audit/data-modifications/', views_audit_dashboard.data_modifications_view, name='data_modifications'),
    path('audit/api-calls/', views_audit_dashboard.api_calls_view, name='api_calls'),
    path('audit/sensitive-data/', views_audit_dashboard.sensitive_data_access_view, name='sensitive_data_access'),
    path('audit/resolve/<int:log_id>/', views_audit_dashboard.resolve_security_event, name='resolve_security_event'),
    path('audit/statistics/', views_audit_dashboard.audit_statistics_api, name='audit_statistics_api'),
]
