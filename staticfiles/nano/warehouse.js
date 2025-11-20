// Warehouse Pages JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializeWarehouseFeatures();
});

function initializeWarehouseFeatures() {
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize search functionality
    initializeSearchFeatures();
    
    // Initialize table interactions
    initializeTableInteractions();
    
    // Initialize file upload preview
    initializeFileUpload();
    
    // Initialize pagination
    initializePagination();
}

// Form Validation
function initializeFormValidation() {
    const warehouseImportForm = document.querySelector('form[method="post"][enctype="multipart/form-data"]');
    
    if (warehouseImportForm) {
        const warehouseNameInput = document.getElementById('warehouse_name');
        const fileInput = document.getElementById('file');
        
        // Validate warehouse name
        if (warehouseNameInput) {
            warehouseNameInput.addEventListener('input', function() {
                validateWarehouseName(this);
            });
            
            warehouseNameInput.addEventListener('blur', function() {
                validateWarehouseName(this);
            });
        }
        
        // Validate file selection
        if (fileInput) {
            fileInput.addEventListener('change', function() {
                validateFileSelection(this);
            });
        }
        
        // Form submission validation
        warehouseImportForm.addEventListener('submit', function(e) {
            if (!validateWarehouseImportForm()) {
                e.preventDefault();
            }
        });
    }
}

function validateWarehouseName(input) {
    const value = input.value.trim();
    const formGroup = input.closest('.warehouse-form-group');
    
    if (value.length < 2) {
        showFieldError(formGroup, 'Warehouse name must be at least 2 characters long');
        return false;
    }
    
    if (value.length > 100) {
        showFieldError(formGroup, 'Warehouse name must be less than 100 characters');
        return false;
    }
    
    clearFieldError(formGroup);
    return true;
}

function validateFileSelection(input) {
    const file = input.files[0];
    const formGroup = input.closest('.warehouse-form-group');
    
    if (!file) {
        showFieldError(formGroup, 'Please select a file to import');
        return false;
    }
    
    // Check file extension
    const allowedExtensions = ['.csv', '.xlsx', '.xls'];
    const fileName = file.name.toLowerCase();
    const isValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext));
    
    if (!isValidExtension) {
        showFieldError(formGroup, 'Invalid file format. Please select CSV or Excel files');
        return false;
    }
    
    // Check file size (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB in bytes
    if (file.size > maxSize) {
        showFieldError(formGroup, 'File size must be less than 10MB');
        return false;
    }
    
    clearFieldError(formGroup);
    return true;
}

function validateWarehouseImportForm() {
    const warehouseNameInput = document.getElementById('warehouse_name');
    const fileInput = document.getElementById('file');
    
    let isValid = true;
    
    if (warehouseNameInput && !validateWarehouseName(warehouseNameInput)) {
        isValid = false;
    }
    
    if (fileInput && !validateFileSelection(fileInput)) {
        isValid = false;
    }
    
    if (!isValid) {
        showNotification('Please fix the errors before submitting', 'error');
    }
    
    return isValid;
}

// Search Features
function initializeSearchFeatures() {
    const searchInput = document.querySelector('.warehouse-search-input');
    const warehouseSelect = document.querySelector('.warehouse-search-select');
    
    if (searchInput) {
        // Add search suggestions (if needed in future)
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                // Let form submit normally
                return true;
            }
        });
        
        // Add clear button functionality
        addClearButton(searchInput);
    }
    
    if (warehouseSelect) {
        warehouseSelect.addEventListener('change', function() {
            // Auto-submit when warehouse is changed
            this.form.submit();
        });
    }
}

function addClearButton(input) {
    const wrapper = document.createElement('div');
    wrapper.style.position = 'relative';
    wrapper.style.display = 'inline-block';
    wrapper.style.width = '100%';
    
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);
    
    const clearBtn = document.createElement('button');
    clearBtn.type = 'button';
    clearBtn.innerHTML = '×';
    clearBtn.style.position = 'absolute';
    clearBtn.style.right = '10px';
    clearBtn.style.top = '50%';
    clearBtn.style.transform = 'translateY(-50%)';
    clearBtn.style.border = 'none';
    clearBtn.style.background = 'none';
    clearBtn.style.fontSize = '20px';
    clearBtn.style.cursor = 'pointer';
    clearBtn.style.color = '#999';
    clearBtn.style.padding = '0';
    clearBtn.style.width = '20px';
    clearBtn.style.height = '20px';
    clearBtn.style.display = 'none';
    
    wrapper.appendChild(clearBtn);
    
    // Show/hide clear button
    input.addEventListener('input', function() {
        clearBtn.style.display = this.value ? 'block' : 'none';
    });
    
    // Clear input
    clearBtn.addEventListener('click', function() {
        input.value = '';
        clearBtn.style.display = 'none';
        input.focus();
    });
}

// Table Interactions
function initializeTableInteractions() {
    const table = document.querySelector('.warehouse-table');
    
    if (table) {
        // Add row hover effects
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            row.addEventListener('mouseenter', function() {
                this.style.cursor = 'pointer';
            });
            
            row.addEventListener('mouseleave', function() {
                this.style.cursor = 'default';
            });
        });
        
        // Add table sorting functionality (if needed)
        initializeTableSorting(table);
        
        // Add table export functionality
        initializeTableExport(table);
    }
}

function initializeTableSorting(table) {
    const headers = table.querySelectorAll('thead th');
    
    headers.forEach((header, index) => {
        if (index < 3) { // Only make first 3 columns sortable
            header.style.cursor = 'pointer';
            header.addEventListener('click', function() {
                sortTable(table, index);
            });
        }
    });
}

function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    const isAscending = table.dataset.sortOrder !== 'asc';
    table.dataset.sortOrder = isAscending ? 'asc' : 'desc';
    
    rows.sort((a, b) => {
        const aValue = a.cells[columnIndex].textContent.trim();
        const bValue = b.cells[columnIndex].textContent.trim();
        
        // Try to parse as number for price columns
        if (columnIndex === 2) { // Price column
            const aNum = parseFloat(aValue.replace(/[^0-9.-]/g, ''));
            const bNum = parseFloat(bValue.replace(/[^0-9.-]/g, ''));
            
            if (!isNaN(aNum) && !isNaN(bNum)) {
                return isAscending ? aNum - bNum : bNum - aNum;
            }
        }
        
        // String comparison
        return isAscending ? 
            aValue.localeCompare(bValue) : 
            bValue.localeCompare(aValue);
    });
    
    // Re-append sorted rows
    rows.forEach(row => tbody.appendChild(row));
}

function initializeTableExport(table) {
    // Add export button functionality
    const exportBtn = document.querySelector('a[href*="export_warehouse_prices"]');
    
    if (exportBtn) {
        exportBtn.addEventListener('click', function(e) {
            // Add loading state
            this.classList.add('loading');
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Exporting...';
            
            // Remove loading state after a delay (in case of slow response)
            setTimeout(() => {
                this.classList.remove('loading');
                this.innerHTML = '<i class="fas fa-download"></i> Export';
            }, 3000);
        });
    }
}

// File Upload Features
function initializeFileUpload() {
    const fileInput = document.getElementById('file');
    
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            displayFileInfo(this);
        });
    }
}

function displayFileInfo(input) {
    const file = input.files[0];
    if (!file) return;
    
    // Create or update file info display
    let fileInfo = document.querySelector('.warehouse-file-info');
    
    if (!fileInfo) {
        fileInfo = document.createElement('div');
        fileInfo.className = 'warehouse-file-info';
        fileInfo.style.marginTop = '0.5rem';
        fileInfo.style.padding = '0.75rem';
        fileInfo.style.backgroundColor = '#e8f4fd';
        fileInfo.style.borderRadius = '6px';
        fileInfo.style.fontSize = '0.875rem';
        
        const formGroup = input.closest('.warehouse-form-group');
        formGroup.appendChild(fileInfo);
    }
    
    const fileSize = formatFileSize(file.size);
    const fileType = file.type || 'Unknown';
    
    fileInfo.innerHTML = `
        <strong>Selected file:</strong> ${file.name}<br>
        <strong>Size:</strong> ${fileSize}<br>
        <strong>Type:</strong> ${fileType}
    `;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Pagination Features
function initializePagination() {
    const paginationLinks = document.querySelectorAll('.warehouse-page-link');
    
    paginationLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Add loading state
            this.classList.add('loading');
            
            // Remove loading state after navigation
            setTimeout(() => {
                this.classList.remove('loading');
            }, 1000);
        });
    });
}

// Utility Functions
function showFieldError(formGroup, message) {
    clearFieldError(formGroup);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'warehouse-field-error';
    errorDiv.style.color = '#dc3545';
    errorDiv.style.fontSize = '0.875rem';
    errorDiv.style.marginTop = '0.25rem';
    errorDiv.textContent = message;
    
    formGroup.appendChild(errorDiv);
    formGroup.classList.add('has-error');
}

function clearFieldError(formGroup) {
    const existingError = formGroup.querySelector('.warehouse-field-error');
    if (existingError) {
        existingError.remove();
    }
    formGroup.classList.remove('has-error');
}

function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.warehouse-notification');
    existingNotifications.forEach(notif => notif.remove());
    
    // Create notification
    const notification = document.createElement('div');
    notification.className = `warehouse-notification warehouse-notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 6px;
        color: white;
        font-weight: 500;
        z-index: 9999;
        max-width: 400px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transform: translateX(100%);
        transition: transform 0.3s ease;
    `;
    
    // Set background color based on type
    const colors = {
        success: '#28a745',
        error: '#dc3545',
        warning: '#ffc107',
        info: '#17a2b8'
    };
    
    notification.style.backgroundColor = colors[type] || colors.info;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 5000);
}

// Keyboard Navigation
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K for search focus
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('.warehouse-search-input');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape to clear search
    if (e.key === 'Escape') {
        const searchInput = document.querySelector('.warehouse-search-input');
        if (searchInput && searchInput.value) {
            searchInput.value = '';
            searchInput.focus();
        }
    }
});

// Print functionality
function initializePrintFeatures() {
    // Add print button if not exists
    const headerActions = document.querySelector('.warehouse-header-actions');
    
    if (headerActions && !headerActions.querySelector('.print-btn')) {
        const printBtn = document.createElement('button');
        printBtn.className = 'warehouse-btn warehouse-btn-light print-btn';
        printBtn.innerHTML = '<i class="fas fa-print"></i> Print';
        printBtn.addEventListener('click', function() {
            window.print();
        });
        
        headerActions.appendChild(printBtn);
    }
}

// Initialize print features
initializePrintFeatures();

// Responsive table handling
function handleResponsiveTable() {
    const table = document.querySelector('.warehouse-table');
    
    if (table && window.innerWidth <= 768) {
        // Add mobile table handling
        addMobileTableFeatures(table);
    }
}

function addMobileTableFeatures(table) {
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        row.addEventListener('click', function() {
            // Show row details on mobile
            showRowDetails(this);
        });
    });
}

function showRowDetails(row) {
    if (window.innerWidth > 768) return;
    
    // Create modal for row details
    const modal = document.createElement('div');
    modal.className = 'warehouse-row-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        z-index: 9998;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
    `;
    
    const modalContent = document.createElement('div');
    modalContent.style.cssText = `
        background: white;
        border-radius: 8px;
        padding: 2rem;
        max-width: 400px;
        width: 100%;
        max-height: 80vh;
        overflow-y: auto;
    `;
    
    // Build row details
    const headers = table.querySelectorAll('thead th');
    const cells = row.querySelectorAll('td');
    
    let detailsHTML = '<h5>Product Details</h5><div class="row-details">';
    
    cells.forEach((cell, index) => {
        if (headers[index]) {
            const headerText = headers[index].textContent.trim();
            const cellText = cell.textContent.trim();
            if (cellText && cellText !== '-') {
                detailsHTML += `
                    <div style="margin-bottom: 0.75rem;">
                        <strong>${headerText}:</strong><br>
                        ${cell.innerHTML}
                    </div>
                `;
            }
        }
    });
    
    detailsHTML += '</div><button class="warehouse-btn warehouse-btn-primary" style="margin-top: 1rem;">Close</button>';
    modalContent.innerHTML = detailsHTML;
    
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    // Close modal handlers
    const closeBtn = modalContent.querySelector('button');
    closeBtn.addEventListener('click', () => {
        document.body.removeChild(modal);
    });
    
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            document.body.removeChild(modal);
        }
    });
}

// Handle window resize
window.addEventListener('resize', function() {
    handleResponsiveTable();
});

// Initialize on load
handleResponsiveTable();
