"""
Main Views for NDtech POS System
Contains core views not moved to specialized modules
"""

from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse, HttpResponse
from django.db import models
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count, Sum, Min, Avg, Max
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import pandas as pd
import json
import re
import csv
import io
import logging
from decimal import Decimal, InvalidOperation
from .models import (
    Product, Sale, UserProfile, PendingOrder, CompletedOrder, Notification, 
    WarehousePrice, PriceComparison, FCMToken, DeviceConnection, ErrorLog, 
    UserActivity, AirtimeProduct, AirtimeSale, AirtimeRequest
)
from .fcm_service import fcm_service, send_fcm_notification_to_user
from .brevo_service import send_receipt_email

# Set up logger
logger = logging.getLogger(__name__)

# Create your views here.
def check_low_stock():
    """Check for low stock products and create notifications"""
    low_stock_products = Product.objects.filter(stock__lt=10)
    for product in low_stock_products:
        # Create notification for admins/managers for low stock
        admin_users = User.objects.filter(
            Q(is_superuser=True) |
            Q(userprofile__role__in=['admin', 'manager'])
        ).distinct()

        for admin_user in admin_users:
            notification = Notification.objects.create(
                title=f"Low Stock Alert: {product.name}",
                message=f"Low stock alert: {product.name} has only {product.stock} units remaining",
                notification_type='low_stock',
                target_role='admin',  # Default to admin role
                target_user=admin_user,
                product=product
            )

            # Send FCM notification
            send_fcm_notification_to_user(notification.target_user, notification.title, notification.message)

@login_required
def home(request):
    # POS Dashboard
    products = Product.objects.all()

    # Check for low stock products when dashboard is loaded
    check_low_stock()

    return render(request, 'nano/home.html', {'products': products})

# Import authentication views from auth_views module
from .views.auth_views import (
    register, sign_up, sign_in, logout_view, forgot_password
)

@login_required
def add_stock(request):
    """Add stock to existing products or create new products"""
    # Allow only superusers or users with admin/manager/cashier roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    # Check if user is manager for Add Product functionality
    is_manager = request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager'])

    if request.method == 'POST':
        mode = request.POST.get('mode', 'add_stock')  # 'add_stock', 'add_product', 'import_products', or 'delete_product'

        if mode == 'delete_product':
            # Delete Product mode - only for managers
            if not is_manager:
                return HttpResponseForbidden("Only managers can delete products.")

            product_id = request.POST.get('product_id')

            if not product_id:
                messages.error(request, 'Product ID is required for deletion')
                return redirect('add_stock')

            try:
                product = Product.objects.get(id=product_id)
                product_name = product.name
                product.delete()
                messages.success(request, f'Product "{product_name}" deleted successfully!')
            except Product.DoesNotExist:
                messages.error(request, 'Product not found')

            return redirect('add_stock')

        elif mode == 'import_products':
            # Import Products mode - only for managers
            if not is_manager:
                return HttpResponseForbidden("Only managers can import products.")

            if 'file' not in request.FILES:
                messages.error(request, 'Please select a file to upload')
                return redirect('add_stock')

            file = request.FILES['file']

            # Check file extension
            file_extension = file.name.split('.')[-1].lower()
            if file_extension not in ['csv', 'xlsx', 'xls']:
                messages.error(request, 'Only CSV and Excel files are supported')
                return redirect('add_stock')

            try:
                # Read file using pandas
                if file_extension == 'csv':
                    df = pd.read_csv(file)
                else:  # Excel file
                    df = pd.read_excel(file)

                # Validate required columns
                required_columns = ['name', 'price', 'category']
                missing_columns = [col for col in required_columns if col not in df.columns]

                if missing_columns:
                    messages.error(request, (
                        f'Missing required columns: {", ".join(missing_columns)}. '
                        'Ensure your file includes of following columns: name, price, category. '
                        'You can use sample CSV `sample_products_import.csv` as a template.'
                    ))
                    return redirect('add_stock')

                # Process each row with detailed error reporting
                imported_count = 0
                skipped_rows = []  # collect (row_number, reason)

                for index, row in df.iterrows():
                    row_number = index + 2  # account for header row in CSV/Excel
                    try:
                        # Clean and validate data
                        product_name = str(row['name']).strip() if 'name' in row and pd.notna(row['name']) else ''
                        try:
                            price = float(row['price']) if 'price' in row and pd.notna(row['price']) else 0
                        except Exception:
                            price = 0
                        category = str(row['category']).strip() if 'category' in row and pd.notna(row['category']) else ''

                        # Optional fields
                        description = str(row.get('description', '')).strip() if 'description' in row and pd.notna(row['description']) else ''
                        stock = int(row.get('stock', 0)) if 'stock' in row and pd.notna(row['stock']) else 0
                        barcode = str(row.get('barcode', '')).strip() if 'barcode' in row and pd.notna(row['barcode']) else None
                        expiry_date_str = str(row.get('expiry_date', '')).strip() if 'expiry_date' in row and pd.notna(row['expiry_date']) else None

                        # Validate required fields
                        if not product_name:
                            skipped_rows.append((row_number, 'Missing product name'))
                            continue
                        if price <= 0:
                            skipped_rows.append((row_number, 'Invalid or missing price (must be > 0)'))
                            continue
                        if not category:
                            skipped_rows.append((row_number, 'Missing category'))
                            continue

                        # Validate category value
                        if category not in dict(Product.CATEGORY_CHOICES):
                            skipped_rows.append((row_number, f'Invalid category: "{category}"'))
                            continue

                        # Parse expiry date if provided
                        expiry_date = None
                        if expiry_date_str:
                            try:
                                try:
                                    expiry_date = timezone.datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
                                except ValueError:
                                    expiry_date = timezone.datetime.strptime(expiry_date_str, '%d/%m/%Y').date()
                            except ValueError:
                                skipped_rows.append((row_number, f'Invalid expiry date format: "{expiry_date_str}"'))
                                continue

                        # Check if product already exists (case-insensitive)
                        if Product.objects.filter(name__iexact=product_name).exists():
                            skipped_rows.append((row_number, 'Duplicate product (already exists)'))
                            continue

                        # Create the product
                        Product.objects.create(
                            name=product_name,
                            price=price,
                            category=category,
                            description=description,
                            stock=stock,
                            barcode=barcode or '',
                            expiry_date=expiry_date
                        )
                        imported_count += 1

                    except Exception as e:
                        skipped_rows.append((row_number, f'Unexpected error: {str(e)}'))
                        continue

                # Build friendly messages for the user
                if imported_count > 0:
                    messages.success(request, f'Successfully imported {imported_count} products.')

                if skipped_rows:
                    total_skipped = len(skipped_rows)
                    # Show up to 6 example row errors to help user identify problems
                    examples = '; '.join([f'Row {r}: {reason}' for r, reason in skipped_rows[:6]])
                    messages.warning(request, (
                        f'{total_skipped} rows were skipped due to issues. Examples: {examples}. '
                        'Please check your file and correct these rows. Required columns: name, price, category. '
                        'See sample CSV `sample_products_import.csv` for the expected format.'
                    ))

                return redirect('add_stock')

            except Exception as e:
                messages.error(request, f'Error processing file: {str(e)}')
                return redirect('add_stock')

        elif mode == 'add_product':
            # Add Product mode - only for managers
            if not is_manager:
                return HttpResponseForbidden("Only managers can add new products.")

            name = request.POST.get('name', '').strip()
            price_str = request.POST.get('price', '').strip()
            description = request.POST.get('description', '').strip()
            category = request.POST.get('category', '').strip()
            expiry_date_str = request.POST.get('expiry_date', '').strip()
            stock_str = request.POST.get('stock', '').strip()

            errors = {}

            if not name:
                errors['name'] = 'Product name is required'
            elif len(name) < 2:
                errors['name'] = 'Product name must be at least 2 characters'
            elif Product.objects.filter(name__iexact=name).exists():
                errors['name'] = f'Product "{name}" already exists (case-insensitive check)'

            if not price_str:
                errors['price'] = 'Price is required'
            else:
                try:
                    price = float(price_str)
                    if price <= 0:
                        errors['price'] = 'Price must be greater than 0'
                except ValueError:
                    errors['price'] = 'Price must be a valid number'

            if not category:
                errors['category'] = 'Category is required'
            elif category not in dict(Product.CATEGORY_CHOICES):
                errors['category'] = 'Invalid category'

            if not stock_str:
                errors['stock'] = 'Stock quantity is required'
            else:
                try:
                    stock = int(stock_str)
                    if stock < 0:
                        errors['stock'] = 'Stock cannot be negative'
                except ValueError:
                    errors['stock'] = 'Stock must be a valid number'

            if errors:
                for field, error in errors.items():
                    messages.error(request, error)

                # Create category examples list for the error case
                category_examples_list = [
                    ('staple_foods', 'Staple Foods', 'e.g., Maize Meal, Samp, Rice, Pap, Flour'),
                    ('snacks_chips', 'Snacks & Chips', 'e.g., Lays, Simba, Doritos, Nik Naks'),
                    ('cold_drinks', 'Cold Drinks', 'e.g., Coke, Fanta, Sprite, Stoney'),
                    ('sweets_treats', 'Sweets & Treats', 'e.g., Chocolates, Sweets, Gum, Biscuits'),
                    ('basic_groceries', 'Basic Groceries', 'e.g., Sugar, Salt, Tea, Coffee, Oil'),
                    ('dairy_eggs', 'Dairy & Eggs', 'e.g., Milk, Cheese, Yogurt, Eggs'),
                    ('bread_baked', 'Bread & Baked Goods', 'e.g., Bread, Rolls, Buns, Cakes'),
                    ('canned_goods', 'Canned Goods', 'e.g., Baked Beans, Tuna, Pilchards'),
                    ('personal_care', 'Personal Care', 'e.g., Soap, Shampoo, Toothpaste'),
                    ('household_items', 'Household Items', 'e.g., Cleaning Products, Detergent'),
                    ('airtime_data', 'Airtime & Data', 'e.g., Vodacom, MTN, Telkom vouchers'),
                    ('frozen_goods', 'Frozen Goods', 'e.g., Frozen Vegetables, Ice Cream'),
                    ('tuckshop_packs', 'Tuckshop Packs', 'e.g., Combo deals, Party packs'),
                    ('stationery', 'Stationery', 'e.g., Pens, Notebooks, Erasers'),
                    ('baby_products', 'Baby Products', 'e.g., Nappies, Baby Formula, Baby Food'),
                    ('seasonal_items', 'Seasonal Items', 'e.g., Christmas decorations, Easter eggs'),
                ]

                return render(request, 'nano/add_stock.html', {
                    'mode': 'add_product',
                    'is_manager': is_manager,
                    'category_examples_list': category_examples_list
                })

            # Parse expiry date if provided
            expiry_date = None
            if expiry_date_str:
                try:
                    expiry_date = timezone.datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
                    if expiry_date <= timezone.now().date():
                        messages.warning(request, 'Expiry date is in the past, but product will be created anyway.')
                except ValueError:
                    messages.warning(request, 'Invalid date format, expiry date not set.')
                    expiry_date = None

            # Create the product
            product = Product.objects.create(
                name=name,
                price=price,
                description=description,
                category=category,
                expiry_date=expiry_date,
                stock=stock
            )

            messages.success(request, f'Product "{name}" added successfully!')
            return redirect('add_stock')

        else:  # add_stock mode
            product_id = request.POST.get('product_id')
            quantity_str = request.POST.get('quantity', '').strip()

            if not product_id:
                messages.error(request, 'Please select a product')
                return redirect('add_stock')

            if not quantity_str:
                messages.error(request, 'Quantity is required')
                return redirect('add_stock')

            try:
                quantity = int(quantity_str)
                if quantity <= 0:
                    messages.error(request, 'Quantity must be greater than 0')
                    return redirect('add_stock')
            except ValueError:
                messages.error(request, 'Quantity must be a valid number')
                return redirect('add_stock')

            try:
                product = Product.objects.get(id=product_id)
                product.stock += quantity
                product.save()
                messages.success(request, f'Added {quantity} units to {product.name}')
            except Product.DoesNotExist:
                messages.error(request, 'Product not found')

            return redirect('add_stock')

    products = Product.objects.all()

    # Create category examples list with examples for each category
    category_examples_list = [
        ('staple_foods', 'Staple Foods', 'e.g., Maize Meal, Samp, Rice, Pap, Flour'),
        ('snacks_chips', 'Snacks & Chips', 'e.g., Lays, Simba, Doritos, Nik Naks'),
        ('cold_drinks', 'Cold Drinks', 'e.g., Coke, Fanta, Sprite, Stoney'),
        ('sweets_treats', 'Sweets & Treats', 'e.g., Chocolates, Sweets, Gum, Biscuits'),
        ('basic_groceries', 'Basic Groceries', 'e.g., Sugar, Salt, Tea, Coffee, Oil'),
        ('dairy_eggs', 'Dairy & Eggs', 'e.g., Milk, Cheese, Yogurt, Eggs'),
        ('bread_baked', 'Bread & Baked Goods', 'e.g., Bread, Rolls, Buns, Cakes'),
        ('canned_goods', 'Canned Goods', 'e.g., Baked Beans, Tuna, Pilchards'),
        ('personal_care', 'Personal Care', 'e.g., Soap, Shampoo, Toothpaste'),
        ('household_items', 'Household Items', 'e.g., Cleaning Products, Detergent'),
        ('airtime_data', 'Airtime & Data', 'e.g., Vodacom, MTN, Telkom vouchers'),
        ('frozen_goods', 'Frozen Goods', 'e.g., Frozen Vegetables, Ice Cream'),
        ('tuckshop_packs', 'Tuckshop Packs', 'e.g., Combo deals, Party packs'),
        ('stationery', 'Stationery', 'e.g., Pens, Notebooks, Erasers'),
        ('baby_products', 'Baby Products', 'e.g., Nappies, Baby Formula, Baby Food'),
        ('seasonal_items', 'Seasonal Items', 'e.g., Christmas decorations, Easter eggs'),
    ]

    return render(request, 'nano/add_stock.html', {
        'products': products,
        'mode': 'add_stock',
        'is_manager': is_manager,
        'category_examples_list': category_examples_list
    })

@login_required
def manage_sales(request):
    """Manage product sales and discounts"""
    # Allow only superusers or users with admin/manager roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    if request.method == 'POST':
        action = request.POST.get('action', '')
        product_id = request.POST.get('product_id', '')

        if not product_id:
            messages.error(request, 'Product ID is required')
            return redirect('manage_sales')

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            messages.error(request, 'Product not found')
            return redirect('manage_sales')

        if action == 'add_sale' or action == 'quick_sale':
            # Add or update sale (including quick sales)
            sale_price_str = request.POST.get('sale_price', '').strip()
            sale_start_date = request.POST.get('sale_start_date', '')
            sale_end_date = request.POST.get('sale_end_date', '')

            errors = {}

            if not sale_price_str:
                errors['sale_price'] = 'Sale price is required'
            else:
                try:
                    sale_price = float(sale_price_str)
                    if sale_price <= 0:
                        errors['sale_price'] = 'Sale price must be greater than 0'
                    elif sale_price >= float(product.price):
                        errors['sale_price'] = 'Sale price must be less than regular price'
                except ValueError:
                    errors['sale_price'] = 'Sale price must be a valid number'

            # Parse dates if provided
            sale_start = None
            if sale_start_date:
                try:
                    # Make datetime timezone-aware
                    naive_datetime = timezone.datetime.strptime(sale_start_date, '%Y-%m-%dT%H:%M')
                    sale_start = timezone.make_aware(naive_datetime)
                    # For quick sales, allow immediate start
                    if action != 'quick_sale' and sale_start < timezone.now():
                        errors['sale_start_date'] = 'Start date cannot be in the past'
                except ValueError:
                    errors['sale_start_date'] = 'Invalid start date format'

            sale_end = None
            if sale_end_date:
                try:
                    # Make datetime timezone-aware
                    naive_datetime = timezone.datetime.strptime(sale
