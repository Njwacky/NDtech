# Food Ordering POS Integration Guide

## Overview

This integration allows your futurePOS system to scan and add food ordering menu items alongside regular POS products. The system uses the same barcode scanning technology but extends it to work with restaurant food items through intelligent pattern matching.

## Features

### 🔍 **Enhanced Barcode Scanning**
- **Dual System Support**: Scans both POS products and food ordering menu items
- **South African Barcode Patterns**: Recognizes common SA food product barcodes (600-603 prefix)
- **Intelligent Matching**: Uses category patterns and name matching to find relevant food items
- **Multiple Results**: Shows all matching items from both systems

### 🍽️ **Food Menu Browser**
- **Restaurant Selection**: Browse menus from multiple restaurants
- **Category Filtering**: Filter by food categories (Beverages, Main Courses, Desserts, etc.)
- **Search Functionality**: Search menu items by name or description
- **Dietary Information**: Display vegetarian, vegan, and gluten-free options
- **Preparation Times**: Shows food preparation estimates

### 🛒 **POS Integration**
- **Automatic Product Creation**: Converts menu items to POS products automatically
- **Category Mapping**: Maps food categories to POS categories
- **Barcode Generation**: Creates unique barcodes for food items
- **Stock Management**: Handles food item inventory separately

## Installation & Setup

### 1. Files Created
```
nano/food_ordering_integration.py    # Main integration logic
nano/templates/nano/food_scanner.html     # Enhanced scanner interface
nano/templates/nano/food_menu_browser.html  # Menu browser interface
nano/static/nano/food_scanner.js          # Scanner JavaScript
nano/urls.py                             # Updated URL patterns
```

### 2. URL Endpoints Added
```
/food/scanner/                    # Enhanced barcode scanner
/food/menu/                       # Restaurant menu browser
/api/food/scanner/lookup/{barcode}/  # Integrated lookup API
/api/food/add-to-pos/             # Add food item to POS API
```

### 3. Database Integration
- Uses existing `Product` model for POS items
- Integrates with `MenuItem` and `Restaurant` models from food ordering
- Creates POS products with `[FOOD]` prefix for identification

## Usage

### 📷 **Using the Food Scanner**

1. **Access the Scanner**: Navigate to `/food/scanner/`
2. **Choose Tab**: Select "Barcode Scanner" tab
3. **Scan Items**: Use camera or manual barcode entry
4. **View Results**: See both POS and food ordering matches
5. **Add to POS**: Click "Add to POS" for food items or "Add to Cart" for POS items

### 🍽️ **Using the Menu Browser**

1. **Access Browser**: Navigate to `/food/menu/`
2. **Select Restaurant**: Choose from dropdown of available restaurants
3. **Browse Menu**: View all available menu items with images and details
4. **Filter/Search**: Use category filters or search functionality
5. **Add Items**: Click "Add to POS" to convert menu items to POS products

### 📊 **Barcode Pattern Matching**

The system recognizes these South African barcode patterns:

| Prefix | Category | Examples |
|---------|-----------|----------|
| 6001007 | Coca-Cola | Soft drinks, sodas |
| 6001063 | Bread | Bread, buns, rolls |
| 6001085 | Chips | Crisps, snacks |
| 600106 | Dairy | Milk, cheese, yogurt |
| 600101 | Sweets | Chocolate, candy |
| 600102 | Beverages | Juices, drinks |
| 600103 | Snacks | Pies, pastries |
| 600104 | Frozen | Ice cream, frozen foods |
| 600105 | Canned | Tinned goods, jars |

## API Reference

### 🔍 **Barcode Lookup API**
```http
GET /api/food/scanner/lookup/{barcode}/
```

**Response Format:**
```json
{
  "success": true,
  "results": [
    {
      "id": 123,
      "name": "Coca-Cola",
      "price": 15.00,
      "category": "cold_drinks",
      "source": "pos_system",
      "stock": 50,
      "is_on_sale": false
    },
    {
      "id": 456,
      "name": "Classic Burger",
      "price": 65.00,
      "restaurant": "Test Restaurant",
      "preparation_time": 15,
      "source": "food_ordering",
      "match_type": "category_pattern",
      "is_vegetarian": false,
      "is_vegan": false
    }
  ],
  "total_found": 2
}
```

### ➕ **Add to POS API**
```http
POST /api/food/add-to-pos/
```

**Request Body:**
```json
{
  "menu_item_id": 456,
  "barcode": "6001007123456",
  "quantity": 1
}
```

**Response Format:**
```json
{
  "success": true,
  "product": {
    "id": 789,
    "name": "[FOOD] Classic Burger",
    "price": 65.00,
    "category": "basic_groceries",
    "barcode": "FOOD00000456",
    "stock": 999
  },
  "menu_item": {
    "name": "Classic Burger",
    "restaurant": "Test Restaurant",
    "preparation_time": 15
  }
}
```

## Category Mapping

Food ordering categories are automatically mapped to POS categories:

| Food Category | POS Category |
|--------------|--------------|
| beverages | cold_drinks |
| snacks | snacks_chips |
| desserts | sweets_treats |
| main course | basic_groceries |
| appetizers | snacks_chips |
| breakfast | bread_baked |
| dairy | dairy_eggs |

## Testing

### 🧪 **Run Test Suite**
```bash
python test_food_ordering_integration.py
```

This script will:
- Create test restaurant and menu items
- Test barcode pattern matching
- Test POS product creation
- Demonstrate API usage

### 📋 **Manual Testing Steps**

1. **Test Scanner Interface**:
   - Go to `/food/scanner/`
   - Test camera access
   - Scan test barcodes
   - Verify multiple results display

2. **Test Menu Browser**:
   - Go to `/food/menu/`
   - Select a restaurant
   - Browse menu items
   - Test search and filters

3. **Test Integration**:
   - Add food items to POS
   - Verify POS products are created
   - Check barcode generation

## Configuration

### 🔧 **Customize Barcode Patterns**

Edit `nano/food_ordering_integration.py` to add custom patterns:

```python
food_patterns = {
    '6001007': 'Coca-Cola',
    '6001063': 'Bread',
    '6001085': 'Chips',
    # Add your custom patterns here
}
```

### 🎨 **Customize UI**

Modify templates to match your branding:
- `nano/templates/nano/food_scanner.html`
- `nano/templates/nano/food_menu_browser.html`
- `nano/static/nano/food_scanner.js`

## Troubleshooting

### 🔍 **Common Issues**

**No food items found for barcode:**
- Check if restaurant has menu items
- Verify barcode matches SA patterns
- Ensure menu items are marked as available

**Camera not working:**
- Check browser permissions
- Try different camera (front/back)
- Ensure HTTPS connection

**POS product creation fails:**
- Verify user has manager role
- Check for duplicate products
- Ensure menu item exists

**Menu browser empty:**
- Create restaurants with menu items
- Check restaurant is active
- Verify user permissions

### 📝 **Debug Mode**

Enable debug logging by adding to settings:
```python
LOGGING = {
    'loggers': {
        'nano.food_ordering_integration': {
            'handlers': ['console'],
            'level': 'DEBUG',
        }
    }
}
```

## Security

### 🔒 **Permissions Required**
- **Scanner Access**: admin, manager, cashier roles
- **Add to POS**: admin, manager roles only
- **Menu Browser**: admin, manager, cashier roles

### 🛡️ **CSRF Protection**
All API endpoints include CSRF token validation for security.

## Performance

### ⚡ **Optimization Tips**
- **Database Indexes**: Ensure proper indexes on barcode fields
- **Caching**: Cache restaurant menu data
- **Lazy Loading**: Load menu items on demand
- **Image Optimization**: Compress menu item images

## Future Enhancements

### 🚀 **Planned Features**
- **Real-time Sync**: Live menu synchronization
- **Advanced Matching**: AI-powered barcode recognition
- **Mobile App**: Dedicated mobile scanner app
- **Inventory Sync**: Automatic stock level updates
- **Analytics**: Food ordering sales reports

## Support

### 📞 **Getting Help**
1. Check this guide for common solutions
2. Review test script output
3. Check browser console for JavaScript errors
4. Verify Django logs for backend issues

### 📚 **Related Documentation**
- [UPC Integration Guide](UPC_INTEGRATION_GUIDE.md)
- [Food Ordering Architecture](FOOD_ORDERING_SYSTEM_ARCHITECTURE.md)
- [POS System Documentation](nano/README.md)

---

## Quick Start Checklist

- [ ] Run test script to verify setup
- [ ] Access `/food/scanner/` and test barcode scanning
- [ ] Access `/food/menu/` and test menu browsing
- [ ] Add sample food items to POS
- [ ] Verify barcode pattern matching works
- [ ] Test with real product barcodes
- [ ] Train staff on new interface

**Integration Complete! 🎉**

Your futurePOS system now supports both traditional POS products and food ordering menu items through a unified scanning interface.
