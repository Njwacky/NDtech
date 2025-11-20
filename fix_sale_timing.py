import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from nano.models import Product
from django.utils import timezone

def fix_sale():
    print("=== Fixing Sale Timing ===\n")
    
    # Get the product with sale
    product = Product.objects.get(name="tomatos")
    
    print(f"Product: {product.name}")
    print(f"Current time: {timezone.now()}")
    print(f"Sale Start: {product.sale_start_date}")
    print(f"Sale End: {product.sale_end_date}")
    print(f"Currently Active: {product.is_currently_on_sale()}")
    
    # Update the sale to be active now
    product.sale_start_date = timezone.now() - timezone.timedelta(minutes=5)  # Started 5 minutes ago
    product.sale_end_date = timezone.now() + timezone.timedelta(hours=1)  # Ends in 1 hour
    product.save()
    
    print(f"\nUpdated sale:")
    print(f"Sale Start: {product.sale_start_date}")
    print(f"Sale End: {product.sale_end_date}")
    print(f"Currently Active: {product.is_currently_on_sale()}")
    print(f"Current Price: R{product.get_current_price()}")
    
    # Also create a few more test sales
    print("\n=== Creating Additional Test Sales ===")
    
    # Get a few other products
    other_products = Product.objects.exclude(name="tomatos")[:3]
    
    for p in other_products:
        p.is_on_sale = True
        p.sale_price = float(p.price) * 0.8  # 20% discount
        p.sale_start_date = timezone.now() - timezone.timedelta(minutes=10)
        p.sale_end_date = timezone.now() + timezone.timedelta(hours=2)
        p.save()
        
        print(f"Created sale for {p.name}:")
        print(f"  - Regular Price: R{p.price}")
        print(f"  - Sale Price: R{p.sale_price}")
        print(f"  - Currently Active: {p.is_currently_on_sale()}")
    
    print("\n=== Summary ===")
    currently_on_sale = Product.objects.filter(is_on_sale=True)
    print(f"Products marked as on sale: {currently_on_sale.count()}")
    
    active_sales = [p for p in currently_on_sale if p.is_currently_on_sale()]
    print(f"Products currently active on sale: {len(active_sales)}")
    
    for product in active_sales:
        print(f"  - {product.name}: R{product.get_current_price()} (was R{product.price})")

if __name__ == '__main__':
    fix_sale()
