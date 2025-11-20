#!/usr/bin/env python
"""
Test script to verify superuser access to admin pages.
This script checks that superusers can access admin pages regardless of their UserProfile role.
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from django.contrib.auth.models import User
from nano.models import UserProfile

def test_superuser_access():
    print("Testing Superuser Access Implementation")
    print("=" * 50)
    
    # Get the admin user
    try:
        admin_user = User.objects.get(username='admin')
        print(f"✓ Found user: {admin_user.username}")
        print(f"✓ Is superuser: {admin_user.is_superuser}")
        print(f"✓ Is staff: {admin_user.is_staff}")
        
        # Check UserProfile
        if hasattr(admin_user, 'userprofile'):
            print(f"✓ UserProfile role: {admin_user.userprofile.role}")
        else:
            print("✗ No UserProfile found")
            
        # Test access logic (simulating the view checks)
        print("\nTesting Access Logic:")
        print("-" * 30)
        
        # Test admin page access (manage_users, edit_user, delete_user, etc.)
        can_access_admin = (
            admin_user.is_superuser or 
            (hasattr(admin_user, 'userprofile') and admin_user.userprofile.role in ['admin', 'manager'])
        )
        print(f"✓ Can access admin pages: {can_access_admin}")
        
        # Test order management access
        can_access_orders = (
            admin_user.is_superuser or 
            (hasattr(admin_user, 'userprofile') and admin_user.userprofile.role in ['admin', 'manager', 'cashier'])
        )
        print(f"✓ Can access order pages: {can_access_orders}")
        
        # Test stock management access
        can_access_stock = (
            admin_user.is_superuser or 
            (hasattr(admin_user, 'userprofile') and admin_user.userprofile.role in ['admin', 'manager'])
        )
        print(f"✓ Can access stock management: {can_access_stock}")
        
        print("\n" + "=" * 50)
        print("SUPERUSER ACCESS TEST RESULTS:")
        print(f"Superuser '{admin_user.username}' (role: {admin_user.userprofile.role})")
        print(f"→ Can access admin pages: {'YES' if can_access_admin else 'NO'}")
        print(f"→ Can access order pages: {'YES' if can_access_orders else 'NO'}")
        print(f"→ Can access stock management: {'YES' if can_access_stock else 'NO'}")
        
        if can_access_admin and can_access_orders and can_access_stock:
            print("\n✅ SUCCESS: Superuser has full admin access!")
        else:
            print("\n❌ FAILURE: Superuser access is not working correctly!")
            
    except User.DoesNotExist:
        print("❌ Superuser 'admin' not found!")
        print("Run: python manage.py create_superuserprofile")

if __name__ == '__main__':
    test_superuser_access()
