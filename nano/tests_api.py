"""
Comprehensive API tests for NDtech POS system
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal

from .models import (
    UserProfile, Product, Notification, ErrorLog, SecurityAuditLog,
    FCMToken, AirtimeProduct, AirtimeSale, WarehousePrice, PriceComparison
)

# tests in this repo expect a `workspace` variable when creating workspace-scoped rows.
# During these unit tests, we don't need a real workspace relationship (it only scopes queries).
# Provide a safe default so the test suite can construct model instances.
workspace = None




class ProductAPITestCase(APITestCase):
    """Test cases for Product API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin', password='testpass123', is_staff=True, is_superuser=True
        )
        self.manager_user = User.objects.create_user(
            username='manager', password='testpass123'
        )
        self.cashier_user = User.objects.create_user(
            username='cashier', password='testpass123'
        )
        
        # Create user profiles
        UserProfile.objects.create(user=self.admin_user, role='admin')
        UserProfile.objects.create(user=self.manager_user, role='manager')
        UserProfile.objects.create(user=self.cashier_user, role='cashier')
        
        # Create test products
        self.product1 = Product.objects.create(
            name='Test Product 1',
            price=Decimal('10.99'),
            category='basic_groceries',
            stock=50,
            barcode='1234567890123'
        , workspace=workspace)
        self.product2 = Product.objects.create(
            name='Test Product 2',
            price=Decimal('5.99'),
            category='cold_drinks',
            stock=5,
            barcode='1234567890124'
        , workspace=workspace)

    def test_get_product_list(self):
        """Test getting list of products"""
        self.client.force_authenticate(user=self.cashier_user)
        response = self.client.get('/api/v1/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_get_product_detail(self):
        """Test getting a single product"""
        self.client.force_authenticate(user=self.cashier_user)
        response = self.client.get(f'/api/v1/products/{self.product1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Product 1')

    def test_create_product_as_manager(self):
        """Test creating a product as manager"""
        self.client.force_authenticate(user=self.manager_user)
        data = {
            'name': 'New Product',
            'price': '15.99',
            'category': 'snacks_chips',
            'stock': 100,
            'barcode': '1234567890125'
        }
        response = self.client.post('/api/v1/products/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 3)

    def test_create_product_as_cashier_fails(self):
        """Test that cashiers cannot create products"""
        self.client.force_authenticate(user=self.cashier_user)
        data = {
            'name': 'New Product',
            'price': '15.99',
            'category': 'snacks_chips',
            'stock': 100
        }
        response = self.client.post('/api/v1/products/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_product_as_manager(self):
        """Test updating a product as manager"""
        self.client.force_authenticate(user=self.manager_user)
        data = {
            'name': 'Updated Product',
            'price': '12.99',
            'category': 'basic_groceries',
            'stock': 75
        }
        response = self.client.patch(f'/api/v1/products/{self.product1.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.name, 'Updated Product')

    def test_delete_product_as_admin(self):
        """Test deleting a product as admin"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(f'/api/v1/products/{self.product1.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.count(), 1)

    def test_filter_products_by_category(self):
        """Test filtering products by category"""
        self.client.force_authenticate(user=self.cashier_user)
        response = self.client.get('/api/v1/products/?category=basic_groceries')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_search_products_by_name(self):
        """Test searching products by name"""
        self.client.force_authenticate(user=self.cashier_user)
        response = self.client.get('/api/v1/products/?search=Product 1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_low_stock_action(self):
        """Test low stock custom action"""
        self.client.force_authenticate(user=self.cashier_user)
        response = self.client.get('/api/v1/products/low_stock/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only product2 has low stock

    def test_barcode_lookup_action(self):
        """Test barcode lookup action"""
        self.client.force_authenticate(user=self.cashier_user)
        response = self.client.get('/api/v1/products/barcode_lookup/?barcode=1234567890123')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Product 1')

    def test_barcode_lookup_not_found(self):
        """Test barcode lookup for non-existent product"""
        self.client.force_authenticate(user=self.cashier_user)
        response = self.client.get('/api/v1/products/barcode_lookup/?barcode=9999999999999')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access API"""
        response = self.client.get('/api/v1/products/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class NotificationAPITestCase(APITestCase):
    """Test cases for Notification API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_user(
            username='admin', password='testpass123', is_superuser=True
        )
        self.cashier_user = User.objects.create_user(
            username='cashier', password='testpass123'
        )
        
        UserProfile.objects.create(user=self.admin_user, role='admin')
        UserProfile.objects.create(user=self.cashier_user, role='cashier')
        
        # Create test notifications
        self.notification1 = Notification.objects.create(
            title='Test Notification 1',
            message='Test message 1',
            notification_type='system_alert',
            target_role='cashier',
            created_by=self.admin_user
        , workspace=workspace)
        self.notification2 = Notification.objects.create(
            title='Test Notification 2',
            message='Test message 2',
            notification_type='low_stock',
            target_user=self.cashier_user,
            created_by=self.admin_user
        , workspace=workspace)

    def test_get_notifications_as_cashier(self):
        """Test cashier getting their notifications"""
        self.client.force_authenticate(user=self.cashier_user)
        response = self.client.get('/api/v1/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should see both notifications (role-targeted and user-targeted)
        self.assertEqual(len(response.data['results']), 2)

    def test_get_notifications_as_admin(self):
        """Test admin getting all notifications"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_mark_notification_as_read(self):
        """Test marking notification as read"""
        self.client.force_authenticate(user=self.cashier_user)
        response = self.client.post(f'/api/v1/notifications/{self.notification1.id}/mark_as_read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification1.refresh_from_db()
        self.assertTrue(self.notification1.is_read)

    def test_mark_all_notifications_as_read(self):
        """Test marking all notifications as read"""
        self.client.force_authenticate(user=self.cashier_user)
        response = self.client.post('/api/v1/notifications/mark_all_as_read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that both notifications are marked as read
        self.notification1.refresh_from_db()
        self.notification2.refresh_from_db()
        self.assertTrue(self.notification1.is_read)
        self.assertTrue(self.notification2.is_read)

    def test_unread_count_action(self):
        """Test getting unread count"""
        self.client.force_authenticate(user=self.cashier_user)
        response = self.client.get('/api/v1/notifications/unread_count/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unread_count'], 2)

    def test_create_notification_as_admin(self):
        """Test creating notification as admin"""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'title': 'New Notification',
            'message': 'New message',
            'notification_type': 'system_alert',
            'target_role': 'manager'
        }
        response = self.client.post('/api/v1/notifications/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.count(), 3)

    def test_filter_notifications_by_type(self):
        """Test filtering notifications by type"""
        self.client.force_authenticate(user=self.cashier_user)
        response = self.client.get('/api/v1/notifications/?notification_type=system_alert')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class ErrorLogAPITestCase(APITestCase):
    """Test cases for ErrorLog API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_user(
            username='admin', password='testpass123', is_superuser=True
        )
        self.cashier_user = User.objects.create_user(
            username='cashier', password='testpass123'
        )
        
        UserProfile.objects.create(user=self.admin_user, role='admin')
        UserProfile.objects.create(user=self.cashier_user, role='cashier')
        
        # Create test error logs
        self.error1 = ErrorLog.objects.create(
            error_type='user_error',
            severity='medium',
            error_message='Test error 1',
            url='/test/url1/',
            request_method='GET',
            user=self.cashier_user
        , workspace=workspace)
        self.error2 = ErrorLog.objects.create(
            error_type='system_error',
            severity='high',
            error_message='Test error 2',
            url='/test/url2/',
            request_method='POST',
            user=self.admin_user
        , workspace=workspace)

    def test_get_error_logs_as_cashier(self):
        """Test cashier getting only their own error logs"""
        self.client.force_authenticate(user=self.cashier_user)
        response = self.client.get('/api/v1/error-logs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Only their own error

    def test_get_error_logs_as_admin(self):
        """Test admin getting all error logs"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/error-logs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # All errors

    def test_resolve_error_as_admin(self):
        """Test resolving an error as admin"""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'resolution_notes': 'Fixed the issue'
        }
        response = self.client.post(f'/api/v1/error-logs/{self.error1.id}/resolve/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.error1.refresh_from_db()
        self.assertTrue(self.error1.is_resolved)
        self.assertEqual(self.error1.resolved_by, self.admin_user)

    def test_resolve_error_as_cashier_fails(self):
        """Test that cashiers cannot resolve errors"""
        self.client.force_authenticate(user=self.cashier_user)
        data = {
            'resolution_notes': 'Trying to fix'
        }
        response = self.client.post(f'/api/v1/error-logs/{self.error1.id}/resolve/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_error_statistics_action(self):
        """Test getting error statistics"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/error-logs/statistics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_errors', response.data)
        self.assertIn('unresolved_errors', response.data)
        self.assertIn('by_severity', response.data)

    def test_filter_errors_by_severity(self):
        """Test filtering errors by severity"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/error-logs/?severity=high')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_error_log(self):
        """Test creating an error log"""
        self.client.force_authenticate(user=self.cashier_user)
        data = {
            'error_type': 'validation_error',
            'severity': 'low',
            'error_message': 'New error',
            'url': '/test/new/',
            'request_method': 'GET'
        }
        response = self.client.post('/api/v1/error-logs/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ErrorLog.objects.count(), 3)


class SecurityEventAPITestCase(APITestCase):
    """Test cases for SecurityAuditLog API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_user(
            username='admin', password='testpass123', is_superuser=True
        )
        self.manager_user = User.objects.create_user(
            username='manager', password='testpass123'
        )
        self.cashier_user = User.objects.create_user(
            username='cashier', password='testpass123'
        )
        
        UserProfile.objects.create(user=self.admin_user, role='admin')
        UserProfile.objects.create(user=self.manager_user, role='manager')
        UserProfile.objects.create(user=self.cashier_user, role='cashier')
        
        # Create test security events
        self.event1 = SecurityAuditLog.objects.create(
            event_type='login_success',
            severity='info',
            description='Successful login',
            user=self.cashier_user,
            ip_address='192.168.1.1'
        , workspace=workspace)
        self.event2 = SecurityAuditLog.objects.create(
            event_type='login_failed',
            severity='warning',
            description='Failed login attempt',
            username_attempted='unknown_user',
            ip_address='192.168.1.2'
        , workspace=workspace)

    def test_get_security_logs_as_admin(self):
        """Test admin getting security logs"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/security-logs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_get_security_logs_as_manager(self):
        """Test manager getting security logs"""
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.get('/api/v1/security-logs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_get_security_logs_as_cashier_fails(self):
        """Test that cashiers cannot access security logs"""
        self.client.force_authenticate(user=self.cashier_user)
        response = self.client.get('/api/v1/security-logs/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_security_statistics_action(self):
        """Test getting security statistics"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/security-logs/statistics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_events', response.data)
        self.assertIn('by_severity', response.data)
        self.assertIn('by_type', response.data)

    def test_filter_events_by_type(self):
        """Test filtering events by type"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/security-logs/?event_type=login_success')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_events_by_severity(self):
        """Test filtering events by severity"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/security-logs/?severity=warning')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_search_events_by_description(self):
        """Test searching events by description"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/security-logs/?search=Successful')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class FCMTokenAPITestCase(APITestCase):
    """Test cases for FCMToken API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.user1 = User.objects.create_user(
            username='user1', password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2', password='testpass123'
        )
        
        # Create test FCM tokens
        self.token1 = FCMToken.objects.create(
            user=self.user1,
            token='token1_device1',
            device_id='device1',
            device_type='web'
        , workspace=workspace)
        self.token2 = FCMToken.objects.create(
            user=self.user2,
            token='token2_device1',
            device_id='device2',
            device_type='android'
        , workspace=workspace)

    def test_get_own_tokens(self):
        """Test user getting their own tokens"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get('/api/v1/fcm-tokens/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Only their own token

    def test_create_fcm_token(self):
        """Test creating FCM token"""
        self.client.force_authenticate(user=self.user1)
        data = {
            'token': 'new_token_device1',
            'device_id': 'device1_new',
            'device_type': 'web'
        }
        response = self.client.post('/api/v1/fcm-tokens/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FCMToken.objects.count(), 3)

    def test_deactivate_token(self):
        """Test deactivating a token"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(f'/api/v1/fcm-tokens/{self.token1.id}/deactivate/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.token1.refresh_from_db()
        self.assertFalse(self.token1.is_active)

    def test_cannot_access_other_users_tokens(self):
        """Test that users cannot access other users' tokens"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f'/api/v1/fcm-tokens/{self.token2.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AirtimeProductAPITestCase(APITestCase):
    """Test cases for AirtimeProduct API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_user(
            username='admin', password='testpass123', is_superuser=True
        )
        self.cashier_user = User.objects.create_user(
            username='cashier', password='testpass123'
        )
        
        UserProfile.objects.create(user=self.admin_user, role='admin')
        UserProfile.objects.create(user=self.cashier_user, role='cashier')
        
        # Create test airtime products
        self.airtime1 = AirtimeProduct.objects.create(
            name='Vodacom Airtime R10',
            network='vodacom',
            airtime_type='airtime',
            value=Decimal('10.00'),
            price=Decimal('10.00'),
            stock=50
        , workspace=workspace)
        self.airtime2 = AirtimeProduct.objects.create(
            name='MTN Data R20',
            network='mtn',
            airtime_type='data',
            value=Decimal('20.00'),
            price=Decimal('19.00'),
            stock=3  # Low stock
        , workspace=workspace)

    def test_get_airtime_products(self):
        """Test getting list of airtime products"""
        self.client.force_authenticate(user=self.cashier_user)
        response = self.client.get('/api/v1/airtime-products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_create_airtime_product_as_admin(self):
        """Test creating airtime product as admin"""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'name': 'Telkom Airtime R50',
            'network': 'telkom',
            'airtime_type': 'airtime',
            'value': '50.00',
            'price': '50.00',
            'stock': 100
        }
        response = self.client.post('/api/v1/airtime-products/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AirtimeProduct.objects.count(), 3)

    def test_create_airtime_product_as_cashier_fails(self):
        """Test that cashiers cannot create airtime products"""
        self.client.force_authenticate(user=self.cashier_user)
        data = {
            'name': 'New Airtime',
            'network': 'vodacom',
            'airtime_type': 'airtime',
            'value': '25.00',
            'price': '25.00',
            'stock': 50
        }
        response = self.client.post('/api/v1/airtime-products/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_low_stock_action(self):
        """Test low stock action for airtime products"""
        self.client.force_authenticate(user=self.cashier_user)
        response = self.client.get('/api/v1/airtime-products/low_stock/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only airtime2 has low stock

    def test_filter_airtime_by_network(self):
        """Test filtering airtime products by network"""
        self.client.force_authenticate(user=self.cashier_user)
        response = self.client.get('/api/v1/airtime-products/?network=vodacom')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class AirtimeSaleAPITestCase(APITestCase):
    """Test cases for AirtimeSale API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_user(
            username='admin', password='testpass123', is_superuser=True
        )
        self.manager_user = User.objects.create_user(
            username='manager', password='testpass123'
        )
        self.cashier_user = User.objects.create_user(
            username='cashier', password='testpass123'
        )
        
        UserProfile.objects.create(user=self.admin_user, role='admin')
        UserProfile.objects.create(user=self.manager_user, role='manager')
        UserProfile.objects.create(user=self.cashier_user, role='cashier')
        
        # Create airtime product
        self.airtime_product = AirtimeProduct.objects.create(
            name='Vodacom Airtime R10',
            network='vodacom',
            airtime_type='airtime',
            value=Decimal('10.00'),
            price=Decimal('10.00'),
            stock=100
        , workspace=workspace)
        
        # Create airtime sale
        self.sale = AirtimeSale.objects.create(
            airtime_product=self.airtime_product,
            quantity=1,
            total_price=Decimal('10.00'),
            customer_phone='0721234567',
            status='pending',
            requested_by=self.cashier_user
        , workspace=workspace)

    def test_get_airtime_sales_as_cashier(self):
        """Test cashier getting their own sales"""
        self.client.force_authenticate(user=self.cashier_user)
        response = self.client.get('/api/v1/airtime-sales/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_get_airtime_sales_as_admin(self):
        """Test admin getting all sales"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/airtime-sales/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_approve_sale_as_manager(self):
        """Test approving sale as manager"""
        self.client.force_authenticate(user=self.manager_user)
        data = {
            'approval_notes': 'Approved by manager'
        }
        response = self.client.post(f'/api/v1/airtime-sales/{self.sale.id}/approve/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.status, 'approved')
        self.assertEqual(self.sale.approved_by, self.manager_user)

    def test_approve_sale_as_cashier_fails(self):
        """Test that cashiers cannot approve sales"""
        self.client.force_authenticate(user=self.cashier_user)
        data = {
            'approval_notes': 'Trying to approve'
        }
        response = self.client.post(f'/api/v1/airtime-sales/{self.sale.id}/approve/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_reject_sale_as_manager(self):
        """Test rejecting sale as manager"""
        self.client.force_authenticate(user=self.manager_user)
        data = {
            'approval_notes': 'Insufficient stock'
        }
        response = self.client.post(f'/api/v1/airtime-sales/{self.sale.id}/reject/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.status, 'cancelled')

    def test_create_airtime_sale(self):
        """Test creating airtime sale"""
        self.client.force_authenticate(user=self.cashier_user)
        data = {
            'airtime_product': self.airtime_product.id,
            'quantity': 2,
            'total_price': '20.00',
            'customer_phone': '0739876543'
        }
        response = self.client.post('/api/v1/airtime-sales/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AirtimeSale.objects.count(), 2)

    def test_filter_sales_by_status(self):
        """Test filtering sales by status"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/airtime-sales/?status=pending')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class WarehousePriceAPITestCase(APITestCase):
    """Test cases for WarehousePrice API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        
        # Create test warehouse prices
        self.price1 = WarehousePrice.objects.create(
            product_name='Test Product 1',
            warehouse_name='Shop A',
            price=Decimal('15.99'),
            barcode='1234567890123',
            category='basic_groceries',
            imported_by=self.user
        )
        self.price2 = WarehousePrice.objects.create(
            product_name='Test Product 2',
            warehouse_name='Shop B',
            price=Decimal('12.99'),
            barcode='1234567890124',
            category='cold_drinks',
            imported_by=self.user
        )

    def test_get_warehouse_prices(self):
        """Test getting list of warehouse prices"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/warehouse-prices/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_filter_by_warehouse(self):
        """Test filtering by warehouse name"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/warehouse-prices/?warehouse_name=Shop A')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_search_by_product_name(self):
        """Test searching by product name"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/warehouse-prices/?search=Product 1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_unauthorized_access_fails(self):
        """Test that unauthorized users cannot access warehouse prices"""
        response = self.client.get('/api/v1/warehouse-prices/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PriceComparisonAPITestCase(APITestCase):
    """Test cases for PriceComparison API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        
        # Create test price comparisons
        self.comparison1 = PriceComparison.objects.create(
            product_name='Test Product 1',
            barcode='1234567890123',
            lowest_price=Decimal('12.99'),
            lowest_warehouse='Shop A',
            price_difference=Decimal('3.00'),
            compared_warehouses=['Shop A', 'Shop B'],
            all_prices={'Shop A': '12.99', 'Shop B': '15.99'}
        )
        self.comparison2 = PriceComparison.objects.create(
            product_name='Test Product 2',
            barcode='1234567890124',
            lowest_price=Decimal('8.99'),
            lowest_warehouse='Shop B',
            price_difference=Decimal('2.00'),
            compared_warehouses=['Shop A', 'Shop B'],
            all_prices={'Shop A': '10.99', 'Shop B': '8.99'}
        )

    def test_get_price_comparisons(self):
        """Test getting list of price comparisons"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/price-comparisons/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_top_savings_action(self):
        """Test getting top savings"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/price-comparisons/top_savings/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # Should be ordered by price_difference descending
        self.assertEqual(response.data[0]['product_name'], 'Test Product 1')

    def test_search_by_product_name(self):
        """Test searching by product name"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/price-comparisons/?search=Product 1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_unauthorized_access_fails(self):
        """Test that unauthorized users cannot access price comparisons"""
        response = self.client.get('/api/v1/price-comparisons/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserAPITestCase(APITestCase):
    """Test cases for User API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_user(
            username='admin', password='testpass123', is_superuser=True
        )
        self.cashier_user = User.objects.create_user(
            username='cashier', password='testpass123'
        )
        
        UserProfile.objects.create(user=self.admin_user, role='admin')
        UserProfile.objects.create(user=self.cashier_user, role='cashier')

    def test_get_users(self):
        """Test getting list of users"""
        self.client.force_authenticate(user=self.cashier_user)
        response = self.client.get('/api/v1/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_get_current_user_info(self):
        """Test getting current user info"""
        self.client.force_authenticate(user=self.cashier_user)
        response = self.client.get('/api/v1/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'cashier_user')
        self.assertEqual(response.data['role'], 'cashier')

    def test_search_users_by_username(self):
        """Test searching users by username"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/users/?search=admin')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_unauthorized_access_fails(self):
        """Test that unauthorized users cannot access user API"""
        response = self.client.get('/api/v1/users/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserProfileAPITestCase(APITestCase):
    """Test cases for UserProfile API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_user(
            username='admin', password='testpass123', is_superuser=True
        )
        self.manager_user = User.objects.create_user(
            username='manager', password='testpass123'
        )
        self.cashier_user = User.objects.create_user(
            username='cashier', password='testpass123'
        )
        
        self.admin_profile = UserProfile.objects.create(
            user=self.admin_user, role='admin', created_by=self.admin_user
        )
        self.manager_profile = UserProfile.objects.create(
            user=self.manager_user, role='manager', created_by=self.admin_user
        )
        self.cashier_profile = UserProfile.objects.create(
            user=self.cashier_user, role='cashier', created_by=self.manager_user
        )

    def test_get_user_profiles_as_admin(self):
        """Test admin getting all user profiles"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/user-profiles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)

    def test_get_user_profiles_as_manager(self):
        """Test manager getting user profiles"""
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.get('/api/v1/user-profiles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)

    def test_get_user_profiles_as_cashier_fails(self):
        """Test that cashiers cannot access user profiles"""
        self.client.force_authenticate(user=self.cashier_user)
        response = self.client.get('/api/v1/user-profiles/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_user_profile_as_admin(self):
        """Test creating user profile as admin"""
        new_user = User.objects.create_user(
            username='newuser', password='testpass123'
        )
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'user': new_user.id,
            'role': 'cashier',
            'is_active': True
        }
        response = self.client.post('/api/v1/user-profiles/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserProfile.objects.count(), 4)

    def test_by_role_action(self):
        """Test getting users by role"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/user-profiles/by_role/?role=cashier')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only one cashier

    def test_filter_profiles_by_role(self):
        """Test filtering profiles by role"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/user-profiles/?role=admin')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
