# Excel Export Guide for Products

## Overview
Your NDtech application includes a comprehensive Excel export feature that allows you to export all product data from your database to a formatted Excel file.

## Features
The Excel export includes the following product information:
- **Basic Information**: ID, Name, Description, Category
- **Pricing Details**: Regular Price, Current Price, Sale Price, Discount Information
- **Stock Information**: Current Stock levels
- **Dates**: Date Added, Expiry Date, Sale Start/End Dates
- **Sales Analytics**: Total Sales Count, Total Quantity Sold, Total Revenue, Average Sale Price
- **Status Indicators**: Is Expired, Is On Sale, Is Currently On Sale

## How to Use

### Method 1: Via the Add Stock Page (Recommended)
1. Log in to your NDtech application as a superuser, admin, or manager
2. Navigate to the "Add Stock" page
3. Click the "Export Products" button (Excel icon) in the toggle buttons section
4. The Excel file will automatically download to your computer with a success notification

### Method 2: Via the Home Dashboard
1. Log in to your NDtech application as a superuser, admin, or manager
2. Navigate to the home page (dashboard)
3. Click the "Export Products" button (Excel icon) in the action buttons section
4. The Excel file will automatically download to your computer

### Method 3: Direct URL Access
You can also access the export directly via URL:
```
/export/products/excel/
```

### Method 4: Keyboard Shortcut
On the Add Stock page, you can use **Ctrl+E** to trigger the export quickly.

### Method 5: Programmatic Access
For API integration, you can make a GET request to the export endpoint:
```python
import requests

# Replace with your actual domain and authentication
url = "https://your-domain.com/export/products/excel/"
headers = {
    'Authorization': 'Bearer your-token',
    # Or use session authentication
}

response = requests.get(url, headers=headers)
if response.status_code == 200:
    with open('products_export.xlsx', 'wb') as f:
        f.write(response.content)
```

## File Format
- **File Type**: Excel (.xlsx)
- **File Naming**: `products_export_YYYYMMDD_HHMMSS.xlsx` (timestamped)
- **Sheet Name**: "Products"
- **Formatting**: Auto-adjusted column widths for better readability

## Security & Permissions
Only users with the following roles can export products:
- Superusers
- Users with 'admin' role
- Users with 'manager' role

## Data Included
The export contains comprehensive product data:

| Column | Description |
|--------|-------------|
| ID | Unique product identifier |
| Name | Product name |
| Description | Product description |
| Category | Product category |
| Regular Price | Standard price |
| Current Stock | Available quantity |
| Barcode | Product barcode (if available) |
| Date Added | When product was added to system |
| Expiry Date | Product expiration date |
| Is Expired | Yes/No indicator |
| Is On Sale | Yes/No indicator |
| Sale Price | Discounted price (if on sale) |
| Sale Start Date | When sale period starts |
| Sale End Date | When sale period ends |
| Is Currently On Sale | Yes/No for active sales |
| Current Price | Effective price (regular or sale) |
| Discount Percentage | Percentage discount (if applicable) |
| Discount Amount | Monetary discount (if applicable) |
| Total Sales Count | Number of sales transactions |
| Total Quantity Sold | Total units sold |
| Total Revenue | Total revenue from sales |
| Average Sale Price | Average price per sale |

## Troubleshooting

### Common Issues
1. **Permission Denied**: Ensure you're logged in as admin/manager/superuser
2. **Empty File**: Check if you have products in your database
3. **Download Fails**: Check your browser's download settings

### Error Messages
- "You do not have permission to access this page" → Contact your system administrator
- "Error exporting products" → Check server logs for detailed error information

## Technical Details

### Dependencies
- Python 3.8+
- Django 4.0+
- pandas (for data processing)
- openpyxl (for Excel file generation)

### File Size
The export can handle thousands of products efficiently. For very large datasets (>10,000 products), consider:
- Using filters to export specific categories
- Scheduling exports during off-peak hours
- Implementing pagination for very large datasets

## Customization
The export functionality can be customized by modifying the `export_products_excel` function in `nano/views_export.py`:
- Add/remove columns
- Change formatting
- Add filters
- Modify file naming convention

## Support
For technical support or customization requests, please contact your development team.
