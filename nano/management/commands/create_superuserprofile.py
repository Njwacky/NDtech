from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from nano.models import UserProfile

class Command(BaseCommand):
    help = 'Creates a superuser with UserProfile if it doesnt exist'

    def handle(self, *args, **options):
        # Check if superuser already exists
        if User.objects.filter(username='admin').exists():
            user = User.objects.get(username='admin')
            if user.is_superuser:
                self.stdout.write(self.style.WARNING('Superuser "admin" already exists'))
                
                # Check if UserProfile exists
                if hasattr(user, 'userprofile'):
                    self.stdout.write(self.style.SUCCESS(f'UserProfile exists with role: {user.userprofile.role}'))
                else:
                    # Create UserProfile for existing superuser
                    UserProfile.objects.create(
                        user=user,
                        role='admin'
                    )
                    self.stdout.write(self.style.SUCCESS('UserProfile created with role "admin"'))
                return
            else:
                # Make existing user a superuser
                user.is_superuser = True
                user.is_staff = True
                user.save()
                self.stdout.write(self.style.SUCCESS('Existing user "admin" promoted to superuser'))

        # Create superuser if doesn't exist
        else:
            user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS('Successfully created superuser "admin" with password "admin123"'))
        
        # Create UserProfile if doesn't exist
        if not hasattr(user, 'userprofile'):
            UserProfile.objects.create(
                user=user,
                role='admin'
            )
            self.stdout.write(self.style.SUCCESS('UserProfile created with role "admin"'))
        else:
            self.stdout.write(self.style.SUCCESS(f'UserProfile already exists with role: {user.userprofile.role}'))
