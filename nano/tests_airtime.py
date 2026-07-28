"""Regression tests for airtime sales."""

import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import AirtimeProduct, AirtimeSale, UserProfile


class AirtimeSaleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("cashier", password="pass-12345")
        UserProfile.objects.create(user=self.user, role="cashier")
        self.product = AirtimeProduct.objects.create(
            name="MTN R10",
            network="mtn",
            airtime_type="airtime",
            value=Decimal("10.00"),
            price=Decimal("10.00"),
            stock=2,
        )
        self.client.force_login(self.user)

    def test_airtime_sale_rejects_missing_fields(self):
        response = self.client.post(
            reverse("process_quick_airtime_sale"),
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertFalse(response.json()["success"])
        self.assertEqual(AirtimeSale.objects.count(), 0)

    def test_airtime_sale_rejects_invalid_phone(self):
        response = self.client.post(
            reverse("process_quick_airtime_sale"),
            data=json.dumps({
                "network": "mtn", "amount": 10, "type": "airtime",
                "price": 10, "customer_phone": "123", "product_name": "MTN R10",
            }),
            content_type="application/json",
        )
        self.assertFalse(response.json()["success"])
        self.assertEqual(AirtimeSale.objects.count(), 0)

    def test_airtime_sale_completes_and_reduces_stock(self):
        response = self.client.post(
            reverse("process_quick_airtime_sale"),
            data=json.dumps({
                "network": "mtn", "amount": 10, "type": "airtime",
                "price": 10, "customer_phone": "0712345678", "product_name": "MTN R10",
            }),
            content_type="application/json",
        )
        self.assertTrue(response.json()["success"])
        sale = AirtimeSale.objects.get()
        self.assertEqual(sale.status, "completed")
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)
