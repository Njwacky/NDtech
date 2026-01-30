// Category examples for better user guidance
const categoryExamples = {
    'snacks_chips': 'Lays, Simba, Nik Naks, Cheese Curls',
    'cold_drinks': 'Coca Cola, Fanta, Sprite, Pepsi, Stoney',
    'sweets_treats': 'Chocolate, Candy, Gum, Biscuits, Cookies',
    'basic_groceries': 'Sugar, Flour, Salt, Rice, Pasta',
    'dairy_eggs': 'Milk, Cheese, Yogurt, Eggs, Butter',
    'bread_baked': 'Bread, Rolls, Croissants, Muffins, Cakes',
    'canned_goods': 'Baked Beans, Tuna, Soup, Vegetables, Fruit',
    'personal_care': 'Soap, Shampoo, Toothpaste, Deodorant, Lotion',
    'household_items': 'Cleaning Supplies, Paper Towels, Trash Bags',
    'airtime_data': 'Vodacom, MTN, Cell C, Telkom Airtime',
    'frozen_goods': 'Frozen Pizza, Ice Cream, Frozen Vegetables',
    'tuckshop_packs': 'Combo Deals, Lunch Packs, Party Packs',
    'stationery': 'Pens, Notebooks, Pencils, Erasers, Rulers',
    'baby_products': 'Diapers, Baby Formula, Baby Food, Wipes',
    'seasonal_items': 'Christmas Decor, Easter Eggs, Halloween Items'
};

// Toggle between different modes
function toggleMode(mode) {
    // Update toggle buttons
    const toggleBtns = document.querySelectorAll('.toggle-btn');
    toggleBtns.forEach(btn => btn.classList.remove('active'));
    
    // Find the clicked button
    const clickedBtn = event.target.closest('.toggle-btn');
    if (clickedBtn) {
        clickedBtn.classList.add('active');
    }
    
    // Update form sections
    const sections = document.querySelectorAll('.form-section');
    sections.forEach(section => section.classList.remove('active'));
    
    if (mode === 'add_stock') {
        document.getElementById('add_stock_section').classList.add('active');
    } else if (mode === 'add_product') {
        document.getElementById('add_product_section').classList.add('active');
    } else if (mode === 'import_products') {
        document.getElementById('import_products_section').classList.add('active');
        setupFileUpload();
    } else if (mode === 'manage_items') {
        document.getElementById('manage_items_section').classList.add('active');
    }
}

// Handle file upload for import
function setupFileUpload() {
    const fileInput = document.getElementById('file');
    const fileUploadInfo = document.querySelector('.file-upload-info');
    
    if (fileInput && fileUploadInfo) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                fileUploadInfo.innerHTML = `
                    <i class="fas fa-file-check"></i>
                    <span>${file.name}</span>
                    <small>Size: ${formatFileSize(file.size)}</small>
                `;
                fileUploadInfo.style.borderColor = '#059669';
                fileUploadInfo.style.background = '#f0fdf4';
            } else {
                // Reset display when file is cleared
                fileUploadInfo.innerHTML = `
                    <i class="fas fa-cloud-upload-alt"></i>
                    <span>Choose a file or drag and drop</span>
                    <small>Supported formats: CSV, Excel (.xlsx, .xls)</small>
                `;
                fileUploadInfo.style.borderColor = '#667eea';
                fileUploadInfo.style.background = '#f8fafc';
            }
        });
        
        // Handle drag and drop
        fileUploadInfo.addEventListener('dragover', function(e) {
            e.preventDefault();
            fileUploadInfo.style.borderColor = '#059669';
            fileUploadInfo.style.background = '#f0fdf4';
        });
        
        fileUploadInfo.addEventListener('dragleave', function(e) {
            e.preventDefault();
            fileUploadInfo.style.borderColor = '#667eea';
            fileUploadInfo.style.background = '#f8fafc';
        });
        
        fileUploadInfo.addEventListener('drop', function(e) {
            e.preventDefault();
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                const event = new Event('change', { bubbles: true });
                fileInput.dispatchEvent(event);
            }
        });
        
        // Make the file upload area clickable
        fileUploadInfo.addEventListener('click', function() {
            fileInput.click();
        });
    }
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Go to Manage Sales page
function goToManageSales(button) {
    const url = button.getAttribute('data-url');
    if (url) {
        window.location.href = url;
    }
}

// Update current stock display
function updateCurrentStock() {
    const select = document.getElementById('product_id');
    const currentStockDiv = document.getElementById('current_stock');
    
    if (select.value) {
        const selectedOption = select.options[select.selectedIndex];
        const stock = selectedOption.getAttribute('data-stock');
        currentStockDiv.textContent = `Current stock: ${stock} units`;
    } else {
        currentStockDiv.textContent = '';
    }
}

// Update category example display
function updateCategoryExample() {
    const select = document.getElementById('category');
    const exampleDiv = document.getElementById('category_example');
    
    if (select.value) {
        const selectedOption = select.options[select.selectedIndex];
        const example = selectedOption.getAttribute('data-example');
        if (example) {
            exampleDiv.innerHTML = `<i class="fas fa-info-circle"></i> Examples: ${example}`;
        } else {
            exampleDiv.innerHTML = '';
        }
    } else {
        exampleDiv.innerHTML = '';
    }
}

// Filter items in the manage items section
function filterItems() {
    const searchTerm = document.getElementById('itemSearch').value.toLowerCase();
    const items = document.querySelectorAll('.item-card');
    
    items.forEach(item => {
        const name = item.getAttribute('data-product-name');
        const category = item.getAttribute('data-product-category');
        
        if (name.includes(searchTerm) || category.includes(searchTerm)) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

// Confirm delete action
function confirmDelete(productId, productName) {
    document.getElementById('deleteProductName').textContent = productName;
    document.getElementById('deleteProductId').value = productId;
    document.getElementById('deleteModal').style.display = 'block';
}

// Close delete modal
function closeDeleteModal() {
    document.getElementById('deleteModal').style.display = 'none';
}

// Delete product
function deleteProduct() {
    const productId = document.getElementById('deleteProductId').value;
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = window.location.href;  // Use current URL
    
    const csrfToken = document.createElement('input');
    csrfToken.type = 'hidden';
    csrfToken.name = 'csrfmiddlewaretoken';
    // Get CSRF token from cookie or meta tag
    const token = getCookie('csrftoken') || document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    csrfToken.value = token;
    form.appendChild(csrfToken);
    
    const modeInput = document.createElement('input');
    modeInput.type = 'hidden';
    modeInput.name = 'mode';
    modeInput.value = 'delete_product';
    form.appendChild(modeInput);
    
    const productIdInput = document.createElement('input');
    productIdInput.type = 'hidden';
    productIdInput.name = 'product_id';
    productIdInput.value = productId;
    form.appendChild(productIdInput);
    
    document.body.appendChild(form);
    form.submit();
}

// Helper function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Toggle barcode scanner
function toggleBarcodeScanner() {
    const scanner = document.getElementById('barcode-scanner');
    const input = document.getElementById('barcode-input');
    
    if (scanner.style.display === 'none') {
        scanner.style.display = 'block';
        input.focus();
        updateScannerStatus('Ready to scan', 'ready');
    } else {
        scanner.style.display = 'none';
        input.value = '';
    }
}

// Handle barcode input
function handleBarcodeInput(event) {
    const input = event.target;
    const barcode = input.value.trim();
    
    // Handle both Enter key and mobile "Go" button
    if (event.key === 'Enter' || event.key === 'Go' || event.type === 'search') {
        event.preventDefault();
        if (barcode) {
            findProductByBarcode(barcode);
        }
    } else if (barcode) {
        updateScannerStatus('Scanning...', 'scanning');
        
        // For mobile, also check for reasonable barcode lengths
        if (barcode.length >= 8) {
            // Auto-submit for common barcode lengths (EAN-13, UPC-A, etc.)
            if (barcode.length >= 12 && barcode.length <= 13) {
                setTimeout(() => {
                    if (input.value.trim() === barcode) {
                        findProductByBarcode(barcode);
                    }
                }, 500);
            }
        }
    }
}

// Find product by barcode
function findProductByBarcode(barcode) {
    const select = document.getElementById('product_id');
    const options = select.querySelectorAll('option');
    
    let found = false;
    options.forEach(option => {
        if (option.getAttribute('data-barcode') === barcode) {
            select.value = option.value;
            updateCurrentStock();
            found = true;
            updateScannerStatus('Product found!', 'success');
            
            // Hide scanner after successful scan
            setTimeout(() => {
                toggleBarcodeScanner();
            }, 1000);
        }
    });
    
    if (!found) {
        updateScannerStatus('Product not found', 'error');
        setTimeout(() => {
            updateScannerStatus('Ready to scan', 'ready');
        }, 2000);
    }
}

// Update scanner status
function updateScannerStatus(message, status) {
    const statusDiv = document.getElementById('scanner-status');
    statusDiv.innerHTML = `<i class="fas fa-${getStatusIcon(status)}"></i> ${message}`;
    statusDiv.className = `scanner-status ${status}`;
}

// Get status icon
function getStatusIcon(status) {
    switch(status) {
        case 'ready': return 'camera';
        case 'scanning': return 'spinner fa-spin';
        case 'success': return 'check-circle';
        case 'error': return 'exclamation-triangle';
        default: return 'camera';
    }
}

// Focus barcode input for add product form
function focusBarcodeInput() {
    const barcodeInput = document.getElementById('barcode');
    if (barcodeInput) {
        barcodeInput.focus();
    }
}

// Validate product name for case-insensitive duplicates
function validateProductName(input) {
    const name = input.value.trim();
    const nameError = document.getElementById('name-error') || createNameErrorElement();
    
    if (name.length < 2) {
        nameError.textContent = 'Product name must be at least 2 characters';
        nameError.style.display = 'block';
        input.classList.add('error');
        return false;
    }
    
    // Check for existing products with case-insensitive comparison
    const existingProducts = document.querySelectorAll('#product_id option');
    let duplicateFound = false;
    
    existingProducts.forEach(option => {
        const existingName = option.textContent.split(' (')[0].trim();
        if (existingName.toLowerCase() === name.toLowerCase()) {
            duplicateFound = true;
        }
    });
    
    if (duplicateFound) {
        nameError.textContent = `Product "${name}" already exists, please use a different name.`;
        nameError.style.display = 'block';
        input.classList.add('error');
        return false;
    }
    
    nameError.style.display = 'none';
    input.classList.remove('error');
    return true;
}

// Create error element for product name validation
function createNameErrorElement() {
    const nameInput = document.getElementById('name');
    const errorDiv = document.createElement('div');
    errorDiv.id = 'name-error';
    errorDiv.className = 'field-error';
    errorDiv.style.display = 'none';
    nameInput.parentNode.appendChild(errorDiv);
    return errorDiv;
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    updateCurrentStock();
    updateCategoryExample();
    
    // Set up category examples in dropdown options
    const categorySelect = document.getElementById('category');
    if (categorySelect) {
        const options = categorySelect.querySelectorAll('option');
        options.forEach(option => {
            const value = option.value;
            if (value && categoryExamples[value]) {
                option.setAttribute('data-example', categoryExamples[value]);
            }
        });
    }
    
    // Set up product name validation
    const nameInput = document.getElementById('name');
    if (nameInput) {
        nameInput.addEventListener('input', function() {
            validateProductName(this);
        });
        
        nameInput.addEventListener('blur', function() {
            validateProductName(this);
        });
    }
    
    // Set up barcode scanner auto-focus
    const barcodeInput = document.getElementById('barcode-input');
    if (barcodeInput) {
        barcodeInput.addEventListener('focus', function() {
            updateScannerStatus('Ready to scan', 'ready');
        });
        
        barcodeInput.addEventListener('blur', function() {
            if (!this.value) {
                updateScannerStatus('Ready to scan', 'ready');
            }
        });
    }
});

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('deleteModal');
    if (event.target == modal) {
        closeDeleteModal();
    }
}

// Export products to Excel
function exportProducts() {
    try {
        // Create a temporary anchor element to trigger download
        const link = document.createElement('a');
        link.href = '/export/products/excel/';
        link.download = 'products_export.xlsx';
        link.click();
        
        // Optional: Show success message
        console.log('Export started successfully');
        
        // Show a brief success notification
        showNotification('Export started successfully! Download will begin shortly.', 'success');
        
    } catch (error) {
        console.error('Error exporting products:', error);
        showNotification('Error exporting products. Please try again.', 'error');
    }
}

// Show notification message
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'}"></i>
        <span>${message}</span>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Add notification styles if not already present
    if (!document.querySelector('#notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 15px 20px;
                border-radius: 8px;
                color: white;
                font-weight: 500;
                z-index: 9999;
                display: flex;
                align-items: center;
                gap: 10px;
                max-width: 400px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                animation: slideIn 0.3s ease-out;
            }
            .notification.success {
                background: linear-gradient(135deg, #10b981, #059669);
            }
            .notification.error {
                background: linear-gradient(135deg, #ef4444, #dc2626);
            }
            .notification.info {
                background: linear-gradient(135deg, #3b82f6, #2563eb);
            }
            .notification-close {
                background: none;
                border: none;
                color: white;
                cursor: pointer;
                padding: 0;
                margin-left: auto;
                opacity: 0.8;
                transition: opacity 0.2s;
            }
            .notification-close:hover {
                opacity: 1;
            }
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Escape key closes modal
    if (event.key === 'Escape') {
        closeDeleteModal();
    }
    
    // Ctrl+K focuses search box in manage items
    if (event.ctrlKey && event.key === 'k') {
        event.preventDefault();
        const searchBox = document.getElementById('itemSearch');
        if (searchBox && document.getElementById('manage_items_section').classList.contains('active')) {
            searchBox.focus();
        }
    }
    
    // Ctrl+E triggers export
    if (event.ctrlKey && event.key === 'e') {
        event.preventDefault();
        exportProducts();
    }
});
