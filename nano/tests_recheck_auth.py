from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from rest_framework.test import APIClient
from nano.views_communications import get_notifications, register_fcm_token
import json


class AuthRecheckTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='u', password='x')

    # Point 1: anonymous API requests return 401, not 403
    def test_api_returns_401_when_anonymous(self):
        for url in ['/api/v1/products/', '/api/v1/users/',
                    '/api/v1/warehouse-prices/', '/api/v1/price-comparisons/',
                    '/api/v1/airtime-sales/']:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 401, f'{url} -> {r.status_code}')

    # Point 2: WWW-Authenticate header present
    def test_www_authenticate_header(self):
        r = self.client.get('/api/v1/products/')
        self.assertIn('WWW-Authenticate', r)

    # Point 3: get_notifications requires login (redirect 302 to login)
    def test_get_notifications_requires_login(self):
        factory = RequestFactory()
        req = factory.get('/api/notifications/')
        req.user = AnonymousUser()
        resp = get_notifications(req)
        # login_required redirects unauthenticated users to the login URL
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/sign_in/', resp.url)

    # Point 4: register_fcm_token requires login
    def test_register_fcm_requires_login(self):
        factory = RequestFactory()
        req = factory.post('/api/fcm/register/', data=json.dumps({'token': 't'}),
                           content_type='application/json')
        req.user = AnonymousUser()
        resp = register_fcm_token(req)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/sign_in/', resp.url)

    # Point 5: authenticated FCM token registration works and binds to user.
    # Use Django's test client (real session login) because @login_required
    # inspects the session user, unlike DRF's force_authenticate.
    def test_authenticated_fcm_registers(self):
        from django.test import Client
        dj_client = Client()
        dj_client.force_login(self.user)
        r = dj_client.post('/api/fcm/register/',
                           data=json.dumps({'token': 'tok-xyz', 'device_id': 'd', 'device_type': 'web'}),
                           content_type='application/json')
        self.assertEqual(r.status_code, 200)
        body = json.loads(r.content)
        self.assertTrue(body['success'])
        from nano.models import FCMToken
        tok = FCMToken.objects.get(token='tok-xyz')
        self.assertEqual(tok.user, self.user)
