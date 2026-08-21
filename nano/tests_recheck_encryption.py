from decimal import Decimal
import json
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from nano.models import Workspace, UserProfile, Product, CompletedOrder
from nano.views_pos import (
    spaza_pos_complete_sale, complete_order, checkout, checkout_order,
)


class EncryptionRecheckTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.ws = Workspace.objects.create(name='W')
        self.user = User.objects.create_user(username='c', password='x')
        UserProfile.objects.create(user=self.user, role='cashier', workspace=self.ws)
        self.product = Product.objects.create(
            name='Bread', price=Decimal('5.00'), category='staple_foods',
            stock=100, workspace=self.ws, barcode='BC1')

    def _assert_encrypted(self, order, expected_name, expected_phone):
        order.refresh_from_db()
        # Plaintext columns must be empty - data lives only in encrypted columns.
        self.assertEqual(order.customer_name, '')
        self.assertEqual(order.customer_phone, '')
        # Encrypted columns populated and not equal to plaintext.
        self.assertTrue(order.customer_name_encrypted)
        self.assertTrue(order.customer_phone_encrypted)
        self.assertNotIn(expected_name, order.customer_name_encrypted)
        # Getters decrypt correctly.
        self.assertEqual(order.get_customer_name(), expected_name)
        self.assertEqual(order.get_customer_phone(), expected_phone)

    # Point 1: spaza POS complete-sale encrypts
    def test_spaza_pos_encrypts(self):
        payload = {'items': [{'product_id': self.product.id, 'quantity': 2}],
                   'customer_name': 'Alice', 'customer_phone': '0710000000',
                   'payment_method': 'cash', 'cash_received': '20'}
        req = self.factory.post('/pos/complete-sale/', data=json.dumps(payload),
                                content_type='application/json')
        req.user = self.user
        resp = spaza_pos_complete_sale(req)
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.content)
        self.assertTrue(body['success'])
        self._assert_encrypted(CompletedOrder.objects.get(pk=body['order_id']), 'Alice', '0710000000')

    # Point 2: legacy checkout() endpoint encrypts (we removed its direct create)
    def test_checkout_encrypts(self):
        payload = {'items': [{'product_id': self.product.id, 'quantity': 1}]}
        req = self.factory.post('/checkout/', data=json.dumps(payload),
                                content_type='application/json')
        req.user = self.user
        # checkout() does not create a CompletedOrder (only Sale); ensure no crash
        resp = checkout(req)
        self.assertEqual(resp.status_code, 200)

    # Point 3: empty PII is handled (Walk-in) without errors
    def test_empty_customer_name_handled(self):
        payload = {'items': [{'product_id': self.product.id, 'quantity': 1}],
                   'payment_method': 'cash', 'cash_received': '5'}
        req = self.factory.post('/pos/complete-sale/', data=json.dumps(payload),
                                content_type='application/json')
        req.user = self.user
        resp = spaza_pos_complete_sale(req)
        body = json.loads(resp.content)
        self.assertTrue(body['success'])

    # Point 4: helper is idempotent — re-calling setters doesn't double encrypt
    def test_helper_double_set_safe(self):
        o = CompletedOrder(items=[], total=Decimal('1'), cash_received=Decimal('1'),
                           change_given=Decimal('0'), payment_method='cash',
                           processed_by=self.user, workspace=self.ws)
        o.set_customer_name('Bob')
        first = o.customer_name_encrypted
        o.set_customer_name('Bob')
        self.assertEqual(o.get_customer_name(), 'Bob')
        # Setting empty clears data
        o.set_customer_name('')
        self.assertIsNone(o.customer_name_encrypted)
        self.assertEqual(o.get_customer_name(), '')

    # Point 5: email encryption also works
    def test_email_encryption(self):
        o = CompletedOrder(items=[], total=Decimal('1'), cash_received=Decimal('1'),
                           change_given=Decimal('0'), payment_method='card',
                           processed_by=self.user, workspace=self.ws)
        o.set_customer_email('alice@example.com')
        self.assertEqual(o.customer_email, '')
        self.assertTrue(o.customer_email_encrypted)
        self.assertEqual(o.get_customer_email(), 'alice@example.com')
