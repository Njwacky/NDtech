#!/usr/bin/env python
"""
Check which authentication backends are being used
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from django.conf import settings

def check_auth_backends():
    """Check configured authentication backends"""
    
    print("🔍 Checking Authentication Backends Configuration")
    print("=" * 60)
    
    # Check AUTHENTICATION_BACKENDS setting
    auth_backends = getattr(settings, 'AUTHENTICATION_BACKENDS', None)
    
    if auth_backends:
        print(f"✅ AUTHENTICATION_BACKENDS is configured:")
        for i, backend in enumerate(auth_backends, 1):
            print(f"   {i}. {backend}")
    else:
        print("❌ AUTHENTICATION_BACKENDS is not configured")
    
    # Try to import our backend
    try:
        from nano.authentication import UserProfileBackend
        print(f"\n✅ UserProfileBackend can be imported: {UserProfileBackend}")
    except ImportError as e:
        print(f"\n❌ Cannot import UserProfileBackend: {e}")
    
    # Test backend instantiation
    try:
        from nano.authentication import UserProfileBackend
        backend = UserProfileBackend()
        print(f"✅ UserProfileBackend can be instantiated: {backend}")
    except Exception as e:
        print(f"❌ Cannot instantiate UserProfileBackend: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Backend Configuration Summary:")
    if auth_backends and 'nano.authentication.UserProfileBackend' in auth_backends:
        print("   ✅ UserProfileBackend is properly configured")
    else:
        print("   ❌ UserProfileBackend is not properly configured")
        print("   💡 Make sure AUTHENTICATION_BACKENDS is set in settings.py")
        print("   💡 Make sure Django server is restarted after changes")
    print("=" * 60)

if __name__ == '__main__':
    try:
        check_auth_backends()
    except Exception as e:
        print(f"\n❌ Check failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
