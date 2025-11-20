#!/usr/bin/env python
"""
Test script to verify that the edit user functionality works with optional password changes.
This script tests the backend logic to ensure password changes are truly optional.
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from nano.models import UserProfile
from django.urls import reverse

def test_edit_user_optional_password():
    """Test that editing a user without changing password works correctly."""
    
    print("Testing edit user functionality with optional password changes...")
    
    # Clean up any existing test users and their profiles
    test_usernames = ['testuser_edit', 'admin_edit']
    User.objects.filter(username__in=test_usernames).delete()
    
    # Create a test user with unique username
    test_user = User.objects.create_user(
        username='testuser_edit',
        email='test@example.com',
        password='testpass123'
    )
    
    # Create user profile using get_or_create to avoid conflicts
    profile, created = UserProfile.objects.get_or_create(
        user=test_user,
        defaults={'role': 'cashier'}
    )
    
    # Create admin user for testing with unique username
    admin_user = User.objects.create_user(
        username='admin_edit',
        email='admin@example.com',
        password='adminpass123',
        is_superuser=True
    )
    
    # Create admin profile using get_or_create to avoid conflicts
    admin_profile, admin_created = UserProfile.objects.get_or_create(
        user=admin_user,
        defaults={'role': 'admin'}
    )
    
    # Create client and login as admin
    client = Client()
    client.login(username='admin_edit', password='adminpass123')
    
    # Test 1: Edit user without changing password
    print("\n1. Testing edit user without password change...")
    
    # Get the edit user page
    response = client.get(reverse('edit_user', args=[test_user.id]))
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    # Submit form without password fields
    edit_data = {
        'username': 'updateduser',
        'email': 'updated@example.com',
        'role': 'manager',
        'current_password': '',
        'new_password': '',
        'confirm_password': ''
    }
    
    response = client.post(reverse('edit_user', args=[test_user.id]), edit_data)
    
    # Check if redirected to manage_users (success)
    assert response.status_code == 302, f"Expected redirect (302), got {response.status_code}"
    
    # Verify user was updated
    updated_user = User.objects.get(id=test_user.id)
    assert updated_user.username == 'updateduser', f"Username not updated: {updated_user.username}"
    assert updated_user.email == 'updated@example.com', f"Email not updated: {updated_user.email}"
    assert updated_user.userprofile.role == 'manager', f"Role not updated: {updated_user.userprofile.role}"
    
    # Verify password wasn't changed
    assert updated_user.check_password('testpass123'), "Password was incorrectly changed"
    
    print("✓ Successfully updated user without changing password")
    
    # Test 2: Edit user with password change
    print("\n2. Testing edit user with password change...")
    
    # Submit form with password fields
    edit_data_with_password = {
        'username': 'updateduser2',
        'email': 'updated2@example.com',
        'role': 'admin',
        'current_password': 'testpass123',  # Current password
        'new_password': 'newpass456',
        'confirm_password': 'newpass456'
    }
    
    response = client.post(reverse('edit_user', args=[test_user.id]), edit_data_with_password)
    
    # Check if redirected to manage_users (success)
    assert response.status_code == 302, f"Expected redirect (302), got {response.status_code}"
    
    # Verify user was updated
    updated_user = User.objects.get(id=test_user.id)
    assert updated_user.username == 'updateduser2', f"Username not updated: {updated_user.username}"
    assert updated_user.email == 'updated2@example.com', f"Email not updated: {updated_user.email}"
    assert updated_user.userprofile.role == 'admin', f"Role not updated: {updated_user.userprofile.role}"
    
    # Verify password was changed
    assert updated_user.check_password('newpass456'), "Password was not changed correctly"
    
    print("✓ Successfully updated user with password change")
    
    # Test 3: Test password validation (incorrect current password)
    print("\n3. Testing password validation with incorrect current password...")
    
    edit_data_wrong_password = {
        'username': 'updateduser3',
        'email': 'updated3@example.com',
        'role': 'cashier',
        'current_password': 'wrongpassword',  # Wrong current password
        'new_password': 'newpass789',
        'confirm_password': 'newpass789'
    }
    
    response = client.post(reverse('edit_user', args=[test_user.id]), edit_data_wrong_password)
    
    # Should stay on same page (validation error)
    assert response.status_code == 200, f"Expected stay on page (200), got {response.status_code}"
    
    # Verify user was NOT updated
    unchanged_user = User.objects.get(id=test_user.id)
    assert unchanged_user.username == 'updateduser2', f"Username should not have changed: {unchanged_user.username}"
    
    print("✓ Correctly rejected password change with incorrect current password")
    
    # Clean up
    test_user.delete()
    admin_user.delete()
    
    print("\n🎉 All tests passed! Edit user functionality works correctly with optional password changes.")
    
    return True

if __name__ == '__main__':
    try:
        test_edit_user_optional_password()
        print("\n✅ Test completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
