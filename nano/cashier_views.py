@login_required
def cashier_airtime_quick_sell(request):
    """Cashier airtime quick sell page"""
    user_profile = request.user.userprofile
    
    # Check if user is cashier
    if user_profile.role != 'cashier':
        return HttpResponseForbidden("Only cashiers can access this page")
    
    # Get available credit (this would come from manager-provided credit)
    # For now, we'll use a default value or get from a credit model
    available_credit = 0.00  # This should be replaced with actual credit logic
    
    context = {
        'available_credit': available_credit
    }
    
    return render(request, 'nano/cashier_airtime_quick_sell.html', context)

@login_required
def process_cashier_airtime_sale(request):
    """Process cashier airtime sale"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST requests are supported'})
    
    try:
        data = json.loads(request.body)
        user_profile = request.user.userprofile
        
        # Check if user is cashier
        if user_profile.role != 'cashier':
            return JsonResponse({'success': False, 'error': 'Only cashiers can process sales'})
        
        # Extract sale data
        network = data.get('network')
        amount = Decimal(str(data.get('amount', 0)))
        sale_type = data.get('type', 'airtime')
        price = Decimal(str(data.get('price', 0)))
        customer_phone = data.get('customer_phone')
        product_name = data.get('product_name')
        use_credit = data.get('use_credit', False)
        
        # Validation
        if not all([network, amount, sale_type, price, customer_phone, product_name]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'})
        
        if amount <= 0 or price <= 0:
            return JsonResponse({'success': False, 'error': 'Invalid amount or price'})
        
        # Validate phone number
        if not re.match(r'^[0-9]{10,15}$', customer_phone):
            return JsonResponse({'success': False, 'error': 'Invalid phone number format'})
        
        # Check credit availability if using credit
        if use_credit:
            # This should check against actual credit balance
            available_credit = Decimal('0.00')  # Replace with actual credit logic
            if price > available_credit:
                return JsonResponse({'success': False, 'error': 'Insufficient credit balance'})
        
        # Create or get airtime product
        airtime_product, created = AirtimeProduct.objects.get_or_create(
            network=network,
            amount=amount,
            product_type=sale_type,
            defaults={
                'price': price,
                'stock': 999999,  # Unlimited stock for quick sell
                'is_active': True
            }
        , workspace=workspace)
        
        if not created and airtime_product.price != price:
            # Update price if different
            airtime_product.price = price
            airtime_product.save()
        
        # Create airtime sale
        airtime_sale = AirtimeSale.objects.create(
            product=airtime_product,
            seller=request.user,
            customer_phone=customer_phone,
            quantity=1,
            total_price=price,
            status='completed',  # Immediate completion for cashier sales
            sale_type='cashier_quick',
            network=network,
            amount=amount,
            product_type=sale_type
        , workspace=workspace)
        
        # Log user activity
        UserActivity.objects.create(
            user=request.user,
            action='airtime_sale',
            details=f'Quick airtime sale: {product_name} to {customer_phone}',
            ip_address=request.META.get('REMOTE_ADDR', '')
        , workspace=workspace)
        
        # Create notification for managers
        manager_users = User.objects.filter(
            Q(userprofile__role='manager') | Q(is_superuser=True)
        ).distinct()
        
        for manager in manager_users:
            notification = Notification.objects.create(
                title=f'Quick Airtime Sale: {product_name}',
                message=f'Cashier {request.user.username} completed quick sale: {product_name} to {customer_phone} for R{price}',
                notification_type='airtime_sale',
                target_user=manager
            , workspace=workspace)
            send_fcm_notification_to_user(manager, notification.title, notification.message)
        
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
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST requests are supported'})
    
    try:
        data = json.loads(request.body)
        user_profile = request.user.userprofile
        
        # Check if user has permission (manager, admin, or superuser)
        if user_profile.role not in ['manager', 'admin'] and not request.user.is_superuser:
            return JsonResponse({'success': False, 'error': 'Permission denied'})
        
        # Extract sale data
        network = data.get('network')
        amount = Decimal(str(data.get('amount', 0)))
        sale_type = data.get('type', 'airtime')
        price = Decimal(str(data.get('price', 0)))
        customer_phone = data.get('customer_phone')
        product_name = data.get('product_name')
        
        # Validation
        if not all([network, amount, sale_type, price, customer_phone, product_name]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'})
        
        if amount <= 0 or price <= 0:
            return JsonResponse({'success': False, 'error': 'Invalid amount or price'})
        
        # Validate phone number
        if not re.match(r'^[0-9]{10,15}$', customer_phone):
            return JsonResponse({'success': False, 'error': 'Invalid phone number format'})
        
        # Create or get airtime product
        airtime_product, created = AirtimeProduct.objects.get_or_create(
            network=network,
            amount=amount,
            product_type=sale_type,
            defaults={
                'price': price,
                'stock': 999999,  # Unlimited stock for quick sell
                'is_active': True
            }
        , workspace=workspace)
        
        if not created and airtime_product.price != price:
            # Update price if different
            airtime_product.price = price
            airtime_product.save()
        
        # Create airtime sale
        airtime_sale = AirtimeSale.objects.create(
            product=airtime_product,
            seller=request.user,
            customer_phone=customer_phone,
            quantity=1,
            total_price=price,
            status='completed',  # Immediate completion for quick sales
            sale_type='manager_quick',
            network=network,
            amount=amount,
            product_type=sale_type
        , workspace=workspace)
        
        # Log user activity
        UserActivity.objects.create(
            user=request.user,
            action='airtime_sale',
            details=f'Quick airtime sale: {product_name} to {customer_phone}',
            ip_address=request.META.get('REMOTE_ADDR', '')
        , workspace=workspace)
        
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
