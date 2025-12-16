from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Sum, Count, Avg, F
from datetime import timedelta
import json

# Import tracking functionality from nano app
from nano.food_ordering_error_tracking import FoodOrderingErrorTracking
from nano.models import ErrorLog, UserActivity

from .models import (
    Restaurant, MenuCategory, MenuItem, Order, Customer,
    DeliveryDriver, DeliveryZone, OrderItem, PlatformIntegration,
    CustomerReview
)
from .serializers import (
    RestaurantSerializer, MenuCategorySerializer, MenuItemSerializer,
    OrderSerializer, CustomerSerializer, DeliveryDriverSerializer,
    DeliveryZoneSerializer, OrderItemSerializer, CustomerReviewSerializer
)

class RestaurantViewSet(viewsets.ModelViewSet):
    """API endpoint for restaurant management"""
    serializer_class = RestaurantSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_superuser:
            return Restaurant.objects.all()
        return Restaurant.objects.filter(owner=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
        return serializer

class MenuViewSet(viewsets.ModelViewSet):
    """API endpoint for menu management"""
    serializer_class = MenuItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        restaurant_id = self.request.query_params.get('restaurant_id')
        if restaurant_id:
            return MenuItem.objects.filter(restaurant_id=restaurant_id, is_available=True)
        return MenuItem.objects.none()
    
    def perform_create(self, serializer):
        # Check if user owns the restaurant
        restaurant = serializer.validated_data['restaurant']
        if restaurant.owner != self.request.user and not self.request.user.is_superuser:
            raise PermissionError("You don't own this restaurant")
        
        serializer.save()
        return serializer

class OrderViewSet(viewsets.ModelViewSet):
    """API endpoint for order management"""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_superuser:
            return Order.objects.all()
        elif hasattr(self.request.user, 'customer_profile'):
            return Order.objects.filter(customer=self.request.user.customer_profile)
        elif hasattr(self.request.user, 'restaurant_owner'):
            return Order.objects.filter(restaurant__owner=self.request.user)
        return Order.objects.none()
    
    def create(self, request, *args, **kwargs):
        """Create new order"""
        serializer = self.get_serializer(data=request.data)
        
        # Validate customer
        if not hasattr(request.user, 'customer_profile'):
            return Response(
                {"error": "Customer profile required for ordering"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Calculate totals
        items = request.data.get('items', [])
        subtotal = sum(item['price'] * item['quantity'] for item in items)
        
        # Get restaurant for delivery calculation
        restaurant = get_object_or_404(Restaurant, id=request.data['restaurant'])
        
        # Calculate delivery fee
        delivery_fee = self.calculate_delivery_fee(restaurant, request.data.get('delivery_address'))
        
        # Calculate service fee (2% of subtotal)
        service_fee = subtotal * 0.02
        
        total_amount = subtotal + delivery_fee + service_fee
        
        # Generate order number
        order_number = f"ORD{timezone.now().strftime('%Y%m%d%H%M%S')}"
        
        # Estimate delivery time
        estimated_delivery_time = timezone.now() + timedelta(minutes=restaurant.delivery_time_minutes)
        
        order_data = {
            'customer': request.user.customer_profile.id,
            'restaurant': restaurant.id,
            'items': items,
            'subtotal': subtotal,
            'delivery_fee': delivery_fee,
            'service_fee': service_fee,
            'total_amount': total_amount,
            'delivery_address': request.data.get('delivery_address'),
            'delivery_instructions': request.data.get('delivery_instructions', ''),
            'payment_method': request.data.get('payment_method'),
            'estimated_delivery_time': estimated_delivery_time,
            'order_number': order_number,
            'tracking_code': self.generate_tracking_code(),
            'status': 'pending'
        }
        
        serializer = self.get_serializer(data=order_data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        
        # Update item popularity
        self.update_item_popularity(items)
        
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
    
    def calculate_delivery_fee(self, restaurant, delivery_address):
        """Calculate delivery fee based on restaurant's zones"""
        if not delivery_address:
            return restaurant.delivery_zones.get('default', {}).get('base_fee', 15.00)
        
        # Simple distance-based calculation (you'd use Google Maps API in production)
        zones = restaurant.delivery_zones
        for zone_name, zone_data in zones.items():
            if zone_data.get('base_fee'):
                # For now, use base fee - you'd implement geolocation here
                return zone_data['base_fee']
        
        return 15.00  # Default delivery fee
    
    def generate_tracking_code(self):
        """Generate unique tracking code"""
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    def update_item_popularity(self, items):
        """Update item order count"""
        for item in items:
            try:
                menu_item = MenuItem.objects.get(id=item['menu_item'])
                menu_item.order_count += item['quantity']
                menu_item.save()
            except MenuItem.DoesNotExist:
                continue

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_tracking(request, tracking_code):
    """Track order by tracking code"""
    try:
        order = Order.objects.get(tracking_code=tracking_code)
        return Response({
            'order': OrderSerializer(order).data,
            'status': order.get_status_display(),
            'estimated_delivery_time': order.estimated_delivery_time,
            'driver_info': DeliveryDriverSerializer(order.driver).data if order.driver else None
        })
    except Order.DoesNotExist:
        return Response(
            {"error": "Order not found"},
            status=status.HTTP_404_NOT_FOUND
        )

class CustomerViewSet(viewsets.ModelViewSet):
    """API endpoint for customer management"""
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_superuser:
            return Customer.objects.all()
        return Customer.objects.filter(user=self.request.user)

class RestaurantDetailView(APIView):
    """Get detailed restaurant information including menu"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, restaurant_id):
        try:
            restaurant = Restaurant.objects.get(id=restaurant_id)
            
            # Check if user has access
            if not (request.user.is_superuser or restaurant.owner == request.user):
                return Response(
                    {"error": "Access denied"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get menu categories with items
            menu_categories = MenuCategory.objects.filter(
                restaurant=restaurant, 
                is_active=True
            ).prefetch_related('menu_items')
            
            menu_data = []
            for category in menu_categories:
                items = MenuItem.objects.filter(
                    category=category,
                    is_available=True
                )
                
                category_data = {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description,
                    'items': MenuItemSerializer(items, many=True).data
                }
                menu_data.append(category_data)
            
            restaurant_data = RestaurantSerializer(restaurant).data
            restaurant_data['menu'] = menu_data
            
            return Response(restaurant_data)
            
        except Restaurant.DoesNotExist:
            return Response(
                {"error": "Restaurant not found"},
                status=status.HTTP_404_NOT_FOUND
            )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nearby_restaurants(request):
    """Get nearby restaurants based on user location"""
    latitude = request.GET.get('latitude')
    longitude = request.GET.get('longitude')
    radius = float(request.GET.get('radius', 5))  # Default 5km radius
    
    if not latitude or not longitude:
        return Response(
            {"error": "Latitude and longitude required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Find restaurants within radius (simplified - you'd use proper geolocation in production)
    restaurants = Restaurant.objects.filter(
        is_active=True,
        latitude__isnull=False,
        longitude__isnull=False
    ).filter(
        Q(latitude__gte=float(latitude) - 0.1) & Q(latitude__lte=float(latitude) + 0.1),
        Q(longitude__gte=float(longitude) - 0.1) & Q(longitude__lte=float(longitude) + 0.1)
    )
    
    # Calculate distance (simplified)
    restaurant_data = []
    for restaurant in restaurants:
        distance = calculate_distance(
            float(latitude), float(longitude),
            float(restaurant.latitude), float(restaurant.longitude)
        )
        
        if distance <= radius:
            data = RestaurantSerializer(restaurant).data
            data['distance'] = round(distance, 2)
            restaurant_data.append(data)
    
    # Sort by distance
    restaurant_data.sort(key=lambda x: x['distance'])
    
    return Response({
        'restaurants': restaurant_data,
        'center': {'latitude': latitude, 'longitude': longitude},
        'radius': radius
    })

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points (Haversine formula)"""
    from math import radians, sin, cos, sqrt, atan2
    
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * sin(dlon/2)**2
    c = sin(lat1)**2 + cos(lat1) * cos(dlon/2)**2
    
    angle = atan2(sqrt(a - c), sqrt(c))
    
    # Radius of earth in km
    r = 6371
    
    return r * angle

class DeliveryDriverViewSet(viewsets.ModelViewSet):
    """API endpoint for delivery driver management"""
    serializer_class = DeliveryDriverSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_superuser:
            return DeliveryDriver.objects.all()
        return DeliveryDriver.objects.filter(user=self.request.user)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_driver_location(request):
    """Update driver's current location"""
    try:
        driver = DeliveryDriver.objects.get(user=request.user)
        
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        
        if latitude and longitude:
            driver.current_location = {
                'latitude': float(latitude),
                'longitude': float(longitude),
                'updated_at': timezone.now().isoformat()
            }
            driver.last_location_update = timezone.now()
            driver.save()
            
            return Response({"status": "Location updated"})
        else:
            return Response(
                {"error": "Latitude and longitude required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except DeliveryDriver.DoesNotExist:
        return Response(
            {"error": "Driver profile not found"},
            status=status.HTTP_404_NOT_FOUND
        )

# Web Views
class RestaurantListView(LoginRequiredMixin, ListView):
    """Web view for restaurant listing"""
    model = Restaurant
    template_name = 'food_ordering/restaurant_list.html'
    context_object_name = 'restaurants'
    paginate_by = 12
    
    def get_queryset(self):
        if self.request.user.is_superuser:
            return Restaurant.objects.filter(is_active=True)
        return Restaurant.objects.filter(owner=self.request.user, is_active=True)

class RestaurantDetailView(LoginRequiredMixin, DetailView):
    """Web view for restaurant details"""
    model = Restaurant
    template_name = 'food_ordering/restaurant_detail.html'
    context_object_name = 'restaurant'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get menu categories with items
        menu_categories = MenuCategory.objects.filter(
            restaurant=self.object,
            is_active=True
        ).prefetch_related('menu_items')
        
        context['menu_categories'] = menu_categories
        return context

class OrderTrackingView(View):
    """Web view for order tracking"""
    template_name = 'food_ordering/order_tracking.html'
    
    def get_context_data(self, **kwargs):
        tracking_code = kwargs.get('tracking_code')
        order = None
        
        if tracking_code:
            try:
                order = Order.objects.get(tracking_code=tracking_code)
                context['order'] = order
            except Order.DoesNotExist:
                context['error'] = "Order not found"
        
        context['tracking_code'] = tracking_code
        return context

# Management Dashboard Views
@login_required
def restaurant_analytics(request, restaurant_id):
    """Analytics dashboard for restaurant owners"""
    if not request.user.is_superuser:
        try:
            restaurant = Restaurant.objects.get(id=restaurant_id, owner=request.user)
        except Restaurant.DoesNotExist:
            return HttpResponseForbidden("You don't own this restaurant")
    else:
        # Superusers can view any restaurant
        restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    
    # Get date range from request
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Sales metrics
    orders = Order.objects.filter(
        restaurant=restaurant,
        created_at__gte=start_date,
        status='delivered'
    )
    
    daily_sales = orders.extra({
        'date': 'date(created_at)',
    }).values('date').annotate(
        daily_orders=Count('id'),
        daily_revenue=Sum('total_amount')
    ).order_by('date')
    
    # Popular items
    popular_items = OrderItem.objects.filter(
        order__restaurant=restaurant,
        order__created_at__gte=start_date
    ).values('menu_item__name').annotate(
        order_count=Count('id'),
        total_quantity=Sum('quantity')
    ).order_by('-order_count')[:10]
    
    # Customer metrics
    total_customers = Customer.objects.filter(
        orders__restaurant=restaurant,
        orders__created_at__gte=start_date
    ).distinct().count()
    
    # Delivery metrics
    delivery_times = Order.objects.filter(
        restaurant=restaurant,
        status='delivered',
        actual_delivery_time__isnull=False
    ).aggregate(
        avg_delivery_time=Avg(
            F('actual_delivery_time') - F('estimated_delivery_time')
        )
    )
    
    context = {
        'restaurant': restaurant,
        'daily_sales': list(daily_sales),
        'popular_items': list(popular_items),
        'total_customers': total_customers,
        'delivery_metrics': delivery_times,
        'days': days,
        'total_revenue': orders.aggregate(total_revenue=Sum('total_amount'))['total_revenue'],
        'total_orders': orders.count()
    }
    
    return render(request, 'food_ordering/restaurant_analytics.html', context)

# Tracking Integration Views
@csrf_exempt
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

@csrf_exempt
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
                data,
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
