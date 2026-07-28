"""Regression tests preventing cross-user data access."""

from decimal import Decimal

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from django.test import TestCase
from django.urls import reverse

from .models import PendingOrder, UserProfile


class UserApiAccessTests(APITestCase):
    def setUp(self):
        self.one = User.objects.create_user("one", password="pass-12345")
        UserProfile.objects.create(user=self.one, role="cashier")
        self.two = User.objects.create_user("two", password="pass-12345")
        UserProfile.objects.create(user=self.two, role="cashier")

    def test_cashier_only_sees_own_user_record(self):
        self.client.force_authenticate(self.one)
        response = self.client.get("/api/v1/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item["id"] for item in response.data["results"]}
        self.assertEqual(ids, {self.one.pk})


class OrderAccessTests(TestCase):
    def setUp(self):
        self.one = User.objects.create_user("one", password="pass-12345")
        UserProfile.objects.create(user=self.one, role="cashier")
        self.two = User.objects.create_user("two", password="pass-12345")
        UserProfile.objects.create(user=self.two, role="cashier")
        self.order = PendingOrder.objects.create(
            user=self.two, customer_name="Customer", customer_phone="0712345678",
            items=[], total=Decimal("0.00"),
        )
        self.client.force_login(self.one)

    def test_cashier_cannot_view_another_users_order(self):
        response = self.client.get(reverse("order_details", args=[self.order.pk]))
        self.assertEqual(response.status_code, 403)
