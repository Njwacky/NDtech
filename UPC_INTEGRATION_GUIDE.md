# UPC Database API Integration Guide

## Overview

This guide documents the UPC Database API integration for the futurePOS system. The integration allows you to:

- Fetch product details using UPC/EAN barcodes
- Automatically create products in your inventory
- Add stock to existing products
- Maintain a history of UPC lookups

## Features

### 🚀 Core Features

1. **UPC Lookup**: Enter or scan UPC/EAN barcodes to fetch product information
2. **Automatic Product Creation**: Create new products from UPC data (managers only)
3. **Stock Management**: Add stock to existing products
4. **Category Mapping**: Automatically map API categories to your system categories
5. **History Tracking**: View all products added via UPC lookup
6. **Role-Based Access**: Different permissions for different user roles

### 🔧 Technical Features

- **API Integration**: Uses UPC Database API with your API key
- **Error Handling**: Comprehensive error handling for API failures
- **Data Validation**: Validates and cleans UPC data before processing
- **Mobile Responsive**: Works on desktop and mobile devices
- **Barcode Scanner Support**: Compatible with USB barcode scanners

## Installation & Setup

### 1. Prerequisites

- Python 3.8+
- Django 4.0+
- Requests library
- Valid UPC Database API key

### 2. Install Dependencies

```bash
pip install requests
```

### 3. Configuration

The API key is already configured in `nano/upc_views.py`:

```python
UPC_API_KEY = "0EF8A07BB103C1A35F6CAF9B64535DD5"
UPC_API_BASE_URL = "https://api.upcdatabase.org"
```

### 4. URL Routes

The following URLs are added to `nano/urls.py`:

```python
# UPC Lookup URLs
path('upc/lookup/', upc_views.upc_lookup, name='upc_lookup'),
path('upc/history/', upc_views.upc_history, name='upc_history'),
path('api/upc/lookup/', upc_views.api_upc_lookup, name='api_upc_lookup'),
```

## Usage Guide

### 📱 For All Users (Admin, Manager, Cashier)

#### 1. Access UPC Lookup

Navigate to **UPC Lookup** in the main navigation menu or go to:
```
http://127.0.0.1:8000/upc/lookup/
```

#### 2. Enter UPC Code

- Type the UPC/EAN barcode manually (8, 12, 13, or 14 digits)
- Or use a USB barcode scanner to scan the barcode
- Click "Lookup" or press Enter

#### 3. View Product Information

The system will display:
- Product name and image (if available)
- Price, brand, size, category
- Description and other details
- Barcode number

#### 4. Add Stock (for existing products)

If the product already exists in your inventory:
- Enter the quantity to add
- Click "Add to Stock"
- Confirmation shows new stock level

### 👨‍💼 For Managers Only

#### Create New Products

If the product doesn't exist in your inventory:
- Fill in the product details (pre-populated from API)
- Set initial stock quantity
- Choose category
- Set expiry date (optional)
- Click "Create Product"

### 📊 View History

Navigate to **UPC History** to see:
- All products added via UPC lookup
- Search and filter options
- Quick actions for each product
- Statistics and insights

## Supported Barcode Formats

| Format | Digits | Example |
|--------|--------|---------|
| UPC-A | 12 | 042100005264 |
| UPC-E | 8 | 01234567 |
| EAN-13 | 13 | 4006381333931 |
| EAN-8 | 8 | 96385074 |

## Category Mapping

The system automatically maps API categories to your inventory categories:

| API Category | System Category |
|--------------|----------------|
| food, grocery | basic_groceries |
| snack, chips | snacks_chips |
| drink, soda | cold_drinks |
| candy, sweet | sweets_treats |
| dairy, milk | dairy_eggs |
| bread, bakery | bread_baked |
| canned | canned_goods |
| personal, beauty | personal_care |
| household, cleaning | household_items |
| stationery | stationery |
| baby | baby_products |
| frozen | frozen_goods |
| airtime, mobile | airtime_data |

## API Integration Details

### Endpoint

```
GET https://api.upcdatabase.org/product/{upc_code}
```

### Headers

```
Authorization: Bearer {API_KEY}
Content-Type: application/json
```

### Response Format

```json
{
  "title": "Product Name",
  "description": "Product description",
  "price": "10.99",
  "category": "Food",
  "brand": "Brand Name",
  "size": "500ml",
  "image_url": "https://example.com/image.jpg"
}
```

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "No product found" | Invalid UPC code | Verify the barcode and try again |
| "API rate limit exceeded" | Too many requests | Wait a few minutes and try again |
| "Network error" | Connection issues | Check internet connection |
| "Invalid request format" | Malformed UPC | Ensure only digits are entered |

### Error Messages

The system provides clear error messages:
- ✅ Success messages for completed actions
- ⚠️ Warning messages for non-critical issues
- ❌ Error messages for failed operations

## Testing

### Run the Test Suite

```bash
python test_upc_integration.py
```

### Test Coverage

1. **Direct API Call**: Tests UPC API connectivity
2. **Category Mapping**: Validates category conversion
3. **View Access**: Tests page accessibility
4. **Product Creation**: Tests product creation workflow
5. **User Permissions**: Tests role-based access

### Manual Testing

1. **Test UPC Codes**:
   - `042100005264` - Common test product
   - `041196910018` - Another test product
   - Try your own product barcodes

2. **Test User Roles**:
   - Admin: Full access
   - Manager: Can create products
   - Cashier: Can add stock only

## Troubleshooting

### Common Issues

#### 1. API Not Responding

**Symptoms**: Loading spinner keeps spinning, timeout errors

**Solutions**:
- Check internet connection
- Verify API key is valid
- Check API service status
- Try a different UPC code

#### 2. Products Not Creating

**Symptoms**: Form submission fails, validation errors

**Solutions**:
- Ensure all required fields are filled
- Check user has manager permissions
- Verify barcode format is correct
- Check for duplicate products

#### 3. Barcode Scanner Not Working

**Symptoms**: Scanner input not being recognized

**Solutions**:
- Ensure scanner is properly connected
- Check scanner is in keyboard wedge mode
- Test scanner in Notepad first
- Check for interference with other USB devices

### Debug Mode

Enable debug mode by adding to settings:

```python
DEBUG = True
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'nano': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## Performance Considerations

### API Rate Limits

- The UPC Database API has rate limits
- Implement caching for frequently accessed products
- Use bulk operations for multiple lookups

### Database Optimization

- Index the barcode field for faster lookups
- Regular cleanup of historical data
- Monitor database size with large product catalogs

### Caching Strategy

Consider implementing Redis caching for:
- Frequently accessed UPC data
- Category mappings
- API responses

## Security Considerations

### API Key Protection

- API key is stored in server-side code
- Never expose API key in client-side JavaScript
- Consider environment variables for production

### Data Validation

- All user input is validated and sanitized
- UPC codes are cleaned and formatted
- Product data is validated before database insertion

### Access Control

- Role-based permissions enforced
- Authentication required for all features
- Audit trail maintained for all actions

## Future Enhancements

### Planned Features

1. **Bulk UPC Import**: Import multiple UPC codes from CSV
2. **Mobile App**: Native mobile app for scanning
3. **Barcode Image Recognition**: Scan barcodes using camera
4. **Price Comparison**: Compare prices across suppliers
5. **Inventory Alerts**: Low stock alerts for UPC products

### Integration Opportunities

1. **Supplier APIs**: Direct integration with supplier catalogs
2. **Accounting Systems**: Sync with accounting software
3. **E-commerce Platforms**: Export to online stores
4. **Analytics**: Advanced reporting and insights

## Support

### Documentation

- This guide: `UPC_INTEGRATION_GUIDE.md`
- Test script: `test_upc_integration.py`
- Code comments in `nano/upc_views.py`

### Contact

For issues or questions:
1. Check this documentation
2. Run the test script
3. Review Django logs
4. Contact system administrator

---

## Quick Start Checklist

- [ ] Install requests library: `pip install requests`
- [ ] Verify API key is set in `upc_views.py`
- [ ] Run test suite: `python test_upc_integration.py`
- [ ] Start Django server: `python manage.py runserver`
- [ ] Navigate to: `http://127.0.0.1:8000/upc/lookup/`
- [ ] Test with sample UPC: `042100005264`
- [ ] Create test product (manager account required)
- [ ] Verify product appears in inventory
- [ ] Check UPC history page

🎉 Your UPC integration is now ready to use!
