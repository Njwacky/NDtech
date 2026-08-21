"""
Error tracking integration for food ordering system
Adds comprehensive error logging to food ordering operations
"""

from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .models import ErrorLog, UserActivity
from food_ordering.models import MenuItem, Restaurant
import json


def _get_workspace(request):
    try:
        return getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    except Exception:
        return None


class FoodOrderingErrorTracking:
    """Handles error tracking for food ordering operations"""
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def log_food_ordering_error(request, error_message, error_type='user_error', severity='low', user_action='', form_data=None, stack_trace=None):
        """Log errors in food ordering system"""
        try:
            workspace = _get_workspace(request)
            ErrorLog.objects.create(
                error_type=error_type,
                severity=severity,
                error_message=error_message,
                url=request.path,
                request_method=request.method,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=FoodOrderingErrorTracking.get_client_ip(request),
                user=request.user if request.user.is_authenticated else None,
                user_action=user_action,
                form_data=form_data or {},
                stack_trace=stack_trace,
                workspace=workspace
            )
        except Exception as e:
            print(f"Error logging food ordering error: {str(e)}")
    
    @staticmethod
    def log_food_ordering_activity(request, activity_type, description, metadata=None):
        """Log user activities in food ordering system"""
        try:
            workspace = _get_workspace(request)
            UserActivity.objects.create(
                user=request.user,
                activity_type=activity_type,
                description=description,
                page_url=request.path,
                ip_address=FoodOrderingErrorTracking.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata=metadata or {},
                workspace=workspace
            )
        except Exception as e:
            print(f"Error logging food ordering activity: {str(e)}")

@login_required
def enhanced_food_scanner_lookup(request, barcode):
    """
    Enhanced food scanner lookup with comprehensive error tracking
    """
    # Allow only superusers or users with admin/manager/cashier roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    try:
        # Log the barcode scan activity
        FoodOrderingErrorTracking.log_food_ordering_activity(
            request, 
            'api_call', 
            f'Scanned barcode: {barcode}',
            {'barcode': barcode, 'scan_type': 'food_scanner'}
        )
        
        # Search for menu items
        results = []
        
        # Try exact barcode match first
        exact_matches = MenuItem.objects.filter(
            Q(description__icontains=barcode) | Q(name__icontains=barcode),
            is_available=True
        ).select_related('restaurant', 'category').distinct()
        
        for item in exact_matches:
            results.append({
                'id': item.id,
                'name': item.name,
                'description': item.description,
                'price': float(item.price),
                'restaurant': item.restaurant.name,
                'restaurant_id': item.restaurant.id,
                'category': item.category.name if item.category else 'Uncategorized',
                'preparation_time': item.preparation_time,
                'is_vegetarian': item.is_vegetarian,
                'is_vegan': item.is_vegan,
                'image_url': item.image.url if item.image else None,
                'source': 'food_ordering',
                'match_type': 'exact_match',
                'matched_barcode': barcode
            })
        
        # Try pattern matching if no exact matches
        if not results:
            food_patterns = {
                '6001007': 'Coca-Cola',
                '6001063': 'Bread',
                '6001085': 'Chips',
                '600106': 'Dairy',
                '600101': 'Sweets',
                '600102': 'Beverages',
                '600103': 'Snacks',
                '600104': 'Frozen',
                '600105': 'Canned',
            }
            
            matched_category = None
            for pattern, category in food_patterns.items():
                if barcode.startswith(pattern):
                    matched_category = category
                    break
            
            if matched_category:
                search_terms = [matched_category.lower()]
                if matched_category == 'Coca-Cola':
                    search_terms.extend(['coke', 'cola', 'soft drink'])
                elif matched_category == 'Bread':
                    search_terms.extend(['bread', 'bun', 'roll'])
                elif matched_category == 'Chips':
                    search_terms.extend(['chips', 'crisps'])
                elif matched_category == 'Dairy':
                    search_terms.extend(['milk', 'cheese', 'yogurt'])
                elif matched_category == 'Sweets':
                    search_terms.extend(['chocolate', 'sweet', 'candy'])
                elif matched_category == 'Beverages':
                    search_terms.extend(['drink', 'juice', 'beverage'])
                elif matched_category == 'Snacks':
                    search_terms.extend(['snack', 'pie'])
                elif matched_category == 'Frozen':
                    search_terms.extend(['frozen', 'ice cream'])
                elif matched_category == 'Canned':
                    search_terms.extend(['canned', 'tin'])
                
                query = Q()
                for term in search_terms:
                    query |= Q(name__icontains=term) | Q(description__icontains=term)
                
                pattern_matches = MenuItem.objects.filter(
                    query,
                    is_available=True
                ).select_related('restaurant', 'category').distinct()
                
                for item in pattern_matches:
                    results.append({
                        'id': item.id,
                        'name': item.name,
                        'description': item.description,
                        'price': float(item.price),
                        'restaurant': item.restaurant.name,
                        'restaurant_id': item.restaurant.id,
                        'category': item.category.name if item.category else 'Uncategorized',
                        'preparation_time': item.preparation_time,
                        'is_vegetarian': item.is_vegetarian,
                        'is_vegan': item.is_vegan,
                        'image_url': item.image.url if item.image else None,
                        'source': 'food_ordering',
                        'match_type': 'pattern_match',
                        'matched_barcode': barcode
                    })
        
        if results:
            return JsonResponse({
                'success': True,
                'results': results,
                'barcode': barcode,
                'total_found': len(results)
            })
        else:
            # Log error for barcode not found
            FoodOrderingErrorTracking.log_food_ordering_error(
                request,
                f'No menu items found for barcode: {barcode}',
                'user_error',
                'low',
                'Scanning barcode for food lookup',
                {'barcode': barcode}
            )
            
            return JsonResponse({
                'success': False,
                'message': f'No menu items found for barcode: {barcode}',
                'barcode': barcode
            })
            
    except Exception as e:
        # Log system error
        FoodOrderingErrorTracking.log_food_ordering_error(
            request,
            f'Error in food scanner lookup: {str(e)}',
            'system_error',
            'medium',
            'Scanning barcode for food lookup',
            {'barcode': barcode},
            str(e)
        )
        
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def enhanced_add_to_cart(request):
    """
    Enhanced add to cart with error tracking
    """
    # Allow only superusers or users with admin/manager/cashier roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            menu_item_id = data.get('menu_item_id')
            quantity = data.get('quantity', 1)
            
            if not menu_item_id:
                FoodOrderingErrorTracking.log_food_ordering_error(
                    request,
                    'Menu item ID is required for adding to cart',
                    'validation_error',
                    'medium',
                    'Adding food item to cart',
                    data
                )
                return JsonResponse({'success': False, 'error': 'Menu item ID is required'})
            
            # Log the add to cart activity
            FoodOrderingErrorTracking.log_food_ordering_activity(
                request,
                'form_submit',
                f'Added menu item #{menu_item_id} to cart with quantity {quantity}',
                {'menu_item_id': menu_item_id, 'quantity': quantity}
            )
            
            # Validate menu item exists
            try:
                menu_item = MenuItem.objects.get(id=menu_item_id, is_available=True)
            except MenuItem.DoesNotExist:
                FoodOrderingErrorTracking.log_food_ordering_error(
                    request,
                    f'Menu item not found: {menu_item_id}',
                    'user_error',
                    'medium',
                    'Adding food item to cart',
                    {'menu_item_id': menu_item_id}
                )
                return JsonResponse({'success': False, 'error': 'Menu item not found'})
            
            # Check stock availability (if applicable)
            if hasattr(menu_item, 'stock') and menu_item.stock is not None:
                if menu_item.stock < quantity:
                    FoodOrderingErrorTracking.log_food_ordering_error(
                        request,
                        f'Insufficient stock for {menu_item.name}: {menu_item.stock} available, {quantity} requested',
                        'user_error',
                        'high',
                        'Adding food item to cart',
                        {'menu_item_id': menu_item_id, 'available_stock': menu_item.stock, 'requested_quantity': quantity}
                    )
                    return JsonResponse({'success': False, 'error': f'Insufficient stock for {menu_item.name}'})
            
            return JsonResponse({
                'success': True,
                'message': f'Added {menu_item.name} to cart',
                'menu_item': {
                    'id': menu_item.id,
                    'name': menu_item.name,
                    'price': float(menu_item.price),
                    'restaurant': menu_item.restaurant.name,
                    'quantity': quantity
                }
            })
            
        except json.JSONDecodeError:
            FoodOrderingErrorTracking.log_food_ordering_error(
                request,
                'Invalid JSON data in add to cart request',
                'validation_error',
                'medium',
                'Adding food item to cart'
            )
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        except Exception as e:
            FoodOrderingErrorTracking.log_food_ordering_error(
                request,
                f'Error in add to cart: {str(e)}',
                'system_error',
                'high',
                'Adding food item to cart',
                {},
                str(e)
            )
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def food_ordering_error_report(request):
    """
    API endpoint to report food ordering errors
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            error_message = data.get('error_message', '')
            error_type = data.get('error_type', 'user_error')
            severity = data.get('severity', 'medium')
            user_action = data.get('user_action', '')
            form_data = data.get('form_data', {})
            
            if not error_message:
                return JsonResponse({'success': False, 'error': 'Error message is required'})
            
            # Log the error
            FoodOrderingErrorTracking.log_food_ordering_error(
                request,
                error_message,
                error_type,
                severity,
                user_action,
                form_data
            )
            
            return JsonResponse({'success': True, 'message': 'Error logged successfully'})
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
