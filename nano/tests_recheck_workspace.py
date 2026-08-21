from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from nano.models import (
    Workspace, UserProfile, Product, AirtimeProduct, AirtimeSale,
    WarehousePrice, PriceComparison, Notification, ErrorLog, FCMToken,
    PendingOrder, CompletedOrder,
)


class WorkspaceIsolationRecheckTests(TestCase):
    def setUp(self):
        self.ws_a = Workspace.objects.create(name='A')
        self.ws_b = Workspace.objects.create(name='B')
        # Two cashiers, one per workspace.
        self.user_a = User.objects.create_user(username='ca', password='x')
        self.user_b = User.objects.create_user(username='cb', password='x')
        UserProfile.objects.create(user=self.user_a, role='cashier', workspace=self.ws_a)
        UserProfile.objects.create(user=self.user_b, role='cashier', workspace=self.ws_b)
        # Manager in A (admin-like, but NOT superuser)
        self.mgr_a = User.objects.create_user(username='ma', password='x')
        UserProfile.objects.create(user=self.mgr_a, role='manager', workspace=self.ws_a)
        self.superuser = User.objects.create_user(username='su', password='x', is_superuser=True)
        UserProfile.objects.create(user=self.superuser, role='admin', workspace=self.ws_a)

        self.prod_a = Product.objects.create(name='A Bread', price=Decimal('5'), category='staple_foods', stock=10, workspace=self.ws_a)
        self.prod_b = Product.objects.create(name='B Bread', price=Decimal('7'), category='staple_foods', stock=10, workspace=self.ws_b)
        self.legacy = Product.objects.create(name='Legacy Bread', price=Decimal('9'), category='staple_foods', stock=10, workspace=None)

        self.ap_a = AirtimeProduct.objects.create(name='A Airtime', network='vodacom', airtime_type='airtime', value=Decimal('10'), price=Decimal('10'), stock=5, workspace=self.ws_a)
        self.ap_b = AirtimeProduct.objects.create(name='B Airtime', network='mtn', airtime_type='airtime', value=Decimal('10'), price=Decimal('10'), stock=5, workspace=self.ws_b)

        self.sale_a = AirtimeSale.objects.create(airtime_product=self.ap_a, quantity=1, total_price=Decimal('10'), customer_phone='0710000000', requested_by=self.user_a, workspace=self.ws_a)
        self.sale_b = AirtimeSale.objects.create(airtime_product=self.ap_b, quantity=1, total_price=Decimal('10'), customer_phone='0720000000', requested_by=self.user_b, workspace=self.ws_b)

        self.wh_a = WarehousePrice.objects.create(product_name='Sugar', warehouse_name='WA', price=Decimal('12'), workspace=self.ws_a, imported_by=self.mgr_a)
        self.wh_b = WarehousePrice.objects.create(product_name='Sugar', warehouse_name='WB', price=Decimal('15'), workspace=self.ws_b, imported_by=self.mgr_a)
        self.pc_a = PriceComparison.objects.create(product_name='Sugar', lowest_price=Decimal('12'), lowest_warehouse='WA', price_difference=Decimal('3'), compared_warehouses=['WA'], all_prices={'WA': 12.0}, workspace=self.ws_a)
        self.pc_b = PriceComparison.objects.create(product_name='Sugar', lowest_price=Decimal('15'), lowest_warehouse='WB', price_difference=Decimal('0'), compared_warehouses=['WB'], all_prices={'WB': 15.0}, workspace=self.ws_b)

        self.notif_a = Notification.objects.create(title='A notif', message='m', notification_type='system_alert', target_role='cashier', created_by=self.mgr_a, workspace=self.ws_a)
        self.notif_b = Notification.objects.create(title='B notif', message='m', notification_type='system_alert', target_role='cashier', created_by=self.mgr_a, workspace=self.ws_b)

        self.err_a = ErrorLog.objects.create(error_type='user_error', severity='low', error_message='A err', url='/x/', request_method='GET', user=self.user_a, workspace=self.ws_a)
        self.err_b = ErrorLog.objects.create(error_type='user_error', severity='low', error_message='B err', url='/x/', request_method='GET', user=self.user_b, workspace=self.ws_b)

    def _names(self, response, key='results'):
        return {r.get('name') or r.get('title') or r.get('product_name') for r in response.data[key]}

    # Point 1: product list is isolated per workspace
    def test_products_isolated(self):
        c = APIClient(); c.force_authenticate(self.user_a)
        r = c.get('/api/v1/products/')
        self.assertEqual(r.status_code, 200)
        names = self._names(r)
        self.assertIn('A Bread', names)
        self.assertNotIn('B Bread', names)
        self.assertIn('Legacy Bread', names)  # legacy NULL rows visible

    # Point 2: cannot retrieve a product from another workspace directly by ID
    def test_product_detail_cross_workspace_404(self):
        c = APIClient(); c.force_authenticate(self.user_a)
        r = c.get(f'/api/v1/products/{self.prod_b.id}/')
        self.assertEqual(r.status_code, 404)

    # Point 3: airtime sales list isolated
    def test_airtime_sales_isolated(self):
        c = APIClient(); c.force_authenticate(self.user_b)
        r = c.get('/api/v1/airtime-sales/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data['results']), 1)
        self.assertEqual(r.data['results'][0]['customer_phone'], '0720000000')

    # Point 4: warehouse prices & comparisons isolated
    def test_warehouse_isolated(self):
        c = APIClient(); c.force_authenticate(self.user_a)
        r = c.get('/api/v1/warehouse-prices/')
        self.assertEqual(self._names(r), {'Sugar'})
        # only A's price appears
        self.assertEqual(r.data['results'][0]['price'], '12.00')
        r2 = c.get('/api/v1/price-comparisons/')
        self.assertEqual(len(r2.data['results']), 1)
        self.assertEqual(r2.data['results'][0]['lowest_warehouse'], 'WA')

    # Point 5: notifications and error logs isolated; superuser sees all
    def test_notifications_and_superuser(self):
        c = APIClient(); c.force_authenticate(self.user_a)
        rn = c.get('/api/v1/notifications/')
        titles = {n['title'] for n in rn.data['results']}
        self.assertIn('A notif', titles)
        self.assertNotIn('B notif', titles)
        re_ = c.get('/api/v1/error-logs/')
        msgs = {e['error_message'] for e in re_.data['results']}
        self.assertEqual(msgs, {'A err'})
        # superuser sees everything
        c.force_authenticate(self.superuser)
        rp = c.get('/api/v1/products/')
        self.assertEqual(len(rp.data['results']), 3)

    # Point 6 (bonus): manager in A cannot list users from B
    def test_manager_user_list_isolated(self):
        c = APIClient(); c.force_authenticate(self.mgr_a)
        r = c.get('/api/v1/users/')
        usernames = {u['username'] for u in r.data['results']}
        self.assertIn('ca', usernames)
        self.assertIn('ma', usernames)
        self.assertNotIn('cb', usernames)
