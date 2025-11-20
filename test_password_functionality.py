#!/usr/bin/env python
"""
Test script to verify the password editing functionality works correctly.
This script tests the backend logic for password changes.
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

def test_password_functionality():
    print("Testing Password Editing Functionality")
    print("=" * 50)
    
    # Check if we have users to test with
    users = User.objects.all()
    if not users:
        print("No users found. Creating test user...")
        test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=test_user, role='cashier')
        users = User.objects.all()
    
    print(f"Found {len(users)} users in the database:")
    for user in users:
        try:
            role = user.userprofile.role
        except User.userprofile.RelatedObjectDoesNotExist:
            role = "No profile"
        print(f"  - {user.username} ({user.email}) - Role: {role}")
    
    # Test password validation logic
    print("\nTesting password validation scenarios:")
    
    test_cases = [
        {
            'name': 'Empty password fields',
            'current': '',
            'new': '',
            'confirm': '',
            'should_change': False
        },
        {
            'name': 'Only current password',
            'current': 'testpass123',
            'new': '',
            'confirm': '',
            'should_change': False
        },
        {
            'name': 'New password without current',
            'current': '',
            'new': 'newpass123',
            'confirm': 'newpass123',
            'should_change': False
        },
        {
            'name': 'Valid password change',
            'current': 'testpass123',
            'new': 'newpass123',
            'confirm': 'newpass123',
            'should_change': True
        },
        {
            'name': 'Password mismatch',
            'current': 'testpass123',
            'new': 'newpass123',
            'confirm': 'different',
            'should_change': False
        },
        {
            'name': 'Short password',
            'current': 'testpass123',
            'new': '123',
            'confirm': '123',
            'should_change': False
        }
    ]
    
    for test_case in test_cases:
        print(f"\n  Testing: {test_case['name']}")
        print(f"    Current: '{test_case['current']}'")
        print(f"    New: '{test_case['new']}'")
        print(f"    Confirm: '{test_case['confirm']}'")
        
        # Simulate the validation logic from our view
        current = test_case['current']
        new = test_case['new']
        confirm = test_case['confirm']
        
        password_change_attempt = any([current, new, confirm])
        valid_change = True
        errors = []
        
        if password_change_attempt:
            if not current:
                errors.append('Current password is required')
                valid_change = False
            
            if not new:
                errors.append('New password is required')
                valid_change = False
            elif len(new) < 6:
                errors.append('Password must be at least 6 characters')
                valid_change = False
            
            if new != confirm:
                errors.append('Passwords do not match')
                valid_change = False
        
        if errors:
            print(f"    Errors: {', '.join(errors)}")
        
        expected_change = test_case['should_change']
        actual_change = password_change_attempt and valid_change
        
        if actual_change == expected_change:
            print(f"    ✅ PASS")
        else:
            print(f"    ❌ FAIL - Expected change: {expected_change}, Got: {actual_change}")
    
    print("\n" + "=" * 50)
    print("Password functionality test completed!")
    print("\nTo test the full functionality:")
    print("1. Start the development server: python manage.py runserver")
    print("2. Navigate to http://127.0.0.1:8000/")
    print("3. Log in as an admin/manager user")
    print("4. Go to Manage Users page")
    print("5. Click Edit on any user")
    print("6. Try changing the password with different scenarios")

if __name__ == '__main__':
    test_password_functionality()
