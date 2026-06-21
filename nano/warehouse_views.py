# Warehouse Management Views
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse, HttpResponse
from django.db.models import Q, Count, Sum, Min
from django.core.paginator import Paginator
import pandas as pd
import json
import csv
from django.utils import timezone
from .models import WarehousePrice, PriceComparison

@login_required
def warehouse_import(request):
    """Import warehouse prices from CSV/Excel files"""
    # Allow only superusers or users with admin/manager roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager'])):
        return HttpResponseForbidden("You do not have permission to access this page.")
    
    if request.method == 'POST':
        if 'file' not in request.FILES:
            messages.error(request, 'Please select a file to upload')
            return redirect('warehouse_import')
        
        file = request.FILES['file']
        warehouse_name = request.POST.get('warehouse_name', '').strip()
        
        if not warehouse_name:
            messages.error(request, 'Warehouse name is required')
            return redirect('warehouse_import')
        
        # Check file extension
        file_extension = file.name.split('.')[-1].lower()
        if file_extension not in ['csv', 'xlsx', 'xls']:
            messages.error(request, 'Only CSV and Excel files are supported')
            return redirect('warehouse_import')
        
        try:
            # Process the file
            if file_extension == 'csv':
                df = pd.read_csv(file)
            else:  # Excel file
                df = pd.read_excel(file)
            
            # Validate required columns
            required_columns = ['product_name', 'price']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                messages.error(request, f'Missing required columns: {", ".join(missing_columns)}')
                return redirect('warehouse_import')
            
            # Process each row
            imported_count = 0
            skipped_count = 0
            
            for index, row in df.iterrows():
                try:
                    product_name = str(row['product_name']).strip()
                    price = float(row['price'])
                    barcode = str(row.get('barcode', '')).strip() if 'barcode' in row and pd.notna(row['barcode']) else None
                    category = str(row.get('category', '')).strip() if 'category' in row and pd.notna(row['category']) else None
                    stock_quantity = int(row['stock_quantity']) if 'stock_quantity' in row and pd.notna(row['stock_quantity']) else None
                    unit_size = str(row.get('unit_size', '')).strip() if 'unit_size' in row and pd.notna(row['unit_size']) else None
                    
                    if product_name and price > 0:
                        # Create or update warehouse price
                        warehouse_price, created = WarehousePrice.objects.update_or_create(
                            product_name=product_name,
                            warehouse_name=warehouse_name,
                            barcode=barcode,
                            defaults={
                                'price': price,
                                'category': category,
                                'stock_quantity': stock_quantity,
                                'unit_size': unit_size,
                                'imported_by': request.user,
                                'file_name': file.name
                            }
                        )
                        imported_count += 1
                    else:
                        skipped_count += 1
                        
                except (ValueError, TypeError) as e:
                    skipped_count += 1
                    continue
            
            # Run price comparison after import
            run_price_comparison()
            
            messages.success(request, f'Successfully imported {imported_count} products from {warehouse_name}. Skipped {skipped_count} invalid rows.')
            return redirect('warehouse_prices')
            
        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
            return redirect('warehouse_import')
    
    return render(request, 'nano/warehouse_import.html')

@login_required
def warehouse_prices(request):
    """Display warehouse prices with search and filtering"""
    # Allow only superusers or users with admin/manager/cashier roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return HttpResponseForbidden("You do not have permission to access this page.")
    
    # Get search parameters
    search_query = request.GET.get('search', '').strip()
    warehouse_filter = request.GET.get('warehouse', '').strip()
    
    # Build query
    warehouse_prices = WarehousePrice.objects.all()
    
    if search_query:
        warehouse_prices = warehouse_prices.filter(
            Q(product_name__icontains=search_query) |
            Q(barcode__icontains=search_query) |
            Q(category__icontains=search_query)
        )
    
    if warehouse_filter:
        warehouse_prices = warehouse_prices.filter(warehouse_name__icontains=warehouse_filter)
    
    # Get unique warehouse names for filter dropdown
    warehouse_names = WarehousePrice.objects.values_list('warehouse_name', flat=True).distinct().order_by('warehouse_name')
    
    # Order by most recent
    warehouse_prices = warehouse_prices.order_by('-date_imported')
    
    # Pagination
    paginator = Paginator(warehouse_prices, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'nano/warehouse_prices.html', {
        'warehouse_prices': page_obj,
        'warehouse_names': warehouse_names,
        'search_query': search_query,
        'warehouse_filter': warehouse_filter
    })
