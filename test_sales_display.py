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

def test_sales():
    print("=== Testing Sales Display ===\n")
    
    # Get all products
    products = Product.objects.all()
    print(f"Total products in database: {products.count()}\n")
    
    # Check products with sales
    products_on_sale = products.filter(is_on_sale=True)
    print(f"Products marked as on sale: {products_on_sale.count()}\n")
    
    # Check each product's sale status
    for product in products:
        print(f"Product: {product.name}")
        print(f"  - Regular Price: R{product.price}")
        print(f"  - Is On Sale: {product.is_on_sale}")
        if product.is_on_sale:
            print(f"  - Sale Price: R{product.sale_price}")
            print(f"  - Sale Start: {product.sale_start_date}")
            print(f"  - Sale End: {product.sale_end_date}")
            print(f"  - Currently Active: {product.is_currently_on_sale()}")
        print(f"  - Current Price: R{product.get_current_price()}")
        print()
    
    # Test products that should currently be on sale
    currently_on_sale = [p for p in products if p.is_currently_on_sale()]
    print(f"Products currently on sale (active): {len(currently_on_sale)}")
    for product in currently_on_sale:
        print(f"  - {product.name}: R{product.get_current_price()} (was R{product.price})")
    
    # Create a test sale if none exist
    if not products_on_sale.exists():
        print("\n=== Creating Test Sale ===")
        if products.exists():
            test_product = products.first()
            print(f"Creating sale for {test_product.name}")
            
            # Set up a sale that starts now and ends in 1 hour
            test_product.is_on_sale = True
            test_product.sale_price = float(test_product.price) * 0.8  # 20% discount
            test_product.sale_start_date = timezone.now()
            test_product.sale_end_date = timezone.now() + timezone.timedelta(hours=1)
            test_product.save()
            
            print(f"Sale created:")
            print(f"  - Regular Price: R{test_product.price}")
            print(f"  - Sale Price: R{test_product.sale_price}")
            print(f"  - Currently Active: {test_product.is_currently_on_sale()}")
        else:
            print("No products found to create test sale")

if __name__ == '__main__':
    test_sales()
