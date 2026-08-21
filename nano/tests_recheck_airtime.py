from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User, AnonymousUser
from rest_framework.test import APIRequestFactory, force_authenticate
from nano.models import UserProfile, AirtimeProduct, AirtimeSale
from nano.views_api_v1 import AirtimeSaleViewSet, IsAdminOrManager


class AirtimeApprovalRecheckTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='a', password='x', is_superuser=True)
        self.manager = User.objects.create_user(username='m', password='x')
        self.cashier = User.objects.create_user(username='c', password='x')
        UserProfile.objects.create(user=self.admin, role='admin')
        UserProfile.objects.create(user=self.manager, role='manager')
        UserProfile.objects.create(user=self.cashier, role='cashier')
        self.product = AirtimeProduct.objects.create(
            name='V R10', network='vodacom', airtime_type='airtime',
            value=Decimal('10'), price=Decimal('10'), stock=100)
        self.sale = AirtimeSale.objects.create(
            airtime_product=self.product, quantity=1, total_price=Decimal('10'),
            customer_phone='0720000000', status='pending', requested_by=self.cashier)

    def _post(self, user, action):
        factory = APIRequestFactory()
        req = factory.post(f'/api/v1/airtime-sales/{self.sale.id}/{action}/', {})
        force_authenticate(req, user=user)
        view = AirtimeSaleViewSet.as_view({'post': action})
        return view(req, pk=self.sale.id)

    # Point 1: cashier blocked from approve
    def test_cashier_cannot_approve(self):
        resp = self._post(self.cashier, 'approve')
        self.assertEqual(resp.status_code, 403)
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.status, 'pending')
        self.assertIsNone(self.sale.approved_by)

    # Point 2: manager allowed
    def test_manager_can_approve(self):
        resp = self._post(self.manager, 'approve')
        self.assertEqual(resp.status_code, 200)
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.status, 'approved')
        self.assertEqual(self.sale.approved_by, self.manager)

    # Point 3: admin allowed
    def test_admin_can_reject(self):
        resp = self._post(self.admin, 'reject')
        self.assertEqual(resp.status_code, 200)
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.status, 'cancelled')

    # Point 4: cashier cannot reach approve via other HTTP methods (PUT/PATCH)
    def test_cashier_cannot_update_status_via_patch(self):
        factory = APIRequestFactory()
        req = factory.patch(f'/api/v1/airtime-sales/{self.sale.id}/', {'status': 'approved'})
        force_authenticate(req, user=self.cashier)
        view = AirtimeSaleViewSet.as_view({'patch': 'partial_update'})
        resp = view(req, pk=self.sale.id)
        # Either 403/405 is acceptable, but status must NOT become 'approved'
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.status, 'pending')

    # Point 5: IsAdminOrManager grants managers AND admins, denies cashiers/anon
    def test_permission_class_logic(self):
        perm = IsAdminOrManager()
        class V: pass
        v = V()
        for u, expected in [(self.admin, True), (self.manager, True), (self.cashier, False)]:
            req = type('R', (), {'user': u})()
            self.assertEqual(perm.has_permission(req, v), expected, u.username)
        anon_req = type('R', (), {'user': AnonymousUser()})()
        self.assertFalse(perm.has_permission(anon_req, v))
