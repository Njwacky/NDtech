"""
API v1 URL configuration for NDtech POS system
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_api_v1

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'users', views_api_v1.UserViewSet, basename='user')
router.register(r'user-profiles', views_api_v1.UserProfileViewSet, basename='userprofile')
router.register(r'products', views_api_v1.ProductViewSet, basename='product')
router.register(r'notifications', views_api_v1.NotificationViewSet, basename='notification')
router.register(r'error-logs', views_api_v1.ErrorLogViewSet, basename='errorlog')
router.register(r'security-logs', views_api_v1.SecurityAuditLogViewSet, basename='securityauditlog')
router.register(r'fcm-tokens', views_api_v1.FCMTokenViewSet, basename='fcmtoken')
router.register(r'airtime-products', views_api_v1.AirtimeProductViewSet, basename='airtimeproduct')
router.register(r'airtime-sales', views_api_v1.AirtimeSaleViewSet, basename='airtimesale')
router.register(r'warehouse-prices', views_api_v1.WarehousePriceViewSet, basename='warehouseprice')
router.register(r'price-comparisons', views_api_v1.PriceComparisonViewSet, basename='pricecomparison')
router.register(r'data-modification-logs', views_api_v1.DataModificationLogViewSet, basename='datamodificationlog')
router.register(r'admin-action-logs', views_api_v1.AdminActionLogViewSet, basename='adminactionlog')
router.register(r'api-call-logs', views_api_v1.APICallLogViewSet, basename='apicalllog')
router.register(r'sensitive-data-logs', views_api_v1.SensitiveDataAccessLogViewSet, basename='sensitivedatalog')

# API URLs
urlpatterns = [
    path('', include(router.urls)),
]
