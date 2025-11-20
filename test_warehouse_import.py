import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

import pandas as pd
from io import StringIO
from django.core.files.uploadedfile import SimpleUploadedFile
from nano.models import WarehousePrice
from django.contrib.auth.models import User
from django.utils import timezone

def test_warehouse_import():
    print("=== Testing Warehouse Import ===")
    
    # Get or create a test user
    user, created = User.objects.get_or_create(username='testuser', defaults={'is_staff': True})
    if created:
        print('Created test user')
    
    # Create test data
    test_data = '''product_name,price,barcode,category
Test Product 1,10.50,1234567890123,Test Category
Test Product 2,15.75,1234567890124,Test Category
Test Product 3,8.25,1234567890125,Test Category'''
    
    warehouse_name = 'Test Warehouse'
    
    # Read file using pandas (same as in view)
    df = pd.read_csv(StringIO(test_data))
    print('DataFrame columns:', df.columns.tolist())
    print('DataFrame shape:', df.shape)
    
    # Process each row (same logic as in the view)
    imported_count = 0
    skipped_count = 0
    
    for index, row in df.iterrows():
        try:
            # Clean and validate data
            product_name = str(row['product_name']).strip()
            price = float(row['price'])
            barcode = str(row.get('barcode', '')).strip() if 'barcode' in row and pd.notna(row['barcode']) else None
            category = str(row.get('category', '')).strip() if 'category' in row and pd.notna(row['category']) else None
            stock_quantity = int(row['stock_quantity']) if 'stock_quantity' in row and pd.notna(row['stock_quantity']) else None
            unit_size = str(row.get('unit_size', '')).strip() if 'unit_size' in row and pd.notna(row['unit_size']) else None
            
            print(f'Processing: {product_name}, price: {price}, barcode: {barcode}')
            
            if product_name and price > 0:
                # Create or update warehouse price
                warehouse_price, created = WarehousePrice.objects.update_or_create(
                    product_name=product_name,
                    warehouse_name=warehouse_name,
                    barcode=barcode,
                    defaults={
                        'price': price,
                        'category': category,
                        'stock_quantity': stock_quantity,
                        'unit_size': unit_size,
                        'imported_by': user,
                        'file_name': 'test.csv'
                    }
                )
                imported_count += 1
                status = "Created" if created else "Updated"
                print(f'  -> {status}: {warehouse_price}')
            else:
                skipped_count += 1
                print(f'  -> Skipped: invalid data')
                
        except (ValueError, TypeError) as e:
            skipped_count += 1
            print(f'  -> Error: {e}')
            continue
    
    print(f'Imported: {imported_count}, Skipped: {skipped_count}')
    
    # Check final count
    final_count = WarehousePrice.objects.count()
    print(f'WarehousePrice count after test: {final_count}')
    
    # Show what was created
    print("\nCreated/Updated WarehousePrice records:")
    for wp in WarehousePrice.objects.all():
        print(f'  - {wp.product_name} ({wp.warehouse_name}): R{wp.price}')
    
    return imported_count > 0

if __name__ == '__main__':
    success = test_warehouse_import()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
