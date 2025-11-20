import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from nano.models import WarehousePrice, PriceComparison
from django.contrib.auth.models import User

# Get or create a user for imported_by field
user, created = User.objects.get_or_create(username='admin', defaults={'is_superuser': True})

# Create test products with same names in both warehouses but different prices
test_products = [
    ('Coca Cola 2L', 'test_1', 25.99),
    ('Coca Cola 2L', 'test_2', 27.50),
    ('Bread White', 'test_1', 15.99),
    ('Bread White', 'test_2', 16.50),
    ('Milk 1L', 'test_1', 18.99),
    ('Milk 1L', 'test_2', 19.99),
    ('Eggs 6 Pack', 'test_1', 22.50),
    ('Eggs 6 Pack', 'test_2', 24.99),
    ('Sugar 1kg', 'test_1', 32.99),
    ('Sugar 1kg', 'test_2', 35.50),
]

print('Creating test warehouse price data...')
for product_name, warehouse, price in test_products:
    warehouse_price, created = WarehousePrice.objects.get_or_create(
        product_name=product_name,
        warehouse_name=warehouse,
        defaults={
            'price': price,
            'imported_by': user,
            'file_name': 'test_data.csv'
        }
    )
    if created:
        print(f'Created: {product_name} - {warehouse} - R{price}')
    else:
        print(f'Updated: {product_name} - {warehouse} - R{price}')

print('\nRunning price comparison...')
from nano.views import run_price_comparison
run_price_comparison()

print(f'Price comparisons created: {PriceComparison.objects.count()}')

if PriceComparison.objects.exists():
    print('\nSample price comparisons:')
    for pc in PriceComparison.objects.all():
        print(f'  {pc.product_name}')
        print(f'    Best: {pc.lowest_warehouse} @ R{pc.lowest_price}')
        print(f'    Savings: R{pc.price_difference}')
        print(f'    Warehouses: {", ".join(pc.compared_warehouses)}')
        print()

print('Test data creation completed!')
