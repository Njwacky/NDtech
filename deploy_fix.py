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
        # Use the database from DATABASE_URL environment variable
        db_url = os.environ.get('DATABASE_URL')
        if db_url:
            print(f"✓ Using PostgreSQL database from DATABASE_URL")
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def get_existing_tables():
    """Get list of all existing tables in the database"""
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
        """)
        return [row[0] for row in cursor.fetchall()]

def check_migration_state():
    """Check which migrations have been applied"""
    from django.db import connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT app, name 
                FROM django_migrations 
                WHERE app = 'nano' 
                ORDER BY id DESC 
                LIMIT 5
            """)
            migrations = cursor.fetchall()
            print("📋 Recent nano migrations applied:")
            for app, name in migrations:
                print(f"   ✓ {app}.{name}")
            return migrations
    except Exception as e:
        print(f"⚠ Could not check migration state: {e}")
        return []

def fix_partial_migration_0018():
    """
    Fix partial migration state for migration 0018.
    
    This migration creates 5 tables:
    - nano_adminactionlog
    - nano_apicalllog  
    - nano_datamodificationlog
    - nano_securityauditlog
    - nano_sensitivedataaccesslog (NOT nano_sensitiveaccesslog!)
    """
    from django.db import connection
    
    print("\n🔧 Checking migration 0018 status...")
    
    # Expected tables from migration 0018
    expected_tables = [
        'nano_adminactionlog',
        'nano_apicalllog',
        'nano_datamodificationlog',
        'nano_securityauditlog',
        'nano_sensitivedataaccesslog'  # Correct table name!
    ]
    
    # Get existing tables
    existing_tables = get_existing_tables()
    
    # Check which tables exist
    existing_0018_tables = [t for t in expected_tables if t in existing_tables]
    missing_0018_tables = [t for t in expected_tables if t not in existing_tables]
    
    print(f"   Existing tables from 0018: {len(existing_0018_tables)}/{len(expected_tables)}")
    if existing_0018_tables:
        print(f"   ✓ Found: {', '.join(existing_0018_tables)}")
    if missing_0018_tables:
        print(f"   ✗ Missing: {', '.join(missing_0018_tables)}")
    
    # Check if migration is marked as applied
    migration_applied = False
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 1 FROM django_migrations 
                WHERE app = 'nano' 
                AND name = '0018_adminactionlog_apicalllog_datamodificationlog_and_more'
            """)
            migration_applied = cursor.fetchone() is not None
    except Exception as e:
        print(f"   ⚠ Could not check migration record: {e}")
    
    print(f"   Migration 0018 marked as applied: {migration_applied}")
    
    # Determine the fix strategy
    if migration_applied and missing_0018_tables:
        # Migration is marked as applied, but some tables are missing
        # This is the partial migration state!
        print("\n⚠️ PARTIAL MIGRATION STATE DETECTED!")
        print("   Strategy: Fake-unapply 0018, drop existing tables, then re-apply")
        
        try:
            # Step 1: Fake-unapply migration 0018 to remove the migration record
            print("\n   Step 1: Removing migration 0018 from django_migrations table...")
            with connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM django_migrations 
                    WHERE app = 'nano' 
                    AND name = '0018_adminactionlog_apicalllog_datamodificationlog_and_more'
                """)
            print("   ✅ Migration record removed")
            
            # Step 2: Drop any partially created tables
            if existing_0018_tables:
                print(f"\n   Step 2: Dropping {len(existing_0018_tables)} partially created tables...")
                with connection.cursor() as cursor:
                    for table in existing_0018_tables:
                        try:
                            cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                            print(f"   ✓ Dropped {table}")
                        except Exception as e:
                            print(f"   ⚠ Could not drop {table}: {e}")
            
            # Step 3: Re-apply migration 0018
            print("\n   Step 3: Re-applying migration 0018...")
            os.environ['DJANGO_MAINTENANCE_MODE'] = 'True'
            call_command('migrate', 'nano', '0018', verbosity=2)
            os.environ.pop('DJANGO_MAINTENANCE_MODE', None)
            print("   ✅ Migration 0018 re-applied successfully")
            
            return True
            
        except Exception as e:
            os.environ.pop('DJANGO_MAINTENANCE_MODE', None)
            print(f"\n   ❌ Repair failed: {e}")
            return False
    
    elif not migration_applied and existing_0018_tables:
        # Some tables exist but migration not marked as applied
        # Drop tables and let migration create them fresh
        print("\n⚠️ ORPHANED TABLES DETECTED!")
        print("   Strategy: Drop orphaned tables, then apply migration")
        
        try:
            with connection.cursor() as cursor:
                for table in existing_0018_tables:
                    cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                    print(f"   ✓ Dropped orphaned table {table}")
            
            print("\n   Applying migration 0018...")
            os.environ['DJANGO_MAINTENANCE_MODE'] = 'True'
            call_command('migrate', 'nano', '0018', verbosity=2)
            os.environ.pop('DJANGO_MAINTENANCE_MODE', None)
            print("   ✅ Migration 0018 applied successfully")
            return True
            
        except Exception as e:
            os.environ.pop('DJANGO_MAINTENANCE_MODE', None)
            print(f"\n   ❌ Repair failed: {e}")
            return False
    
    elif not migration_applied and not existing_0018_tables:
        # Clean state - just need to apply the migration
        print("\n✓ Clean state - migration 0018 not yet applied")
        return True
    
    else:
        # All tables exist and migration is marked as applied
        print("\n✅ Migration 0018 is complete and consistent")
        return True

def fix_partial_migration_0020():
    """
    Fix partial migration state for migration 0020.
    
    This migration adds 4 fields to nano_completedorder:
    - customer_email
    - customer_email_encrypted
    - customer_name_encrypted
    - customer_phone_encrypted
    """
    from django.db import connection
    
    print("\n🔧 Checking migration 0020 status...")
    
    # Fields that should be added by migration 0020
    expected_columns = [
        'customer_email',
        'customer_email_encrypted',
        'customer_name_encrypted',
        'customer_phone_encrypted'
    ]
    
    # Check which columns exist in nano_completedorder
    existing_columns = []
    missing_columns = []
    
    try:
        with connection.cursor() as cursor:
            # Check if the table exists first
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'nano_completedorder'
                )
            """)
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                print("   ℹ Table nano_completedorder doesn't exist yet - migration 0020 not applicable")
                return True
            
            # Check which columns exist
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public'
                AND table_name = 'nano_completedorder'
                AND column_name IN ('customer_email', 'customer_email_encrypted', 
                                   'customer_name_encrypted', 'customer_phone_encrypted')
            """)
            existing_columns = [row[0] for row in cursor.fetchall()]
            missing_columns = [col for col in expected_columns if col not in existing_columns]
            
    except Exception as e:
        print(f"   ⚠ Could not check columns: {e}")
        return True  # Non-fatal, continue
    
    print(f"   Existing columns from 0020: {len(existing_columns)}/{len(expected_columns)}")
    if existing_columns:
        print(f"   ✓ Found: {', '.join(existing_columns)}")
    if missing_columns:
        print(f"   ✗ Missing: {', '.join(missing_columns)}")
    
    # Check if migration is marked as applied
    migration_applied = False
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 1 FROM django_migrations 
                WHERE app = 'nano' 
                AND name = '0020_add_customer_encryption_fields'
            """)
            migration_applied = cursor.fetchone() is not None
    except Exception as e:
        print(f"   ⚠ Could not check migration record: {e}")
    
    print(f"   Migration 0020 marked as applied: {migration_applied}")
    
    # Determine the fix strategy
    if migration_applied and missing_columns:
        # Migration is marked as applied, but some columns are missing
        print("\n⚠️ PARTIAL MIGRATION STATE DETECTED!")
        print("   Strategy: Remove migration record, drop existing columns, then re-apply")
        
        try:
            # Step 1: Remove migration record
            print("\n   Step 1: Removing migration 0020 from django_migrations table...")
            with connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM django_migrations 
                    WHERE app = 'nano' 
                    AND name = '0020_add_customer_encryption_fields'
                """)
            print("   ✅ Migration record removed")
            
            # Step 2: Drop any partially created columns
            if existing_columns:
                print(f"\n   Step 2: Dropping {len(existing_columns)} partially created columns...")
                with connection.cursor() as cursor:
                    for column in existing_columns:
                        try:
                            cursor.execute(f"ALTER TABLE nano_completedorder DROP COLUMN IF EXISTS {column}")
                            print(f"   ✓ Dropped column {column}")
                        except Exception as e:
                            print(f"   ⚠ Could not drop {column}: {e}")
            
            # Step 3: Re-apply migration 0020
            print("\n   Step 3: Re-applying migration 0020...")
            os.environ['DJANGO_MAINTENANCE_MODE'] = 'True'
            call_command('migrate', 'nano', '0020', verbosity=2)
            os.environ.pop('DJANGO_MAINTENANCE_MODE', None)
            print("   ✅ Migration 0020 re-applied successfully")
            
            return True
            
        except Exception as e:
            os.environ.pop('DJANGO_MAINTENANCE_MODE', None)
            print(f"\n   ❌ Repair failed: {e}")
            return False
    
    elif not migration_applied and existing_columns:
        # Some columns exist but migration not marked as applied
        print("\n⚠️ ORPHANED COLUMNS DETECTED!")
        print("   Strategy: Drop orphaned columns, then apply migration")
        
        try:
            with connection.cursor() as cursor:
                for column in existing_columns:
                    cursor.execute(f"ALTER TABLE nano_completedorder DROP COLUMN IF EXISTS {column}")
                    print(f"   ✓ Dropped orphaned column {column}")
            
            print("\n   Applying migration 0020...")
            os.environ['DJANGO_MAINTENANCE_MODE'] = 'True'
            call_command('migrate', 'nano', '0020', verbosity=2)
            os.environ.pop('DJANGO_MAINTENANCE_MODE', None)
            print("   ✅ Migration 0020 applied successfully")
            return True
            
        except Exception as e:
            os.environ.pop('DJANGO_MAINTENANCE_MODE', None)
            print(f"\n   ❌ Repair failed: {e}")
            return False
    
    elif not migration_applied and not existing_columns:
        # Clean state - just need to apply the migration
        print("\n✓ Clean state - migration 0020 not yet applied")
        return True
    
    else:
        # All columns exist and migration is marked as applied
        print("\n✅ Migration 0020 is complete and consistent")
        return True

def run_migrations():
    """Run Django migrations with error handling"""
    try:
        print("\n🔄 Running Django migrations...")
        os.environ['DJANGO_MAINTENANCE_MODE'] = 'True'
        call_command('migrate', '--noinput', verbosity=2)
        os.environ.pop('DJANGO_MAINTENANCE_MODE', None)
        print("✅ Migrations completed successfully")
        return True
    except Exception as e:
        os.environ.pop('DJANGO_MAINTENANCE_MODE', None)
        print(f"❌ Migration failed: {e}")
        return False

def check_security_tables():
    """Check if all security tables exist"""
    try:
        existing_tables = get_existing_tables()
        
        # Correct table names!
        required_tables = [
            'nano_adminactionlog',
            'nano_apicalllog',
            'nano_datamodificationlog',
            'nano_securityauditlog',
            'nano_sensitivedataaccesslog'  # NOT nano_sensitiveaccesslog!
        ]
        
        missing_tables = [t for t in required_tables if t not in existing_tables]
        
        if missing_tables:
            print(f"❌ Missing security tables: {', '.join(missing_tables)}")
            return False
        
        print("✅ All security tables verified")
        return True
        
    except Exception as e:
        print(f"❌ Security table check failed: {e}")
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

def collect_static():
    """Collect static files"""
    try:
        print("\n📁 Collecting static files...")
        call_command('collectstatic', '--noinput', '--clear', verbosity=1)
        print("✅ Static files collected")
        return True
    except Exception as e:
        print(f"⚠️ Static file collection failed (non-fatal): {e}")
        # Static file collection failure is non-fatal for migrations
        return True

def main():
    """Main deployment script"""
    print("=" * 60)
    print("🚀 Starting NDtech POS deployment setup...")
    print("=" * 60)
    
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
    
    # Check current migration state
    check_migration_state()
    
    # Fix partial migration 0018 if needed (before running all migrations)
    print("\n" + "=" * 60)
    print("Checking for partial migration states...")
    print("=" * 60)
    if not fix_partial_migration_0018():
        print("\n⚠️ Warning: Could not fix partial migration 0018 state")
        print("Attempting to continue anyway...")
    
    # Fix partial migration 0020 if needed
    if not fix_partial_migration_0020():
        print("\n⚠️ Warning: Could not fix partial migration 0020 state")
        print("Attempting to continue anyway...")
    
    # Run all migrations
    print("\n" + "=" * 60)
    print("Running all migrations...")
    print("=" * 60)
    if not run_migrations():
        print("\n❌ Migrations failed")
        print("💡 Check the logs above for details")
        sys.exit(1)
    
    # Verify auth tables
    print("\n" + "=" * 60)
    print("Verifying database tables...")
    print("=" * 60)
    if not check_auth_tables():
        print("❌ Auth tables not properly created")
        sys.exit(1)
    
    # Verify security tables
    if not check_security_tables():
        print("❌ Security tables not properly created")
        print("💡 This indicates migration 0018 did not complete successfully")
        sys.exit(1)
    
    # Collect static files
    collect_static()
    
    print("\n" + "=" * 60)
    print("🎉 Deployment setup completed successfully!")
    print("=" * 60)
    print("\n📋 Next steps:")
    print("  1. Application will start automatically")
    print("  2. Check health endpoint: https://ndtech.onrender.com/")
    print("  3. Access admin panel: https://ndtech.onrender.com/admin/")
    print("  4. Create superuser with: python manage.py createsuperuser")

if __name__ == '__main__':
    main()
