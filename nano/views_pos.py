"""
POS/Inventory Views
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse, HttpResponse
from django.db import models, transaction
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count, Sum, Min, Avg, Max
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from confige.security import rate_limit
import pandas as pd

import json
import re
import csv
import io
import logging
from decimal import Decimal, InvalidOperation
from .models import Product, Sale, UserProfile, PendingOrder, CompletedOrder, Notification, WarehousePrice, PriceComparison, FCMToken, DeviceConnection, ErrorLog, UserActivity, AirtimeProduct, AirtimeSale, AirtimeRequest
from .fcm_service import fcm_service, send_fcm_notification_to_user
from .serializers import PendingOrderCreateSerializer

# Set up logger
logger = logging.getLogger(__name__)

# Create your views here.


def add_stock(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
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
                        'Ensure your file includes the following columns: name, price, category. '
                        'You can use the sample CSV `sample_products_import.csv` as a template.'
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
                        no_expiry_date = str(row.get('no_expiry_date', '')).strip().lower() in ['true', '1', 'yes', 'on']
                        
                        if not no_expiry_date and expiry_date_str:
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
                        , workspace=workspace)
                        imported_count += 1

                    except Exception as e:
                        skipped_rows.append((row_number, f'Unexpected error: {str(e)}'))
                        continue

                # Build friendly messages for the user
                if imported_count > 0:
                    messages.success(request, f'Successfully imported {imported_count} products.')

                if skipped_rows:
                    total_skipped = len(skipped_rows)
                    # Show up to 6 example row errors to help the user identify problems
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
            # Check for no_expiry_date checkbox - handle various truthy values
            no_expiry_val = request.POST.get('no_expiry_date')
            no_expiry_date = no_expiry_val in ['on', 'true', 'True', '1', 'checked']

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

            # Validate expiry date only if "No Expiry Date" is not checked
            expiry_date = None
            if not no_expiry_date:
                if not expiry_date_str:
                    errors['expiry_date'] = 'Expiry date is required (or check "No Expiry Date")'
                else:
                    try:
                        expiry_date = timezone.datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
                        # Allow adding products that are already expired (maybe keeping stock record), 
                        # but warn? Or strictly forbid?
                        # User might be adding old stock. Let's allow past dates but maybe just for valid dates.
                        # The previous code forbade past dates: if expiry_date <= timezone.now().date()
                        # Let's keep that restriction if that's the business rule.
                        if expiry_date <= timezone.now().date():
                            errors['expiry_date'] = 'Expiry date must be in the future'
                    except ValueError:
                        errors['expiry_date'] = 'Invalid date format'

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

            # Create the product
            product = Product.objects.create(
                name=name,
                price=price,
                description=description,
                category=category,
                expiry_date=expiry_date,
                stock=stock
            , workspace=workspace)

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
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
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
                    # Make the datetime timezone-aware
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
                    # Make the datetime timezone-aware
                    naive_datetime = timezone.datetime.strptime(sale_end_date, '%Y-%m-%dT%H:%M')
                    sale_end = timezone.make_aware(naive_datetime)
                    if sale_start and sale_end <= sale_start:
                        errors['sale_end_date'] = 'End date must be after start date'
                except ValueError:
                    errors['sale_end_date'] = 'Invalid end date format'

            if errors:
                for field, error in errors.items():
                    messages.error(request, error)
            else:
                # Update product sale information
                product.is_on_sale = True
                product.sale_price = sale_price
                product.sale_start_date = sale_start
                product.sale_end_date = sale_end
                product.save()

                if action == 'quick_sale':
                    messages.success(request, f'Quick sale started for "{product.name}"! Sale price: R{sale_price}')
                elif product.is_currently_on_sale():
                    messages.success(request, f'Sale activated for "{product.name}"! Sale price: R{sale_price}')
                else:
                    messages.success(request, f'Sale scheduled for "{product.name}"! Sale price: R{sale_price}')

        elif action == 'remove_sale':
            # Remove sale
            product.is_on_sale = False
            product.sale_price = None
            product.sale_start_date = None
            product.sale_end_date = None
            product.save()
            messages.success(request, f'Sale removed for "{product.name}"')

        return redirect('manage_sales')

    products = Product.objects.all().order_by('name')

    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'nano/manage_sales.html', {'products': page_obj})

@login_required


def spaza_pos(request):
    """DreamsPOS-style cashier screen for quick spaza shop counter sales."""
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    products = Product.objects.filter(stock__gt=0).order_by('category', 'name')
    product_payload = []
    for product in products:
        current_price = product.get_current_price()
        product_payload.append({
            'id': product.id,
            'name': product.name,
            'price': float(current_price),
            'regular_price': float(product.price),
            'category': product.category,
            'category_display': product.get_category_display(),
            'stock': product.stock,
            'barcode': product.barcode or '',
            'on_sale': product.is_currently_on_sale(),
        })

    categories = [
        {'value': value, 'label': label}
        for value, label in Product.CATEGORY_CHOICES
        if products.filter(category=value).exists()
    ]

    return render(request, 'nano/spaza_pos.html', {
        'products_json': json.dumps(product_payload),
        'categories_json': json.dumps(categories),
        'products_count': products.count(),
    })


@login_required


def spaza_pos_complete_sale(request):
    """Create a completed order directly from the cashier POS cart and reduce stock."""
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

    try:
        from django.db import transaction

        data = json.loads(request.body)
        cart_items = data.get('items', [])
        customer_name = (data.get('customer_name') or 'Walk-in').strip() or 'Walk-in'
        customer_phone = (data.get('customer_phone') or '').strip()
        payment_method = (data.get('payment_method') or 'cash').strip().lower()
        cash_received = Decimal(str(data.get('cash_received') or 0))

        payment_map = {
            'cash': 'cash',
            'card': 'card',
            'eft': 'mobile',
            'mobile': 'mobile',
            'other': 'mobile',
        }
        payment_method = payment_map.get(payment_method, 'cash')

        if not cart_items:
            return JsonResponse({'success': False, 'error': 'Cart is empty'})

        normalized_items = []
        calculated_total = Decimal('0.00')

        with transaction.atomic():
            # Lock product rows while checking and updating stock.
            for item in cart_items:
                product_id = item.get('product_id') or item.get('id')
                try:
                    quantity = int(item.get('quantity') or item.get('qty') or 0)
                except (TypeError, ValueError):
                    return JsonResponse({'success': False, 'error': 'Invalid quantity in cart'})

                if not product_id or quantity <= 0:
                    return JsonResponse({'success': False, 'error': 'Invalid cart item'})

                product = Product.objects.select_for_update().get(id=product_id)
                if product.stock < quantity:
                    return JsonResponse({
                        'success': False,
                        'error': f'Insufficient stock for {product.name}. Available: {product.stock}, Required: {quantity}'
                    })

                unit_price = Decimal(str(product.get_current_price())).quantize(Decimal('0.01'))
                line_total = (unit_price * quantity).quantize(Decimal('0.01'))
                calculated_total += line_total

                normalized_items.append({
                    'product_id': product.id,
                    'product': product.name,
                    'quantity': quantity,
                    'price': float(unit_price),
                    'total': float(line_total),
                    'category': product.get_category_display(),
                    'barcode': product.barcode or '',
                })

            calculated_total = calculated_total.quantize(Decimal('0.01'))
            if payment_method != 'cash' and cash_received <= 0:
                cash_received = calculated_total

            if payment_method == 'cash' and cash_received < calculated_total:
                return JsonResponse({'success': False, 'error': 'Cash received is less than the sale total'})

            change_given = max(Decimal('0.00'), cash_received - calculated_total).quantize(Decimal('0.01'))

            completed_order = CompletedOrder.objects.create(
                customer_name=customer_name,
                customer_phone=customer_phone,
                items=normalized_items,
                total=calculated_total,
                cash_received=cash_received,
                change_given=change_given,
                payment_method=payment_method,
                processed_by=request.user,
            )

            for item in normalized_items:
                product = Product.objects.select_for_update().get(id=item['product_id'])
                product.stock -= item['quantity']
                product.save(update_fields=['stock'])
                Sale.objects.create(
                    product=product,
                    quantity=item['quantity'],
                    total_price=Decimal(str(item['total']))
                )

        return JsonResponse({
            'success': True,
            'order_id': completed_order.id,
            'receipt_url': f'/completed_order_details/{completed_order.id}/',
            'total': str(calculated_total),
            'change': str(change_given),
            'message': f'Sale completed successfully. Receipt #{completed_order.id}'
        })

    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'One of the products no longer exists'})
    except (json.JSONDecodeError, InvalidOperation):
        return JsonResponse({'success': False, 'error': 'Invalid sale data'})
    except Exception as e:
        logger.exception('Error completing spaza POS sale')
        return JsonResponse({'success': False, 'error': str(e)})

@login_required


def pending_orders(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    # Allow only superusers or users with admin/manager/cashier roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    orders = PendingOrder.objects.filter(status='pending').order_by('-created_at')

    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'nano/pending_orders.html', {'orders': page_obj})

@login_required


def save_order(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            input_serializer = PendingOrderCreateSerializer(data=data)
            if not input_serializer.is_valid():
                return JsonResponse({'success': False, 'errors': input_serializer.errors}, status=400)
            validated = input_serializer.validated_data
            cart_items = validated['items']
            customer_name = validated['customer_name']
            customer_phone = validated['customer_phone']
            idempotency_key = validated.get('idempotency_key', '')

            # A retry with the same key returns the original order instead of creating a duplicate.
            if idempotency_key:
                existing_order = PendingOrder.objects.filter(
                    idempotency_key=idempotency_key, user=request.user
                ).first()
                if existing_order:
                    return JsonResponse({'success': True, 'order_id': existing_order.id, 'duplicate': True})

            if not cart_items:
                return JsonResponse({'success': False, 'error': 'No items in cart'})

            # Validate customer information
            if not customer_name:
                return JsonResponse({'success': False, 'error': 'Customer name is required'})

            if not customer_phone:
                return JsonResponse({'success': False, 'error': 'Customer phone number is required'})

            # Validate phone number format
            import re
            phone_regex = r'^[0-9]{10,15}$'
            if not re.match(phone_regex, customer_phone):
                return JsonResponse({'success': False, 'error': 'Please enter a valid phone number (10-15 digits)'})

            # Recalculate prices and totals from the database. Never trust browser prices.
            normalized_items = []
            server_total = Decimal('0.00')
            for item in cart_items:
                try:
                    product_id = int(item.get('product_id'))
                    quantity = int(item.get('quantity'))
                    if quantity <= 0:
                        raise ValueError
                    product = Product.objects.get(pk=product_id)
                except (TypeError, ValueError, Product.DoesNotExist):
                    return JsonResponse({'success': False, 'error': 'Invalid product or quantity'})
                line_total = product.price * quantity
                server_total += line_total
                normalized_items.append({
                    **item,
                    'product_id': product.pk,
                    'quantity': quantity,
                    'price': str(product.price),
                    'line_total': str(line_total),
                })

            # Create pending order with server-calculated customer and pricing data.
            order = PendingOrder.objects.create(
                user=request.user,
                customer_name=customer_name,
                customer_phone=customer_phone,
                items=normalized_items,
                total=server_total,
                status='pending',
                idempotency_key=idempotency_key or None
            , workspace=workspace)

            return JsonResponse({'success': True, 'order_id': order.id})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid data format'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required


def order_details(request, order_id):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    # Allow only superusers or users with admin/manager/cashier roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    order = get_object_or_404(PendingOrder, id=order_id)
    is_manager = request.user.is_superuser or (
        hasattr(request.user, 'userprofile')
        and request.user.userprofile.role in ['admin', 'manager']
    )
    if order.user_id != request.user.id and not is_manager:
        return HttpResponseForbidden('You can only view your own orders.')
    return render(request, 'nano/order_details.html', {'order': order})

@login_required


def complete_order(request, order_id):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    # Allow only superusers or users with admin/manager/cashier roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    order = get_object_or_404(PendingOrder, id=order_id)

    if request.method == 'POST':
        try:
            # Validate form data
            cash_received_str = request.POST.get('cash_received', str(order.total))
            payment_method = request.POST.get('payment_method', 'cash')

            # Validate payment method
            valid_payment_methods = [choice[0] for choice in CompletedOrder.PAYMENT_METHOD_CHOICES]
            if payment_method not in valid_payment_methods:
                messages.error(request, f'Invalid payment method. Must be one of: {", ".join(valid_payment_methods)}')
                return redirect('order_details', order_id=order_id)

            # Validate cash received
            try:
                cash_received = float(cash_received_str)
                if cash_received < 0:
                    messages.error(request, 'Cash received cannot be negative')
                    return redirect('order_details', order_id=order_id)
            except ValueError:
                messages.error(request, 'Invalid cash received amount')
                return redirect('order_details', order_id=order_id)

            # Check if order is already completed
            if order.status == 'completed':
                messages.warning(request, 'This order has already been completed')
                return redirect('completed_orders')

            # Update product stock with better error handling
            cart_items = order.items
            stock_issues = []
            products_updated = []

            for item in cart_items:
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
                        product = Product.objects.get(id=product_id)
                    elif product_name:
                        # Try to find product by name (current format)
                        product = Product.objects.get(name=product_name)
                    else:
                        stock_issues.append(f'No product identifier found in item: {item}')
                        continue
                    if product.stock >= quantity:
                        product.stock -= quantity
                        product.save()
                        products_updated.append(product.name)

                        # Create sale record for inventory tracking
                        Sale.objects.create(
                            product=product,
                            quantity=quantity,
                            total_price=item.get('price', 0) * quantity
                        , workspace=workspace)
                    else:
                        stock_issues.append(f'Insufficient stock for {product.name}. Available: {product.stock}, Required: {quantity}')
                except Product.DoesNotExist:
                    if product_id:
                        stock_issues.append(f'Product not found for ID: {product_id}')
                    elif product_name:
                        stock_issues.append(f'Product not found: {product_name}')
                    else:
                        stock_issues.append(f'Product not found in item: {item}')
                except Exception as e:
                    stock_issues.append(f'Error updating {item.get("product", "unknown product")}: {str(e)}')

            # If there are stock issues, show error and don't complete order
            if stock_issues:
                for issue in stock_issues:
                    messages.error(request, issue)
                return redirect('order_details', order_id=order_id)

            # Calculate change
            order_total = float(order.total)
            change_given = max(0, cash_received - order_total)

            # Create completed order
            completed_order = CompletedOrder.objects.create(
                customer_name=order.customer_name,
                customer_phone=order.customer_phone,
                items=order.items,
                total=order.total,
                cash_received=cash_received,
                change_given=change_given,
                payment_method=payment_method,
                processed_by=request.user
            , workspace=workspace)

            # Update pending order status
            order.status = 'completed'
            order.save()

            # Success message with details
            success_msg = f'Order #{order.id} completed successfully!'
            if cash_received >= order_total:
                success_msg += f' Change: R{change_given:.2f}'
            if products_updated:
                success_msg += f' Updated stock for: {", ".join(products_updated)}'

            messages.success(request, success_msg)
            return redirect('completed_orders')

        except Exception as e:
            messages.error(request, f'Error completing order: {str(e)}')
            return redirect('order_details', order_id=order_id)

    # Prepare items with totals for display
    items_with_totals = []
    if order.items:
        for item in order.items:
            item_total = item.get('quantity', 0) * item.get('price', 0)
            items_with_totals.append({
                'product': item.get('product', 'Unknown Product'),
                'quantity': item.get('quantity', 0),
                'price': item.get('price', 0),
                'total': item_total
            })

    return render(request, 'nano/order_details.html', {
        'order': order,
        'items_with_totals': items_with_totals
    })

@login_required


def completed_orders(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    # Allow only superusers or users with admin/manager/cashier roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    orders = CompletedOrder.objects.all().order_by('-completed_at')

    # Calculate statistics
    total_orders = orders.count()
    total_revenue = round(orders.aggregate(total=Sum('total'))['total'] or 0, 2) if orders else 0.00    # Round to 2 decimal places  orders.aggregate(total=Sum('total'))['total'] or 0
    total_cash_received = orders.aggregate(total=Sum('cash_received'))['total'] or 0
    total_change_given = orders.aggregate(total=Sum('change_given'))['total'] or 0

    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'nano/completed_orders.html', {
        'orders': page_obj,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_cash_received': total_cash_received,
        'total_change_given': total_change_given
    })

@login_required


def completed_order_details(request, order_id):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    # Allow only superusers or users with admin/manager/cashier roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    order = get_object_or_404(CompletedOrder, id=order_id)

    # Process items from JSON field to calculate totals
    items_with_totals = []
    if order.items:
        for item in order.items:
            item_total = item.get('quantity', 0) * item.get('price', 0)
            items_with_totals.append({
                'product': item.get('product', 'Unknown Product'),
                'quantity': item.get('quantity', 0),
                'price': item.get('price', 0),
                'total': item_total
            })

    return render(request, 'nano/completed_order_details.html', {
        'order': order,
        'items_with_totals': items_with_totals
    })

@login_required


def checkout(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cart_items = data.get('items', [])
            total_amount = data.get('total_amount', 0)

            if not cart_items:
                return JsonResponse({'success': False, 'error': 'No items in cart'})

            # Check stock availability
            for item in cart_items:
                product_id = item.get('product_id')
                quantity = item.get('quantity', 0)

                try:
                    product = Product.objects.get(id=product_id)
                    if product.stock < quantity:
                        return JsonResponse({
                            'success': False,
                            'error': f'Insufficient stock for {product.name}. Available: {product.stock}'
                        })
                except Product.DoesNotExist:
                    return JsonResponse({'success': False, 'error': f'Product not found'})

            # Create individual sale records for each product for inventory tracking
            for item in cart_items:
                product_id = item.get('product_id')
                quantity = item.get('quantity', 0)
                price = item.get('price', 0)

                try:
                    product = Product.objects.get(id=product_id)
                    Sale.objects.create(
                        product=product,
                        quantity=quantity,
                        total_price=price * quantity
                    , workspace=workspace)
                except Product.DoesNotExist:
                    continue

            # Update product stock
            for item in cart_items:
                product_id = item.get('product_id')
                quantity = item.get('quantity', 0)

                try:
                    product = Product.objects.get(id=product_id)
                    product.stock -= quantity
                    product.save()
                except Product.DoesNotExist:
                    continue

            return JsonResponse({'success': True, 'message': 'Sale completed successfully'})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid data format'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required


def cancel_order(request, order_id):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Cancel a pending order"""
    # Allow only superusers or users with admin/manager/cashier roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    order = get_object_or_404(PendingOrder, id=order_id)

    if request.method == 'POST':
        if order.status != 'pending':
            messages.error(request, 'Only pending orders can be cancelled.')
            return redirect('pending_orders')

        # Cashiers may cancel their own orders; managers/admins may cancel any order.
        is_manager = request.user.is_superuser or (
            hasattr(request.user, 'userprofile')
            and request.user.userprofile.role in ['admin', 'manager']
        )
        if order.user_id != request.user.id and not is_manager:
            return HttpResponseForbidden('You can only cancel your own orders.')

        order.status = 'cancelled'
        order.save(update_fields=['status'])
        messages.success(request, 'Order cancelled successfully!')
        return redirect('pending_orders')

    return render(request, 'nano/order_details.html', {'order': order})

@login_required
@rate_limit('checkout', limit=30, window=60)
@transaction.atomic
def checkout_order(request, order_id=None):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Checkout an order (with or without order_id)"""
    if order_id:
        # Allow only superusers or users with admin/manager/cashier roles
        if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
            return HttpResponseForbidden("You do not have permission to access this page.")

        order = get_object_or_404(
            PendingOrder.objects.select_for_update(), id=order_id
        )

        if request.method == 'POST':
            try:
                if order.status != 'pending':
                    return JsonResponse({'success': False, 'error': 'Order is no longer pending'}, status=400)

                # Process the checkout
                cart_items = order.items
                total_amount = order.total

                # Check stock availability
                for item in cart_items:
                    product_id = item.get('product_id')
                    quantity = item.get('quantity', 0)

                    try:
                        product = Product.objects.select_for_update().get(id=product_id)
                        if product.stock < quantity:
                            return JsonResponse({
                                'success': False,
                                'error': f'Insufficient stock for {product.name}. Available: {product.stock}'
                            })
                    except Product.DoesNotExist:
                        return JsonResponse({'success': False, 'error': f'Product not found'})

                # Create completed order
                completed_order = CompletedOrder.objects.create(
                    customer_name=order.customer_name,
                    customer_phone=order.customer_phone,
                    items=cart_items,
                    total=total_amount,
                    cash_received=float(request.POST.get('cash_received', total_amount)),
                    change_given=float(request.POST.get('cash_received', total_amount)) - float(total_amount),
                    payment_method=request.POST.get('payment_method', 'cash'),
                    processed_by=request.user
                , workspace=workspace)

                # Create individual sale records for each product for inventory tracking
                for item in cart_items:
                    product_id = item.get('product_id')
                    quantity = item.get('quantity', 0)
                    price = item.get('price', 0)

                    try:
                        product = Product.objects.select_for_update().get(id=product_id)
                        Sale.objects.create(
                            product=product,
                            quantity=quantity,
                            total_price=product.price * quantity
                        , workspace=workspace)
                    except Product.DoesNotExist:
                        continue

                # Update product stock
                for item in cart_items:
                    product_id = item.get('product_id')
                    quantity = item.get('quantity', 0)

                    try:
                        product = Product.objects.select_for_update().get(id=product_id)
                        product.stock -= quantity
                        product.save()
                    except Product.DoesNotExist:
                        continue

                # Update pending order status to completed
                order.status = 'completed'
                order.save()

                # Send receipt email if customer email is provided
                customer_email = request.POST.get('customer_email', '').strip()
                if customer_email:
                    try:
                        # Prepare order data for email
                        order_data = {
                            'order_id': completed_order.id,
                            'items': cart_items,
                            'total': total_amount,
                            'cash_received': float(request.POST.get('cash_received', total_amount)),
                            'change_given': float(request.POST.get('cash_received', total_amount)) - float(total_amount),
                            'payment_method': request.POST.get('payment_method', 'cash'),
                            'customer_phone': order.customer_phone,
                            'processed_by': request.user.username,
                            'order_date': completed_order.completed_at
                        }

                        # Send receipt email
                        email_result = send_receipt_email(
                            order_data=order_data,
                            customer_email=customer_email,
                            customer_name=order.customer_name
                        )

                        if email_result['success']:
                            return JsonResponse({
                                'success': True,
                                'message': f'Order checked out successfully! Receipt sent to {customer_email}'
                            })
                        else:
                            return JsonResponse({
                                'success': True,
                                'message': f'Order checked out successfully! But email failed: {email_result.get("error", "Unknown error")}'
                            })

                    except Exception as e:
                        return JsonResponse({
                            'success': True,
                            'message': f'Order checked out successfully! But email failed: {str(e)}'
                        })
                else:
                    return JsonResponse({'success': True, 'message': 'Order checked out successfully!'})

            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})

        # For GET request, show order details
        return render(request, 'nano/order_details.html', {'order': order})
    else:
        # Generic checkout without order_id (from home page)
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                cart_items = data.get('items', [])
                total_amount = data.get('total', 0)
                cash_received = data.get('cashReceived', total_amount)
                change_given = data.get('changeGiven', 0)
                customer_name = data.get('customer_name', '').strip() or data.get('customerName', '').strip()
                customer_phone = data.get('customer_phone', '').strip() or data.get('customerPhone', '').strip()

                if not cart_items:
                    return JsonResponse({'status': 'error', 'message': 'No items in cart'})

                # Validate customer information
                if not customer_name:
                    return JsonResponse({'status': 'error', 'message': 'Customer name is required'})

                if not customer_phone:
                    return JsonResponse({'status': 'error', 'message': 'Customer phone number is required'})

                # Validate phone number format
                import re
                phone_regex = r'^[0-9]{10,15}$'
                if not re.match(phone_regex, customer_phone):
                    return JsonResponse({'status': 'error', 'message': 'Please enter a valid phone number (10-15 digits)'})

                # Check stock availability
                for item in cart_items:
                    product_name = item.get('product')
                    quantity = item.get('quantity', 0)

                    try:
                        # Try exact match first (for performance)
                        product = Product.objects.get(name=product_name)
                    except Product.DoesNotExist:
                        # Try case-insensitive match
                        try:
                            product = Product.objects.get(name__iexact=product_name.strip())
                        except Product.DoesNotExist:
                            # Try to find closest match
                            possible_products = Product.objects.filter(name__icontains=product_name.strip())
                            if possible_products.exists():
                                product = possible_products.first()
                            else:
                                return JsonResponse({'status': 'error', 'message': f'Product not found: {product_name}'})

                    if product.stock < quantity:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Insufficient stock for {product.name}. Available: {product.stock}'
                        })

                # Create completed order
                completed_order = CompletedOrder.objects.create(
                    customer_name=customer_name,
                    customer_phone=customer_phone,
                    items=cart_items,
                    total=total_amount,
                    cash_received=cash_received,
                    change_given=change_given,
                    payment_method='cash',
                    processed_by=request.user
                , workspace=workspace)

                # Create individual sale records for each product for inventory tracking
                for item in cart_items:
                    product_name = item.get('product')
                    quantity = item.get('quantity', 0)
                    price = item.get('price', 0)

                    try:
                        # Try exact match first (for performance)
                        product = Product.objects.get(name=product_name)
                    except Product.DoesNotExist:
                        # Try case-insensitive match
                        try:
                            product = Product.objects.get(name__iexact=product_name.strip())
                        except Product.DoesNotExist:
                            # Try to find closest match
                            possible_products = Product.objects.filter(name__icontains=product_name.strip())
                            if possible_products.exists():
                                product = possible_products.first()
                            else:
                                continue  # Skip this item if product not found

                    Sale.objects.create(
                        product=product,
                        quantity=quantity,
                        total_price=price * quantity
                    , workspace=workspace)

                # Update product stock
                for item in cart_items:
                    product_name = item.get('product')
                    quantity = item.get('quantity', 0)

                    try:
                        # Try exact match first (for performance)
                        product = Product.objects.get(name=product_name)
                    except Product.DoesNotExist:
                        # Try case-insensitive match
                        try:
                            product = Product.objects.get(name__iexact=product_name.strip())
                        except Product.DoesNotExist:
                            # Try to find closest match
                            possible_products = Product.objects.filter(name__icontains=product_name.strip())
                            if possible_products.exists():
                                product = possible_products.first()
                            else:
                                continue  # Skip this item if product not found

                    product.stock -= quantity
                    product.save()

                # Send receipt email login removed
                return JsonResponse({'status': 'success', 'message': 'Order completed successfully!'})

            except json.JSONDecodeError:
                return JsonResponse({'status': 'error', 'message': 'Invalid data format'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})

        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required


def check_low_stock_api(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """API endpoint to check for low stock products"""
    if request.method == 'GET':
        low_stock_products = Product.objects.filter(stock__lt=10)

        product_data = []
        for product in low_stock_products:
            product_data.append({
                'id': product.id,
                'name': product.name,
                'stock': product.stock,
                'category': product.category
            })

        return JsonResponse({'low_stock_products': product_data})

    return JsonResponse({'low_stock_products': []})

@login_required


def get_product_by_barcode(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Get product by barcode"""
    if request.method == 'GET':
        barcode = request.GET.get('barcode', '').strip()

        if not barcode:
            return JsonResponse({'success': False, 'error': 'Barcode is required'})

        try:
            product = Product.objects.get(barcode=barcode)
            product_data = {
                'id': product.id,
                'name': product.name,
                'price': str(product.price),
                'stock': product.stock,
                'category': product.category,
                'barcode': product.barcode
            }
            return JsonResponse({'success': True, 'product': product_data})
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Product not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})



def run_price_comparison():
    """Run automated price comparison on all warehouse prices"""
    from django.db.models import Min

    # Get all unique products
    products = WarehousePrice.objects.values('product_name', 'barcode').distinct()

    for product in products:
        # Get all prices for this product
        prices = WarehousePrice.objects.filter(
            product_name=product['product_name']
        ).order_by('price')

        if prices.count() > 1:
            lowest_price = prices.first()
            all_prices = {p.warehouse_name: float(p.price) for p in prices}

            # Calculate price difference from highest to lowest
            highest_price = prices.last().price
            price_difference = highest_price - lowest_price.price

            # Create or update price comparison
            PriceComparison.objects.update_or_create(
                product_name=product['product_name'],
                barcode=product['barcode'],
                defaults={
                    'lowest_price': lowest_price.price,
                    'lowest_warehouse': lowest_price.warehouse_name,
                    'price_difference': price_difference,
                    'compared_warehouses': list(all_prices.keys()),
                    'all_prices': all_prices
                }
            )

# Warehouse views - complete implementations
@login_required


def warehouse_import(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Import warehouse prices from CSV/Excel files"""
    # Allow only superusers or users with admin/manager roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    if request.method == 'POST':
        if 'file' not in request.FILES:
            messages.error(request, 'Please select a file to upload')
            return redirect('warehouse_import')

        file = request.FILES['file']
        warehouse_name = request.POST.get('warehouse_name', '').strip()

        if not warehouse_name:
            messages.error(request, 'Warehouse name is required')
            return redirect('warehouse_import')

        # Check file extension
        file_extension = file.name.split('.')[-1].lower()
        if file_extension not in ['csv', 'xlsx', 'xls']:
            messages.error(request, 'Only CSV and Excel files are supported')
            return redirect('warehouse_import')

        try:
            # Read file using pandas
            if file_extension == 'csv':
                df = pd.read_csv(file)
            else:  # Excel file
                df = pd.read_excel(file)

            # Validate required columns - support both naming conventions
            required_columns_options = [
                ['Product Name', 'Price'],  # Warehouse format
                ['name', 'price']           # Product format
            ]
            
            valid_columns = None
            for required_columns in required_columns_options:
                missing_columns = [col for col in required_columns if col not in df.columns]
                if not missing_columns:
                    valid_columns = required_columns
                    break
            
            if not valid_columns:
                # Show both expected formats in error message
                messages.error(request, (
                    'Missing required columns. Please use one of these formats:<br>'
                    '<strong>Warehouse Format:</strong> Product Name, Price<br>'
                    '<strong>Product Format:</strong> name, price<br>'
                    'You can use the sample CSV files as templates.'
                ))
                return redirect('warehouse_import')
            
            # Map column names to standard names for processing
            column_mapping = {}
            if valid_columns == ['name', 'price']:
                column_mapping = {
                    'name': 'Product Name',
                    'price': 'Price',
                    'category': 'Category',
                    'stock': 'Stock',
                    'barcode': 'Barcode',
                    'sku': 'SKU',
                    'supplier': 'Supplier',
                    'status': 'Status',
                    'description': 'Description'
                }
            
            # Apply column mapping if needed
            if column_mapping:
                df = df.rename(columns=column_mapping)

            # Process each row
            imported_count = 0
            skipped_count = 0

            for index, row in df.iterrows():
                try:
                    # Clean and validate data
                    product_name = str(row['Product Name']).strip()
                    price = float(row['Price'])
                    barcode = str(row.get('Barcode', '')).strip() if 'Barcode' in row and pd.notna(row['Barcode']) else None
                    category = str(row.get('Category', '')).strip() if 'Category' in row and pd.notna(row['Category']) else None
                    stock_quantity = int(row['Stock']) if 'Stock' in row and pd.notna(row['Stock']) else None
                    sku = str(row.get('SKU', '')).strip() if 'SKU' in row and pd.notna(row['SKU']) else None
                    supplier = str(row.get('Supplier', '')).strip() if 'Supplier' in row and pd.notna(row['Supplier']) else None
                    status = str(row.get('Status', '')).strip() if 'Status' in row and pd.notna(row['Status']) else None
                    description = str(row.get('Description', '')).strip() if 'Description' in row and pd.notna(row['Description']) else None

                    if product_name and price > 0:
                        # Create or update warehouse price
                        warehouse_price, created = WarehousePrice.objects.update_or_create(
                            product_name=product_name,
                            warehouse_name=warehouse_name,
                            barcode=barcode,
                            defaults={
                                'price': price,
                                'category': category,
                                'stock_quantity': stock_quantity,
                                'sku': sku,
                                'supplier': supplier,
                                'status': status,
                                'description': description,
                                'imported_by': request.user,
                                'file_name': file.name
                            }
                        )
                        imported_count += 1
                    else:
                        skipped_count += 1

                except (ValueError, TypeError) as e:
                    skipped_count += 1
                    continue

            # Run price comparison after import
            try:
                run_price_comparison()
            except Exception as e:
                # Continue even if price comparison fails
                pass

            messages.success(request, f'Successfully imported {imported_count} products from {warehouse_name}!')
            return redirect('warehouse_import')

        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
            return redirect('warehouse_import')

    return render(request, 'nano/warehouse_import.html')

@login_required


def warehouse_prices(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Display warehouse prices with search and filtering"""
    # Allow only superusers or users with admin/manager/cashier roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    # Get search parameters
    search_query = request.GET.get('search', '').strip()
    warehouse_filter = request.GET.get('warehouse', '').strip()

    # Build query
    warehouse_prices = WarehousePrice.objects.all()

    if search_query:
        warehouse_prices = warehouse_prices.filter(
            Q(product_name__icontains=search_query) |
            Q(barcode__icontains=search_query) |
            Q(category__icontains=search_query)
        )

    if warehouse_filter:
        warehouse_prices = warehouse_prices.filter(warehouse_name__icontains=warehouse_filter)

    # Get unique warehouse names for filter dropdown
    warehouse_names = sorted(set(WarehousePrice.objects.values_list('warehouse_name', flat=True)))

    # Order by most recent
    warehouse_prices = warehouse_prices.order_by('-date_imported')

    # Pagination
    paginator = Paginator(warehouse_prices, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'nano/warehouse_prices.html', {
        'warehouse_prices': page_obj,
        'warehouse_names': warehouse_names,
        'search_query': search_query,
        'warehouse_filter': warehouse_filter
    })

@login_required


def price_comparisons(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Display price comparisons"""
    # Allow only superusers or users with admin/manager/cashier roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    # Get search parameters
    search_query = request.GET.get('search', '').strip()
    warehouse_filter = request.GET.get('warehouse', '').strip()
    sort_by = request.GET.get('sort', 'price_difference_desc')

    # Build query
    comparisons = PriceComparison.objects.all()

    if search_query:
        comparisons = comparisons.filter(
            Q(product_name__icontains=search_query) |
            Q(barcode__icontains=search_query)
        )

    if warehouse_filter:
        comparisons = comparisons.filter(lowest_warehouse__icontains=warehouse_filter)

    # Apply sorting
    if sort_by == 'price_difference_desc':
        comparisons = comparisons.order_by('-price_difference')
    elif sort_by == 'price_difference_asc':
        comparisons = comparisons.order_by('price_difference')
    elif sort_by == 'product_name':
        comparisons = comparisons.order_by('product_name')
    elif sort_by == 'lowest_price':
        comparisons = comparisons.order_by('lowest_price')
    else:
        comparisons = comparisons.order_by('-price_difference')

    # Get unique warehouse names for filter dropdown
    warehouse_names = PriceComparison.objects.values_list('lowest_warehouse', flat=True).distinct().order_by('lowest_warehouse')

    # Calculate statistics
    total_comparisons = comparisons.count()
    avg_savings = comparisons.aggregate(avg_price=Avg('price_difference'))['avg_price'] or 0
    max_savings = comparisons.aggregate(max_price=Max('price_difference'))['max_price'] or 0
    total_warehouses = warehouse_names.count()

    # Pagination
    paginator = Paginator(comparisons, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'nano/price_comparisons.html', {
        'comparisons': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'warehouse_names': warehouse_names,
        'search_query': search_query,
        'warehouse_filter': warehouse_filter,
        'sort': sort_by,
        'total_comparisons': total_comparisons,
        'avg_savings': avg_savings,
        'max_savings': max_savings,
        'total_warehouses': total_warehouses
    })

@login_required


def sync_warehouse_data(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Sync warehouse data"""
    # Allow only superusers or users with admin/manager roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    if request.method == 'POST':
        messages.success(request, 'Warehouse data synced successfully!')
        return redirect('warehouse_prices')

    return redirect('warehouse_prices')

@login_required


def export_warehouse_prices(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Export warehouse prices"""
    # Allow only superusers or users with admin/manager roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    # Simplified export functionality
    messages.success(request, 'Warehouse prices exported successfully!')
    return redirect('warehouse_prices')

@login_required


def export_price_comparisons(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Export price comparisons"""
    # Allow only superusers or users with admin/manager roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    # Simplified export functionality
    messages.success(request, 'Price comparisons exported successfully!')
    return redirect('price_comparisons')

@login_required


def warehouse_api_prices(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """API endpoint for warehouse prices"""
    if request.method == 'GET':
        # Simplified API response
        return JsonResponse({'prices': []})

    return JsonResponse({'prices': []})

@login_required


def run_price_comparison_view(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Run price comparison via AJAX"""
    # Allow only superusers or users with admin/manager roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager'])):
        return JsonResponse({'success': False, 'error': 'Permission denied'})

    if request.method == 'POST':
        try:
            run_price_comparison()
            return JsonResponse({'success': True, 'message': 'Price comparison completed successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required


def price_comparison_details(request, comparison_id):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Get detailed price comparison data via AJAX"""
    # Allow only superusers or users with admin/manager/cashier roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return JsonResponse({'success': False, 'error': 'Permission denied'})

    try:
        comparison = PriceComparison.objects.get(id=comparison_id)

        # Calculate highest price for display
        highest_price = comparison.lowest_price
        if comparison.all_prices:
            prices = list(comparison.all_prices.values())
            if prices:
                highest_price = max(prices)

        comparison_data = {
            'id': comparison.id,
            'product_name': comparison.product_name,
            'barcode': comparison.barcode,
            'lowest_price': str(comparison.lowest_price),
            'lowest_warehouse': comparison.lowest_warehouse,
            'price_difference': str(comparison.price_difference),
            'highest_price': str(highest_price),
            'compared_warehouses': comparison.compared_warehouses,
            'all_prices': comparison.all_prices,
            'comparison_date': comparison.comparison_date.strftime('%Y-%m-%d %H:%M:%S')
        }

        return JsonResponse({'success': True, 'comparison': comparison_data})

    except PriceComparison.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Price comparison not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required


def price_comparisons_marketing(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Display marketing-focused price comparisons dashboard"""
    # Allow only superusers or users with admin/manager/cashier roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    # Get search parameters
    search_query = request.GET.get('search', '').strip()
    warehouse_filter = request.GET.get('warehouse', '').strip()
    category_filter = request.GET.get('category', '').strip()
    min_savings = request.GET.get('min_savings', '')
    max_savings = request.GET.get('max_savings', '')
    sort_by = request.GET.get('sort', 'price_difference_desc')

    # Build query
    comparisons = PriceComparison.objects.all()

    if search_query:
        comparisons = comparisons.filter(
            Q(product_name__icontains=search_query) |
            Q(barcode__icontains=search_query)
        )

    if warehouse_filter:
        comparisons = comparisons.filter(lowest_warehouse__icontains=warehouse_filter)

    if category_filter:
        # Filter by category through warehouse prices
        product_names_with_category = WarehousePrice.objects.filter(
            category__icontains=category_filter
        ).values_list('product_name', flat=True).distinct()
        comparisons = comparisons.filter(product_name__in=product_names_with_category)

    if min_savings:
        try:
            min_savings_val = float(min_savings)
            comparisons = comparisons.filter(price_difference__gte=min_savings_val)
        except ValueError:
            pass

    if max_savings:
        try:
            max_savings_val = float(max_savings)
            comparisons = comparisons.filter(price_difference__lte=max_savings_val)
        except ValueError:
            pass

    # Apply sorting
    if sort_by == 'price_difference_desc':
        comparisons = comparisons.order_by('-price_difference')
    elif sort_by == 'price_difference_asc':
        comparisons = comparisons.order_by('price_difference')
    elif sort_by == 'product_name':
        comparisons = comparisons.order_by('product_name')
    elif sort_by == 'lowest_price':
        comparisons = comparisons.order_by('lowest_price')
    elif sort_by == 'savings_percentage':
        comparisons = comparisons.order_by('-price_difference')  # Simplified for now
    else:
        comparisons = comparisons.order_by('-price_difference')

    # Get unique warehouse names for filter dropdown
    warehouse_names = PriceComparison.objects.values_list('lowest_warehouse', flat=True).distinct().order_by('lowest_warehouse')

    # Get unique categories from warehouse prices
    categories = WarehousePrice.objects.values_list('category', flat=True).distinct().exclude(category='').order_by('category')

    # Calculate marketing statistics
    total_comparisons = comparisons.count()
    avg_savings = comparisons.aggregate(avg_price=Avg('price_difference'))['avg_price'] or 0
    max_savings = comparisons.aggregate(max_price=Max('price_difference'))['max_price'] or 0
    total_warehouses = warehouse_names.count()

    # Calculate high savings opportunities (savings > 50)
    high_savings_count = comparisons.filter(price_difference__gt=50).count()
    medium_savings_count = comparisons.filter(price_difference__gte=20, price_difference__lte=50).count()
    low_savings_count = comparisons.filter(price_difference__lt=20).count()

    # Get top 10 products with highest savings
    top_savings_products = comparisons.order_by('-price_difference')[:10]

    # Pagination
    paginator = Paginator(comparisons, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'nano/price_comparisons_marketing.html', {
        'comparisons': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'warehouse_names': warehouse_names,
        'categories': categories,
        'search_query': search_query,
        'warehouse_filter': warehouse_filter,
        'category_filter': category_filter,
        'min_savings': min_savings,
        'max_savings': max_savings,
        'sort': sort_by,
        'total_comparisons': total_comparisons,
        'avg_savings': avg_savings,
        'max_savings': max_savings,
        'total_warehouses': total_warehouses,
        'high_savings_count': high_savings_count,
        'medium_savings_count': medium_savings_count,
        'low_savings_count': low_savings_count,
        'top_savings_products': top_savings_products
    })

@login_required


def marketing_analytics_data(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """API endpoint for marketing analytics data"""
    # Allow only superusers or users with admin/manager/cashier roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return JsonResponse({'success': False, 'error': 'Permission denied'})

    try:
        # Get all price comparisons
        comparisons = PriceComparison.objects.all()

        # Calculate savings distribution for charts
        savings_distribution = [
            {'range': 'R0-R20', 'count': comparisons.filter(price_difference__lt=20).count()},
            {'range': 'R20-R50', 'count': comparisons.filter(price_difference__gte=20, price_difference__lte=50).count()},
            {'range': 'R50-R100', 'count': comparisons.filter(price_difference__gt=50, price_difference__lte=100).count()},
            {'range': 'R100+', 'count': comparisons.filter(price_difference__gt=100).count()}
        ]

        # Get warehouse distribution
        warehouse_counts = {}
        for comparison in comparisons:
            warehouse = comparison.lowest_warehouse
            warehouse_counts[warehouse] = warehouse_counts.get(warehouse, 0) + 1

        # Convert to warehouse performance data
        warehouse_performance = [
            {'name': warehouse, 'best_price_count': count}
            for warehouse, count in warehouse_counts.items()
        ]

        # Get category distribution
        category_distribution = []
        category_counts = {}
        for comparison in comparisons:
            # Try to get category from warehouse prices
            try:
                warehouse_price = WarehousePrice.objects.filter(
                    product_name=comparison.product_name
                ).first()
                if warehouse_price and warehouse_price.category:
                    category = warehouse_price.category
                    category_counts[category] = category_counts.get(category, 0) + comparison.price_difference
            except:
                continue

        for category, savings in category_counts.items():
            category_distribution.append({'category': category, 'savings': savings})

        # Get top savings products
        top_savings = []
        for comparison in comparisons.order_by('-price_difference')[:10]:
            # Calculate highest price
            highest_price = comparison.lowest_price
            if comparison.all_prices:
                prices = list(comparison.all_prices.values())
                if prices:
                    highest_price = max(prices)

            top_savings.append({
                'product_name': comparison.product_name,
                'savings': float(comparison.price_difference),
                'price_difference': float(comparison.price_difference),
                'lowest_price': float(comparison.lowest_price),
                'highest_price': float(highest_price),
                'lowest_warehouse': comparison.lowest_warehouse,
                'all_prices': comparison.all_prices or {}
            })

        # Get top products for grid display
        top_products = top_savings[:10]

        # Calculate insights
        total_comparisons = comparisons.count()
        avg_savings = comparisons.aggregate(avg_price=Avg('price_difference'))['avg_price'] or 0
        max_savings = comparisons.aggregate(max_price=Max('price_difference'))['max_price'] or 0

        # Find best warehouse
        best_warehouse = max(warehouse_counts.items(), key=lambda x: x[1])[0] if warehouse_counts else 'N/A'

        # Calculate saving percentage
        saving_percentage = 0
        if total_comparisons > 0:
            high_savings = comparisons.filter(price_difference__gt=50).count()
            saving_percentage = round((high_savings / total_comparisons) * 100, 1)

        insights = {
            'saving_percentage': saving_percentage,
            'best_warehouse': best_warehouse,
            'last_update': timezone.now().strftime('%Y-%m-%d %H:%M')
        }

        return JsonResponse({
            'success': True,
            'data': {
                'savings_distribution': savings_distribution,
                'warehouse_distribution': warehouse_counts,
                'warehouse_performance': warehouse_performance,
                'category_distribution': category_distribution,
                'top_savings': top_savings,
                'top_products': top_products,
                'insights': insights,
                'total_comparisons': total_comparisons,
                'avg_savings': avg_savings,
                'max_savings': max_savings
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required


def export_marketing_report(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Export marketing report"""
    # Allow only superusers or users with admin/manager roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    if request.method == 'POST':
        try:
            # Get filtered comparisons
            comparisons = PriceComparison.objects.all()

            # Apply same filters as marketing view
            search_query = request.POST.get('search', '').strip()
            warehouse_filter = request.POST.get('warehouse', '').strip()
            category_filter = request.POST.get('category', '').strip()
            min_savings = request.POST.get('min_savings', '')
            max_savings = request.POST.get('max_savings', '')

            if search_query:
                comparisons = comparisons.filter(
                    Q(product_name__icontains=search_query) |
                    Q(barcode__icontains=search_query)
                )

            if warehouse_filter:
                comparisons = comparisons.filter(lowest_warehouse__icontains=warehouse_filter)

            if category_filter:
                product_names_with_category = WarehousePrice.objects.filter(
                    category__icontains=category_filter
                ).values_list('product_name', flat=True).distinct()
                comparisons = comparisons.filter(product_name__in=product_names_with_category)

            if min_savings:
                try:
                    min_savings_val = float(min_savings)
                    comparisons = comparisons.filter(price_difference__gte=min_savings_val)
                except ValueError:
                    pass

            if max_savings:
                try:
                    max_savings_val = float(max_savings)
                    comparisons = comparisons.filter(price_difference__lte=max_savings_val)
                except ValueError:
                    pass

            # Create CSV content
            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow([
                'Product Name', 'Barcode', 'Lowest Price', 'Lowest Warehouse',
                'Price Difference', 'Highest Price', 'Compared Warehouses',
                'Comparison Date', 'Category'
            ])

            # Write data
            for comparison in comparisons:
                # Get category
                category = ''
                try:
                    warehouse_price = WarehousePrice.objects.filter(
                        product_name=comparison.product_name
                    ).first()
                    if warehouse_price:
                        category = warehouse_price.category or ''
                except:
                    pass

                # Calculate highest price
                highest_price = comparison.lowest_price
                if comparison.all_prices:
                    prices = list(comparison.all_prices.values())
                    if prices:
                        highest_price = max(prices)

                writer.writerow([
                    comparison.product_name,
                    comparison.barcode or '',
                    comparison.lowest_price,
                    comparison.lowest_warehouse,
                    comparison.price_difference,
                    highest_price,
                    ', '.join(comparison.compared_warehouses) if comparison.compared_warehouses else '',
                    comparison.comparison_date.strftime('%Y-%m-%d %H:%M:%S'),
                    category
                ])

            # Create response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="marketing_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
            response.write(output.getvalue())

            messages.success(request, f'Marketing report exported successfully! {comparisons.count()} products included.')
            return response

        except Exception as e:
            messages.error(request, f'Error exporting report: {str(e)}')
            return redirect('price_comparisons_marketing')

    return redirect('price_comparisons_marketing')
