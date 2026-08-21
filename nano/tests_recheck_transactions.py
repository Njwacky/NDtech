from decimal import Decimal
import json
from django.test import TestCase, RequestFactory, TransactionTestCase
from django.contrib.auth.models import User
from django.db import connection
from nano.models import Workspace, UserProfile, Product, Sale, PendingOrder, CompletedOrder
from nano import views_pos


class TransactionAtomicityRecheckTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.ws = Workspace.objects.create(name='W')
        self.user = User.objects.create_user(username='c', password='x')
        UserProfile.objects.create(user=self.user, role='cashier', workspace=self.ws)
        # Two products: one with plenty of stock, one with insufficient stock.
        self.ok_product = Product.objects.create(
            name='Bread', price=Decimal('5.00'), category='staple_foods',
            stock=100, workspace=self.ws, barcode='BC1')
        self.low_product = Product.objects.create(
            name='Milk', price=Decimal('15.00'), category='dairy_eggs',
            stock=1, workspace=self.ws, barcode='BC2')

    def test_spaza_sale_decrements_stock_and_creates_sales(self):
        payload = {'items': [
            {'product_id': self.ok_product.id, 'quantity': 3}
        ], 'customer_name': 'Alice', 'customer_phone': '0710000000',
           'payment_method': 'cash', 'cash_received': '20'}
        req = self.factory.post('/pos/complete-sale/', data=json.dumps(payload),
                                content_type='application/json')
        req.user = self.user
        resp = views_pos.spaza_pos_complete_sale(req)
        self.assertEqual(resp.status_code, 200)
        self.ok_product.refresh_from_db()
        self.assertEqual(self.ok_product.stock, 97)
        self.assertEqual(Sale.objects.filter(product=self.ok_product).count(), 1)

    def test_spaza_sale_insufficient_stock_rolls_back_completely(self):
        # One item in stock, request 5.
        payload = {'items': [
            {'product_id': self.low_product.id, 'quantity': 5}
        ], 'payment_method': 'cash', 'cash_received': '100'}
        req = self.factory.post('/pos/complete-sale/', data=json.dumps(payload),
                                content_type='application/json')
        req.user = self.user
        resp = views_pos.spaza_pos_complete_sale(req)
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.content)
        self.assertFalse(body['success'])
        # Stock must NOT have been decremented (transaction rolled back)
        self.low_product.refresh_from_db()
        self.assertEqual(self.low_product.stock, 1)
        # No Sale or CompletedOrder rows should exist
        self.assertEqual(Sale.objects.count(), 0)
        self.assertEqual(CompletedOrder.objects.count(), 0)

    def test_checkout_view_is_atomic_and_recalculates_prices(self):
        # Browser submits a tampered price; server should use product price.
        payload = {'items': [
            {'product_id': self.ok_product.id, 'quantity': 2, 'price': '0.01'}
        ], 'total_amount': '0.02'}
        req = self.factory.post('/checkout/', data=json.dumps(payload),
                                content_type='application/json')
        req.user = self.user
        resp = views_pos.checkout(req)
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.content)
        self.assertTrue(body['success'])
        sale = Sale.objects.get(product=self.ok_product)
        # Server price (5.00) used, not tampered 0.01
        self.assertEqual(sale.total_price, Decimal('10.00'))
        self.ok_product.refresh_from_db()
        self.assertEqual(self.ok_product.stock, 98)

    def test_complete_order_rolls_back_when_one_item_oversells(self):
        # Pending order with two items; the second has insufficient stock.
        order = PendingOrder.objects.create(
            customer_name='Bob', customer_phone='0720000000',
            items=[
                {'product_id': self.ok_product.id, 'quantity': 2, 'price': '5.00', 'product': 'Bread'},
                {'product_id': self.low_product.id, 'quantity': 99, 'price': '15.00', 'product': 'Milk'},
            ],
            total=Decimal('1495.00'), status='pending', user=self.user, workspace=self.ws)
        req = self.factory.post(f'/pending_orders/{order.id}/complete/',
                                data={'cash_received': '1500', 'payment_method': 'cash'})
        req.user = self.user
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(req, 'session', 'session')
        setattr(req, '_messages', FallbackStorage(req))
        resp = views_pos.complete_order(req, order.id)
        self.assertEqual(resp.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, 'pending')  # NOT completed
        # First item's stock must have been rolled back too.
        self.ok_product.refresh_from_db()
        self.assertEqual(self.ok_product.stock, 100)
        self.assertEqual(Sale.objects.count(), 0)
        self.assertEqual(CompletedOrder.objects.count(), 0)

    def test_select_for_update_runs_inside_atomic_block(self):
        """Static check: every select_for_update() in views_pos is inside
        a transaction.atomic block (or the enclosing function is decorated
        with @transaction.atomic)."""
        import inspect
        src = inspect.getsource(views_pos)
        lines = src.splitlines()
        bad = []
        for i, line in enumerate(lines):
            if 'select_for_update()' in line and not line.strip().startswith('#'):
                found_atomic = False
                indent = len(line) - len(line.lstrip())
                # Walk upwards; track whether we've crossed the enclosing def.
                crossed_def = False
                for j in range(i - 1, -1, -1):
                    above = lines[j]
                    s = above.strip()
                    above_indent = len(above) - len(above.lstrip())
                    if s.startswith('def ') and above_indent < indent:
                        # Reached the enclosing function def: check decorators
                        # immediately above it (same/lower indent, @-prefixed).
                        k = j - 1
                        while k >= 0 and (lines[k].strip().startswith('@') or lines[k].strip() == ''):
                            if '@transaction.atomic' in lines[k]:
                                found_atomic = True
                            k -= 1
                        crossed_def = True
                        break
                    if 'transaction.atomic()' in above and above_indent < indent:
                        found_atomic = True
                        break
                if not found_atomic:
                    bad.append((i + 1, line.strip()))
        self.assertEqual(bad, [], f'select_for_update outside atomic block: {bad}')
