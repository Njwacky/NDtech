import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from nano.models import WarehousePrice, PriceComparison

print('Warehouse Prices:')
for wp in WarehousePrice.objects.all()[:10]:
    print(f'  {wp.product_name} - {wp.warehouse_name} - R{wp.price}')

print(f'\nTotal Warehouse Prices: {WarehousePrice.objects.count()}')
print(f'Total Price Comparisons: {PriceComparison.objects.count()}')

print('\nPrice Comparisons:')
for pc in PriceComparison.objects.all()[:5]:
    print(f'  {pc.product_name} - {pc.lowest_warehouse} - R{pc.lowest_price} - Warehouses: {len(pc.compared_warehouses)}')

# Check unique warehouses
warehouses = WarehousePrice.objects.values_list('warehouse_name', flat=True).distinct()
print(f'\nUnique Warehouses: {list(warehouses)}')

# Check products with multiple warehouses
products_with_multiple = []
for product_name in WarehousePrice.objects.values_list('product_name', flat=True).distinct():
    warehouse_count = WarehousePrice.objects.filter(product_name=product_name).values_list('warehouse_name', flat=True).distinct().count()
    if warehouse_count > 1:
        products_with_multiple.append((product_name, warehouse_count))

print(f'\nProducts with multiple warehouses: {len(products_with_multiple)}')
for product_name, count in products_with_multiple[:5]:
    print(f'  {product_name}: {count} warehouses')
