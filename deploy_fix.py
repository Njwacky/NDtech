#!/usr/bin/env python
"""
Deployment fix script for Render.com
This script ensures proper database migration and setup
"""
import os
import sys
import django
from django.core.management import call_command
from django.core.exceptions import ImproperlyConfigured

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
    django.setup()

def check_database_connection():
    """Check if database is accessible"""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def run_migrations():
    """Run Django migrations with error handling"""
    try:
        print("🔄 Running Django migrations...")
        call_command('migrate', '--noinput', verbosity=2)
        print("✅ Migrations completed successfully")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def check_auth_tables():
    """Check if auth tables exist"""
    try:
        from django.contrib.auth.models import User
        from django.contrib.contenttypes.models import ContentType
        
        user_count = User.objects.count()
        content_type_count = ContentType.objects.count()
        
        print(f"✅ Auth tables exist (Users: {user_count}, ContentTypes: {content_type_count})")
        return True
    except Exception as e:
        print(f"❌ Auth tables check failed: {e}")
        return False

def create_superuser_if_needed():
    """Create superuser if none exists"""
    try:
        from django.contrib.auth.models import User
        from django.core.management import call_command
        
        if not User.objects.filter(is_superuser=True).exists():
            print("👤 Creating default superuser...")
            call_command('createsuperuser', 
                       username='admin',
                       email='admin@ndtechpos.com',
                       interactive=False,
                       verbosity=0)
            print("✅ Superuser created (username: admin, password: prompts during deployment)")
        else:
            print("✅ Superuser already exists")
        return True
    except Exception as e:
        print(f"⚠ Superuser creation warning: {e}")
        return False

def collect_static():
    """Collect static files"""
    try:
        print("📁 Collecting static files...")
        call_command('collectstatic', '--noinput', '--clear', verbosity=1)
        print("✅ Static files collected")
        return True
    except Exception as e:
        print(f"❌ Static file collection failed: {e}")
        return False

def main():
    """Main deployment script"""
    print("🚀 Starting NDtech POS deployment setup...")
    
    # Setup Django
    try:
        setup_django()
        print("✅ Django environment configured")
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        sys.exit(1)
    
    # Check database connection
    if not check_database_connection():
        print("❌ Cannot proceed without database connection")
        sys.exit(1)
    
    # Run migrations
    if not run_migrations():
        print("❌ Cannot proceed without successful migrations")
        sys.exit(1)
    
    # Check auth tables
    if not check_auth_tables():
        print("❌ Auth tables not properly created")
        sys.exit(1)
    
    # Create superuser if needed
    create_superuser_if_needed()
    
    # Collect static files
    if not collect_static():
        print("❌ Static file collection failed")
        sys.exit(1)
    
    print("🎉 Deployment setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Deploy to Render.com")
    print("2. Check health endpoint: https://ndtech.onrender.com/health/")
    print("3. Access admin panel: https://ndtech.onrender.com/admin/")
    print("4. Create additional users as needed")

if __name__ == '__main__':
    main()
