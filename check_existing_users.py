#!/usr/bin/env python
"""
Check existing users and their profiles to identify differences.
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

def check_existing_users():
    """Check all existing users and their profiles."""
    
    print("Checking all existing users...")
    
    users = User.objects.all()
    print(f"Total users in database: {users.count()}")
    
    print("\n=== User Details ===")
    for user in users:
        print(f"\nUsername: {user.username}")
        print(f"Email: {user.email}")
        print(f"Is Superuser: {user.is_superuser}")
        print(f"Is Staff: {user.is_staff}")
        print(f"Is Active: {user.is_active}")
        print(f"Date Joined: {user.date_joined}")
        
        # Check if user has a profile
        try:
            profile = user.userprofile
            print(f"Profile Role: {profile.role}")
            print(f"Profile Created: {profile}")
        except UserProfile.DoesNotExist:
            print("❌ NO PROFILE FOUND!")
        except AttributeError:
            print("❌ NO PROFILE FOUND!")
        
        # Check password
        print(f"Password has been set: {user.password != ''}")
        print(f"Password starts with pbkdf2: {user.password.startswith('pbkdf2_')}")
        
        print("-" * 50)

if __name__ == '__main__':
    try:
        check_existing_users()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
