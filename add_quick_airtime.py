import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from nano.models import AirtimeProduct

# Check existing products
existing = AirtimeProduct.objects.count()
print(f'Existing airtime products: {existing}')

# Always create missing quick airtime products
print('Checking and creating quick airtime products...')

# Define quick airtime products
networks = ['vodacom', 'mtn', 'telkom', 'cell_c']
denominations = [10, 20, 50, 100]

created_count = 0
for network in networks:
    for value in denominations:
        product_name = f'{network.title()} R{value} Airtime'
        
        # Check if product already exists
        if not AirtimeProduct.objects.filter(name=product_name).exists():
            # Calculate price (add small markup)
            price = float(value) + (float(value) * 0.05)  # 5% markup
            
            AirtimeProduct.objects.create(
                name=product_name,
                network=network,
                airtime_type='airtime',
                value=value,
                price=round(price, 2),
                stock=100,  # Initial stock
                is_active=True
            )
            print(f'Created: {product_name} - R{value} - Price: R{round(price, 2)}')
            created_count += 1
        else:
            print(f'Already exists: {product_name}')

print(f'\nTotal products created: {created_count}')
print(f'Total products in database: {AirtimeProduct.objects.count()}')
