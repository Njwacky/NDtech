"""
Integration between POS system and Food Ordering API
Allows barcode scanning to work with both POS products and food ordering menu items
"""

import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q
from .models import Product, ErrorLog, UserActivity
from food_ordering.models import MenuItem, Restaurant


def _get_workspace(request):
    try:
        return getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None
    except Exception:
        return None


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class FoodOrderingIntegration:
    """Handles integration between POS and Food Ordering systems"""
    
    @staticmethod
    def search_menu_items_by_barcode(barcode):
        """
        Search for menu items that might match a barcode
        This uses a combination of barcode patterns and name matching
        """
        try:
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
            
            search_results = []
            
            if matched_category:
                search_terms = [matched_category.lower()]
                if matched_category == 'Coca-Cola':
                    search_terms.extend(['coke', 'cola', 'soft drink'])
                elif matched_category == 'Bread':
                    search_terms.extend(['bread', 'bun', 'roll', 'loaf'])
                elif matched_category == 'Chips':
                    search_terms.extend(['chips', 'crisps', 'snack'])
                elif matched_category == 'Dairy':
                    search_terms.extend(['milk', 'cheese', 'yogurt', 'dairy'])
                elif matched_category == 'Sweets':
                    search_terms.extend(['chocolate', 'sweet', 'candy', 'dessert'])
                elif matched_category == 'Beverages':
                    search_terms.extend(['drink', 'juice', 'beverage', 'soda'])
                elif matched_category == 'Snacks':
                    search_terms.extend(['snack', 'pie', 'pastry'])
                elif matched_category == 'Frozen':
                    search_terms.extend(['frozen', 'ice cream'])
                elif matched_category == 'Canned':
                    search_terms.extend(['canned', 'tin', 'jar'])
                
                query = Q()
                for term in search_terms:
                    query |= Q(name__icontains=term) | Q(description__icontains=term)
                
                menu_items = MenuItem.objects.filter(
                    query,
                    is_available=True
                ).select_related('restaurant', 'category').distinct()
                
                for item in menu_items:
                    search_results.append({
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
                        'match_type': 'category_pattern',
                        'matched_barcode': barcode
                    })
            
            exact_matches = MenuItem.objects.filter(
                Q(description__icontains=barcode) | Q(name__icontains=barcode),
                is_available=True
            ).select_related('restaurant', 'category').distinct()
            
            for item in exact_matches:
                if not any(result['id'] == item.id for result in search_results):
                    search_results.append({
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
            
            return search_results
            
        except Exception as e:
            print(f"Error searching menu items: {str(e)}")
            return []
    
    @staticmethod
    def create_pos_product_from_menu_item(menu_item, barcode=None, workspace=None):
        """
        Create a POS product from a food ordering menu item
        This allows the menu item to be added to POS cart
        """
        try:
            existing_product = Product.objects.filter(
                name=menu_item.name,
                price=menu_item.price
            ).first()
            
            if existing_product:
                return existing_product
            
            category_mapping = {
                'beverages': 'cold_drinks',
                'snacks': 'snacks_chips',
                'desserts': 'sweets_treats',
                'main course': 'basic_groceries',
                'appetizers': 'snacks_chips',
                'breakfast': 'bread_baked',
                'dairy': 'dairy_eggs',
            }
            
            pos_category = 'basic_groceries'
            if menu_item.category:
                category_name = menu_item.category.name.lower()
                for food_cat, pos_cat in category_mapping.items():
                    if food_cat in category_name:
                        pos_category = pos_cat
                        break
            
            pos_product = Product.objects.create(
                name=f"[FOOD] {menu_item.name}",
                price=menu_item.price,
                description=f"Food item from {menu_item.restaurant.name}: {menu_item.description}",
                category=pos_category,
                barcode=barcode or f"FOOD{menu_item.id:08d}",
                stock=999,
                expiry_date=None,
                workspace=workspace
            )
            
            return pos_product
            
        except Exception as e:
            print(f"Error creating POS product from menu item: {str(e)}")
            return None

    @staticmethod
    def _get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    @staticmethod
    def log_food_ordering_error(request, error_message, error_type='user_error', severity='low', user_action='', form_data=None):
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
                ip_address=FoodOrderingIntegration._get_client_ip(request),
                user=request.user if request.user.is_authenticated else None,
                user_action=user_action,
                form_data=form_data or {},
                workspace=workspace
            )
        except Exception as e:
            print(f"Error logging food ordering error: {str(e)}")


@login_required
def food_scanner_integration(request):
    """
    Enhanced barcode scanner that can scan both POS products and food ordering items
    """
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return HttpResponseForbidden("You do not have permission to access this page.")
    
    return render(request, 'nano/food_scanner.html')


@login_required
def api_food_scanner_lookup(request, barcode):
    """
    API endpoint that searches both POS products and food ordering menu items
    """
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    workspace = _get_workspace(request)

    if request.method == 'GET':
        try:
            results = []
            
            pos_product = Product.objects.filter(barcode=barcode).first()
            if pos_product:
                results.append({
                    'id': pos_product.id,
                    'name': pos_product.name,
                    'price': float(pos_product.get_current_price()),
                    'stock': pos_product.stock,
                    'category': pos_product.get_category_display(),
                    'description': pos_product.description,
                    'barcode': pos_product.barcode,
                    'source': 'pos_system',
                    'is_on_sale': pos_product.is_currently_on_sale(),
                    'sale_price': float(pos_product.sale_price) if pos_product.is_currently_on_sale() else None,
                    'discount_percentage': pos_product.get_discount_percentage()
                })
            
            food_items = FoodOrderingIntegration.search_menu_items_by_barcode(barcode)
            results.extend(food_items)
            
            UserActivity.objects.create(
                user=request.user,
                activity_type='api_call',
                description=f'Scanned barcode: {barcode}',
                page_url='/food/scanner/',
                ip_address=_get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata={
                    'barcode': barcode,
                    'results_found': len(results),
                    'scan_type': 'food_scanner'
                },
                workspace=workspace
            )
            
            if results:
                return JsonResponse({
                    'success': True,
                    'results': results,
                    'barcode': barcode,
                    'total_found': len(results)
                })
            else:
                ErrorLog.objects.create(
                    error_type='user_error',
                    severity='low',
                    error_message=f'No products or menu items found for barcode: {barcode}',
                    url='/food/scanner/',
                    request_method='GET',
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    ip_address=_get_client_ip(request),
                    user=request.user,
                    user_action='Scanning barcode for product lookup',
                    form_data={'barcode': barcode},
                    workspace=workspace
                )
                
                return JsonResponse({
                    'success': False,
                    'message': f'No products or menu items found for barcode: {barcode}',
                    'barcode': barcode
                })
                
        except Exception as e:
            ErrorLog.objects.create(
                error_type='system_error',
                severity='medium',
                error_message=f'Error in food scanner lookup: {str(e)}',
                url='/food/scanner/',
                request_method='GET',
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=_get_client_ip(request),
                user=request.user,
                user_action='Scanning barcode for product lookup',
                stack_trace=str(e),
                workspace=workspace
            )
            
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def api_add_food_item_to_pos(request):
    """
    API endpoint to add a food ordering menu item to POS cart
    This creates a POS product from the menu item if it doesn't exist
    """
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    workspace = _get_workspace(request)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            menu_item_id = data.get('menu_item_id')
            barcode = data.get('barcode')
            quantity = data.get('quantity', 1)
            
            if not menu_item_id:
                return JsonResponse({'success': False, 'error': 'Menu item ID is required'})
            
            menu_item = MenuItem.objects.get(id=menu_item_id, is_available=True)
            
            pos_product = FoodOrderingIntegration.create_pos_product_from_menu_item(menu_item, barcode, workspace=workspace)
            
            if not pos_product:
                return JsonResponse({'success': False, 'error': 'Failed to create POS product'})
            
            return JsonResponse({
                'success': True,
                'product': {
                    'id': pos_product.id,
                    'name': pos_product.name,
                    'price': float(pos_product.price),
                    'stock': pos_product.stock,
                    'category': pos_product.get_category_display(),
                    'barcode': pos_product.barcode,
                    'quantity': quantity
                },
                'menu_item': {
                    'name': menu_item.name,
                    'restaurant': menu_item.restaurant.name,
                    'preparation_time': menu_item.preparation_time
                }
            })
            
        except MenuItem.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Menu item not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def food_menu_browser(request):
    """
    Browse food ordering menu items and add them to POS
    """
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return HttpResponseForbidden("You do not have permission to access this page.")
    
    restaurants = Restaurant.objects.filter(is_active=True).order_by('name')
    
    selected_restaurant = request.GET.get('restaurant')
    menu_items = []
    
    if selected_restaurant:
        try:
            restaurant = Restaurant.objects.get(id=selected_restaurant)
            menu_items = MenuItem.objects.filter(
                restaurant=restaurant,
                is_available=True
            ).select_related('category').order_by('category__display_order', 'name')
        except Restaurant.DoesNotExist:
            pass
    
    return render(request, 'nano/food_menu_browser.html', {
        'restaurants': restaurants,
        'menu_items': menu_items,
        'selected_restaurant': selected_restaurant
    })
