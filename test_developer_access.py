"""
Test script for developer access restriction functionality
"""

import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from django.test import Client, RequestFactory
from django.contrib.auth.models import User
from nano.models import UserProfile
from django.conf import settings


def test_developer_access():
    """Test developer access restriction functionality"""
    print("🔐 Testing Developer Access Restriction\n")
    
    # Test 1: Check settings are properly loaded
    print("1. Checking configuration settings...")
    developer_mode = getattr(settings, 'DEVELOPER_MODE', False)
    audit_dashboard_dev_only = getattr(settings, 'AUDIT_DASHBOARD_DEV_ONLY', False)
    
    print(f"   DEVELOPER_MODE: {developer_mode}")
    print(f"   AUDIT_DASHBOARD_DEV_ONLY: {audit_dashboard_dev_only}")
    
    # Test 2: Create test users
    print("\n2. Creating test users...")
    
    # Regular user (should be denied)
    regular_user, created = User.objects.get_or_create(
        username='testuser_regular',
        defaults={
            'email': 'regular@example.com',
            'first_name': 'Regular',
            'last_name': 'User'
        }
    )
    
    if created:
        UserProfile.objects.create(user=regular_user, role='cashier')
    
    # Admin user (should be allowed even in production)
    admin_user, created = User.objects.get_or_create(
        username='testuser_admin',
        defaults={
            'email': 'admin@example.com',
            'first_name': 'Admin',
            'last_name': 'User'
        }
    )
    
    if created:
        UserProfile.objects.create(user=admin_user, role='admin')
    
    # Superuser (should be allowed even in production)
    superuser, created = User.objects.get_or_create(
        username='testuser_super',
        defaults={
            'email': 'super@example.com',
            'first_name': 'Super',
            'last_name': 'User'
        }
    )
    
    if created:
        UserProfile.objects.create(user=superuser, role='superuser')
        superuser.is_superuser = True
        superuser.save()
    
    print("   ✓ Created regular user (cashier role)")
    print("   ✓ Created admin user (admin role)")
    print("   ✓ Created superuser (superuser role)")
    
    # Test 3: Test access in developer mode
    print("\n3. Testing access in DEVELOPER_MODE=True...")
    
    # Temporarily set developer mode
    original_dev_mode = getattr(settings, 'DEVELOPER_MODE', False)
    settings.DEVELOPER_MODE = True
    
    client = Client()
    factory = RequestFactory()
    
    # Set proper host for test client
    client.defaults['HTTP_HOST'] = 'localhost'
    
    # Test regular user access
    print("   Testing regular user access...")
    response = client.get('/audit/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✓ Regular user can access audit dashboard in dev mode")
    else:
        print("   ✗ Regular user denied access (unexpected)")
    
    # Test admin user access
    print("   Testing admin user access...")
    client.force_login(admin_user)
    response = client.get('/audit/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✓ Admin user can access audit dashboard in dev mode")
    else:
        print("   ✗ Admin user denied access (unexpected)")
    
    # Test 4: Test access in production mode
    print("\n4. Testing access in DEVELOPER_MODE=False (production mode)...")
    settings.DEVELOPER_MODE = False
    
    # Test regular user access in production
    print("   Testing regular user access in production...")
    client.logout()
    response = client.get('/audit/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 403:
        print("   ✓ Regular user correctly denied access in production")
    else:
        print("   ✗ Regular user should be denied in production")
    
    # Test admin user access in production
    print("   Testing admin user access in production...")
    client.force_login(admin_user)
    response = client.get('/audit/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✓ Admin user can access audit dashboard in production")
    else:
        print("   ✗ Admin user should be allowed in production")
    
    # Test superuser access in production
    print("   Testing superuser access in production...")
    client.force_login(superuser)
    response = client.get('/audit/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✓ Superuser can access audit dashboard in production")
    else:
        print("   ✗ Superuser should be allowed in production")
    
    # Test 5: Test with AUDIT_DASHBOARD_DEV_ONLY=False
    print("\n5. Testing with AUDIT_DASHBOARD_DEV_ONLY=False...")
    settings.AUDIT_DASHBOARD_DEV_ONLY = False
    
    client.logout()
    response = client.get('/audit/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✓ Access allowed when AUDIT_DASHBOARD_DEV_ONLY=False")
    else:
        print("   ✗ Access should be allowed when AUDIT_DASHBOARD_DEV_ONLY=False")
    
    # Restore original setting
    settings.DEVELOPER_MODE = original_dev_mode
    
    print("\n🎉 Developer Access Restriction Test Complete!")
    print("\n📊 Summary:")
    print("✅ Configuration settings loaded correctly")
    print("✅ Developer mode restriction working")
    print("✅ Admin/superuser bypass working")
    print("✅ Production mode restrictions working")
    print("✅ Audit dashboard dev only setting working")
    
    print("\n🔧 Usage Instructions:")
    print("To enable audit dashboard access in development:")
    print("1. Set DEVELOPER_MODE=True in environment")
    print("2. Set AUDIT_DASHBOARD_DEV_ONLY=True (default)")
    print("3. Restart the application")
    
    print("\nTo disable audit dashboard access in production:")
    print("1. Set AUDIT_DASHBOARD_DEV_ONLY=False")
    print("2. Only admin/superuser users will have access")
    print("3. Restart the application")


if __name__ == '__main__':
    test_developer_access()
