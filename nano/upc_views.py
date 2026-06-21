import requests
import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Product, UserProfile
from .openfoodfacts_integration import fetch_openfoodfacts_data

# UPC Database API Configuration
UPC_API_KEY = "0EF8A07BB103C1A35F6CAF9B64535DD5"
UPC_API_BASE_URL = "https://api.upcdatabase.org"

def suggest_category_from_barcode(barcode):
    """Suggest category based on barcode patterns"""
    # South African barcode patterns (600-603 prefix)
    if barcode.startswith('600'):
        # Common SA product patterns
        if barcode.startswith('6001007'):  # Coca-Cola products
            return 'cold_drinks'
        elif barcode.startswith('6001063'):  # Bread/bakery products
            return 'bread_baked'
        elif barcode.startswith('6001085'):  # Chips/snacks
            return 'snacks_chips'
        elif barcode.startswith('600106'):  # Dairy products
            return 'dairy_eggs'
    
    # Default fallback
    return 'basic_groceries'

@login_required
def upc_lookup_detail(request, barcode):
    """Direct barcode lookup via URL - shows product details for a specific barcode"""
    # Allow only superusers or users with admin/manager/cashier roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return HttpResponseForbidden("You do not have permission to access this page.")
    
    # Check if user is manager for Add Product functionality
    is_manager = request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager'])
    
    try:
        # First check if product exists in local database
        existing_product = Product.objects.filter(barcode=barcode).first()
        
        if existing_product:
            # Product found in local database
            product_data = {
                'id': existing_product.id,
                'name': existing_product.name,
                'barcode': existing_product.barcode,
                'price': str(existing_product.price),
                'stock': existing_product.stock,
                'category': existing_product.category,
                'description': existing_product.description,
                'expiry_date': existing_product.expiry_date.strftime('%Y-%m-%d') if existing_product.expiry_date else None,
                'source': 'local_database'
            }
            
            return render(request, 'nano/upc_lookup.html', {
                'is_manager': is_manager,
                'product_data': product_data,
                'upc_code': barcode,
                'existing_product': existing_product,
                'direct_lookup': True
            })
        
        # If not found locally, try UPC database API
        upc_data = fetch_upc_data(barcode)
        
        if upc_data:
            # Product found in UPC database
            return render(request, 'nano/upc_lookup.html', {
                'is_manager': is_manager,
                'product_data': upc_data,
                'upc_code': barcode,
                'existing_product': None,
                'direct_lookup': True
            })
        else:
            # No product found - show manual entry form with barcode
            messages.warning(request, f'No product found for barcode: {barcode}. You can add this product manually.')
            
            # Pre-fill form with barcode and suggest category based on barcode patterns
            suggested_category = suggest_category_from_barcode(barcode)
            
            manual_product_data = {
                'barcode': barcode,
                'name': '',
                'price': '0.00',
                'category': suggested_category,
                'description': f'Manually entered product with barcode {barcode}',
                'stock': '1'
            }
            
            return render(request, 'nano/upc_lookup.html', {
                'is_manager': is_manager,
                'product_data': manual_product_data,
                'upc_code': barcode,
                'existing_product': None,
                'manual_entry': True,
                'direct_lookup': True
            })
            
    except Exception as e:
        messages.error(request, f'Error looking up barcode: {str(e)}')
        return render(request, 'nano/upc_lookup.html', {
            'is_manager': is_manager,
            'upc_code': barcode,
            'direct_lookup': True,
            'error': True
        })

@login_required
def upc_lookup(request):
    """UPC lookup interface for adding products to stock"""
    # Allow only superusers or users with admin/manager/cashier roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return HttpResponseForbidden("You do not have permission to access this page.")
    
    # Check if user is manager for Add Product functionality
    is_manager = request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager'])
    
    if request.method == 'POST':
        action = request.POST.get('action', '')
        
        if action == 'lookup_upc':
            upc_code = request.POST.get('upc_code', '').strip()
            
            if not upc_code:
                messages.error(request, 'UPC code is required')
                return render(request, 'nano/upc_lookup.html', {'is_manager': is_manager})
            
            try:
                product_data = fetch_upc_data(upc_code)
                
                if product_data:
                    # Check if product already exists in database
                    existing_product = None
                    if 'barcode' in product_data and product_data['barcode']:
                        existing_product = Product.objects.filter(barcode=product_data['barcode']).first()
                    
                    return render(request, 'nano/upc_lookup.html', {
                        'is_manager': is_manager,
                        'product_data': product_data,
                        'upc_code': upc_code,
                        'existing_product': existing_product
                    })
                else:
                    # No product found - show manual entry form with barcode
                    messages.warning(request, f'No product found for UPC code: {upc_code}. You can add this product manually.')
                    
                    # Pre-fill form with barcode and suggest category based on barcode patterns
                    suggested_category = suggest_category_from_barcode(upc_code)
                    
                    manual_product_data = {
                        'barcode': upc_code,
                        'name': '',
                        'price': '0.00',
                        'category': suggested_category,
                        'description': f'Manually entered product with barcode {upc_code}',
                        'stock': '1'
                    }
                    
                    return render(request, 'nano/upc_lookup.html', {
                        'is_manager': is_manager,
                        'product_data': manual_product_data,
                        'upc_code': upc_code,
                        'existing_product': None,
                        'manual_entry': True
                    })
                    
            except Exception as e:
                messages.error(request, f'Error fetching product data: {str(e)}')
        
        elif action == 'add_to_stock':
            # Add product to stock
            product_id = request.POST.get('product_id')
            quantity_str = request.POST.get('quantity', '').strip()
            
            if not product_id:
                messages.error(request, 'Product ID is required')
                return redirect('upc_lookup')
            
            if not quantity_str:
                messages.error(request, 'Quantity is required')
                return redirect('upc_lookup')
            
            try:
                quantity = int(quantity_str)
                if quantity <= 0:
                    messages.error(request, 'Quantity must be greater than 0')
                    return redirect('upc_lookup')
                
                product = Product.objects.get(id=product_id)
                product.stock += quantity
                product.save()
                
                messages.success(request, f'Added {quantity} units to {product.name}. New stock: {product.stock}')
                
            except Product.DoesNotExist:
                messages.error(request, 'Product not found')
            except ValueError:
                messages.error(request, 'Invalid quantity')
            
            return redirect('upc_lookup')
        
        elif action == 'create_product':
            # Create new product from UPC data
            if not is_manager:
                return HttpResponseForbidden("Only managers can create new products.")
            
            name = request.POST.get('name', '').strip()
            price_str = request.POST.get('price', '').strip()
            description = request.POST.get('description', '').strip()
            category = request.POST.get('category', '').strip()
            barcode = request.POST.get('barcode', '').strip()
            expiry_date_str = request.POST.get('expiry_date', '').strip()
            stock_str = request.POST.get('stock', '').strip()
            
            errors = {}
            
            if not name:
                errors['name'] = 'Product name is required'
            
            if not price_str:
                errors['price'] = 'Price is required'
            else:
                try:
                    price = float(price_str)
                    if price <= 0:
                        errors['price'] = 'Price must be greater than 0'
                except ValueError:
                    errors['price'] = 'Price must be a valid number'
            
            if not category:
                errors['category'] = 'Category is required'
            elif category not in dict(Product.CATEGORY_CHOICES):
                errors['category'] = 'Invalid category'
            
            if not stock_str:
                errors['stock'] = 'Stock quantity is required'
            else:
                try:
                    stock = int(stock_str)
                    if stock < 0:
                        errors['stock'] = 'Stock cannot be negative'
                except ValueError:
                    errors['stock'] = 'Stock must be a valid number'
            
            if errors:
                for field, error in errors.items():
                    messages.error(request, f'{field.replace("_", " ").title()}: {error}')
                
                # Return with form data to refill
                product_data = {
                    'name': name,
                    'price': price_str,
                    'description': description,
                    'category': category,
                    'barcode': barcode,
                    'expiry_date': expiry_date_str,
                    'stock': stock_str
                }
                
                return render(request, 'nano/upc_lookup.html', {
                    'is_manager': is_manager,
                    'product_data': product_data,
                    'create_mode': True
                })
            
            # Parse expiry date if provided
            expiry_date = None
            if expiry_date_str:
                try:
                    expiry_date = timezone.datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
                    if expiry_date <= timezone.now().date():
                        messages.warning(request, 'Expiry date is in the past, but product will be created anyway.')
                except ValueError:
                    messages.warning(request, 'Invalid date format, expiry date not set.')
                    expiry_date = None
            
            # Create the product
            product = Product.objects.create(
                name=name,
                price=price,
                description=description,
                category=category,
                barcode=barcode if barcode else None,
                expiry_date=expiry_date,
                stock=stock
            , workspace=workspace)
            
            messages.success(request, f'Product "{name}" created successfully with {stock} units in stock!')
            return redirect('upc_lookup')
    
    return render(request, 'nano/upc_lookup.html', {'is_manager': is_manager})

def fetch_upc_data(upc_code):
    """Fetch product data from multiple sources (UPC database API, then OpenFoodFacts)"""
    try:
        # Clean the UPC code (remove spaces, hyphens, etc.)
        upc_code = ''.join(c for c in upc_code if c.isdigit())
        
        if len(upc_code) not in [8, 12, 13, 14]:  # Common UPC/EAN lengths
            return None
        
        # First try UPC database API
        upc_result = None
        try:
            url = f"{UPC_API_BASE_URL}/product/{upc_code}"
            headers = {
                'Authorization': f'Bearer {UPC_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract product name with better fallbacks
                name = data.get('title', data.get('name', data.get('product_name', '')))
                if not name or name.lower() in ['unknown product', 'product', 'item']:
                    name = None  # Will try OpenFoodFacts
                
                # Only proceed if we have a meaningful product name
                if name:
                    # Map API response to our product structure
                    product_data = {
                        'barcode': upc_code,
                        'name': name[:100],  # Limit to 100 chars
                        'description': data.get('description', ''),
                        'price': data.get('price', '0.00'),
                        'category': map_category(data.get('category', '')),
                        'brand': data.get('brand', ''),
                        'size': data.get('size', ''),
                        'color': data.get('color', ''),
                        'weight': data.get('weight', ''),
                        'currency': data.get('currency', 'ZAR'),
                        'image_url': data.get('image_url', ''),
                        'source': 'upc_database',
                        'raw_data': data  # Store raw data for debugging
                    }
                    
                    # Try to extract price from various fields
                    if not product_data['price'] or product_data['price'] == '0.00':
                        # Look for price in other fields
                        for field in ['retail_price', 'msrp', 'cost']:
                            if field in data and data[field]:
                                try:
                                    price_str = str(data[field]).replace('$', '').replace('R', '').replace(',', '')
                                    product_data['price'] = float(price_str)
                                    if product_data['price'] > 0:
                                        break
                                except (ValueError, TypeError):
                                    continue
                    
                    # Only return if we have meaningful data
                    if (product_data['name'] and 
                        product_data['name'].lower() not in ['unknown product', 'product', 'item'] and
                        len(product_data['name']) > 3):
                        upc_result = product_data
                
            elif response.status_code == 429:
                print("UPC database API rate limit exceeded. Trying OpenFoodFacts...")
            elif response.status_code == 404:
                print(f"UPC {upc_code} not found in UPC database. Trying OpenFoodFacts...")
            else:
                print(f"UPC database returned status {response.status_code}. Trying OpenFoodFacts...")
                
        except requests.RequestException as e:
            print(f"UPC database API error: {str(e)}. Trying OpenFoodFacts...")
        
        # If UPC database didn't return good data, try OpenFoodFacts
        if not upc_result:
            try:
                openfoodfacts_data = fetch_openfoodfacts_data(upc_code)
                if openfoodfacts_data and openfoodfacts_data.get('name'):
                    # Ensure OpenFoodFacts data has meaningful content
                    if (openfoodfacts_data['name'].lower() not in ['unknown product', 'product', 'item'] and
                        len(openfoodfacts_data['name']) > 3):
                        return openfoodfacts_data
            except Exception as e:
                print(f"OpenFoodFacts error: {str(e)}")
        
        # Return the best result we have
        return upc_result if upc_result else None
            
    except Exception as e:
        print(f"Error processing UPC data: {str(e)}")
        return None

def map_category(api_category):
    """Map API category to our system categories"""
    if not api_category:
        return 'basic_groceries'
    
    category_lower = api_category.lower()
    
    # Category mapping
    category_map = {
        'food': 'basic_groceries',
        'grocery': 'basic_groceries',
        'snack': 'snacks_chips',
        'chips': 'snacks_chips',
        'drink': 'cold_drinks',
        'beverage': 'cold_drinks',
        'soda': 'cold_drinks',
        'candy': 'sweets_treats',
        'sweet': 'sweets_treats',
        'chocolate': 'sweets_treats',
        'dairy': 'dairy_eggs',
        'milk': 'dairy_eggs',
        'cheese': 'dairy_eggs',
        'bread': 'bread_baked',
        'bakery': 'bread_baked',
        'canned': 'canned_goods',
        'personal': 'personal_care',
        'beauty': 'personal_care',
        'soap': 'personal_care',
        'household': 'household_items',
        'cleaning': 'household_items',
        'stationery': 'stationery',
        'baby': 'baby_products',
        'frozen': 'frozen_goods',
        'airtime': 'airtime_data',
        'mobile': 'airtime_data'
    }
    
    # Check for keyword matches
    for keyword, category in category_map.items():
        if keyword in category_lower:
            return category
    
    # Default category
    return 'basic_groceries'

@csrf_exempt
@login_required
def api_upc_lookup(request):
    """API endpoint for UPC lookup (AJAX)"""
    # Allow only superusers or users with admin/manager/cashier roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            upc_code = data.get('upc_code', '').strip()
            
            if not upc_code:
                return JsonResponse({'success': False, 'error': 'UPC code is required'})
            
            product_data = fetch_upc_data(upc_code)
            
            if product_data:
                # Check if product already exists
                existing_product = None
                if product_data.get('barcode'):
                    existing_product = Product.objects.filter(barcode=product_data['barcode']).first()
                    if existing_product:
                        product_data['existing_product'] = {
                            'id': existing_product.id,
                            'name': existing_product.name,
                            'price': str(existing_product.price),
                            'stock': existing_product.stock
                        }
                
                return JsonResponse({'success': True, 'product_data': product_data})
            else:
                return JsonResponse({'success': False, 'error': 'No product found for this UPC code'})
                
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid request format'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def barcode_scanner(request):
    """Barcode scanner interface using device camera"""
    # Allow only superusers or users with admin/manager/cashier roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return HttpResponseForbidden("You do not have permission to access this page.")
    
    return render(request, 'nano/barcode_scanner.html')

@csrf_exempt
@login_required
def api_upc_lookup_detail(request, barcode):
    """API endpoint for detailed barcode lookup (for scanner)"""
    # Allow only superusers or users with admin/manager/cashier roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    if request.method == 'GET':
        try:
            # First check if product exists in local database
            product = Product.objects.filter(barcode=barcode).first()
            
            if product:
                product_data = {
                    'id': product.id,
                    'name': product.name,
                    'barcode': product.barcode,
                    'price': float(product.price),
                    'stock': product.stock,
                    'category': product.get_category_display(),
                    'description': product.description,
                    'expiry_date': product.expiry_date.strftime('%Y-%m-%d') if product.expiry_date else None,
                    'source': 'local_database'
                }
                return JsonResponse({'success': True, 'product': product_data})
            
            # If not found locally, try UPC database API
            upc_data = fetch_upc_data(barcode)
            
            if upc_data:
                # Convert UPC data to product format
                product_data = {
                    'name': upc_data.get('name', 'Unknown Product'),
                    'barcode': upc_data.get('barcode', barcode),
                    'price': float(upc_data.get('price', '0.00')),
                    'stock': 0,  # Not in local database
                    'category': upc_data.get('category', 'basic_groceries'),
                    'description': upc_data.get('description', ''),
                    'source': 'upc_database',
                    'brand': upc_data.get('brand', ''),
                    'size': upc_data.get('size', ''),
                    'image_url': upc_data.get('image_url', '')
                }
                return JsonResponse({'success': True, 'product': product_data})
            else:
                return JsonResponse({'success': False, 'message': f'No product found for barcode: {barcode}'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def upc_history(request):
    """Show history of UPC lookups and added products"""
    # Allow only superusers or users with admin/manager/cashier roles
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['admin', 'manager', 'cashier'])):
        return HttpResponseForbidden("You do not have permission to access this page.")
    
    # Get recently added products with barcodes
    recent_products = Product.objects.filter(
        barcode__isnull=False
    ).exclude(
        barcode=''
    ).order_by('-date_added')[:50]
    
    return render(request, 'nano/upc_history.html', {
        'recent_products': recent_products
    })
