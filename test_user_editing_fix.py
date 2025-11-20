#!/usr/bin/env python3
"""
Test script to verify user editing fixes:
1. Password is optional when editing user role
2. First user registration creates admin automatically
"""

import os
import sys
import django
from django.test import Client, TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from nano.models import UserProfile

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

def test_password_optional_edit():
    """Test that password is optional when editing user"""
    print("🧪 Testing password optional in user edit...")
    
    # Create test admin user
    admin_user = User.objects.create_user(
        username='testadmin',
        email='admin@test.com',
        password='adminpass123'
    )
    UserProfile.objects.create(
        user=admin_user,
        role='admin',
        created_by=None
    )
    
    # Create test regular user
    test_user = User.objects.create_user(
        username='testuser',
        email='user@test.com',
        password='userpass123'
    )
    UserProfile.objects.create(
        user=test_user,
        role='cashier',
        created_by=admin_user
    )
    
    client = Client()
    client.login(username='testadmin', password='adminpass123')
    
    # Test editing user without password (should work)
    edit_url = reverse('edit_user', args=[test_user.id])
    response = client.post(edit_url, {
        'username': 'testuser_updated',
        'email': 'user_updated@test.com',
        'role': 'manager',
        'current_password': '',
        'new_password': '',
        'confirm_password': ''
    })
    
    # Should redirect to manage_users on success
    if response.status_code == 302:
        test_user.refresh_from_db()
        if test_user.username == 'testuser_updated':
            print("✅ SUCCESS: User edited successfully without password")
        else:
            print("❌ FAILED: Username not updated")
    else:
        print(f"❌ FAILED: Expected redirect, got {response.status_code}")
        print(f"Response content: {response.content.decode()}")
    
    # Clean up
    admin_user.delete()
    test_user.delete()

def test_first_user_admin():
    """Test that first user becomes admin automatically"""
    print("\n🧪 Testing first user becomes admin...")
    
    # Clear all users first
    User.objects.all().delete()
    UserProfile.objects.all().delete()
    
    client = Client()
    
    # Check no users exist
    assert not User.objects.exists(), "Users should be cleared for this test"
    
    # Register first user
    signup_url = reverse('sign_up')
    response = client.post(signup_url, {
        'username': 'firstuser',
        'email': 'first@test.com',
        'password': 'firstpass123',
        'confirm_password': 'firstpass123'
    })
    
    if response.status_code == 302:
        first_user = User.objects.get(username='firstuser')
        profile = UserProfile.objects.get(user=first_user)
        
        if profile.role == 'admin' and first_user.is_staff:
            print("✅ SUCCESS: First user became admin automatically")
        else:
            print(f"❌ FAILED: Role={profile.role}, is_staff={first_user.is_staff}")
    else:
        print(f"❌ FAILED: Expected redirect, got {response.status_code}")
        print(f"Response content: {response.content.decode()}")
    
    # Clean up
    User.objects.all().delete()
    UserProfile.objects.all().delete()

def test_password_change_validation():
    """Test that password change still works when needed"""
    print("\n🧪 Testing password change validation...")
    
    # Create test admin user
    admin_user = User.objects.create_user(
        username='testadmin2',
        email='admin2@test.com',
        password='adminpass123'
    )
    UserProfile.objects.create(
        user=admin_user,
        role='admin',
        created_by=None
    )
    
    # Create test regular user
    test_user = User.objects.create_user(
        username='testuser2',
        email='user2@test.com',
        password='userpass123'
    )
    UserProfile.objects.create(
        user=test_user,
        role='cashier',
        created_by=admin_user
    )
    
    client = Client()
    client.login(username='testadmin2', password='adminpass123')
    
    edit_url = reverse('edit_user', args=[test_user.id])
    
    # Test password change without current password (should fail)
    response = client.post(edit_url, {
        'username': 'testuser2',
        'email': 'user2@test.com',
        'role': 'manager',
        'current_password': '',  # Missing current password
        'new_password': 'newpass123',
        'confirm_password': 'newpass123'
    })
    
    if response.status_code == 200:  # Should stay on form page
        print("✅ SUCCESS: Password change rejected without current password")
    else:
        print(f"❌ FAILED: Expected form page, got {response.status_code}")
    
    # Test password change with correct current password (should work)
    response = client.post(edit_url, {
        'username': 'testuser2',
        'email': 'user2@test.com',
        'role': 'manager',
        'current_password': 'userpass123',  # Correct current password
        'new_password': 'newpass123',
        'confirm_password': 'newpass123'
    })
    
    if response.status_code == 302:  # Should redirect on success
        test_user.refresh_from_db()
        if test_user.check_password('newpass123'):
            print("✅ SUCCESS: Password changed correctly with current password")
        else:
            print("❌ FAILED: Password not updated correctly")
    else:
        print(f"❌ FAILED: Expected redirect, got {response.status_code}")
    
    # Clean up
    admin_user.delete()
    test_user.delete()

def main():
    print("🚀 Testing User Editing Fixes\n")
    print("=" * 50)
    
    try:
        test_password_optional_edit()
        test_first_user_admin()
        test_password_change_validation()
        
        print("\n" + "=" * 50)
        print("🎉 All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
