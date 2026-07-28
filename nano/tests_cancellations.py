"""Regression tests for order cancellation rules."""

from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import PendingOrder, Product, UserProfile


class OrderCancellationTests(TestCase):
    def setUp(self):
        self.cashier = User.objects.create_user("cashier", password="pass-12345")
        UserProfile.objects.create(user=self.cashier, role="cashier")
        self.product = Product.objects.create(
            name="Bread", price=Decimal("15.00"), category="bread_baked", stock=3
        )
        self.order = PendingOrder.objects.create(
            user=self.cashier,
            customer_name="Customer",
            customer_phone="0712345678",
            items=[{"product_id": self.product.pk, "quantity": 1}],
            total=Decimal("15.00"),
        )
        self.client.force_login(self.cashier)

    def test_cashier_can_cancel_own_pending_order(self):
        response = self.client.post(reverse("cancel_order", args=[self.order.pk]))
        self.assertEqual(response.status_code, 302)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "cancelled")

    def test_completed_order_cannot_be_cancelled(self):
        self.order.status = "completed"
        self.order.save(update_fields=["status"])
        self.client.post(reverse("cancel_order", args=[self.order.pk]))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "completed")
