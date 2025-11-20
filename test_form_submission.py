#!/usr/bin/env python
"""
Test script to simulate form submission and debug the password issue.
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

def test_form_submission():
    """Test the form submission exactly as it would happen in browser."""
    
    print("Testing form submission...")
    
    # Clean up any existing test users
    User.objects.filter(username__in=['testuser_form', 'admin_form']).delete()
    
    # Create a test user
    test_user = User.objects.create_user(
        username='testuser_form',
        email='test@example.com',
        password='testpass123'
    )
    
    # Create user profile
    profile, created = UserProfile.objects.get_or_create(
        user=test_user,
        defaults={'role': 'cashier'}
    )
    
    # Create admin user for testing
    admin_user = User.objects.create_user(
        username='admin_form',
        email='admin@example.com',
        password='adminpass123',
        is_superuser=True
    )
    
    admin_profile, admin_created = UserProfile.objects.get_or_create(
        user=admin_user,
        defaults={'role': 'admin'}
    )
    
    # Create client and login as admin
    client = Client()
    client.login(username='admin_form', password='adminpass123')
    
    print(f"\nTest user ID: {test_user.id}")
    print(f"Admin user ID: {admin_user.id}")
    
    # Test 1: Submit form with empty password fields (as strings)
    print("\n=== Test 1: Submit form with empty password fields ===")
    
    # This simulates what happens when browser submits empty form fields
    form_data = {
        'username': 'updated_username',
        'email': 'updated@example.com',
        'role': 'manager',
        'current_password': '',  # Empty string from browser
        'new_password': '',      # Empty string from browser
        'confirm_password': ''   # Empty string from browser
    }
    
    print(f"Form data: {form_data}")
    
    response = client.post(reverse('edit_user', args=[test_user.id]), form_data)
    
    print(f"Response status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    
    if response.status_code == 302:
        print("✅ Form submitted successfully (redirect)")
        # Check if user was updated
        updated_user = User.objects.get(id=test_user.id)
        print(f"Updated username: {updated_user.username}")
        print(f"Updated email: {updated_user.email}")
        print(f"Password still works: {updated_user.check_password('testpass123')}")
    else:
        print("❌ Form submission failed")
        if hasattr(response, 'context'):
            messages = list(response.context.get('messages', []))
            if messages:
                for message in messages:
                    print(f"Message: {message.tags} - {message}")
        print(f"Response content: {response.content.decode()[:500]}...")
    
    # Test 2: Submit form without password fields at all
    print("\n=== Test 2: Submit form without password fields ===")
    
    form_data_no_password = {
        'username': 'updated_username2',
        'email': 'updated2@example.com',
        'role': 'admin'
        # No password fields at all
    }
    
    print(f"Form data: {form_data_no_password}")
    
    response = client.post(reverse('edit_user', args=[test_user.id]), form_data_no_password)
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 302:
        print("✅ Form submitted successfully (redirect)")
        updated_user = User.objects.get(id=test_user.id)
        print(f"Updated username: {updated_user.username}")
        print(f"Updated email: {updated_user.email}")
    else:
        print("❌ Form submission failed")
        if hasattr(response, 'context'):
            messages = list(response.context.get('messages', []))
            if messages:
                for message in messages:
                    print(f"Message: {message.tags} - {message}")
    
    # Clean up
    test_user.delete()
    admin_user.delete()
    
    print("\n✅ Test completed!")

if __name__ == '__main__':
    try:
        test_form_submission()
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
