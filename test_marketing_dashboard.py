#!/usr/bin/env python
"""
Test script to create sample data for the marketing dashboard
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from nano.models import WarehousePrice, PriceComparison
from django.contrib.auth.models import User
from decimal import Decimal

def create_sample_data():
    """Create sample warehouse price data for testing the marketing dashboard"""
    
    print("Creating sample warehouse price data...")
    
    # Sample warehouses
    warehouses = ['Main Warehouse', 'North Warehouse', 'East Warehouse', 'South Warehouse']
    
    # Sample products with different categories
    products = [
        ('Coca Cola 2L', 'cold_drinks', '6001234567890'),
        ('Bread White', 'bread_baked', '6001234567891'),
        ('Maize Meal 5kg', 'staple_foods', '6001234567892'),
        ('Sugar 1kg', 'basic_groceries', '6001234567893'),
        ('Cooking Oil 2L', 'basic_groceries', '6001234567894'),
        ('Milk 1L', 'dairy_eggs', '6001234567895'),
        ('Eggs 30 pack', 'dairy_eggs', '6001234567896'),
        ('Lays Chips', 'snacks_chips', '6001234567897'),
        ('Chocolate Bar', 'sweets_treats', '6001234567898'),
        ('Toilet Paper', 'household_items', '6001234567899'),
        ('Soap', 'personal_care', '6001234567900'),
        ('Airtime R50', 'airtime_data', '6001234567901'),
    ]
    
    # Clear existing data
    WarehousePrice.objects.all().delete()
    PriceComparison.objects.all().delete()
    
    # Create warehouse prices with varying prices
    for product_name, category, barcode in products:
        base_price = Decimal('20.00') + (hash(product_name) % 80)
        
        for i, warehouse in enumerate(warehouses):
            # Vary prices by warehouse with more significant differences
            price_multipliers = [1.0, 1.15, 0.85, 1.25]  # Different multipliers for each warehouse
            price = base_price * Decimal(str(price_multipliers[i]))
            price = max(Decimal('5.00'), price)  # Minimum price of R5
            
            WarehousePrice.objects.create(
                product_name=product_name,
                warehouse_name=warehouse,
                price=price,
                category=category,
                barcode=barcode,
                stock_quantity=100,
                unit_size='1 unit'
            )
    
    print(f"Created {WarehousePrice.objects.count()} warehouse price records")
    
    # Run price comparison
    from nano.views import run_price_comparison
    run_price_comparison()
    
    print(f"Created {PriceComparison.objects.count()} price comparison records")
    
    # Show some statistics
    comparisons = PriceComparison.objects.all()
    if comparisons.exists():
        total_savings = sum(c.price_difference for c in comparisons)
        avg_savings = total_savings / comparisons.count()
        max_savings = max(c.price_difference for c in comparisons)
        
        print(f"\nMarketing Dashboard Statistics:")
        print(f"Total products compared: {comparisons.count()}")
        print(f"Total savings potential: R{total_savings:.2f}")
        print(f"Average savings: R{avg_savings:.2f}")
        print(f"Maximum single saving: R{max_savings:.2f}")
        print(f"Unique warehouses: {len(set(c.lowest_warehouse for c in comparisons))}")
        
        # Show top 3 savings
        top_savings = comparisons.order_by('-price_difference')[:3]
        print(f"\nTop 3 Savings Opportunities:")
        for i, comp in enumerate(top_savings, 1):
            print(f"{i}. {comp.product_name}: Save R{comp.price_difference:.2f} at {comp.lowest_warehouse}")
    
    print("\nSample data created successfully!")
    print("You can now access the marketing dashboard at:")
    print("http://localhost:8000/warehouse/comparisons/marketing/")

if __name__ == '__main__':
    create_sample_data()
