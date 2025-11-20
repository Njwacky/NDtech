"""
Production settings for futurePOS
Import this in settings.py for production environment
"""

import os
from decouple import config

# Security settings
SECRET_KEY = config('DJANGO_SECRET_KEY')
DEBUG = config('DJANGO_DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Security middleware
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_REDIRECT_EXEMPT = []
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'

# CORS settings
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# API Keys
FCM_API_KEY = config('FCM_API_KEY')
FCM_SENDER_ID = config('FCM_SENDER_ID', default='')
FCM_PROJECT_ID = config('FCM_PROJECT_ID', default='')

BREVO_API_KEY = config('BREVO_API_KEY')
BREVO_SENDER_EMAIL = config('BREVO_SENDER_EMAIL')
BREVO_SENDER_NAME = config('BREVO_SENDER_NAME')
