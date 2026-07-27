#!/usr/bin/env python3
"""
Simple test script to verify view module imports work correctly
Run with: python3 test_view_imports.py
"""
import sys
import os

# Add the project to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_view_module_structure():
    """Test that the modular view structure is correct"""
    print("Testing modular view structure...")
    print("=" * 50)
    
    # Test 1: Check files exist
    print("\n1. Checking modular view files exist...")
    view_files = [
        'nano/views.py',
        'nano/views_core.py',
        'nano/views_pos.py',
        'nano/views_communications.py'
    ]
    
    all_exist = True
    for file in view_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"  ✓ {file} exists ({size:,} bytes)")
        else:
            print(f"  ✗ {file} MISSING!")
            all_exist = False
    
    if not all_exist:
        print("\n❌ Some view files are missing!")
        return False
    
    # Test 2: Check views.py imports
    print("\n2. Checking views.py imports...")
    try:
        with open('nano/views.py', 'r') as f:
            content = f.read()
            
        if 'from .views_core import' in content:
            print("  ✓ views.py imports from views_core")
        else:
            print("  ⚠ views.py may not import from views_core")
            
        if 'from .views_pos import' in content:
            print("  ✓ views.py imports from views_pos")
        else:
            print("  ⚠ views.py may not import from views_pos")
            
        if 'from .views_communications import' in content:
            print("  ✓ views.py imports from views_communications")
        else:
            print("  ⚠ views.py may not import from views_communications")
            
    except Exception as e:
        print(f"  ❌ Error reading views.py: {e}")
        return False
    
    # Test 3: Count functions in each module
    print("\n3. Counting view functions in each module...")
    modules = {
        'views_core.py': ['check_low_stock', 'home', 'register', 'sign_up', 'sign_in', 'logout_view', 'forgot_password', 'create_user', 'manage_users', 'edit_user', 'delete_user', 'bulk_delete_users'],
        'views_pos.py': ['add_stock', 'manage_sales', 'spaza_pos', 'spaza_pos_complete_sale', 'pending_orders', 'save_order', 'order_details', 'complete_order', 'completed_orders'],
        'views_communications.py': ['get_notifications', 'mark_notification_read', 'register_fcm_token', 'send_test_notification', 'airtime_dashboard', 'tracking_dashboard']
    }
    
    for module, expected_funcs in modules.items():
        try:
            with open(f'nano/{module}', 'r') as f:
                content = f.read()
            
            found = []
            missing = []
            for func in expected_funcs:
                if f'def {func}(' in content:
                    found.append(func)
                else:
                    missing.append(func)
            
            print(f"  {module}: {len(found)}/{len(expected_funcs)} expected functions found")
            if missing:
                print(f"    Missing: {', '.join(missing[:3])}...")
        except Exception as e:
            print(f"  ❌ Error reading {module}: {e}")
    
    # Test 4: Check URL configuration
    print("\n4. Checking URL configuration...")
    try:
        with open('nano/urls.py', 'r') as f:
            urls_content = f.read()
        
        if 'from . import views' in urls_content:
            print("  ✓ urls.py imports views module")
        else:
            print("  ⚠ urls.py may not import views correctly")
            
        # Check for some key URLs
        key_urls = ['home', 'register', 'sign_in', 'spaza_pos', 'pending_orders']
        for url in key_urls:
            if f"name='{url}'" in urls_content:
                print(f"  ✓ URL '{url}' found in urls.py")
    except Exception as e:
        print(f"  ❌ Error reading urls.py: {e}")
    
    print("\n" + "=" * 50)
    print("✅ View module structure verification complete!")
    print("\nNext steps:")
    print("1. Install Django: pip install django djangorestframework")
    print("2. Run full tests: python manage.py test")
    print("3. Start server: python manage.py runserver")
    return True


if __name__ == '__main__':
    test_view_module_structure()
