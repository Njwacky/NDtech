from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

# Create a router for the food ordering API endpoints
router = DefaultRouter()
router.register(r'restaurants', views.RestaurantViewSet)
router.register(r'menu', views.MenuViewSet)
router.register(r'orders', views.OrderViewSet)
router.register(r'customers', views.CustomerViewSet)
router.register(r'drivers', views.DeliveryDriverViewSet)

app_name = 'food_ordering'

urlpatterns = [
    # API endpoints
    path('api/v1/', include(router.urls)),
    
    # Direct API views
    path('api/v1/restaurants/<int:restaurant_id>/', views.RestaurantDetailView.as_view()),
    path('api/v1/orders/', views.OrderViewSet.as_view({'post': 'create'})),
    path('api/v1/orders/<int:order_id>/', views.OrderDetailView.as_view()),
    path('api/v1/orders/track/<str:tracking_code>/', views.order_tracking),
    path('api/v1/customers/', views.CustomerViewSet.as_view({'get': 'list'})),
    path('api/v1/nearby/', views.nearby_restaurants),
    
    # Driver management
    path('api/v1/drivers/', views.DeliveryDriverViewSet.as_view()),
    path('api/v1/drivers/update-location/', views.update_driver_location),
    
    # Web interface views
    path('restaurants/', views.RestaurantListView.as_view(), name='restaurant-list'),
    path('restaurants/<int:restaurant_id>/', views.RestaurantDetailView.as_view(), name='restaurant-detail'),
    path('orders/track/<str:tracking_code>/', views.OrderTrackingView.as_view(), name='order-tracking'),
    path('analytics/<int:restaurant_id>/', views.restaurant_analytics, name='restaurant-analytics'),
]
