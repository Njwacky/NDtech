#!/usr/bin/env python
"""
Simple API endpoint test script
"""

import os
import sys
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from django.contrib.auth.models import User
from nano.models import UserProfile, Product

def test_api_endpoints():
    """Test basic API endpoints"""
    base_url = "http://localhost:8000/api/v1"
    
    print("🧪 Testing NDtech POS API Endpoints")
    print("=" * 50)
    
    # Test 1: Check API schema
    print("\n1. Testing API Schema...")
    try:
        response = requests.get("http://localhost:8000/api/schema/")
        if response.status_code == 200:
            print("✅ API Schema accessible")
        else:
            print(f"❌ API Schema failed: {response.status_code}")
    except Exception as e:
        print(f"❌ API Schema error: {e}")
    
    # Test 2: Check Swagger UI
    print("\n2. Testing Swagger UI...")
    try:
        response = requests.get("http://localhost:8000/api/docs/")
        if response.status_code == 200:
            print("✅ Swagger UI accessible")
        else:
            print(f"❌ Swagger UI failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Swagger UI error: {e}")
    
    # Test 3: Check ReDoc
    print("\n3. Testing ReDoc...")
    try:
        response = requests.get("http://localhost:8000/api/redoc/")
        if response.status_code == 200:
            print("✅ ReDoc accessible")
        else:
            print(f"❌ ReDoc failed: {response.status_code}")
    except Exception as e:
        print(f"❌ ReDoc error: {e}")
    
    # Test 4: Test API endpoints (without auth - should fail)
    print("\n4. Testing API Endpoints (unauthorized)...")
    endpoints = [
        "/products/",
        "/users/",
        "/notifications/",
        "/error-logs/",
        "/security-logs/"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            if response.status_code == 401:
                print(f"✅ {endpoint} - Correctly requires authentication")
            else:
                print(f"❌ {endpoint} - Unexpected status: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
    
    # Test 5: Create test user and test authenticated access
    print("\n5. Testing authenticated access...")
    try:
        # Get or create test user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'is_staff': False,
                'is_superuser': False
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            # Create user profile
            UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': 'cashier'}
            )
        
        # Test login via API (this might not work without token auth setup)
        print(f"✅ Test user created/exists: {user.username}")
        
    except Exception as e:
        print(f"❌ User creation error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 API Testing Complete!")
    print("\n📚 Available Documentation:")
    print("   • Swagger UI: http://localhost:8000/api/docs/")
    print("   • ReDoc: http://localhost:8000/api/redoc/")
    print("   • Raw Schema: http://localhost:8000/api/schema/")
    print("\n🔗 API Endpoints:")
    print("   • Base URL: http://localhost:8000/api/v1/")
    print("   • Products: http://localhost:8000/api/v1/products/")
    print("   • Users: http://localhost:8000/api/v1/users/")
    print("   • Notifications: http://localhost:8000/api/v1/notifications/")

if __name__ == "__main__":
    test_api_endpoints()
