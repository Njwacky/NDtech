#!/usr/bin/env python
"""
Script to add initial airtime products to the database
Run this script to populate your airtime system with initial products
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('c:/Users/njway/OneDrive/Desktop/NDtech')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from django.db import transaction
from nano.models import AirtimeProduct

def create_initial_airtime_products():
    """Create initial airtime products for all networks"""
    
    initial_products = [
        # Vodacom Products
        {'name': 'Vodacom R5 Airtime', 'network': 'vodacom', 'airtime_type': 'airtime', 'value': 5.00, 'price': 5.50, 'stock': 100},
        {'name': 'Vodacom R10 Airtime', 'network': 'vodacom', 'airtime_type': 'airtime', 'value': 10.00, 'price': 11.00, 'stock': 100},
        {'name': 'Vodacom R20 Airtime', 'network': 'vodacom', 'airtime_type': 'airtime', 'value': 20.00, 'price': 22.00, 'stock': 100},
        {'name': 'Vodacom R50 Airtime', 'network': 'vodacom', 'airtime_type': 'airtime', 'value': 50.00, 'price': 55.00, 'stock': 100},
        
        # MTN Products
        {'name': 'MTN R5 Airtime', 'network': 'mtn', 'airtime_type': 'airtime', 'value': 5.00, 'price': 5.50, 'stock': 100},
        {'name': 'MTN R10 Airtime', 'network': 'mtn', 'airtime_type': 'airtime', 'value': 10.00, 'price': 11.00, 'stock': 100},
        {'name': 'MTN R20 Airtime', 'network': 'mtn', 'airtime_type': 'airtime', 'value': 20.00, 'price': 22.00, 'stock': 100},
        {'name': 'MTN R50 Airtime', 'network': 'mtn', 'airtime_type': 'airtime', 'value': 50.00, 'price': 55.00, 'stock': 100},
        
        # Telkom Products
        {'name': 'Telkom R5 Airtime', 'network': 'telkom', 'airtime_type': 'airtime', 'value': 5.00, 'price': 5.50, 'stock': 100},
        {'name': 'Telkom R10 Airtime', 'network': 'telkom', 'airtime_type': 'airtime', 'value': 10.00, 'price': 11.00, 'stock': 100},
        {'name': 'Telkom R20 Airtime', 'network': 'telkom', 'airtime_type': 'airtime', 'value': 20.00, 'price': 22.00, 'stock': 100},
        {'name': 'Telkom R50 Airtime', 'network': 'telkom', 'airtime_type': 'airtime', 'value': 50.00, 'price': 55.00, 'stock': 100},
        
        # Cell C Products
        {'name': 'Cell C R5 Airtime', 'network': 'cell_c', 'airtime_type': 'airtime', 'value': 5.00, 'price': 5.50, 'stock': 100},
        {'name': 'Cell C R10 Airtime', 'network': 'cell_c', 'airtime_type': 'airtime', 'value': 10.00, 'price': 11.00, 'stock': 100},
        {'name': 'Cell C R20 Airtime', 'network': 'cell_c', 'airtime_type': 'airtime', 'value': 20.00, 'price': 22.00, 'stock': 100},
        {'name': 'Cell C R50 Airtime', 'network': 'cell_c', 'airtime_type': 'airtime', 'value': 50.00, 'price': 55.00, 'stock': 100},
        
        # Rain Products
        {'name': 'Rain R5 Data', 'network': 'rain', 'airtime_type': 'data', 'value': 5.00, 'price': 6.00, 'stock': 50},
        {'name': 'Rain R10 Data', 'network': 'rain', 'airtime_type': 'data', 'value': 10.00, 'price': 12.00, 'stock': 50},
        {'name': 'Rain R20 Data', 'network': 'rain', 'airtime_type': 'data', 'value': 20.00, 'price': 24.00, 'stock': 50},
        
        # BLU Products
        {'name': 'BLU R5 Airtime', 'network': 'blu', 'airtime_type': 'airtime', 'value': 5.00, 'price': 5.50, 'stock': 100},
        {'name': 'BLU R10 Airtime', 'network': 'blu', 'airtime_type': 'airtime', 'value': 10.00, 'price': 11.00, 'stock': 100},
        {'name': 'BLU R20 Airtime', 'network': 'blu', 'airtime_type': 'airtime', 'value': 20.00, 'price': 22.00, 'stock': 100},
    ]
    
    print("Creating initial airtime products...")
    
    with transaction.atomic():
        created_count = 0
        for product_data in initial_products:
            try:
                # Check if product already exists
                existing_product = AirtimeProduct.objects.filter(
                    name=product_data['name'],
                    network=product_data['network'],
                    airtime_type=product_data['airtime_type'],
                    value=product_data['value']
                ).first()
                
                if existing_product:
                    print(f"Product '{product_data['name']}' already exists, skipping...")
                    continue
                
                # Create new product
                product = AirtimeProduct.objects.create(
                    name=product_data['name'],
                    network=product_data['network'],
                    airtime_type=product_data['airtime_type'],
                    value=product_data['value'],
                    price=product_data['price'],
                    description=f"Initial {product_data['network']} {product_data['airtime_type']} - R{product_data['value']}",
                    stock=product_data['stock'],
                    is_active=True
                )
                created_count += 1
                print(f"✓ Created: {product.get_display_name()}")
                
            except Exception as e:
                print(f"✗ Error creating {product_data.get('name', 'Unknown Product')}: {str(e)}")
    
    print(f"\n✅ Successfully created {created_count} airtime products!")
    print("\nYou can now:")
    print("1. Access the airtime dashboard")
    print("2. The network dropdown should show all networks")
    print("3. Stock will be deducted when airtime is sold")
    print("4. Managers can add/update products and stock")

if __name__ == '__main__':
    create_initial_airtime_products()
