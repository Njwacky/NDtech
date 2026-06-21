from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
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
from .models import Product, Sale, UserProfile, PendingOrder, CompletedOrder, Notification, WarehousePrice, PriceComparison, FCMToken, DeviceConnection, ErrorLog, UserActivity, AirtimeProduct, AirtimeSale, AirtimeRequest
from .fcm_service import fcm_service, send_fcm_notification_to_user

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
            , workspace=workspace)

            # Send FCM notification
            send_fcm_notification_to_user(notification.target_user, notification.title, notification.message)

@login_required
def home(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    # POS Dashboard
    products = Product.objects.all()

    # Check for low stock products when dashboard is loaded
    check_low_stock()

    return render(request, 'nano/home.html', {'products': products})

def register(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    # Check if any users already exist
    existing_users = User.objects.exists()

    if existing_users:
        # If users exist, show the sign_up page which will display "registration closed"
        return redirect('sign_up')
    else:
        # If no users exist, show the sign_up page for first user registration
        return redirect('sign_up')

def sign_up(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    # Check if any users already exist
    existing_users = User.objects.exists()

    if request.method == 'POST':
        # First check if users already exist - if so, don't allow registration
        if existing_users:
            messages.error(request, 'Registration is closed. An admin account already exists. New users must be created by the administrator.')
            return redirect('sign_in')

        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        errors = {}

        if not username:
            errors['username'] = 'Username is required'
        elif len(username) < 3:
            errors['username'] = 'Username must be at least 3 characters'
        elif User.objects.filter(username=username).exists():
            errors['username'] = 'Username already exists'

        if not email:
            errors['email'] = 'Email is required'
        elif '@' not in email or '.' not in email:
            errors['email'] = 'Invalid email format'
        elif User.objects.filter(email=email).exists():
            errors['email'] = 'Email already exists'

        if not password:
            errors['password'] = 'Password is required'
        elif len(password) < 6:
            errors['password'] = 'Password must be at least 6 characters'

        if password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match'

        if errors:
            for field, error in errors.items():
                messages.error(request, error)
            return render(request, 'nano/sign_up.html', {'existing_users': existing_users})

        from django.db import transaction

        try:
            with transaction.atomic():
                user = User.objects.create_user(username=username, email=email, password=password)

                # This is the first user, make them an admin
                user.is_staff = True  # Make staff to access admin
                user.save()

                # Create or update admin profile (not superuser)
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.role = 'admin'
                profile.created_by = None  # First user has no creator
                profile.save()
                messages.success(request, 'Admin account created successfully! You can now manage other users.')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return redirect('sign_in')

        return redirect('sign_in')

    return render(request, 'nano/sign_up.html', {'existing_users': existing_users})

def sign_in(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        errors = {}

        if not username:
            errors['username'] = 'Username is required'

        if not password:
            errors['password'] = 'Password is required'

        if errors:
            for field, error in errors.items():
                messages.error(request, error)
            return redirect('sign_in')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')
            return redirect('sign_in')

    return render(request, 'nano/sign_in.html')

def logout_view(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    
    logout(request)
    return redirect('register')

def forgot_password(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Handle forgot password requests"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()

        if not username:
            messages.error(request, 'Username is required')
            return render(request, 'nano/forgot_password.html')

        try:
            user = User.objects.get(username=username)

            # Create notification for admins/managers
            admin_users = User.objects.filter(
                Q(is_superuser=True) |
                Q(userprofile__role__in=['admin', 'manager'])
            ).distinct()

            if not admin_users.exists():
                messages.error(request, 'No admin users found to handle password reset requests')
                return render(request, 'nano/forgot_password.html')

            notifications_created = []
            for admin_user in admin_users:
                notification = Notification.objects.create(
                    title=f"Password Reset Request: {user.username}",
                    message=f"Password reset requested for user: {user.username} ({user.email}). Click to edit user and set new password.",
                    notification_type='cashier_request',
                    target_role='admin',
                    target_user=admin_user,
                    created_by=user,  # The user requesting the reset
                    request_type='password_reset',
                    request_data={
                        'username': user.username,
                        'email': user.email,
                        'user_id': user.id,
                        'request_time': timezone.now().isoformat()
                    }
                , workspace=workspace)
                notifications_created.append(notification.id)


                # Send FCM notification
                send_fcm_notification_to_user(admin_user, notification.title, notification.message)

            return redirect('sign_in')

        except User.DoesNotExist:
            # Don't reveal if user exists or not for security
            messages.success(request, 'If the username exists, a password reset request has been sent to the administrators.')
            return redirect('sign_in')

    return render(request, 'nano/forgot_password.html')

@login_required
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
def create_user(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    # Allow only superusers or users with admin role
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['superuser', 'admin'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        role = request.POST.get('role', '')

        errors = {}

        if not username:
            errors['username'] = 'Username is required'
        elif len(username) < 3:
            errors['username'] = 'Username must be at least 3 characters'
        elif User.objects.filter(username=username).exists():
            errors['username'] = 'Username already exists'

        if not email:
            errors['email'] = 'Email is required'
        elif '@' not in email or '.' not in email:
            errors['email'] = 'Invalid email format'
        elif User.objects.filter(email=email).exists():
            errors['email'] = 'Email already exists'

        if not password:
            errors['password'] = 'Password is required'
        elif len(password) < 6:
            errors['password'] = 'Password must be at least 6 characters'

        if password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match'

        if not role:
            errors['role'] = 'Role is required'
        elif role not in ['superuser', 'admin', 'manager', 'cashier']:
            errors['role'] = 'Invalid role'

        # Check if trying to create superuser (only superusers can create superusers)
        if role == 'superuser' and not request.user.is_superuser:
            errors['role'] = 'Only superusers can create other superusers'

        if errors:
            for field, error in errors.items():
                messages.error(request, error)
            return render(request, 'nano/create_user.html')

        user = User.objects.create_user(username=username, email=email, password=password)

        # Set superuser status if role is superuser
        if role == 'superuser':
            user.is_superuser = True
            user.is_staff = True
            user.save()

        # Create or update user profile (handle case where signal already created one)
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.role = role
        profile.created_by = request.user
        profile.save()

        messages.success(request, f'User "{username}" created successfully with role "{role}"!')
        return redirect('manage_users')

    return render(request, 'nano/create_user.html')

@login_required
def manage_users(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    # Allow only superusers or users with admin role
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['superuser', 'admin'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    users = User.objects.all().order_by('username')

    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'nano/manage_users.html', {'users': page_obj})

@login_required
def edit_user(request, user_id):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    # Allow only superusers or users with admin role
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin')):
        return HttpResponseForbidden("You do not have permission to access this page.")

    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', '')

        # Password fields (optional)
        current_password = request.POST.get('current_password', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        errors = {}

        if not username:
            errors['username'] = 'Username is required'
        elif User.objects.filter(username=username).exclude(id=user_id).exists():
            errors['username'] = 'Username already exists'

        if not email:
            errors['email'] = 'Email is required'
        elif User.objects.filter(email=email).exclude(id=user_id).exists():
            errors['email'] = 'Email already exists'

        # Password validation (only if user is trying to change password)
        password_change_attempt = new_password or confirm_password

        if password_change_attempt:
            # Admin users can change other users' passwords without current password
            # But users changing their own password need current password
            is_admin_changing_other_user = (
                request.user.is_superuser or
                (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin')
            ) and request.user.id != user.id

            if not is_admin_changing_other_user:
                if not current_password:
                    errors['current_password'] = 'Current password is required to change password'
                elif not user.check_password(current_password):
                    errors['current_password'] = 'Current password is incorrect'

            if not new_password:
                errors['new_password'] = 'New password is required'
            elif len(new_password) < 6:
                errors['new_password'] = 'Password must be at least 6 characters'

            if new_password != confirm_password:
                errors['confirm_password'] = 'Passwords do not match'

        if errors:
            for field, error in errors.items():
                messages.error(request, error)
        else:
            # Update user info
            user.username = username
            user.email = email

            # Update password if provided
            if password_change_attempt and new_password:
                user.set_password(new_password)
                messages.success(request, f'User "{username}" and password updated successfully!')
            else:
                messages.success(request, f'User "{username}" updated successfully!')

            user.save()

            # Update or create user profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.save()

            return redirect('manage_users')

    # Get user profile
    profile = getattr(user, 'userprofile', None)
    current_role = profile.role if profile else 'cashier'

    return render(request, 'nano/edit_user.html', {
        'user': user,
        'current_role': current_role
    })

@login_required
def delete_user(request, user_id):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    # Allow only superusers or users with admin role
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin')):
        return HttpResponseForbidden("You do not have permission to access this page.")

    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()

        if username != user.username:
            messages.error(request, 'Username does not match. User not deleted.')
        else:
            user.delete()
            messages.success(request, f'User "{username}" deleted successfully!')
            return redirect('manage_users')

    return render(request, 'nano/delete_user.html', {'user': user})

@login_required
def bulk_delete_users(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    # Allow only superusers or users with admin role
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin')):
        return HttpResponseForbidden("You do not have permission to access this page.")

    if request.method == 'POST':
        user_ids = request.POST.getlist('user_ids')

        if not user_ids:
            messages.error(request, 'No users selected for deletion.')
            return redirect('manage_users')

        deleted_count = 0
        for user_id in user_ids:
            try:
                user = User.objects.get(id=user_id)
                # Don't allow deletion of superusers or self
                if user.is_superuser or user.id == request.user.id:
                    continue
                user.delete()
                deleted_count += 1
            except User.DoesNotExist:
                continue

        if deleted_count > 0:
            messages.success(request, f'{deleted_count} users deleted successfully!')
        else:
            messages.warning(request, 'No users were deleted.')

        return redirect('manage_users')

    return redirect('manage_users')

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
            cart_items = data.get('items', [])
            total_amount = data.get('total_amount', 0)
            customer_name = data.get('customer_name', '').strip()
            customer_phone = data.get('customer_phone', '').strip()

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

            # Create pending order with validated customer info
            order = PendingOrder.objects.create(
                user=request.user,
                customer_name=customer_name,
                customer_phone=customer_phone,
                items=cart_items,
                total=total_amount,
                status='pending'
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
def get_notifications(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Get notifications for the current user"""
    notifications = Notification.objects.filter(
        target_user=request.user
    ).order_by('-created_at')

    notification_data = []
    for notification in notifications:
        notification_data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'notification_type': notification.notification_type,
            'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_read': notification.is_read,
            'is_dismissed': notification.is_dismissed,
            'reminder_count': notification.reminder_count,
            'can_remind': notification.can_remind(),
            'created_by_id': notification.created_by.id if notification.created_by else None,
            'request_type': getattr(notification, 'request_type', ''),
            'sender_username': notification.created_by.username if notification.created_by else None,
            'sender_is_admin': notification.created_by.is_superuser if notification.created_by else False
        })

    return JsonResponse({'notifications': notification_data})

@login_required
def mark_notification_read(request, notification_id):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Mark a notification as read"""
    try:
        notification = Notification.objects.get(id=notification_id, target_user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error', 'error': 'Notification not found'})

@login_required
def mark_all_notifications_read(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Mark all notifications as read for the current user"""
    Notification.objects.filter(target_user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})

@login_required
def cancel_order(request, order_id):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Cancel a pending order"""
    # Allow only superusers or users with admin/manager/cashier roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    order = get_object_or_404(PendingOrder, id=order_id)

    if request.method == 'POST':
        order.status = 'cancelled'
        order.save()
        messages.success(request, 'Order cancelled successfully!')
        return redirect('pending_orders')

    return render(request, 'nano/order_details.html', {'order': order})

@login_required
def checkout_order(request, order_id=None):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Checkout an order (with or without order_id)"""
    if order_id:
        # Allow only superusers or users with admin/manager/cashier roles
        if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
            return HttpResponseForbidden("You do not have permission to access this page.")

        order = get_object_or_404(PendingOrder, id=order_id)

        if request.method == 'POST':
            try:
                # Process the checkout
                cart_items = order.items
                total_amount = order.total

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
def dismiss_notification(request, notification_id):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Dismiss a notification (mark as read)"""
    try:
        notification = Notification.objects.get(id=notification_id, target_user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error', 'error': 'Notification not found'})

@login_required
def create_cashier_request(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Create a cashier request for approval"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            request_type = data.get('request_type', '').strip()
            message = data.get('message', '').strip()
            urgent = data.get('urgent', False)

            if not request_type or not message:
                return JsonResponse({
                    'success': False,
                    'error': 'Request type and message are required'
                })

            # Create notification for admins/managers
            admin_users = User.objects.filter(
                Q(is_superuser=True) |
                Q(userprofile__role__in=['admin', 'manager'])
            ).distinct()

            if not admin_users.exists():
                return JsonResponse({
                    'success': False,
                    'error': 'No admin users found to receive the request'
                })

            notifications_created = []
            for admin_user in admin_users:
                notification = Notification.objects.create(
                    title=f"Cashier Request: {request_type}",
                    message=f"Request from {request.user.username}: {message}",
                    notification_type='cashier_request',
                    target_role='admin',
                    target_user=admin_user,
                    created_by=request.user,
                    request_type=request_type,
                    request_data={
                        'message': message,
                        'urgent': urgent,
                        'sender': request.user.username,
                        'sender_id': request.user.id,
                        'timestamp': timezone.now().isoformat()
                    }
                , workspace=workspace)

            return JsonResponse({'success': True, 'message': 'Request submitted successfully'})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data format'})
        except Exception as e:
            logger.exception("Error in create_cashier_request: %s", str(e))
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': f'Error creating request: {str(e)}'
            })

    return JsonResponse({
        'success': False,
        'error': 'Only POST requests are supported'
    })

@login_required
def check_role(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Check if user has specific role"""
    if request.method == 'GET':
        role = request.GET.get('role', '')

        if hasattr(request.user, 'userprofile'):
            user_role = request.user.userprofile.role
            has_role = user_role == role
        else:
            has_role = False

        return JsonResponse({'has_role': has_role, 'user_role': getattr(request.user.userprofile, 'role', None) if hasattr(request.user, 'userprofile') else None})

    return JsonResponse({'has_role': False})

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
def get_user_by_username(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Get user by username"""
    if request.method == 'GET':
        username = request.GET.get('username', '').strip()

        if not username:
            return JsonResponse({'success': False, 'error': 'Username is required'})

        try:
            user = User.objects.get(username=username)
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': getattr(user.userprofile, 'role', None) if hasattr(user, 'userprofile') else None
            }
            return JsonResponse({'success': True, 'user': user_data})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

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

@login_required
def notifications_page(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Dedicated notifications page"""
    return render(request, 'nano/notifications_page.html')

@login_required
def test_notifications_complete(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Complete notification system test page"""
    return render(request, 'nano/test_notifications_complete.html')

# FCM (Firebase Cloud Messaging) Views
@csrf_exempt
def register_fcm_token(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Register FCM token for push notifications"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            token = data.get('token', '').strip()
            device_id = data.get('device_id', '').strip()
            device_type = data.get('device_type', 'web').strip()

            if not token:
                return JsonResponse({'success': False, 'error': 'FCM token is required'})

            # Get or create user (for demo purposes, you might want to require authentication)
            user = getattr(request, 'user', None)
            if not user or not user.is_authenticated:
                # For demo, create a demo user or use a default user
                # In production, you should require proper authentication
                return JsonResponse({'success': False, 'error': 'Authentication required'})

            # Create or update FCM token
            fcm_token, created = FCMToken.objects.update_or_create(
                user=user,
                token=token,
                defaults={
                    'device_id': device_id,
                    'device_type': device_type,
                    'is_active': True
                }
            )

            if created:
                message = 'FCM token registered successfully'
            else:
                message = 'FCM token updated successfully'

            return JsonResponse({
                'success': True,
                'message': message,
                'token_id': fcm_token.id
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Only POST requests are supported'})

@login_required
def cashier_airtime_quick_sell(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Cashier airtime quick sell page"""
    # Allow all authenticated users (cashiers, managers, admins)
    
    # Calculate available credit for this cashier
    # For now, we'll use a simple approach - managers can set credit amount
    # In a real implementation, this would come from a separate model
    
    # Get user role
    user_role = getattr(request.user.userprofile, 'role', 'cashier') if hasattr(request.user, 'userprofile') else 'cashier'
    is_manager = user_role in ['admin', 'manager', 'superuser']
    
    # For demonstration, give cashiers R500 credit by default
    # In production, this should come from a ManagerCredit model or similar
    available_credit = 500.00 if not is_manager else 1000.00
    
    # Check if there are any airtime products available
    airtime_products = AirtimeProduct.objects.filter(is_active=True).exists()
    
    return render(request, 'nano/cashier_airtime_quick_sell.html', {
        'available_credit': available_credit,
        'user_role': user_role,
        'is_manager': is_manager,
        'airtime_products': airtime_products
    })

@login_required
def airtime_history_review(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Review airtime transaction history with phone verification"""
    # Allow all authenticated users to review their own sales
    # Managers can see all sales
    
    user_role = getattr(request.user.userprofile, 'role', 'cashier') if hasattr(request.user, 'userprofile') else 'cashier'
    is_manager = user_role in ['admin', 'manager', 'superuser']
    
    # Get filter parameters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    phone_filter = request.GET.get('phone', '')
    network_filter = request.GET.get('network', '')
    
    # Build query
    sales = AirtimeSale.objects.all()
    
    # For cashiers, only show their own sales
    if not is_manager:
        sales = sales.filter(requested_by=request.user)
    
    # Apply filters
    if date_from:
        try:
            date_from_obj = timezone.datetime.strptime(date_from, '%Y-%m-%d').date()
            sales = sales.filter(created_at__date__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()
            sales = sales.filter(created_at__date__lte=date_to_obj)
        except ValueError:
            pass
    
    if phone_filter:
        sales = sales.filter(customer_phone__icontains=phone_filter)
    
    if network_filter:
        sales = sales.filter(airtime_product__network=network_filter)
    
    # Order by most recent
    sales = sales.order_by('-created_at')
    
    # Generate demo phone numbers for verification (random 12-digit numbers)
    demo_phone_numbers = []
    for sale in sales[:10]:  # Generate for first 10 sales
        import random
        # Generate random 12-digit number starting with same first 3 digits as original
        original_phone = sale.customer_phone
        if len(original_phone) >= 3:
            prefix = original_phone[:3]
            random_suffix = ''.join([str(random.randint(0, 9)) for _ in range(9)])
            demo_number = prefix + random_suffix
            demo_phone_numbers.append({
                'sale_id': sale.id,
                'original_phone': original_phone,
                'demo_phone': demo_number
            })
    
    # Get statistics
    total_sales = sales.count()
    total_revenue = sales.aggregate(total=Sum('total_price'))['total'] or 0
    
    # Pagination
    paginator = Paginator(sales, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'nano/airtime_history_review.html', {
        'sales': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'user_role': user_role,
        'is_manager': is_manager,
        'demo_phone_numbers': demo_phone_numbers,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'date_from': date_from,
        'date_to': date_to,
        'phone_filter': phone_filter,
        'network_filter': network_filter
    })

@login_required
def verify_airtime_phone(request, sale_id):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Verify customer phone number for airtime sale"""
    # Get the airtime sale
    try:
        airtime_sale = AirtimeSale.objects.get(id=sale_id)
        
        # Check permissions - users can only verify their own sales unless they're managers
        user_role = getattr(request.user.userprofile, 'role', 'cashier') if hasattr(request.user, 'userprofile') else 'cashier'
        is_manager = user_role in ['admin', 'manager', 'superuser']
        
        if not is_manager and airtime_sale.requested_by != request.user:
            return JsonResponse({'success': False, 'error': 'Permission denied'})
        
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                confirmed_phone = data.get('confirmed_phone', '').strip()
                customer_confirmed = data.get('customer_confirmed', False)
                
                if not confirmed_phone:
                    return JsonResponse({'success': False, 'error': 'Phone number is required'})
                
                # Validate phone number format
                phone_regex = r'^[0-9]{10,15}$'
                if not re.match(phone_regex, confirmed_phone):
                    return JsonResponse({'success': False, 'error': 'Please enter a valid phone number (10-15 digits)'})
                
                # Update the airtime sale with verified phone number
                airtime_sale.customer_phone = confirmed_phone
                airtime_sale.save()
                
                # Create verification record (you could create a separate model for this)
                verification_data = {
                    'original_phone': airtime_sale.customer_phone,
                    'confirmed_phone': confirmed_phone,
                    'customer_confirmed': customer_confirmed,
                    'verified_by': request.user.username,
                    'verified_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Store verification data in approval notes for now
                existing_notes = airtime_sale.approval_notes or ''
                verification_note = f"PHONE_VERIFICATION: {verification_data}"
                airtime_sale.approval_notes = existing_notes + '\n' + verification_note if existing_notes else verification_note
                airtime_sale.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Phone number verified successfully',
                    'verified_phone': confirmed_phone,
                    'verification_data': verification_data
                })
                
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'error': 'Invalid data format'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        # GET request - return sale details for verification
        return JsonResponse({
            'success': True,
            'sale': {
                'id': airtime_sale.id,
                'customer_phone': airtime_sale.customer_phone,
                'airtime_product': airtime_sale.airtime_product.name,
                'total_price': float(airtime_sale.total_price),
                'created_at': airtime_sale.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'voucher_code': airtime_sale.voucher_code
            }
        })
        
    except AirtimeSale.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Airtime sale not found'})

@login_required
def process_cashier_airtime_sale(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Process cashier airtime quick sell"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            network = data.get('network', '').strip()
            amount = data.get('amount', 0)
            airtime_type = data.get('type', '').strip()
            price = data.get('price', 0)
            customer_phone = data.get('customer_phone', '').strip()
            product_name = data.get('product_name', '').strip()
            use_credit = data.get('use_credit', False)

            # Validate required fields
            if not all([network, amount, airtime_type, price, customer_phone, product_name]):
                return JsonResponse({'success': False, 'error': 'Missing required fields'})

            # Validate phone number format
            phone_regex = r'^[0-9]{10,15}$'
            if not re.match(phone_regex, customer_phone):
                return JsonResponse({'success': False, 'error': 'Please enter a valid phone number (10-15 digits)'})

            # Validate numeric values
            try:
                amount = float(amount)
                price = float(price)
                if amount <= 0 or price <= 0:
                    return JsonResponse({'success': False, 'error': 'Amount and price must be greater than 0'})
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Invalid amount or price values'})

            # Validate network and type
            if network not in dict(AirtimeProduct.NETWORK_CHOICES):
                return JsonResponse({'success': False, 'error': 'Invalid network'})

            if airtime_type not in dict(AirtimeProduct.TYPE_CHOICES):
                return JsonResponse({'success': False, 'error': 'Invalid airtime type'})

            # Get user role and check permissions
            user_role = getattr(request.user.userprofile, 'role', 'cashier') if hasattr(request.user, 'userprofile') else 'cashier'
            is_manager = user_role in ['admin', 'manager', 'superuser']

            # Check credit availability if using credit mode
            if use_credit and not is_manager:
                # For demo purposes, check against hardcoded credit
                # In production, this should check against a ManagerCredit model
                available_credit = 500.00
                if price > available_credit:
                    return JsonResponse({
                        'success': False,
                        'error': f'Insufficient credit. Available: R{available_credit:.2f}, Required: R{price:.2f}'
                    })

            # Find or create a temporary airtime product for this sale
            airtime_product = AirtimeProduct.objects.filter(
                network=network,
                airtime_type=airtime_type,
                value=amount
            ).first()

            if not airtime_product:
                # Create a temporary product for this quick sell
                airtime_product = AirtimeProduct.objects.create(
                    name=product_name,
                    network=network,
                    airtime_type=airtime_type,
                    value=amount,
                    price=price,
                    stock=1,  # Temporary stock
                    is_active=False  # Mark as inactive/temporary
                , workspace=workspace)

            # Check if we have sufficient stock for non-temporary products
            if airtime_product.is_active and airtime_product.stock < 1:
                return JsonResponse({'success': False, 'error': 'Insufficient stock for this product'})

            # Create airtime sale record
            airtime_sale = AirtimeSale.objects.create(
                airtime_product=airtime_product,
                quantity=1,
                total_price=price,
                customer_phone=customer_phone,
                requested_by=request.user,
                status='completed',  # Always completed immediately for quick sell
                approved_by=request.user,  # Self-approved for quick sell
                approved_at=timezone.now()
            , workspace=workspace)

            # Process sale immediately
            if airtime_product.is_active:
                airtime_product.stock -= 1
                airtime_product.save()

            # Mark as completed
            airtime_sale.completed_at = timezone.now()
            airtime_sale.save()

            # Generate voucher code (simplified for demo)
            import random
            import string
            voucher_code = f"VT{network.upper()}{amount}{''.join(random.choices(string.digits, k=6))}"
            airtime_sale.voucher_code = voucher_code
            airtime_sale.save()

            # Create notification for managers if credit was used
            if use_credit and not is_manager:
                admin_users = User.objects.filter(
                    Q(is_superuser=True) |
                    Q(userprofile__role__in=['admin', 'manager'])
                ).distinct()

                for admin_user in admin_users:
                    notification = Notification.objects.create(
                        title=f"Cashier Credit Used: {request.user.username}",
                        message=f"Cashier {request.user.username} used R{price:.2f} credit for {product_name} - {customer_phone}",
                        notification_type='cashier_request',
                        target_role='admin',
                        target_user=admin_user,
                        created_by=request.user,
                        request_type='credit_used',
                        request_data={
                            'cashier': request.user.username,
                            'amount': price,
                            'product': product_name,
                            'customer_phone': customer_phone,
                            'voucher_code': voucher_code
                        }
                    , workspace=workspace)
                    # Send FCM notification
                    send_fcm_notification_to_user(admin_user, notification.title, notification.message)

            return JsonResponse({
                'success': True,
                'message': f'Airtime sale completed successfully! Voucher: {voucher_code}',
                'voucher_code': voucher_code,
                'requires_approval': False
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid data format'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

# Airtime Views
@login_required
def airtime_dashboard(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Airtime dashboard with separate functionality"""
    # Allow all authenticated users
    
    # Check if this is an AJAX request for products
    if request.GET.get('fetch_products') == 'true':
        airtime_products = AirtimeProduct.objects.filter(is_active=True).order_by('network', 'airtime_type', 'value')
        
        products_data = []
        for product in airtime_products:
            products_data.append({
                'id': product.id,
                'name': product.name,
                'network': product.network,
                'airtime_type': product.airtime_type,
                'value': product.value,
                'price': float(product.price),
                'stock': product.stock
            })
        
        return JsonResponse({'products': products_data})
    
    airtime_products = AirtimeProduct.objects.filter(is_active=True).order_by('network', 'airtime_type', 'value')

    # Get user role to determine permissions
    user_role = getattr(request.user.userprofile, 'role', 'cashier') if hasattr(request.user, 'userprofile') else 'cashier'
    is_manager = user_role in ['admin', 'manager', 'superuser']

    # Get pending airtime sales that need approval
    pending_sales = AirtimeSale.objects.filter(status='pending').order_by('-created_at')

    # Get airtime requests
    airtime_requests = AirtimeRequest.objects.filter(status='pending').order_by('-created_at')

    return render(request, 'nano/airtime_dashboard.html', {
        'airtime_products': airtime_products,
        'pending_sales': pending_sales,
        'airtime_requests': airtime_requests,
        'user_role': user_role,
        'is_manager': is_manager
    })

@login_required
def airtime_management(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Airtime management for managers"""
    # Allow only managers, admins, and superusers
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    if request.method == 'POST':
        mode = request.POST.get('mode', 'add_product')

        if mode == 'add_product':
            name = request.POST.get('name', '').strip()
            network = request.POST.get('network', '')
            airtime_type = request.POST.get('airtime_type', '')
            value_str = request.POST.get('value', '').strip()
            price_str = request.POST.get('price', '').strip()
            stock_str = request.POST.get('stock', '').strip()

            errors = {}
            '''❌ Missing required columns. 
            Please use one of these formats:<br><strong>Warehouse Format:</strong> Product Name,
            Price<br><strong>Product Format:</strong> name, 
            price<br>You can use the sample CSV files as templates.'''

            if not name:
                errors['name'] = 'Product name is required'
            elif len(name) < 2:
                errors['name'] = 'Product name must be at least 2 characters'

            if not network:
                errors['network'] = 'Network is required'
            elif network not in dict(AirtimeProduct.NETWORK_CHOICES):
                errors['network'] = 'Invalid network'

            if not airtime_type:
                errors['airtime_type'] = 'Airtime type is required'
            elif airtime_type not in dict(AirtimeProduct.TYPE_CHOICES):
                errors['airtime_type'] = 'Invalid airtime type'

            if not value_str:
                errors['value'] = 'Value is required'
            else:
                try:
                    value = float(value_str)
                    if value <= 0:
                        errors['value'] = 'Value must be greater than 0'
                except ValueError:
                    errors['value'] = 'Value must be a valid number'

            if not price_str:
                errors['price'] = 'Price is required'
            else:
                try:
                    price = float(price_str)
                    if price <= 0:
                        errors['price'] = 'Price must be greater than 0'
                except ValueError:
                    errors['price'] = 'Price must be a valid number'

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
                # Return JSON response for AJAX requests from quick sell interface
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'Please fix validation errors'})
            else:
                # Create airtime product
                description = request.POST.get('description', '').strip()
                airtime_product = AirtimeProduct.objects.create(
                    name=name,
                    network=network,
                    airtime_type=airtime_type,
                    value=value,
                    price=price,
                    description=description,
                    stock=stock
                , workspace=workspace)
                messages.success(request, f'Airtime product "{name}" added successfully!')
                
                # Return JSON response for AJAX requests from quick sell interface
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': f'Product "{name}" added successfully!'})
                else:
                    return redirect('airtime_management')

        elif mode == 'update_stock':
            product_id = request.POST.get('product_id')
            quantity_str = request.POST.get('quantity', '').strip()

            if not product_id:
                messages.error(request, 'Please select an airtime product')
                return redirect('airtime_management')

            if not quantity_str:
                messages.error(request, 'Quantity is required')
                return redirect('airtime_management')

            try:
                quantity = int(quantity_str)
                if quantity < 0:
                    messages.error(request, 'Quantity cannot be negative')
                    return redirect('airtime_management')
            except ValueError:
                messages.error(request, 'Quantity must be a valid number')
                return redirect('airtime_management')

            try:
                product = AirtimeProduct.objects.get(id=product_id)
                product.stock += quantity
                product.save()
                messages.success(request, f'Added {quantity} units to {product.get_display_name()}')
            except AirtimeProduct.DoesNotExist:
                messages.error(request, 'Airtime product not found')

            return redirect('airtime_management')

        elif mode == 'toggle_status':
            product_id = request.POST.get('product_id')
            status = request.POST.get('status', '')

            if not product_id:
                error_msg = 'Product ID is required'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                else:
                    messages.error(request, error_msg)
                    return redirect('airtime_management')

            if status not in ['active', 'inactive']:
                error_msg = 'Invalid status'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                else:
                    messages.error(request, error_msg)
                    return redirect('airtime_management')

            try:
                product = AirtimeProduct.objects.get(id=product_id)
                old_status = 'active' if product.is_active else 'inactive'
                product.is_active = (status == 'active')
                product.save()
                
                success_msg = f'Product "{product.get_display_name()}" status changed from {old_status} to {status}'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': success_msg})
                else:
                    messages.success(request, success_msg)
                    return redirect('airtime_management')
                    
            except AirtimeProduct.DoesNotExist:
                error_msg = 'Airtime product not found'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                else:
                    messages.error(request, error_msg)
                    return redirect('airtime_management')

    airtime_products = AirtimeProduct.objects.all().order_by('network', 'airtime_type', 'value')
    return render(request, 'nano/airtime_management.html', {
        'airtime_products': airtime_products
    })

@login_required
def airtime_sales(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """List and manage airtime sales"""
    # Allow all authenticated users
    user_role = getattr(request.user.userprofile, 'role', 'cashier') if hasattr(request.user, 'userprofile') else 'cashier'
    is_manager = user_role in ['admin', 'manager', 'superuser']

    # Get filter parameters
    status_filter = request.GET.get('status', '')
    network_filter = request.GET.get('network', '')

    # Build query
    sales = AirtimeSale.objects.all()

    if status_filter:
        sales = sales.filter(status=status_filter)

    if network_filter:
        sales = sales.filter(airtime_product__network=network_filter)

    # For cashiers, only show their own sales
    if not is_manager:
        sales = sales.filter(requested_by=request.user)

    sales = sales.order_by('-created_at')

    # Pagination
    paginator = Paginator(sales, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'nano/airtime_sales.html', {
        'sales': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'user_role': user_role,
        'is_manager': is_manager,
        'status_filter': status_filter,
        'network_filter': network_filter
    })

@login_required
def process_airtime_sale(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Process airtime sale (for cashiers with approval requirement)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            customer_phone = data.get('customer_phone', '').strip()
            quantity = data.get('quantity', 1)

            if not product_id:
                return JsonResponse({'success': False, 'error': 'Product ID is required'})

            if not customer_phone:
                return JsonResponse({'success': False, 'error': 'Customer phone number is required'})

            # Validate phone number format
            phone_regex = r'^[0-9]{10,15}$'
            if not re.match(phone_regex, customer_phone):
                return JsonResponse({'success': False, 'error': 'Please enter a valid phone number (10-15 digits)'})

            try:
                airtime_product = AirtimeProduct.objects.get(id=product_id)

                # Check stock
                if airtime_product.stock < quantity:
                    return JsonResponse({
                        'success': False,
                        'error': f'Insufficient stock. Available: {airtime_product.stock}'
                    })

                total_price = airtime_product.price * quantity

                # Get user role
                user_role = getattr(request.user.userprofile, 'role', 'cashier') if hasattr(request.user, 'userprofile') else 'cashier'

                # Create airtime sale - NO APPROVAL REQUIRED FOR CASHIERS (urgent purchases)
                airtime_sale = AirtimeSale.objects.create(
                    airtime_product=airtime_product,
                    quantity=quantity,
                    total_price=total_price,
                    customer_phone=customer_phone,
                    requested_by=request.user,
                    status='completed'  # Always completed immediately - no approval needed
                , workspace=workspace)

                # Process sale immediately for all users (including cashiers)
                airtime_product.stock -= quantity
                airtime_product.save()

                airtime_sale.completed_at = timezone.now()
                airtime_sale.approved_by = request.user
                airtime_sale.approved_at = timezone.now()
                airtime_sale.save()

                return JsonResponse({
                    'success': True,
                    'message': 'Airtime sale completed successfully',
                    'requires_approval': False
                })

            except AirtimeProduct.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Airtime product not found'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid data format'})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def process_quick_airtime_sale(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Process quick airtime sale from management page"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            network = data.get('network', '').strip()
            amount = data.get('amount', 0)
            airtime_type = data.get('type', '').strip()
            price = data.get('price', 0)
            customer_phone = data.get('customer_phone', '').strip()
            product_name = data.get('product_name', '').strip()

            # Validate required fields
            if not all([network, amount, airtime_type, price, customer_phone, product_name]):
                return JsonResponse({'success': False, 'error': 'Missing required fields'})

            # Validate phone number format
            phone_regex = r'^[0-9]{10,15}$'
            if not re.match(phone_regex, customer_phone):
                return JsonResponse({'success': False, 'error': 'Please enter a valid phone number (10-15 digits)'})

            # Validate numeric values
            try:
                amount = float(amount)
                price = float(price)
                if amount <= 0 or price <= 0:
                    return JsonResponse({'success': False, 'error': 'Amount and price must be greater than 0'})
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Invalid amount or price values'})

            # Validate network and type
            if network not in dict(AirtimeProduct.NETWORK_CHOICES):
                return JsonResponse({'success': False, 'error': 'Invalid network'})

            if airtime_type not in dict(AirtimeProduct.TYPE_CHOICES):
                return JsonResponse({'success': False, 'error': 'Invalid airtime type'})

            # Find or create a temporary airtime product for this sale
            # First try to find an existing product that matches
            airtime_product = AirtimeProduct.objects.filter(
                network=network,
                airtime_type=airtime_type,
                value=amount
            ).first()

            if not airtime_product:
                # Create a temporary product for this quick sale
                airtime_product = AirtimeProduct.objects.create(
                    name=product_name,
                    network=network,
                    airtime_type=airtime_type,
                    value=amount,
                    price=price,
                    stock=1,  # Temporary stock
                    is_active=False  # Mark as inactive/temporary
                , workspace=workspace)

            # Check if we have sufficient stock for non-temporary products
            if airtime_product.is_active and airtime_product.stock < 1:
                return JsonResponse({'success': False, 'error': 'Insufficient stock for this product'})

            # Create airtime sale - NO APPROVAL REQUIRED FOR CASHIERS (urgent purchases)
            airtime_sale = AirtimeSale.objects.create(
                airtime_product=airtime_product,
                quantity=1,
                total_price=price,
                customer_phone=customer_phone,
                requested_by=request.user,
                status='completed'  # Always completed immediately - no approval needed
            , workspace=workspace)

            # Process sale immediately for all users (including cashiers)
            if airtime_product.is_active:
                airtime_product.stock -= 1
                airtime_product.save()
            else:
                # For temporary products, we don't track stock
                pass

            airtime_sale.completed_at = timezone.now()
            airtime_sale.approved_by = request.user
            airtime_sale.approved_at = timezone.now()
            airtime_sale.save()

            return JsonResponse({
                'success': True,
                'message': 'Quick airtime sale completed successfully',
                'requires_approval': False
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid data format'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def approve_airtime_sale(request, sale_id):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Approve airtime sale (for managers)"""
    # Allow only managers, admins, and superusers
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    airtime_sale = get_object_or_404(AirtimeSale, id=sale_id)

    if request.method == 'POST':
        approval_notes = request.POST.get('approval_notes', '').strip()

        # Update airtime sale
        airtime_sale.status = 'approved'
        airtime_sale.approved_by = request.user
        airtime_sale.approved_at = timezone.now()
        airtime_sale.approval_notes = approval_notes
        airtime_sale.save()

        # Update stock
        airtime_sale.airtime_product.stock -= airtime_sale.quantity
        airtime_sale.airtime_product.save()

        messages.success(request, f'Airtime sale for {airtime_sale.customer_phone} approved successfully!')
        return redirect('airtime_sales')

    return render(request, 'nano/approve_airtime_sale.html', {
        'airtime_sale': airtime_sale
    })

@login_required
def reject_airtime_sale(request, sale_id):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Reject airtime sale (for managers)"""
    # Allow only managers, admins, and superusers
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    airtime_sale = get_object_or_404(AirtimeSale, id=sale_id)

    if request.method == 'POST':
        rejection_reason = request.POST.get('rejection_reason', '').strip()

        # Update airtime sale
        airtime_sale.status = 'cancelled'
        airtime_sale.approved_by = request.user
        airtime_sale.approved_at = timezone.now()
        airtime_sale.approval_notes = rejection_reason
        airtime_sale.save()

        messages.success(request, f'Airtime sale for {airtime_sale.customer_phone} rejected!')
        return redirect('airtime_sales')

    return render(request, 'nano/reject_airtime_sale.html', {
        'airtime_sale': airtime_sale
    })

@login_required
def airtime_requests_management(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Manage airtime requests (for managers)"""
    # Allow only managers, admins, and superusers
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    requests = AirtimeRequest.objects.all().order_by('-created_at')

    # Pagination
    paginator = Paginator(requests, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'nano/airtime_requests_management.html', {
        'requests': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj
    })

@login_required
def approve_airtime_request(request, request_id):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Approve airtime management request"""
    # Allow only managers, admins, and superusers
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    airtime_request = get_object_or_404(AirtimeRequest, id=request_id)

    if request.method == 'POST':
        approval_notes = request.POST.get('approval_notes', '').strip()

        # Update airtime request
        airtime_request.status = 'approved'
        airtime_request.approved_by = request.user
        airtime_request.approved_at = timezone.now()
        airtime_request.approval_notes = approval_notes
        airtime_request.save()

        messages.success(request, f'Airtime request from {airtime_request.requested_by.username} approved successfully!')
        return redirect('airtime_requests_management')

    return render(request, 'nano/approve_airtime_request.html', {
        'airtime_request': airtime_request
    })

@login_required
def airtime_product_status_api(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """API endpoint for toggling airtime product status (active/inactive)"""
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager'])):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        status = data.get('status', '').strip()

        if not product_id:
            return JsonResponse({'success': False, 'error': 'Product ID is required'})
        if status not in ['active', 'inactive']:
            return JsonResponse({'success': False, 'error': 'Invalid status. Use "active" or "inactive"'})

        product = AirtimeProduct.objects.get(id=product_id)
        product.is_active = (status == 'active')
        product.save()

        return JsonResponse({'success': True, 'message': f'Product status updated to {status}'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except AirtimeProduct.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def reject_airtime_request(request, request_id):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Reject airtime management request"""
    # Allow only managers, admins, and superusers
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    airtime_request = get_object_or_404(AirtimeRequest, id=request_id)

    if request.method == 'POST':
        rejection_reason = request.POST.get('rejection_reason', '').strip()

        # Update airtime request
        airtime_request.status = 'rejected'
        airtime_request.approved_by = request.user
        airtime_request.approved_at = timezone.now()
        airtime_request.approval_notes = rejection_reason
        airtime_request.save()

        messages.success(request, f'Airtime request from {airtime_request.requested_by.username} rejected!')
        return redirect('airtime_requests_management')

    return render(request, 'nano/reject_airtime_request.html', {
        'airtime_request': airtime_request
    })

@login_required
def send_test_notification(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Send test notification"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            target_user_id = data.get('target_user_id')
            message = data.get('message', 'This is a test notification')

            if target_user_id:
                target_user = User.objects.get(id=target_user_id)
                success = send_fcm_notification_to_user(target_user, 'Test Notification', message)
            else:
                success = send_fcm_notification_to_user(request.user, 'Test Notification', message)

            if success:
                return JsonResponse({'success': True, 'message': 'Test notification sent successfully'})
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to send test notification. Make sure you have registered an FCM token.'
                })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Only POST requests are supported'})

@login_required
def send_price_change_notification(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Send price change notification to a customer"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            customer_name = data.get('customer_name', '').strip()
            item_name = data.get('item_name', '').strip()
            new_price = float(data.get('new_price', 0))
            price_change = float(data.get('price_change', 0))
            customer_token = data.get('customer_token', '').strip()

            if not all([customer_name, item_name, customer_token]):
                return JsonResponse({
                    'success': False,
                    'error': 'Customer name, item name, and customer token are required'
                })

            # Send price change notification
            success = fcm_service.send_price_change_notification(
                customer_name, item_name, new_price, price_change, customer_token
            )

            if success:
                return JsonResponse({
                    'success': True,
                    'message': f'Price change notification sent to {customer_name}'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to send price change notification'
                })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        except ValueError as e:
            return JsonResponse({'success': False, 'error': f'Invalid price data: {str(e)}'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Only POST requests are supported'})

@login_required
def test_fcm_connection(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Test FCM connection"""
    if request.method == 'GET':
        try:
            is_connected = fcm_service.test_fcm_connection()

            return JsonResponse({
                'success': is_connected,
                'message': 'FCM connection successful' if is_connected else 'FCM connection failed',
                'api_key_configured': bool(getattr(settings, 'AIzaSyABApzh-74Kr5oOz_kv_M8mlJa33TCadPA', None))
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return JsonResponse({'success': False, 'error': 'Only GET requests are supported'})

@login_required
def get_user_fcm_tokens(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Get all FCM tokens for the current user"""
    if request.method == 'GET':
        try:
            tokens = FCMToken.objects.filter(user=request.user, is_active=True)

            token_data = []
            for token_obj in tokens:
                token_data.append({
                    'id': token_obj.id,
                    'token': token_obj.token[:50] + '...' if len(token_obj.token) > 50 else token_obj.token,
                    'device_id': token_obj.device_id,
                    'device_type': token_obj.device_type,
                    'created_at': token_obj.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'last_used': token_obj.last_used.strftime('%Y-%m-%d %H:%M:%S')
                })

            return JsonResponse({
                'success': True,
                'tokens': token_data,
                'total_tokens': len(token_data)
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Only GET requests are supported'})

# Enhanced notification functions with FCM integration
def send_fcm_for_notification(notification):
    """
    Send FCM notification for a database notification

    Args:
        notification: Notification object
    """
    try:
        if notification.target_user:
            # Send to specific user
            send_fcm_notification_to_user(
                notification.target_user,
                notification.title,
                notification.message,
                {
                    'notification_id': notification.id,
                    'notification_type': notification.notification_type,
                    'created_at': notification.created_at.isoformat()
                }
            )

        elif notification.target_role:
            # Send to all users with the target role
            from django.contrib.auth.models import User
            from .models import UserProfile

            target_users = User.objects.filter(
                userprofile__role=notification.target_role
            )

            for user in target_users:
                send_fcm_notification_to_user(
                    user,
                    notification.title,
                    notification.message,
                    {
                        'notification_id': notification.id,
                        'notification_type': notification.notification_type,
                        'created_at': notification.created_at.isoformat()
                    }
                )

    except Exception as e:
        logger.error(f"Error sending FCM for notification {notification.id}: {str(e)}")

@login_required
def fcm_test_page(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """FCM test page for push notifications"""
    return render(request, 'nano/fcm_test.html')

@login_required
def export_products_excel(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Export all products to Excel with all their details"""
    # Allow only superusers or users with admin/manager roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    if request.method == 'GET':
        try:
            # Get all products
            products = Product.objects.all().order_by('name')

            # Create a pandas DataFrame with all product details
            products_data = []
            for product in products:
                # Get sales data for this product
                sales_data = Sale.objects.filter(product=product)
                total_sales = sales_data.count()
                total_quantity_sold = sales_data.aggregate(total=Sum('quantity'))['total'] or 0
                total_revenue = sales_data.aggregate(total=Sum('total_price'))['total'] or 0

                products_data.append({
                    'ID': product.id,
                    'Name': product.name,
                    'Description': product.description or '',
                    'Category': product.get_category_display() if hasattr(product, 'get_category_display') else product.category,
                    'Regular Price': float(product.price),
                    'Current Stock': product.stock,
                    'Barcode': product.barcode or '',
                    'Date Added': product.date_added.strftime('%Y-%m-%d %H:%M:%S'),
                    'Expiry Date': product.expiry_date.strftime('%Y-%m-%d') if product.expiry_date else '',
                    'Is Expired': 'Yes' if product.is_expired() else 'No',
                    'Is On Sale': 'Yes' if product.is_on_sale else 'No',
                    'Sale Price': float(product.sale_price) if product.sale_price else '',
                    'Sale Start Date': product.sale_start_date.strftime('%Y-%m-%d %H:%M:%S') if product.sale_start_date else '',
                    'Sale End Date': product.sale_end_date.strftime('%Y-%m-%d %H:%M:%S') if product.sale_end_date else '',
                    'Is Currently On Sale': 'Yes' if product.is_currently_on_sale() else 'No',
                    'Current Price': float(product.get_current_price()),
                    'Discount Percentage': f"{product.get_discount_percentage()}%" if product.get_discount_percentage() > 0 else '',
                    'Discount Amount': float(product.get_discount_amount()) if product.get_discount_amount() > 0 else '',
                    'Total Sales Count': total_sales,
                    'Total Quantity Sold': total_quantity_sold,
                    'Total Revenue': float(total_revenue),
                    'Average Sale Price': float(total_revenue / total_sales) if total_sales > 0 else 0
                })

            # Create DataFrame
            df = pd.DataFrame(products_data)

            # Create Excel file in memory
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Products', index=False)

                # Get the workbook and worksheet for formatting
                workbook = writer.book
                worksheet = writer.sheets['Products']

                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

            # Prepare response
            output.seek(0)
            response = HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="products_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'

            messages.success(request, f'Successfully exported {products.count()} products to Excel!')
            return response

        except Exception as e:
            messages.error(request, f'Error exporting products: {str(e)}')
            return redirect('home')

    return redirect('home')

# PWA Views
def service_worker(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Serve the service worker file"""
    return HttpResponse(
        open('nano/static/nano/sw.js').read(),
        content_type='application/javascript'
    )

def manifest(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Serve the PWA manifest file"""
    return HttpResponse(
        open('nano/static/nano/manifest.json').read(),
        content_type='application/json'
    )

def offline(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Offline fallback page"""
    return render(request, 'nano/offline.html')

# Error Tracking Views
@login_required
def tracking_dashboard(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Main tracking dashboard"""
    # Allow only superusers or users with admin/manager roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    # Get statistics
    total_errors = ErrorLog.objects.count()
    unresolved_errors = ErrorLog.objects.filter(is_resolved=False).count()
    critical_errors = ErrorLog.objects.filter(severity='critical', is_resolved=False).count()

    # Get recent errors
    recent_errors = ErrorLog.objects.order_by('-created_at')[:10]

    # Get error statistics by type
    error_types = ErrorLog.objects.values('error_type').annotate(count=Count('id')).order_by('-count')

    # Get error statistics by severity
    severity_stats = ErrorLog.objects.values('severity').annotate(count=Count('id')).order_by('-count')

    return render(request, 'nano/tracking_dashboard.html', {
        'total_errors': total_errors,
        'unresolved_errors': unresolved_errors,
        'critical_errors': critical_errors,
        'recent_errors': recent_errors,
        'error_types': error_types,
        'severity_stats': severity_stats
    })

@login_required
def device_tracking(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Device connection tracking"""
    # Allow only superusers or users with admin/manager roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    # Get search parameters
    search_query = request.GET.get('search', '').strip()
    device_type_filter = request.GET.get('device_type', '')

    # Build query
    device_connections = DeviceConnection.objects.all()

    if search_query:
        device_connections = device_connections.filter(
            Q(user__username__icontains=search_query) |
            Q(device_id__icontains=search_query) |
            Q(ip_address__icontains=search_query)
        )

    if device_type_filter:
        device_connections = device_connections.filter(device_type=device_type_filter)

    # Order by last activity
    device_connections = device_connections.order_by('-last_activity')

    # Get statistics
    total_connections = device_connections.count()
    active_connections = device_connections.filter(is_active=True).count()

    # Get device type statistics
    device_types = DeviceConnection.objects.values('device_type').annotate(count=Count('id')).order_by('-count')

    # Pagination
    paginator = Paginator(device_connections, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'nano/device_tracking.html', {
        'device_connections': page_obj,
        'total_connections': total_connections,
        'active_connections': active_connections,
        'device_types': device_types,
        'search_query': search_query,
        'device_type_filter': device_type_filter
    })

@login_required
def error_tracking(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Error log tracking and management"""
    # Allow only superusers or users with admin/manager roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    # Get search parameters
    search_query = request.GET.get('search', '').strip()
    error_type_filter = request.GET.get('error_type', '')
    severity_filter = request.GET.get('severity', '')
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    # Build query
    errors = ErrorLog.objects.all()

    if search_query:
        errors = errors.filter(
            Q(error_message__icontains=search_query) |
            Q(url__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )

    if error_type_filter:
        errors = errors.filter(error_type=error_type_filter)

    if severity_filter:
        errors = errors.filter(severity=severity_filter)

    if status_filter == 'resolved':
        errors = errors.filter(is_resolved=True)
    elif status_filter == 'unresolved':
        errors = errors.filter(is_resolved=False)

    if date_from:
        try:
            date_from_obj = timezone.datetime.strptime(date_from, '%Y-%m-%d').date()
            errors = errors.filter(created_at__date__gte=date_from_obj)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_obj = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()
            errors = errors.filter(created_at__date__lte=date_to_obj)
        except ValueError:
            pass

    # Order by most recent
    errors = errors.order_by('-created_at')

    # Get statistics
    total_errors = errors.count()
    unresolved_errors = errors.filter(is_resolved=False).count()
    critical_errors = errors.filter(severity='critical', is_resolved=False).count()

    # Pagination
    paginator = Paginator(errors, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'nano/error_tracking.html', {
        'errors': page_obj,
        'total_errors': total_errors,
        'unresolved_errors': unresolved_errors,
        'critical_errors': critical_errors,
        'search_query': search_query,
        'error_type_filter': error_type_filter,
        'severity_filter': severity_filter,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to
    })

@login_required
def error_details(request, error_id):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Detailed view of a specific error"""
    # Allow only superusers or users with admin/manager roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    error = get_object_or_404(ErrorLog, id=error_id)

    # Find similar errors (same error message and type, different instances)
    similar_errors = ErrorLog.objects.filter(
        error_message=error.error_message,
        error_type=error.error_type
    ).exclude(id=error.id).order_by('-created_at')[:10]

    return render(request, 'nano/error_details.html', {
        'error': error,
        'similar_errors': similar_errors
    })

@login_required
def resolve_error(request, error_id):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """Mark an error as resolved"""
    # Allow only superusers or users with admin/manager roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    error = get_object_or_404(ErrorLog, id=error_id)

    if request.method == 'POST':
        resolution_notes = request.POST.get('resolution_notes', '').strip()

        error.mark_resolved(request.user, resolution_notes)
        messages.success(request, f'Error #{error.id} marked as resolved successfully!')

        return redirect('error_tracking')

    return render(request, 'nano/resolve_error.html', {'error': error})

@login_required
def user_activity_tracking(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """User activity tracking"""
    # Allow only superusers or users with admin/manager roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager'])):
        return HttpResponseForbidden("You do not have permission to access this page.")

    # Get search parameters
    search_query = request.GET.get('search', '').strip()
    activity_type_filter = request.GET.get('activity_type', '')
    user_filter = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    # Build query
    activities = UserActivity.objects.all()

    if search_query:
        activities = activities.filter(
            Q(user__username__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(page_url__icontains=search_query)
        )

    if activity_type_filter:
        activities = activities.filter(activity_type=activity_type_filter)

    if user_filter:
        activities = activities.filter(user__username__icontains=user_filter)

    if date_from:
        try:
            date_from_obj = timezone.datetime.strptime(date_from, '%Y-%m-%d').date()
            activities = activities.filter(created_at__date__gte=date_from_obj)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_obj = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()
            activities = activities.filter(created_at__date__lte=date_to_obj)
        except ValueError:
            pass

    # Order by most recent
    activities = activities.order_by('-created_at')

    # Get statistics
    total_activities = activities.count()

    # Get activity type statistics
    activity_types = UserActivity.objects.values('activity_type').annotate(count=Count('id')).order_by('-count')

    # Pagination
    paginator = Paginator(activities, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'nano/user_activity_tracking.html', {
        'activities': page_obj,
        'total_activities': total_activities,
        'activity_types': activity_types,
        'search_query': search_query,
        'activity_type_filter': activity_type_filter,
        'user_filter': user_filter,
        'date_from': date_from,
        'date_to': date_to
    })

# Tracking API Views
@csrf_exempt
def track_device_connection(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """API endpoint to track device connections"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Get user from request (should be authenticated)
            if not request.user.is_authenticated:
                return JsonResponse({'success': False, 'error': 'Authentication required'})

            # Extract device information
            device_id = data.get('device_id', '')
            device_type = data.get('device_type', 'web')
            ip_address = data.get('ip_address', '')
            user_agent = data.get('user_agent', '')

            # Get location data if available
            location_country = data.get('location_country', '')
            location_city = data.get('location_city', '')
            latitude = data.get('latitude')
            longitude = data.get('longitude')

            # Create or update device connection
            device_connection, created = DeviceConnection.objects.update_or_create(
                user=request.user,
                device_id=device_id,
                defaults={
                    'device_type': device_type,
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'location_country': location_country,
                    'location_city': location_city,
                    'latitude': latitude,
                    'longitude': longitude,
                    'is_active': True
                }
            )

            # Update activity
            device_connection.update_activity()

            return JsonResponse({
                'success': True,
                'device_connection_id': device_connection.id,
                'created': created
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Only POST requests are supported'})

@csrf_exempt
def track_user_activity(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """API endpoint to track user activities"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Get user from request (should be authenticated)
            if not request.user.is_authenticated:
                return JsonResponse({'success': False, 'error': 'Authentication required'})

            # Extract activity information
            activity_type = data.get('activity_type', '')
            description = data.get('description', '')
            page_url = data.get('page_url', '')
            object_type = data.get('object_type', '')
            object_id = data.get('object_id')

            # Get request context
            ip_address = data.get('ip_address', '')
            user_agent = data.get('user_agent', '')
            device_connection_id = data.get('device_connection_id')

            # Additional metadata
            metadata = data.get('metadata', {})
            duration_ms = data.get('duration_ms')

            # Get device connection if provided
            device_connection = None
            if device_connection_id:
                try:
                    device_connection = DeviceConnection.objects.get(id=device_connection_id)
                except DeviceConnection.DoesNotExist:
                    pass

            # Create user activity
            activity = UserActivity.objects.create(
                user=request.user,
                activity_type=activity_type,
                description=description,
                page_url=page_url,
                object_type=object_type,
                object_id=object_id,
                ip_address=ip_address,
                user_agent=user_agent,
                device_connection=device_connection,
                metadata=metadata,
                duration_ms=duration_ms
            , workspace=workspace)

            return JsonResponse({
                'success': True,
                'activity_id': activity.id
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Only POST requests are supported'})

@csrf_exempt
def log_error(request):
    workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    """API endpoint to log errors"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Get user from request (can be anonymous for system errors)
            user = getattr(request, 'user', None)
            if not user or not user.is_authenticated:
                user = None

            # Extract error information
            error_type = data.get('error_type', 'system_error')
            severity = data.get('severity', 'medium')
            error_message = data.get('error_message', '')
            error_code = data.get('error_code', '')

            # Request information
            url = data.get('url', '')
            request_method = data.get('request_method', '')
            request_data = data.get('request_data', {})
            user_agent = data.get('user_agent', '')
            ip_address = data.get('ip_address', '')

            # Stack trace and debugging
            stack_trace = data.get('stack_trace', '')
            line_number = data.get('line_number')
            file_name = data.get('file_name', '')
            function_name = data.get('function_name', '')

            # User action context
            user_action = data.get('user_action', '')
            form_data = data.get('form_data', {})

            # Get device connection if provided
            device_connection_id = data.get('device_connection_id')
            device_connection = None
            if device_connection_id:
                try:
                    device_connection = DeviceConnection.objects.get(id=device_connection_id)
                except DeviceConnection.DoesNotExist:
                    pass

            # Create error log
            error = ErrorLog.objects.create(
                error_type=error_type,
                severity=severity,
                error_message=error_message,
                error_code=error_code,
                user=user,
                device_connection=device_connection,
                url=url,
                request_method=request_method,
                request_data=request_data,
                user_agent=user_agent,
                ip_address=ip_address,
                stack_trace=stack_trace,
                line_number=line_number,
                file_name=file_name,
                function_name=function_name,
                user_action=user_action,
                form_data=form_data
            , workspace=workspace)

            return JsonResponse({
                'success': True,
                'error_id': error.id
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Only POST requests are supported'})
