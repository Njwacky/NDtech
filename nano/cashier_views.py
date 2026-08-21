import json
import re
import logging
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import timezone

from .models import AirtimeProduct, AirtimeSale, UserActivity, Notification
from .fcm_service import send_fcm_notification_to_user

logger = logging.getLogger(__name__)


def _get_workspace(request):
    try:
        return getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    except Exception:
        return None


@login_required
def cashier_airtime_quick_sell(request):
    """Cashier airtime quick sell page"""
    try:
        user_profile = request.user.userprofile
    except Exception:
        return HttpResponseForbidden("User profile not found")
    
    # Check if user is cashier
    if user_profile.role != 'cashier':
        return HttpResponseForbidden("Only cashiers can access this page")
    
    # Get available credit (this would come from manager-provided credit)
    available_credit = 0.00
    
    context = {
        'available_credit': available_credit
    }
    
    from django.shortcuts import render
    return render(request, 'nano/cashier_airtime_quick_sell.html', context)


@login_required
def process_cashier_airtime_sale(request):
    """Process cashier airtime sale"""
    workspace = _get_workspace(request)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST requests are supported'})
    
    try:
        data = json.loads(request.body)
        user_profile = request.user.userprofile
        
        if user_profile.role != 'cashier':
            return JsonResponse({'success': False, 'error': 'Only cashiers can process sales'})
        
        network = data.get('network')
        amount = Decimal(str(data.get('amount', 0)))
        sale_type = data.get('type', 'airtime')
        price = Decimal(str(data.get('price', 0)))
        customer_phone = data.get('customer_phone')
        product_name = data.get('product_name')
        use_credit = data.get('use_credit', False)
        
        if not all([network, amount, sale_type, price, customer_phone, product_name]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'})
        
        if amount <= 0 or price <= 0:
            return JsonResponse({'success': False, 'error': 'Invalid amount or price'})
        
        if not re.match(r'^[0-9]{10,15}$', customer_phone):
            return JsonResponse({'success': False, 'error': 'Invalid phone number format'})
        
        if use_credit:
            available_credit = Decimal('0.00')
            if price > available_credit:
                return JsonResponse({'success': False, 'error': 'Insufficient credit balance'})
        
        # Create or get airtime product - map to correct model fields
        airtime_product, created = AirtimeProduct.objects.get_or_create(
            network=network,
            value=amount,
            airtime_type=sale_type,
            defaults={
                'name': product_name,
                'price': price,
                'stock': 999999,
                'is_active': True,
                'workspace': workspace
            }
        )
        
        if not created and airtime_product.price != price:
            airtime_product.price = price
            airtime_product.save()
        
        # Create airtime sale with correct fields
        airtime_sale = AirtimeSale.objects.create(
            airtime_product=airtime_product,
            quantity=1,
            total_price=price,
            customer_phone=customer_phone,
            status='completed',
            requested_by=request.user,
            approved_by=request.user,
            approved_at=timezone.now(),
            approval_notes=f'Quick cashier sale: {product_name}',
            workspace=workspace
        )
        
        UserActivity.objects.create(
            user=request.user,
            activity_type='payment',
            description=f'Quick airtime sale: {product_name} to {customer_phone}',
            page_url='/airtime/cashier-quick-sell/',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={'product_name': product_name, 'customer_phone': customer_phone, 'price': str(price)},
            workspace=workspace
        )
        
        manager_users = User.objects.filter(
            Q(userprofile__role='manager') | Q(is_superuser=True)
        ).distinct()
        
        for manager in manager_users:
            notification = Notification.objects.create(
                title=f'Quick Airtime Sale: {product_name}',
                message=f'Cashier {request.user.username} completed quick sale: {product_name} to {customer_phone} for R{price}',
                notification_type='system_alert',
                target_role='manager',
                target_user=manager,
                workspace=workspace
            )
            try:
                send_fcm_notification_to_user(manager, notification.title, notification.message)
            except Exception:
                pass
        
        return JsonResponse({
            'success': True,
            'message': f'Airtime sale completed successfully! {product_name} sold to {customer_phone} for R{price}',
            'sale_id': airtime_sale.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except InvalidOperation:
        return JsonResponse({'success': False, 'error': 'Invalid amount format'})
    except Exception as e:
        logger.error(f"Error processing cashier airtime sale: {str(e)}")
        return JsonResponse({'success': False, 'error': 'An error occurred while processing sale'})


@login_required
def process_quick_airtime_sale(request):
    """Process quick airtime sale from airtime management page"""
    workspace = _get_workspace(request)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST requests are supported'})
    
    try:
        data = json.loads(request.body)
        user_profile = request.user.userprofile
        
        if user_profile.role not in ['manager', 'admin'] and not request.user.is_superuser:
            return JsonResponse({'success': False, 'error': 'Permission denied'})
        
        network = data.get('network')
        amount = Decimal(str(data.get('amount', 0)))
        sale_type = data.get('type', 'airtime')
        price = Decimal(str(data.get('price', 0)))
        customer_phone = data.get('customer_phone')
        product_name = data.get('product_name')
        
        if not all([network, amount, sale_type, price, customer_phone, product_name]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'})
        
        if amount <= 0 or price <= 0:
            return JsonResponse({'success': False, 'error': 'Invalid amount or price'})
        
        if not re.match(r'^[0-9]{10,15}$', customer_phone):
            return JsonResponse({'success': False, 'error': 'Invalid phone number format'})
        
        airtime_product, created = AirtimeProduct.objects.get_or_create(
            network=network,
            value=amount,
            airtime_type=sale_type,
            defaults={
                'name': product_name,
                'price': price,
                'stock': 999999,
                'is_active': True,
                'workspace': workspace
            }
        )
        
        if not created and airtime_product.price != price:
            airtime_product.price = price
            airtime_product.save()
        
        airtime_sale = AirtimeSale.objects.create(
            airtime_product=airtime_product,
            quantity=1,
            total_price=price,
            customer_phone=customer_phone,
            status='completed',
            requested_by=request.user,
            approved_by=request.user,
            approved_at=timezone.now(),
            approval_notes=f'Quick manager sale: {product_name}',
            workspace=workspace
        )
        
        UserActivity.objects.create(
            user=request.user,
            activity_type='payment',
            description=f'Quick airtime sale: {product_name} to {customer_phone}',
            page_url='/airtime/management/',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={'product_name': product_name, 'customer_phone': customer_phone, 'price': str(price)},
            workspace=workspace
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Airtime sale completed successfully! {product_name} sold to {customer_phone} for R{price}',
            'sale_id': airtime_sale.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except InvalidOperation:
        return JsonResponse({'success': False, 'error': 'Invalid amount format'})
    except Exception as e:
        logger.error(f"Error processing quick airtime sale: {str(e)}")
        return JsonResponse({'success': False, 'error': 'An error occurred while processing sale'})
