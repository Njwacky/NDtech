#!/usr/bin/env python
"""
Test script to verify add stock page export functionality
"""
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
# Add testserver to allowed hosts for testing
os.environ.setdefault('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth.models import User
from nano.models import Product
from nano.views import add_stock

def test_add_stock_page():
    """Test that the add stock page loads correctly and contains export button"""
    print("Testing Add Stock page with export functionality...")
    
    # Create a test client
    client = Client()
    
    # Create or get a superuser for testing
    try:
        superuser = User.objects.get(username='admin')
    except User.DoesNotExist:
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        print("Created test superuser")
    
    # Log in the user
    client.login(username='admin', password='testpass123')
    
    try:
        # Test GET request to add_stock page
        response = client.get('/add_stock/')
        
        if response.status_code == 200:
            print("✓ Add Stock page loads successfully")
            
            # Check if export button is present in the HTML
            content = response.content.decode('utf-8')
            
            if 'exportProducts()' in content:
                print("✓ Export Products button JavaScript function found")
            else:
                print("✗ Export Products button JavaScript function not found")
            
            if 'Export Products' in content:
                print("✓ Export Products button text found in page")
            else:
                print("✗ Export Products button text not found in page")
            
            if 'fa-file-excel' in content:
                print("✓ Excel icon found in export button")
            else:
                print("✗ Excel icon not found in export button")
                
            if '/export/products/excel/' in content:
                print("✓ Export URL found in page")
            else:
                print("✗ Export URL not found in page")
            
            # Check if products are available on the page
            if 'product_id' in content:
                print("✓ Product selection dropdown found")
            else:
                print("✗ Product selection dropdown not found")
                
            # Check for manager/admin specific features
            if 'is_manager' in content or 'user.is_superuser' in content:
                print("✓ User role checking present in template")
            else:
                print("! User role checking may be missing")
            
        else:
            print(f"✗ Add Stock page failed with status code: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error testing Add Stock page: {e}")
        import traceback
        traceback.print_exc()

def test_export_endpoint_access():
    """Test that the export endpoint is accessible from add stock page context"""
    print("\nTesting export endpoint accessibility...")
    
    # Create a test client
    client = Client()
    
    # Create or get a superuser for testing
    try:
        superuser = User.objects.get(username='admin')
    except User.DoesNotExist:
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
    
    # Log in the user
    client.login(username='admin', password='testpass123')
    
    try:
        # Test export endpoint
        response = client.get('/export/products/excel/')
        
        if response.status_code == 200:
            print("✓ Export endpoint accessible from logged in admin")
            
            # Check content type
            if 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in response['Content-Type']:
                print("✓ Correct Excel content type returned")
            else:
                print("✗ Incorrect content type returned")
                
            if 'Content-Disposition' in response:
                print("✓ Content-Disposition header present")
            else:
                print("✗ Content-Disposition header missing")
                
        else:
            print(f"✗ Export endpoint failed with status code: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error testing export endpoint: {e}")

if __name__ == '__main__':
    test_add_stock_page()
    test_export_endpoint_access()
    print("\n🎉 Add Stock Export Integration Test Complete!")
