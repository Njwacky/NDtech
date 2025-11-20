"""
OpenFoodFacts integration module for futurePOS
This module provides functions to fetch and process product data from OpenFoodFacts
"""

import openfoodfacts
import requests
from typing import Dict, Optional, Any
from .models import Product

def fetch_openfoodfacts_data(barcode: str) -> Optional[Dict[str, Any]]:
    """
    Fetch product data from OpenFoodFacts API
    
    Args:
        barcode: The product barcode to lookup
        
    Returns:
        Dictionary containing product data or None if not found
    """
    try:
        # Clean the barcode
        barcode = ''.join(c for c in barcode if c.isdigit())
        
        if len(barcode) not in [8, 12, 13, 14]:  # Common UPC/EAN lengths
            return None
        
        # Initialize API with user agent
        api = openfoodfacts.API(user_agent='futurePOS/1.0')
        
        # Fetch product from OpenFoodFacts
        product = api.product.get(barcode)
        
        if product:
            # Extract relevant product information
            product_data = product
            
            # Map OpenFoodFacts data to our format
            mapped_data = {
                'barcode': barcode,
                'name': extract_product_name(product_data),
                'description': extract_description(product_data),
                'price': '0.00',  # OpenFoodFacts doesn't provide pricing
                'category': map_openfoodfacts_category(product_data),
                'brand': product_data.get('brands', ''),
                'size': extract_size(product_data),
                'weight': extract_weight(product_data),
                'ingredients': product_data.get('ingredients_text', ''),
                'nutrients': extract_nutrients(product_data),
                'image_url': extract_image_url(product_data),
                'source': 'openfoodfacts',
                'raw_data': product_data
            }
            
            return mapped_data
        
        return None
        
    except Exception as e:
        print(f"Error fetching from OpenFoodFacts: {str(e)}")
        return None

def extract_product_name(product_data: Dict[str, Any]) -> str:
    """Extract product name from OpenFoodFacts data"""
    # Try different fields for product name
    name = (
        product_data.get('product_name', '') or
        product_data.get('product_name_en', '') or
        product_data.get('generic_name', '') or
        product_data.get('product_name_fr', '') or
        product_data.get('product_name_de', '') or
        product_data.get('product_name_es', '') or
        product_data.get('product_name_it', '') or
        product_data.get('product_name_nl', '') or
        'Unknown Product'
    )
    
    # Clean up the name
    if name and name.lower() not in ['unknown product', 'product', 'item']:
        # Remove common prefixes/suffixes that aren't useful
        name = name.replace('Product ', '').replace('Item ', '')
        name = name.strip()
        return name[:100] if name else 'Unknown Product'
    
    return 'Unknown Product'

def extract_description(product_data: Dict[str, Any]) -> str:
    """Extract product description from OpenFoodFacts data"""
    description_parts = []
    
    # Add ingredients if available
    if product_data.get('ingredients_text'):
        description_parts.append(f"Ingredients: {product_data['ingredients_text'][:200]}")
    
    # Add categories
    if product_data.get('categories'):
        description_parts.append(f"Categories: {product_data['categories']}")
    
    # Add countries if available
    if product_data.get('countries'):
        description_parts.append(f"Countries: {product_data['countries']}")
    
    return ' | '.join(description_parts)

def map_openfoodfacts_category(product_data: Dict[str, Any]) -> str:
    """Map OpenFoodFacts categories to our system categories"""
    categories = product_data.get('categories', '').lower()
    categories_tags = product_data.get('categories_tags', [])
    
    # Category mapping for OpenFoodFacts
    category_map = {
        'beverages': 'cold_drinks',
        'drinks': 'cold_drinks',
        'sugary-beverages': 'cold_drinks',
        'sodas': 'cold_drinks',
        'snacks': 'snacks_chips',
        'chips': 'snacks_chips',
        'crisps': 'snacks_chips',
        'confectioneries': 'sweets_treats',
        'candies': 'sweets_treats',
        'chocolates': 'sweets_treats',
        'sweets': 'sweets_treats',
        'dairies': 'dairy_eggs',
        'milk': 'dairy_eggs',
        'cheeses': 'dairy_eggs',
        'yogurts': 'dairy_eggs',
        'breads': 'bread_baked',
        'baked-goods': 'bread_baked',
        'pastries': 'bread_baked',
        'canned': 'canned_goods',
        'canned-foods': 'canned_goods',
        'beauty': 'personal_care',
        'cosmetics': 'personal_care',
        'toiletries': 'personal_care',
        'household': 'household_items',
        'cleaning': 'household_items',
        'stationery': 'stationery',
        'baby': 'baby_products',
        'frozen': 'frozen_goods',
        'frozen-foods': 'frozen_goods',
        'fruits': 'basic_groceries',
        'vegetables': 'basic_groceries',
        'groceries': 'basic_groceries'
    }
    
    # Check categories text first
    for keyword, category in category_map.items():
        if keyword in categories:
            return category
    
    # Check categories tags
    for tag in categories_tags:
        tag_clean = tag.replace('-', ' ')
        for keyword, category in category_map.items():
            if keyword in tag_clean:
                return category
    
    # Default category
    return 'basic_groceries'

def extract_size(product_data: Dict[str, Any]) -> str:
    """Extract product size information"""
    quantity = product_data.get('quantity', '')
    serving_size = product_data.get('serving_size', '')
    
    size_parts = []
    if quantity:
        size_parts.append(quantity)
    if serving_size:
        size_parts.append(f"Serving: {serving_size}")
    
    return ' | '.join(size_parts)

def extract_weight(product_data: Dict[str, Any]) -> str:
    """Extract product weight information"""
    net_weight = product_data.get('net_weight', '')
    gross_weight = product_data.get('gross_weight', '')
    
    weight_parts = []
    if net_weight:
        weight_parts.append(f"Net: {net_weight}")
    if gross_weight:
        weight_parts.append(f"Gross: {gross_weight}")
    
    return ' | '.join(weight_parts)

def extract_nutrients(product_data: Dict[str, Any]) -> Dict[str, str]:
    """Extract key nutritional information"""
    nutriments = product_data.get('nutriments', {})
    
    key_nutrients = {
        'energy': nutriments.get('energy-kcal_100g', ''),
        'protein': nutriments.get('proteins_100g', ''),
        'carbohydrates': nutriments.get('carbohydrates_100g', ''),
        'fat': nutriments.get('fat_100g', ''),
        'fiber': nutriments.get('fiber_100g', ''),
        'sugar': nutriments.get('sugars_100g', ''),
        'sodium': nutriments.get('sodium_100g', ''),
        'salt': nutriments.get('salt_100g', '')
    }
    
    return {k: str(v) + ('g' if 'kcal' not in k else 'kcal') if v else '' 
            for k, v in key_nutrients.items()}

def extract_image_url(product_data: Dict[str, Any]) -> str:
    """Extract the best available product image URL"""
    # Try different image sizes in order of preference
    image_keys = [
        'image_front_url',
        'image_front_small_url',
        'image_url',
        'image_nutrition_url'
    ]
    
    for key in image_keys:
        if product_data.get(key):
            return product_data[key]
    
    return ''

def search_products_by_name(query: str, limit: int = 10) -> list:
    """
    Search for products by name using OpenFoodFacts
    
    Args:
        query: Search query
        limit: Maximum number of results
        
    Returns:
        List of product summaries
    """
    try:
        # Initialize API with user agent
        api = openfoodfacts.API(user_agent='futurePOS/1.0')
        
        # Search for products using the correct method
        search_results = api.product.text_search(query, page_size=limit)
        
        products = []
        for product in search_results.products:
            product_summary = {
                'barcode': getattr(product, 'code', ''),
                'name': extract_product_name(vars(product)),
                'brand': getattr(product, 'brands', ''),
                'categories': getattr(product, 'categories', ''),
                'image_url': extract_image_url(vars(product))
            }
            products.append(product_summary)
        
        return products
        
    except Exception as e:
        print(f"Error searching OpenFoodFacts: {str(e)}")
        return []

def get_product_alternatives(barcode: str, limit: int = 5) -> list:
    """
    Find alternative products based on the same category
    
    Args:
        barcode: Original product barcode
        limit: Maximum number of alternatives
        
    Returns:
        List of alternative products
    """
    try:
        # First get the original product
        api = openfoodfacts.API(user_agent='futurePOS/1.0')
        original_product = api.product.get(barcode)
        
        if not original_product:
            return []
        
        product_data = original_product
        categories_tags = getattr(product_data, 'categories_tags', [])
        
        if not categories_tags:
            return []
        
        # Search for products in the same category
        search_query = categories_tags[0].replace('-', ' ')
        alternatives = search_products_by_name(search_query, limit + 1)
        
        # Remove the original product from alternatives
        alternatives = [p for p in alternatives if p['barcode'] != barcode]
        
        return alternatives[:limit]
        
    except Exception as e:
        print(f"Error finding alternatives: {str(e)}")
        return []
