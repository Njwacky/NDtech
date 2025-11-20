#!/usr/bin/env python
"""
Fix missing user profiles for existing users.
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

def fix_missing_profiles():
    """Create missing user profiles."""
    
    print("Fixing missing user profiles...")
    
    users = User.objects.all()
    fixed_count = 0
    
    for user in users:
        try:
            profile = user.userprofile
            print(f"✅ {user.username} - Profile exists ({profile.role})")
        except (UserProfile.DoesNotExist, AttributeError):
            # Create missing profile
            role = 'admin' if user.is_superuser else 'cashier'
            profile = UserProfile.objects.create(
                user=user,
                role=role
            )
            print(f"🔧 {user.username} - Created profile with role: {role}")
            fixed_count += 1
    
    print(f"\n✅ Fixed {fixed_count} missing profiles")
    print("All users now have profiles!")

if __name__ == '__main__':
    try:
        fix_missing_profiles()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
