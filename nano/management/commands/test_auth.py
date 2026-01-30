from django.core.management.base import BaseCommand
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from nano.models import UserProfile

class Command(BaseCommand):
    help = 'Test authentication system'

    def handle(self, *args, **options):
        self.stdout.write("🔐 Testing Authentication System")
        self.stdout.write("=" * 50)
        
        # Create test user
        user, created = User.objects.get_or_create(
            username='auth_test_user',
            defaults={
                'email': 'authtest@example.com',
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(f"✅ Created test user: {user.username}")
        else:
            self.stdout.write(f"📋 Using existing test user: {user.username}")
        
        # Create UserProfile
        profile, profile_created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'role': 'cashier',
                'is_active': True
            }
        )
        
        if profile_created:
            self.stdout.write(f"✅ Created UserProfile for {user.username}")
        else:
            self.stdout.write(f"📋 Using existing UserProfile for {user.username}")
        
        # Test 1: Active profile
        self.stdout.write("\n🧪 Test 1: Active UserProfile")
        user.is_active = True
        profile.is_active = True
        user.save()
        profile.save()
        
        auth_user = authenticate(username='auth_test_user', password='testpass123')
        self.stdout.write(f"   Result: {'✅ PASS' if auth_user else '❌ FAIL'} - Authentication: {auth_user is not None}")
        
        # Test 2: Inactive profile
        self.stdout.write("\n🧪 Test 2: Inactive UserProfile")
        profile.is_active = False
        profile.save()
        
        auth_user = authenticate(username='auth_test_user', password='testpass123')
        self.stdout.write(f"   Result: {'✅ PASS' if not auth_user else '❌ FAIL'} - Authentication: {auth_user is not None}")
        
        # Clean up
        profile.delete()
        user.delete()
        self.stdout.write("\n🧹 Test data cleaned up")
        
        self.stdout.write("\n🎯 Authentication test completed!")
