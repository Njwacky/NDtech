#!/usr/bin/env python3
"""
Quick Security Fixes for futurePOS
Run this script to apply immediate critical security fixes
"""

import os
import secrets
from pathlib import Path

def generate_secret_key():
    """Generate a new Django secret key"""
    return secrets.token_urlsafe(50)

def create_env_file():
    """Create .env file with secure configuration"""
    env_content = f"""# Django Configuration
DJANGO_SECRET_KEY={generate_secret_key()}
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Firebase Cloud Messaging (FCM) Settings
FCM_API_KEY=your-fcm-api-key-here
FCM_SENDER_ID=your-sender-id
FCM_PROJECT_ID=your-project-id

# Brevo Email Service Settings
BREVO_API_KEY=your-brevo-api-key-here
BREVO_SENDER_EMAIL=njwayelodlamini@gmail.com
BREVO_SENDER_NAME=futurePOS
"""

    env_path = Path('.env')
    if env_path.exists():
        backup_path = Path('.env.backup')
        if backup_path.exists():
            backup_path.unlink()
        env_path.rename(backup_path)
        print(f"✓ Backed up existing .env to .env.backup")

    with open(env_path, 'w') as f:
        f.write(env_content)

    print(f"✓ Created secure .env file")
    print(f"⚠️  IMPORTANT: Update the API keys in .env with your actual values")

def update_requirements():
    """Add missing security packages to requirements.txt"""
    additional_packages = [
        'django-cors-headers>=4.0.0',
        'python-decouple>=3.8',
        'django-extensions>=3.2.0'
    ]

    requirements_path = Path('requirements.txt')
    existing_packages = set()

    if requirements_path.exists():
        with open(requirements_path, 'r') as f:
            existing_packages = set(line.strip() for line in f if line.strip() and not line.startswith('#'))

    new_packages = [pkg for pkg in additional_packages if pkg not in existing_packages]

    if new_packages:
        with open(requirements_path, 'a') as f:
            for pkg in new_packages:
                f.write(f'\n{pkg}')
        print(f"✓ Added {len(new_packages)} security packages to requirements.txt")
    else:
        print("✓ All security packages already in requirements.txt")

def create_production_settings():
    """Create production settings template"""
    settings_template = '''"""
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
'''

    with open('production_settings.py', 'w') as f:
        f.write(settings_template)

    print("✓ Created production_settings.py template")

def main():
    """Apply all quick security fixes"""
    print("🔒 Applying Quick Security Fixes to futurePOS...")
    print()

    # Create .env file
    create_env_file()
    print()

    # Update requirements.txt
    update_requirements()
    print()

    # Create production settings template
    create_production_settings()
    print()

    print("📋 NEXT STEPS:")
    print("1. Update API keys in .env file with your actual values")
    print("2. Run: pip install -r requirements.txt")
    print("3. Import production_settings in your main settings.py")
    print("4. Set DEBUG=False for production")
    print("5. Configure CORS middleware in settings.py")
    print("6. Run: python manage.py check --deploy")
    print()
    print("✅ Quick security fixes completed!")

if __name__ == '__main__':
    main()
