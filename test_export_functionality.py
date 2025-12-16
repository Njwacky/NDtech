#!/usr/bin/env python
"""
Test script to verify the Excel export functionality for products
"""
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from nano.models import Product
from nano.views_export import export_products_excel
from io import BytesIO
import pandas as pd

def test_export_functionality():
    """Test the export products Excel functionality"""
    print("Testing Excel export functionality...")
    
    # Create a mock request factory
    factory = RequestFactory()
    
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
    
    # Create a mock GET request
    request = factory.get('/export/products/excel/')
    request.user = superuser
    
    # Check if there are any products in the database
    product_count = Product.objects.count()
    print(f"Found {product_count} products in the database")
    
    if product_count == 0:
        print("No products found. Creating a test product...")
        # Create a test product
        Product.objects.create(
            name='Test Product',
            description='Test Description',
            price=99.99,
            stock=10,
            barcode='1234567890123'
        )
        product_count = Product.objects.count()
        print(f"Created test product. Total products: {product_count}")
    
    try:
        # Call the export function
        response = export_products_excel(request)
        
        # Check if response is successful
        if response.status_code == 200:
            print("✓ Export function executed successfully")
            
            # Check response content type
            expected_content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            if response['Content-Type'] == expected_content_type:
                print("✓ Correct content type returned")
            else:
                print(f"✗ Wrong content type: {response['Content-Type']}")
            
            # Check if file is properly formatted
            content = response.content
            if len(content) > 0:
                print(f"✓ Excel file generated successfully ({len(content)} bytes)")
                
                # Try to read the Excel file with pandas
                try:
                    df = pd.read_excel(BytesIO(content))
                    print(f"✓ Excel file is valid and contains {len(df)} rows")
                    print(f"✓ Columns: {list(df.columns)}")
                    
                    # Display first few rows
                    if not df.empty:
                        print("\nSample data:")
                        print(df.head(2).to_string())
                    
                except Exception as e:
                    print(f"✗ Error reading Excel file: {e}")
            else:
                print("✗ Empty response content")
                
            # Check Content-Disposition header
            if 'Content-Disposition' in response:
                print(f"✓ Content-Disposition: {response['Content-Disposition']}")
            else:
                print("✗ Missing Content-Disposition header")
                
        else:
            print(f"✗ Export failed with status code: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error during export: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_export_functionality()
