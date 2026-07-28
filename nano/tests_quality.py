"""Regression tests for the highest-risk POS API guarantees."""

from decimal import Decimal

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from .models import PendingOrder, Product, UserProfile


class ProductSecurityTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user("admin", password="test-pass-123")
        UserProfile.objects.create(user=self.admin, role="admin")
        self.manager = User.objects.create_user("manager", password="test-pass-123")
        UserProfile.objects.create(user=self.manager, role="manager")
        self.cashier = User.objects.create_user("cashier", password="test-pass-123")
        UserProfile.objects.create(user=self.cashier, role="cashier")
        self.product = Product.objects.create(
            name="Milk",
            price=Decimal("19.99"),
            category="dairy_eggs",
            stock=10,
            barcode="6000000000001",
        )

    def test_product_api_requires_authentication(self):
        response = self.client.get("/api/v1/products/")
        self.assertIn(response.status_code, {
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        })

    def test_cashier_cannot_create_or_edit_product(self):
        self.client.force_authenticate(self.cashier)
        create_response = self.client.post(
            "/api/v1/products/",
            {
                "name": "Bread",
                "price": "15.00",
                "category": "bread_baked",
                "stock": 5,
                "barcode": "6000000000002",
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)
        edit_response = self.client.patch(
            f"/api/v1/products/{self.product.pk}/",
            {"price": "25.00"},
            format="json",
        )
        self.assertEqual(edit_response.status_code, status.HTTP_403_FORBIDDEN)
        self.product.refresh_from_db()
        self.assertEqual(self.product.price, Decimal("19.99"))

    def test_manager_can_create_and_edit_product(self):
        self.client.force_authenticate(self.manager)
        create_response = self.client.post(
            "/api/v1/products/",
            {
                "name": "Bread",
                "price": "15.00",
                "category": "bread_baked",
                "stock": 5,
                "barcode": "6000000000002",
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        edit_response = self.client.patch(
            f"/api/v1/products/{self.product.pk}/",
            {"name": "Full Cream Milk", "price": "21.50"},
            format="json",
        )
        self.assertEqual(edit_response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "Full Cream Milk")
        self.assertEqual(self.product.price, Decimal("21.50"))

    def test_product_api_rejects_invalid_price_and_negative_stock(self):
        self.client.force_authenticate(self.manager)
        response = self.client.post(
            "/api/v1/products/",
            {
                "name": "Invalid",
                "price": "0",
                "category": "bread_baked",
                "stock": -1,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Product.objects.filter(name="Invalid").count(), 0)

    def test_admin_can_edit_product(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            f"/api/v1/products/{self.product.pk}/",
            {"stock": 25},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 25)
