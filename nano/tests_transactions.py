"""Regression tests for authentication, stock, and order creation flows."""

import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import CompletedOrder, PendingOrder, Product, UserProfile


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="cashier", password="correct-pass")
        UserProfile.objects.create(user=self.user, role="cashier")

    def test_login_with_valid_credentials(self):
        response = self.client.post(reverse("sign_in"), {
            "username": "cashier",
            "password": "correct-pass",
        })
        self.assertRedirects(response, reverse("home"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_invalid_login_does_not_authenticate(self):
        response = self.client.post(reverse("sign_in"), {
            "username": "cashier",
            "password": "wrong-pass",
        })
        self.assertRedirects(response, reverse("sign_in"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_clears_session(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("register"))
        self.assertNotIn("_auth_user_id", self.client.session)


class StockAndOrderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="cashier", password="pass-12345")
        UserProfile.objects.create(user=self.user, role="cashier")
        self.product = Product.objects.create(
            name="Rice", price=Decimal("30.00"), category="staple_foods", stock=5,
        )
        self.client.force_login(self.user)

    def test_add_stock_increases_quantity(self):
        response = self.client.post(reverse("add_stock"), {
            "mode": "add_stock", "product_id": self.product.pk, "quantity": "3",
        })
        self.assertRedirects(response, reverse("add_stock"))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)

    def test_add_stock_rejects_non_positive_quantity(self):
        self.client.post(reverse("add_stock"), {
            "mode": "add_stock", "product_id": self.product.pk, "quantity": "0",
        })
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)

    def test_save_order_creates_pending_order(self):
        response = self.client.post(
            reverse("save_order"),
            data=json.dumps({
                "items": [{"product_id": self.product.pk, "quantity": 2, "price": "30.00"}],
                "total_amount": "60.00",
                "customer_name": "Customer",
                "customer_phone": "0712345678",
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        order = PendingOrder.objects.get(pk=response.json()["order_id"])
        self.assertEqual(order.status, "pending")
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.total, Decimal("60.00"))

    def test_order_total_uses_server_product_price(self):
        response = self.client.post(
            reverse("save_order"),
            data=json.dumps({
                "items": [{"product_id": self.product.pk, "quantity": 2, "price": "0.01"}],
                "total_amount": "0.02",
                "customer_name": "Customer",
                "customer_phone": "0712345678",
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        order = PendingOrder.objects.get(pk=response.json()["order_id"])
        self.assertEqual(order.total, Decimal("60.00"))
        self.assertEqual(order.items[0]["price"], "30.00")

    def test_retried_save_order_with_same_key_returns_original(self):
        payload = {
            "items": [{"product_id": self.product.pk, "quantity": 1, "price": "30.00"}],
            "total_amount": "30.00",
            "customer_name": "Customer",
            "customer_phone": "0712345678",
            "idempotency_key": "checkout-retry-001",
        }
        first = self.client.post(reverse("save_order"), data=json.dumps(payload), content_type="application/json")
        second = self.client.post(reverse("save_order"), data=json.dumps(payload), content_type="application/json")
        self.assertTrue(first.json()["success"])
        self.assertTrue(second.json()["duplicate"])
        self.assertEqual(first.json()["order_id"], second.json()["order_id"])
        self.assertEqual(PendingOrder.objects.count(), 1)

    def test_checkout_rejects_insufficient_stock_without_creating_sale(self):
        order = PendingOrder.objects.create(
            user=self.user,
            customer_name="Customer",
            customer_phone="0712345678",
            items=[{"product_id": self.product.pk, "quantity": 99, "price": "30.00"}],
            total=Decimal("2970.00"),
        )
        response = self.client.post(reverse("checkout_order", args=[order.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["success"])
        self.assertEqual(CompletedOrder.objects.count(), 0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)

    def test_checkout_completes_order_and_decrements_stock_atomically(self):
        order = PendingOrder.objects.create(
            user=self.user,
            customer_name="Customer",
            customer_phone="0712345678",
            items=[{"product_id": self.product.pk, "quantity": 2, "price": "30.00"}],
            total=Decimal("60.00"),
        )
        response = self.client.post(reverse("checkout_order", args=[order.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"], response.content)
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, "completed")
        self.assertEqual(self.product.stock, 3)

    def test_save_order_requires_login(self):
        self.client.logout()
        response = self.client.post(reverse("save_order"), data="{}", content_type="application/json")
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("sign_in"), response["Location"])
