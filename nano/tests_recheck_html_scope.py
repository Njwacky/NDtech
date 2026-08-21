from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from nano.models import Workspace, UserProfile, Product, PendingOrder, CompletedOrder
from nano.views_pos import (
    spaza_pos, add_stock, pending_orders, completed_orders,
    check_low_stock_api, get_product_by_barcode, _scope_by_workspace,
)


class HtmlWorkspaceScopeRecheckTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.ws_a = Workspace.objects.create(name='A')
        self.ws_b = Workspace.objects.create(name='B')
        self.user_a = User.objects.create_user(username='ca', password='x')
        UserProfile.objects.create(user=self.user_a, role='cashier', workspace=self.ws_a)
        self.prod_a = Product.objects.create(name='A Bread', price=Decimal('5'), category='staple_foods', stock=10, workspace=self.ws_a, barcode='111')
        self.prod_b = Product.objects.create(name='B Bread', price=Decimal('7'), category='staple_foods', stock=10, workspace=self.ws_b, barcode='222')
        self.legacy = Product.objects.create(name='Legacy', price=Decimal('9'), category='staple_foods', stock=10, workspace=None, barcode='333')

    def _request(self, method, path, user, **kw):
        req = getattr(self.factory, method)(path, **kw)
        req.user = user
        return req

    # Point 1: spaza_pos only lists A + legacy
    def test_spaza_pos_scope(self):
        req = self._request('get', '/pos/', self.user_a)
        resp = spaza_pos(req)
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn('A Bread', content)
        self.assertNotIn('B Bread', content)

    # Point 2: add_stock GET only lists A + legacy
    def test_add_stock_listing_scope(self):
        req = self._request('get', '/add_stock/', self.user_a)
        resp = add_stock(req)
        content = resp.content.decode()
        self.assertIn('A Bread', content)
        self.assertNotIn('B Bread', content)

    # Point 3: cannot add stock to another workspace's product
    def test_add_stock_cross_workspace_rejected(self):
        before = self.prod_b.stock
        req = self._request('post', '/add_stock/', self.user_a,
                            data={'product_id': str(self.prod_b.id), 'quantity': '5'})
        # follow the redirect manually
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(req, 'session', 'session')
        setattr(req, '_messages', FallbackStorage(req))
        resp = add_stock(req)
        self.assertEqual(resp.status_code, 302)
        self.prod_b.refresh_from_db()
        self.assertEqual(self.prod_b.stock, before)  # unchanged

    # Point 4: barcode lookup scoped
    def test_barcode_lookup_cross_workspace(self):
        req = self._request('get', '/api/get_product_by_barcode/?barcode=222', self.user_a)
        resp = get_product_by_barcode(req)
        import json
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertFalse(data['success'])  # B's product not visible to A

    # Point 5: _scope_by_workspace includes own + NULL, excludes other, superuser sees all
    def test_helper_directly(self):
        qs = _scope_by_workspace(Product.objects, self.user_a)
        ids = set(qs.values_list('id', flat=True))
        self.assertEqual(ids, {self.prod_a.id, self.legacy.id})
        su = User.objects.create_superuser(username='su2', password='x', email='a@b.c')
        self.assertEqual(set(_scope_by_workspace(Product.objects, su).values_list('id', flat=True)),
                         {self.prod_a.id, self.prod_b.id, self.legacy.id})
