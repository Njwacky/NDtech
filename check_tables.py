#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from django.db import connection

def check_tables():
    """Check what tables exist in the database"""
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'nano_%';")
        tables = [row[0] for row in cursor.fetchall()]
        
        print("=== Nano Tables ===")
        for table in sorted(tables):
            print(f"  ✓ {table}")
        
        # Check for security tables specifically
        security_tables = [t for t in tables if any(log_type in t.lower() for log_type in ['admin', 'api', 'data', 'security', 'sensitive'])]
        print(f"\n=== Security Tables ({len(security_tables)}) ===")
        for table in sorted(security_tables):
            print(f"  ✓ {table}")
        
        # Expected tables from migration 0018
        expected_0018_tables = [
            'nano_adminactionlog',
            'nano_apicalllog', 
            'nano_datamodificationlog',
            'nano_securityauditlog',
            'nano_sensitivedataaccesslog'
        ]
        
        print(f"\n=== Migration 0018 Status ===")
        missing_0018 = [t for t in expected_0018_tables if t not in tables]
        if missing_0018:
            print(f"  ❌ Missing: {', '.join(missing_0018)}")
        else:
            print("  ✅ All 0018 tables present")
        
        # Check completedorder table for migration 0020 fields
        print(f"\n=== Migration 0020 Status ===")
        if 'nano_completedorder' in tables:
            cursor.execute("PRAGMA table_info(nano_completedorder);")
            columns = [row[1] for row in cursor.fetchall()]
            
            expected_0020_columns = [
                'customer_email',
                'customer_email_encrypted', 
                'customer_name_encrypted',
                'customer_phone_encrypted'
            ]
            
            missing_0020 = [c for c in expected_0020_columns if c not in columns]
            if missing_0020:
                print(f"  ❌ Missing columns: {', '.join(missing_0020)}")
            else:
                print("  ✅ All 0020 columns present")
        else:
            print("  ❌ nano_completedorder table not found")

if __name__ == '__main__':
    check_tables()
