#!/usr/bin/env python
"""
Test editing an existing user that had a missing profile.
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from nano.models import UserProfile
from django.urls import reverse

def test_existing_user_edit():
    """Test editing an existing user that previously had no profile."""
    
    print("Testing edit functionality for existing user 'njwa'...")
    
    # Get the existing user
    try:
        existing_user = User.objects.get(username='njwa')
        print(f"Found user: {existing_user.username}")
        print(f"Email: {existing_user.email}")
        print(f"Profile role: {existing_user.userprofile.role}")
    except User.DoesNotExist:
        print("❌ User 'njwa' not found!")
        return
    
    # Create an admin user for testing
    admin_user = User.objects.create_user(
        username='test_admin_existing',
        email='admin_existing@example.com',
        password='adminpass123',
        is_superuser=True
    )
    
    admin_profile, _ = UserProfile.objects.get_or_create(
        user=admin_user,
        defaults={'role': 'admin'}
    )
    
    # Create client and login as admin
    client = Client()
    client.login(username='test_admin_existing', password='adminpass123')
    
    # Test 1: Edit existing user without changing password
    print("\n=== Test 1: Edit existing user without password change ===")
    
    form_data = {
        'username': 'njwa_updated',
        'email': 'njwa_updated@example.com',
        'role': 'manager',
        'current_password': '',
        'new_password': '',
        'confirm_password': ''
    }
    
    response = client.post(reverse('edit_user', args=[existing_user.id]), form_data)
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 302:
        print("✅ Form submitted successfully (redirect)")
        # Check if user was updated
        updated_user = User.objects.get(id=existing_user.id)
        print(f"Updated username: {updated_user.username}")
        print(f"Updated email: {updated_user.email}")
        print(f"Updated role: {updated_user.userprofile.role}")
        print(f"Password still works: {updated_user.check_password('password')}") # Assuming original password
    else:
        print("❌ Form submission failed")
        if hasattr(response, 'context'):
            messages = list(response.context.get('messages', []))
            if messages:
                for message in messages:
                    print(f"Message: {message.tags} - {message}")
    
    # Test 2: Edit existing user with password change
    print("\n=== Test 2: Edit existing user with password change ===")
    
    # First, let's set a known password for testing
    existing_user.set_password('knownpass123')
    existing_user.save()
    
    form_data_with_password = {
        'username': 'njwa_final',
        'email': 'njwa_final@example.com',
        'role': 'admin',
        'current_password': 'knownpass123',  # Current password
        'new_password': 'newpass456',
        'confirm_password': 'newpass456'
    }
    
    response = client.post(reverse('edit_user', args=[existing_user.id]), form_data_with_password)
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 302:
        print("✅ Form submitted successfully (redirect)")
        updated_user = User.objects.get(id=existing_user.id)
        print(f"Updated username: {updated_user.username}")
        print(f"Updated email: {updated_user.email}")
        print(f"Updated role: {updated_user.userprofile.role}")
        print(f"New password works: {updated_user.check_password('newpass456')}")
    else:
        print("❌ Form submission failed")
        if hasattr(response, 'context'):
            messages = list(response.context.get('messages', []))
            if messages:
                for message in messages:
                    print(f"Message: {message.tags} - {message}")
    
    # Clean up
    admin_user.delete()
    
    print("\n✅ Test completed!")

if __name__ == '__main__':
    try:
        test_existing_user_edit()
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
