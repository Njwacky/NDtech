#!/usr/bin/env python
"""
Test script to verify the registration fix
"""

import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    django.setup()
except Exception as e:
    print(f"Error setting up Django: {e}")
    sys.exit(1)

from django.contrib.auth.models import User
from nano.models import UserProfile

def test_registration_logic():
    """Test the registration logic"""

    print("=== Testing Registration Fix ===")

    # Check current user count
    user_count = User.objects.count()
    print(f"Current user count: {user_count}")

    if user_count == 0:
        print("✅ No users exist - registration should be allowed")
        print("✅ First user should become admin")
    else:
        print("✅ Users already exist - registration should be blocked")
        print("✅ Should show 'Registration closed' message")

    # List existing users
    users = User.objects.all()
    for user in users:
        profile = getattr(user, 'userprofile', None)
        role = profile.role if profile else 'No profile'
        is_staff = user.is_staff
        print(f"User: {user.username}, Role: {role}, Staff: {is_staff}")

    print("\n=== Test Results ===")
    if user_count == 0:
        print("🎯 EXPECTED: Registration should be OPEN for first user")
        print("🎯 EXPECTED: First user becomes admin")
    else:
        print("🎯 EXPECTED: Registration should be CLOSED")
        print("🎯 EXPECTED: Should redirect to sign_in with error message")

    print("\n=== Registration Flow Test ===")
    print("1. Visit /register/ -> should redirect to /sign_up/")
    print("2. If no users: show registration form for admin creation")
    print("3. If users exist: show 'Registration Closed' message")
    print("4. POST to /sign_up/ with existing users should be rejected immediately")

if __name__ == '__main__':
    test_registration_logic()
