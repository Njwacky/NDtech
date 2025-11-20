# South African Food Ordering System Architecture

## 🎯 Goal
Build a complete food ordering and delivery management system that integrates with your existing futurePOS, specifically designed for South African market needs.

## 🏗️ System Components

### 1. Core Ordering Engine
```
Customer Apps → Order API → futurePOS → Kitchen Display → Delivery Management
```

### 2. Platform Integrations
- **Mr D Food Integration** (Takealot ecosystem)
- **Uber Eats Integration** (Global API with SA support)
- **Local Platform Support** (KasiD, Heyfood, etc.)
- **WhatsApp Ordering** (For markets with limited internet)
- **Self-hosted Web Ordering** (For restaurants)

### 3. Delivery Management
- **Driver Assignment System**
- **Real-time Tracking**
- **Route Optimization**
- **Delivery Fee Calculation** (SA-specific zones)
- **Payment Integration** (Yoco, SnapScan, etc.)

## 📱 Customer-facing Applications

### Web Ordering Platform
```python
# Proposed Django App Structure
food_ordering/
├── models.py          # Orders, Customers, Restaurants, Menus
├── views.py           # Order API, Menu API, Customer API
├── serializers.py     # DRF serializers for API endpoints
├── tasks.py           # Celery tasks for notifications
└── management/
    └── commands/
        └── setup_sample_restaurant.py
```

### WhatsApp Ordering Bot
```python
# WhatsApp Integration (using Twilio/WhatsApp Business API)
whatsapp_ordering/
├── bot.py             # Message handling logic
├── order_parser.py     # Parse orders from text messages
└── response_templates.py # Pre-defined responses
```

### Mobile App (React Native)
```javascript
// Cross-platform mobile app
src/
├── screens/
│   ├── RestaurantList.js
│   ├── Menu.js
│   ├── Cart.js
│   ├── Checkout.js
│   └── OrderTracking.js
├── services/
│   ├── api.js          # API communication
│   ├── location.js      # GPS tracking
│   └── payments.js      # Payment processing
└── utils/
    ├── storage.js       # Local data management
    └── validation.js    # Form validation
```

## 🔧 Backend API Design

### Core Models
```python
# food_ordering/models.py
class Restaurant(models.Model):
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.TextField()
    delivery_zones = models.JSONField(default=dict)
    operating_hours = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.15)

class MenuCategory(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

class MenuItem(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    category = models.ForeignKey(MenuCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='menu_items/')
    ingredients = models.TextField()
    allergens = models.JSONField(default=list)
    preparation_time = models.PositiveIntegerField(default=15)  # minutes
    is_available = models.BooleanField(default=True)
    spice_level = models.CharField(max_length=20, choices=[
        ('mild', 'Mild'),
        ('medium', 'Medium'),
        ('hot', 'Hot'),
        ('extra_hot', 'Extra Hot')
    ])

class Order(models.Model):
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded')
    ]
    
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    items = models.JSONField(default=list)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_address = models.TextField()
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    special_instructions = models.TextField(blank=True)
    payment_method = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=20, default='pending')
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    estimated_delivery_time = models.DateTimeField(null=True, blank=True)
    actual_delivery_time = models.DateTimeField(null=True, blank=True)
    driver = models.ForeignKey('DeliveryDriver', null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class DeliveryDriver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    vehicle_type = models.CharField(max_length=50)
    license_plate = models.CharField(max_length=20)
    is_available = models.BooleanField(default=True)
    current_location = models.JSONField(default=dict)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.0)
    total_deliveries = models.PositiveIntegerField(default=0)

class DeliveryZone(models.Model):
    name = models.CharField(max_length=100)
    coordinates = models.PolygonField()  # For delivery area mapping
    base_fee = models.DecimalField(max_digits=10, decimal_places=2)
    per_km_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estimated_time = models.PositiveIntegerField(default=30)  # minutes
```

### API Endpoints
```python
# food_ordering/urls.py
urlpatterns = [
    # Restaurant Management
    path('api/restaurants/', views.RestaurantViewSet.as_view({'get': 'list'})),
    path('api/restaurants/<int:id>/', views.RestaurantDetailView.as_view()),
    
    # Menu Management
    path('api/restaurants/<int:restaurant_id>/menu/', views.MenuViewSet.as_view()),
    path('api/menu/<int:item_id>/', views.MenuItemDetail.as_view()),
    
    # Ordering
    path('api/orders/', views.OrderViewSet.as_view({'post': 'create'})),
    path('api/orders/<int:id>/', views.OrderDetailView.as_view()),
    path('api/orders/track/<str:tracking_code>/', views.OrderTrackingView.as_view()),
    
    # Customer Management
    path('api/customers/', views.CustomerViewSet.as_view()),
    path('api/customers/login/', views.CustomerLoginView.as_view()),
    
    # Delivery Management
    path('api/delivery/drivers/', views.DriverViewSet.as_view()),
    path('api/delivery/assign/', views.AssignDeliveryView.as_view()),
    path('api/delivery/update-location/', views.UpdateDriverLocation.as_view()),
]
```

## 🌐 Platform Integration Strategies

### 1. Mr D Food Integration
```python
# mr_d_integration.py
import requests

class MrDFoodAPI:
    def __init__(self, api_key, restaurant_id):
        self.api_key = api_key
        self.restaurant_id = restaurant_id
        self.base_url = "https://api.mrdfood.com/v1"
    
    def sync_menu(self, menu_items):
        """Sync menu items to Mr D Food platform"""
        endpoint = f"{self.base_url}/restaurants/{self.restaurant_id}/menu"
        
        payload = {
            "menu_items": [
                {
                    "id": item.id,
                    "name": item.name,
                    "description": item.description,
                    "price": float(item.price),
                    "category": item.category.name,
                    "image_url": item.image.url if item.image else None,
                    "available": item.is_available,
                    "preparation_time": item.preparation_time
                }
                for item in menu_items
            ]
        }
        
        response = requests.post(
            endpoint,
            json=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        
        return response.json()
    
    def receive_orders(self):
        """Receive orders from Mr D Food platform"""
        endpoint = f"{self.base_url}/restaurants/{self.restaurant_id}/orders/webhook"
        
        # This would be a webhook endpoint
        # Mr D Food sends orders to this endpoint
        pass
```

### 2. Uber Eats Integration
```python
# uber_eats_integration.py
class UberEatsAPI:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://api.uber.com/v1"
    
    def get_access_token(self):
        """Get OAuth access token for Uber Eats"""
        auth_response = requests.post(
            f"{self.base_url}/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "eats.deliveries"
            }
        )
        
        return auth_response.json().get("access_token")
    
    def sync_availability(self, restaurant_id):
        """Sync restaurant availability and operating hours"""
        token = self.get_access_token()
        
        endpoint = f"{self.base_url}/eats/stores/{restaurant_id}/availability"
        response = requests.put(
            endpoint,
            headers={"Authorization": f"Bearer {token}"},
            json={
                "is_active": True,
                "operating_hours": self.get_operating_hours()
            }
        )
        
        return response.json()
```

### 3. WhatsApp Ordering Bot
```python
# whatsapp_bot.py
from twilio.rest import Client
import re

class WhatsAppOrderBot:
    def __init__(self, account_sid, auth_token, phone_number):
        self.client = Client(account_sid, auth_token)
        self.phone_number = phone_number
        
    def parse_order_message(self, message_body):
        """Parse order from WhatsApp message"""
        # Example: "Hi, I'd like to order 2x burger meal and 1x coke"
        
        order_pattern = r'(\d+)x?\s*(.+?)(?:\s+and\s+(\d+)x?\s*(.+))?'
        match = re.search(order_pattern, message_body, re.IGNORECASE)
        
        if match:
            items = []
            
            # First item
            if match.group(1) and match.group(2):
                quantity = int(match.group(1))
                item_name = match.group(2).strip()
                items.append({"quantity": quantity, "item": item_name})
            
            # Second item (optional)
            if match.group(3) and match.group(4):
                quantity = int(match.group(3))
                item_name = match.group(4).strip()
                items.append({"quantity": quantity, "item": item_name})
            
            return items
        return None
    
    def send_order_confirmation(self, customer_phone, order_details):
        """Send order confirmation via WhatsApp"""
        message = f"""
🍔 *Order Confirmation*

Your order has been received:
📱 Items: {len(order_details['items'])}
💰 Total: R{order_details['total']}
⏱️ Est. delivery: {order_details['estimated_time']}
📍 Delivery to: {order_details['delivery_address']}

Reply *CONFIRM* to proceed or *CANCEL* to cancel.
        """
        
        self.client.messages.create(
            body=message,
            from_=f'whatsapp:{self.phone_number}',
            to=f'whatsapp:{customer_phone}'
        )
```

## 📊 Analytics and Reporting

### Sales Analytics Dashboard
```python
# analytics/views.py
from django.db.models import Sum, Count, Avg
from food_ordering.models import Order, MenuItem

def restaurant_analytics(request, restaurant_id):
    """Comprehensive analytics for restaurant owners"""
    
    # Sales metrics
    daily_sales = Order.objects.filter(
        restaurant__id=restaurant_id,
        created_at__date=today
    ).aggregate(
        total_orders=Count('id'),
        total_revenue=Sum('total_amount'),
        average_order_value=Avg('total_amount')
    )
    
    # Popular items
    popular_items = Order.objects.filter(
        restaurant__id=restaurant_id,
        created_at__date__gte=today - timedelta(days=30)
    ).values('items__name').annotate(
        order_count=Count('id'),
        total_revenue=Sum('total_amount')
    ).order_by('-order_count')[:10]
    
    # Delivery metrics
    delivery_times = Order.objects.filter(
        restaurant__id=restaurant_id,
        status='delivered'
    ).aggregate(
        avg_delivery_time=Avg(
            F('actual_delivery_time') - F('estimated_delivery_time')
        )
    )
    
    return Response({
        'daily_sales': daily_sales,
        'popular_items': popular_items,
        'delivery_metrics': delivery_times,
        'peak_hours': self.get_peak_hours(restaurant_id)
    })
```

## 🚀 Implementation Plan

### Phase 1: Core Infrastructure (2-3 weeks)
1. **Setup Django app structure**
   - Create `food_ordering` Django app
   - Define models for restaurants, menus, orders, delivery
   - Setup database migrations

2. **Build basic APIs**
   - Restaurant management endpoints
   - Menu CRUD operations
   - Basic order creation and tracking

3. **Admin interface**
   - Restaurant registration and management
   - Menu upload and management
   - Order management dashboard

### Phase 2: Customer Interface (3-4 weeks)
1. **Web ordering platform**
   - Restaurant discovery and search
   - Menu browsing and ordering
   - Customer registration and profiles
   - Order tracking

2. **Mobile app foundation**
   - React Native setup
   - Basic UI components
   - API integration

### Phase 3: Platform Integrations (4-5 weeks)
1. **Mr D Food integration**
   - API authentication and setup
   - Menu synchronization
   - Order webhook handling

2. **WhatsApp bot**
   - Twilio integration
   - Order parsing logic
   - Automated responses

3. **Uber Eats integration**
   - Partner application process
   - API integration
   - Menu and availability sync

### Phase 4: Advanced Features (6-8 weeks)
1. **Delivery management**
   - Driver app and tracking
   - Route optimization
   - Real-time notifications

2. **Analytics and reporting**
   - Sales analytics dashboard
   - Customer insights
   - Performance metrics

3. **Payment integration**
   - Yoco payment integration
   - SnapScan support
   - EFT and card payments

## 💰 Monetization Strategy

### Revenue Streams
1. **Commission Fees**
   - Restaurant commission: 10-15% per order
   - Delivery fee: R5-15 per delivery
   - Service fee: 2-3% of order value

2. **Premium Features**
   - Advanced analytics: R299/month
   - Priority delivery: R50/month
   - Marketing tools: R199/month

3. **Partnership Programs**
   - Mr D Food integration fee
   - Platform advertising revenue
   - Data insights and analytics

## 🔒 Security Considerations

### Data Protection
- POPIA compliance for South Africa
- Customer data encryption
- Secure payment processing
- GDPR-style data handling

### API Security
- JWT authentication for APIs
- Rate limiting per customer
- Input validation and sanitization
- SQL injection prevention

### Payment Security
- PCI DSS compliance
- Fraud detection
- Secure payment gateways
- Transaction logging

## 📈 Success Metrics

### KPIs to Track
1. **Order Volume**
   - Daily/weekly/monthly orders
   - Average order value
   - Customer retention rate

2. **Platform Performance**
   - API response times
   - System uptime
   - Error rates

3. **Business Growth**
   - New restaurant signups
   - Customer acquisition cost
   - Market penetration rate

This architecture provides a solid foundation for building a comprehensive food ordering system specifically tailored for the South African market, with integration capabilities for major platforms and local needs.
