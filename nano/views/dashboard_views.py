"""
Dashboard Views for NDtech POS System
Handles main dashboard and utility functions.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from ..models import Product, Notification
from ..fcm_service import send_fcm_notification_to_user


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
            notification = Notification.objects.create(
                title=f"Low Stock Alert: {product.name}",
                message=f"Low stock alert: {product.name} has only {product.stock} units remaining",
                notification_type='low_stock',
                target_role='admin',  # Default to admin role
                target_user=admin_user,
                product=product
            )

            # Send FCM notification
            send_fcm_notification_to_user(notification.target_user, notification.title, notification.message)


@login_required
def home(request):
    """POS Dashboard - Main view"""
    # POS Dashboard
    products = Product.objects.all()

    # Check for low stock products when dashboard is loaded
    check_low_stock()

    return render(request, 'nano/home.html', {'products': products})
