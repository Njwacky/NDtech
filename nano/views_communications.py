"""
Communications/Tracking Views
"""

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
from confige.security import rate_limit

# Set up logger
logger = logging.getLogger(__name__)

# Create your views here.


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
@rate_limit('airtime', limit=20, window=60)
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