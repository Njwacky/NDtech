document.addEventListener('DOMContentLoaded', function() {
    // Get CSRF token
    function getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return null;
    }

    // Checkout order function - redirect to order details page
    window.checkoutOrder = function(orderId) {
        window.location.href = `/order_details/${orderId}`;
    };

    // Complete order function - redirect to order details page with completion intent
    window.completeOrder = function(orderId) {
        window.location.href = `/order_details/${orderId}`;
    };

    // Cancel order function
    window.cancelOrder = function(orderId) {
        if (confirm('Cancel this order?')) {
            showLoadingState(orderId, 'cancelling');
            
            fetch(`/pending_orders/${orderId}/cancel/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                }
            })
            .then(response => {
                if (response.ok) {
                    showSuccessMessage('Order cancelled successfully!');
                    setTimeout(() => {
                        location.reload();
                    }, 1000);
                } else {
                    throw new Error('Failed to cancel order');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showErrorMessage('Failed to cancel order. Please try again.');
                hideLoadingState(orderId);
            });
        }
    };

    // Show loading state for a specific row
    function showLoadingState(orderId, action) {
        const row = document.querySelector(`tr:has(button[onclick*="${orderId}"])`);
        if (row) {
            const buttons = row.querySelectorAll('button');
            buttons.forEach(button => {
                button.disabled = true;
                button.style.opacity = '0.6';
                button.style.cursor = 'not-allowed';
            });
            
            // Add loading indicator
            const actionCell = row.cells[row.cells.length - 1];
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading-indicator';
            loadingDiv.innerHTML = `
                <div class="spinner"></div>
                <p>${action.charAt(0).toUpperCase() + action.slice(1)}...</p>
            `;
            actionCell.appendChild(loadingDiv);
            
            // Add visual feedback to the row
            row.style.opacity = '0.7';
            row.style.pointerEvents = 'none';
        }
    }

    // Hide loading state for a specific row
    function hideLoadingState(orderId) {
        const row = document.querySelector(`tr:has(button[onclick*="${orderId}"])`);
        if (row) {
            const buttons = row.querySelectorAll('button');
            buttons.forEach(button => {
                button.disabled = false;
                button.style.opacity = '1';
                button.style.cursor = 'pointer';
            });
            
            // Remove loading indicator
            const loadingIndicator = row.querySelector('.loading-indicator');
            if (loadingIndicator) {
                loadingIndicator.remove();
            }
            
            // Restore row state
            row.style.opacity = '1';
            row.style.pointerEvents = 'auto';
        }
    }

    // Show success message
    function showSuccessMessage(message) {
        showMessage(message, 'success');
    }

    // Show error message
    function showErrorMessage(message) {
        showMessage(message, 'error');
    }

    // Show message function
    function showMessage(message, type) {
        const container = document.querySelector('.auth-container');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.innerHTML = type === 'success' ? '✅ ' : '❌ ' + message;
        
        // Style the message
        messageDiv.style.cssText = `
            padding: 15px 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-weight: 500;
            animation: slideDown 0.3s ease-out;
            ${type === 'success' ? 
                'background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); color: #155724; border-left: 4px solid #28a745;' : 
                'background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%); color: #721c24; border-left: 4px solid #dc3545;'
            }
        `;
        
        // Insert at the top of container
        container.insertBefore(messageDiv, container.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            messageDiv.style.opacity = '0';
            messageDiv.style.transform = 'translateY(-20px)';
            setTimeout(() => {
                messageDiv.remove();
            }, 300);
        }, 5000);
    }

    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Press 'R' to refresh the page
        if (e.key === 'r' && !e.ctrlKey && !e.metaKey) {
            if (confirm('Refresh the page to check for new orders?')) {
                location.reload();
            }
        }
    });

    // Auto-refresh functionality (optional)
    let autoRefreshInterval;
    const autoRefreshCheckbox = document.createElement('input');
    autoRefreshCheckbox.type = 'checkbox';
    autoRefreshCheckbox.id = 'auto-refresh';
    
    const autoRefreshLabel = document.createElement('label');
    autoRefreshLabel.htmlFor = 'auto-refresh';
    autoRefreshLabel.textContent = 'Auto-refresh every 30 seconds';
    autoRefreshLabel.style.cssText = 'margin-left: 10px; cursor: pointer;';
    
    // Add auto-refresh option
    const container = document.querySelector('.auth-container');
    if (container) {
        const autoRefreshDiv = document.createElement('div');
        autoRefreshDiv.style.cssText = 'text-align: center; margin-bottom: 20px;';
        autoRefreshDiv.appendChild(autoRefreshCheckbox);
        autoRefreshDiv.appendChild(autoRefreshLabel);
        container.insertBefore(autoRefreshDiv, container.firstChild.nextSibling);
        
        autoRefreshCheckbox.addEventListener('change', function() {
            if (this.checked) {
                autoRefreshInterval = setInterval(() => {
                    location.reload();
                }, 30000);
                showSuccessMessage('Auto-refresh enabled (every 30 seconds)');
            } else {
                clearInterval(autoRefreshInterval);
                showSuccessMessage('Auto-refresh disabled');
            }
        });
    }

    // Add row hover effects
    const rows = document.querySelectorAll('tbody tr');
    rows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.01)';
            this.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
        });
        
        row.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
            this.style.boxShadow = 'none';
        });
    });

    // Add table sorting functionality
    const table = document.querySelector('table');
    if (table) {
        const headers = table.querySelectorAll('th');
        headers.forEach((header, index) => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => sortTable(index));
        });
    }

    function sortTable(columnIndex) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        rows.sort((a, b) => {
            const aValue = a.cells[columnIndex].textContent.trim();
            const bValue = b.cells[columnIndex].textContent.trim();
            
            // Try to parse as numbers for numeric columns
            const aNum = parseFloat(aValue.replace(/[^0-9.-]/g, ''));
            const bNum = parseFloat(bValue.replace(/[^0-9.-]/g, ''));
            
            if (!isNaN(aNum) && !isNaN(bNum)) {
                return aNum - bNum;
            }
            
            return aValue.localeCompare(bValue);
        });
        
        rows.forEach(row => tbody.appendChild(row));
    }
});
