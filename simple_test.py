import os
import sys
sys.path.append('c:/Users/njway/OneDrive/Desktop/NDtech')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')

import django
django.setup()

from django.contrib.auth.models import User

print("Current users:")
for user in User.objects.all():
    print(f"  - {user.username} (staff: {user.is_staff})")

print(f"Total user count: {User.objects.count()}")
