import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from nano.models import Product
from django.template import Template, Context
from django.template.loader import render_to_string

def test_template_rendering():
    print("=== Testing Template Rendering ===\n")
    
    # Get products with sales
    products = Product.objects.all()
    
    # Test the template logic for a product on sale
    test_product = products.filter(is_on_sale=True).first()
    
    if test_product:
        print(f"Testing template rendering for: {test_product.name}")
        print(f"  - is_on_sale: {test_product.is_on_sale}")
        print(f"  - is_currently_on_sale(): {test_product.is_currently_on_sale()}")
        print(f"  - price: {test_product.price}")
        print(f"  - sale_price: {test_product.sale_price}")
        print(f"  - get_current_price(): {test_product.get_current_price()}")
        print(f"  - get_discount_amount(): {test_product.get_discount_amount()}")
        print(f"  - get_discount_percentage(): {test_product.get_discount_percentage()}")
        
        # Test the template conditions
        template_content = """
        Product: {{ product.name }}
        {% if product.is_currently_on_sale %}
            ON SALE - Regular: R{{ product.price }}, Sale: R{{ product.sale_price }}
            Discount: R{{ product.get_discount_amount }} ({{ product.get_discount_percentage }}%)
        {% else %}
            Regular Price: R{{ product.price }}
        {% endif %}
        """
        
        template = Template(template_content)
        context = Context({'product': test_product})
        rendered = template.render(context)
        
        print(f"\nTemplate Output:")
        print(rendered)
    else:
        print("No products with sales found!")
    
    # Test all products
    print(f"\n=== All Products Template Test ===")
    for product in products:
        on_sale_display = "SALE" if product.is_currently_on_sale() else "REGULAR"
        price_display = f"R{product.get_current_price()}"
        if product.is_currently_on_sale():
            price_display += f" (was R{product.price})"
        print(f"{product.name}: {on_sale_display} - {price_display}")

if __name__ == '__main__':
    test_template_rendering()
