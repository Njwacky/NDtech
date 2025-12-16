from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.shortcuts import redirect
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
import logging
import pandas as pd
import json
import re
import csv
import io
from decimal import Decimal, InvalidOperation
from .models import Product, Sale, UserProfile, PendingOrder, CompletedOrder, Notification, WarehousePrice, PriceComparison, FCMToken, DeviceConnection, ErrorLog, UserActivity
from .fcm_service import fcm_service, send_fcm_notification_to_user
from .brevo_service import send_receipt_email

# Configure logger
logger = logging.getLogger(__name__)

@login_required
def export_products_excel(request):
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
            
            # Add success message if messages framework is available
            try:
                from django.contrib import messages
                messages.success(request, f'Successfully exported {products.count()} products to Excel!')
            except:
                pass  # Messages not available, continue without message
            
            return response

        except Exception as e:
            # Add error message if messages framework is available
            try:
                from django.contrib import messages
                messages.error(request, f'Error exporting products: {str(e)}')
            except:
                pass  # Messages not available, continue without message
            
            return redirect('home')

    return redirect('home')
