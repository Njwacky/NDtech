"""Regression tests for notification visibility and read state."""

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Notification, UserProfile


class NotificationVisibilityTests(APITestCase):
    def setUp(self):
        self.cashier = User.objects.create_user("cashier", password="pass-12345")
        UserProfile.objects.create(user=self.cashier, role="cashier")
        self.manager = User.objects.create_user("manager", password="pass-12345")
        UserProfile.objects.create(user=self.manager, role="manager")
        self.own = Notification.objects.create(
            title="Own", message="Private", notification_type="system_alert",
            target_role="cashier", target_user=self.cashier, created_by=self.manager,
        )
        self.manager_only = Notification.objects.create(
            title="Manager", message="Private", notification_type="system_alert",
            target_role="manager", created_by=self.manager,
        )

    def test_cashier_sees_own_notifications_but_not_manager_only(self):
        self.client.force_authenticate(self.cashier)
        response = self.client.get("/api/v1/notifications/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = {item["title"] for item in response.data["results"]}
        self.assertIn("Own", titles)
        self.assertNotIn("Manager", titles)

    def test_user_can_mark_visible_notification_as_read(self):
        self.client.force_authenticate(self.cashier)
        response = self.client.post(f"/api/v1/notifications/{self.own.pk}/mark_as_read/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.own.refresh_from_db()
        self.assertTrue(self.own.is_read)

    def test_cashier_cannot_create_notification(self):
        self.client.force_authenticate(self.cashier)
        response = self.client.post('/api/v1/notifications/', {
            'title': 'Injected', 'message': 'x', 'notification_type': 'system_alert',
            'target_role': 'cashier',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unread_count_is_scoped_to_visible_notifications(self):
        self.client.force_authenticate(self.cashier)
        response = self.client.get("/api/v1/notifications/unread_count/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["unread_count"], 1)
