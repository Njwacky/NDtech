#!/usr/bin/env python
import os
import sys
import django

# Add project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from nano.models import CompletedOrder

def main():
    print("Checking completed orders...")
    
    # Get all completed orders
    orders = CompletedOrder.objects.all().order_by('-completed_at')
    
    print(f"Total completed orders: {orders.count()}")
    
    # Show last 5 orders with customer info
    for i, order in enumerate(orders[:5]):
        print(f"\nOrder {i+1}:")
        print(f"  ID: {order.id}")
        print(f"  Customer Name: '{order.customer_name}'")
        print(f"  Customer Phone: '{order.customer_phone}'")
        print(f"  Total: R{order.total}")
        print(f"  Completed At: {order.completed_at}")
        print(f"  Items: {order.items}")
    
    if orders.count() == 0:
        print("No completed orders found in the database.")
    
    # Check for orders with empty customer data
    empty_name_orders = CompletedOrder.objects.filter(customer_name='')
    empty_phone_orders = CompletedOrder.objects.filter(customer_phone='')
    
    print(f"\nOrders with empty customer name: {empty_name_orders.count()}")
    print(f"Orders with empty customer phone: {empty_phone_orders.count()}")

if __name__ == '__main__':
    main()
