#!/usr/bin/env python
import os
import django
import json

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from nano.models import PendingOrder, Product, Sale, CompletedOrder
from django.contrib.auth.models import User

def test_checkout_fix():
    print("=== TEST CHECKOUT FIX ===")
    
    # Get the pending order
    order = PendingOrder.objects.first()
    if not order:
        print("No pending orders found")
        return
    
    print(f"Testing checkout for Order ID: {order.id}")
    print(f"Customer: {order.customer_name}")
    print(f"Items: {order.items}")
    
    # Test product lookup for each item
    cart_items = order.items
    stock_issues = []
    products_updated = []
    
    for item in cart_items:
        print(f"\nProcessing item: {item}")
        
        # Handle both product_id (for backward compatibility) and product name
        product_id = item.get('product_id')
        product_name = item.get('product')
        quantity = item.get('quantity', 0)

        if quantity <= 0:
            stock_issues.append(f'Invalid item data: quantity={quantity}')
            continue

        try:
            # Try to find product by ID first (for backward compatibility)
            if product_id:
                print(f"  Looking up product by ID: {product_id}")
                product = Product.objects.get(id=product_id)
            elif product_name:
                # Try to find product by name (current format)
                print(f"  Looking up product by name: {product_name}")
                product = Product.objects.get(name=product_name)
            else:
                stock_issues.append(f'No product identifier found in item: {item}')
                continue
            
            print(f"  ✓ Found product: {product.name} (ID: {product.id}, Stock: {product.stock})")
            
            if product.stock >= quantity:
                print(f"  ✓ Sufficient stock: {product.stock} >= {quantity}")
                products_updated.append(product.name)
            else:
                print(f"  ✗ Insufficient stock: {product.stock} < {quantity}")
                stock_issues.append(f'Insufficient stock for {product.name}. Available: {product.stock}, Required: {quantity}')
                
        except Product.DoesNotExist:
            if product_id:
                print(f"  ✗ Product not found for ID: {product_id}")
                stock_issues.append(f'Product not found for ID: {product_id}')
            elif product_name:
                print(f"  ✗ Product not found for name: {product_name}")
                stock_issues.append(f'Product not found: {product_name}')
            else:
                print(f"  ✗ No product identifier in item")
                stock_issues.append(f'Product not found in item: {item}')
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            stock_issues.append(f'Error updating {item.get("product", "unknown product")}: {str(e)}')
    
    print(f"\n=== RESULTS ===")
    if stock_issues:
        print("❌ Stock issues found:")
        for issue in stock_issues:
            print(f"  - {issue}")
    else:
        print("✅ All products found and stock is sufficient!")
        print(f"Products that would be updated: {products_updated}")
        
        # Simulate the stock update
        print("\n=== SIMULATING STOCK UPDATE ===")
        for item in cart_items:
            product_name = item.get('product')
            quantity = item.get('quantity', 0)
            
            try:
                product = Product.objects.get(name=product_name)
                old_stock = product.stock
                new_stock = old_stock - quantity
                print(f"  {product.name}: {old_stock} -> {new_stock} (-{quantity})")
            except Product.DoesNotExist:
                print(f"  ✗ Could not find product: {product_name}")

if __name__ == '__main__':
    test_checkout_fix()
