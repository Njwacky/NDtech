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
from django.db.models import Q, Count, Sum, Min
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import pandas as pd
import json
import re
import csv
import io
from decimal import Decimal, InvalidOperation
from .models import Product, Sale, UserProfile, PendingOrder, CompletedOrder, Notification, WarehousePrice, PriceComparison

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
            Notification.objects.create(
                title=f"Low Stock Alert: {product.name}",
                message=f"Low stock alert: {product.name} has only {product.stock} units remaining",
                notification_type='low_stock',
                target_role='admin',  # Default to admin role
                target_user=admin_user,
                product=product
            )

@login_required
def home(request):
    # POS Dashboard
    products = Product.objects.all()
    
    # Check for low stock products when dashboard is loaded
    check_low_stock()
    
    return render(request, 'nano/home.html', {'products': products})

def register(request):
    return render(request, 'nano/register.html')

def sign_up(request):
    if request.method == 'POST':
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
            return redirect('sign_in')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        messages.success(request, 'Account created successfully')
        return redirect('sign_in')

    return render(request, 'nano/sign_up.html')

def sign_in(request):
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
    logout(request)
    return redirect('register')

@login_required
def add_stock(request):
    # Allow only superusers or users with admin/manager/cashier roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return HttpResponseForbidden("You do not have permission to access this page.")
    
    # Check if user is manager for Add Product functionality
    is_manager = request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager'])
    
    if request.method == 'POST':
        mode = request.POST.get('mode', 'add_stock')  # 'add_stock' or 'add_product'
        
        if mode == 'add_product':
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

            if not expiry_date_str:
                errors['expiry_date'] = 'Expiry date is required'
            else:
                try:
                    expiry_date = timezone.datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
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
                return render(request, 'nano/add_stock.html', {
                    'mode': 'add_product',
                    'is_manager': is_manager
                })

            # Create the product
            product = Product.objects.create(
                name=name,
                price=price,
                description=description,
                category=category,
                expiry_date=expiry_date,
                stock=
            )