let cart = [];
let total = 0;
let allProducts = [];

function addToCartFromData(element) {
    const productName = element.dataset.productName;
    const currentPrice = parseFloat(element.dataset.currentPrice);
    const isOnSale = element.dataset.isOnSale === 'true';
    const regularPrice = parseFloat(element.dataset.regularPrice);
    const salePrice = element.dataset.salePrice ? parseFloat(element.dataset.salePrice) : null;
    
    addToCart(productName, currentPrice, isOnSale, regularPrice, salePrice);
}

function addToCart(product, price, isOnSale = false, regularPrice = null, salePrice = null) {
    let existingItem = cart.find(item => item.product === product);
    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({ 
            product, 
            price, 
            regularPrice: regularPrice || price,
            salePrice: salePrice,
            isOnSale,
            quantity: 1 
        });
    }
    total += price;
    updateCart();
}

function removeFromCart(product, price) {
    let existingItem = cart.find(item => item.product === product);
    if (existingItem) {
        if (existingItem.quantity > 1) {
            existingItem.quantity -= 1;
            total -= price;
        } else {
            // Remove the item completely if quantity is 1
            const index = cart.indexOf(existingItem);
            cart.splice(index, 1);
            total -= price;
        }
        updateCart();
    }
}

function updateCart() {
    const cartItems = document.getElementById('cart-items');
    cartItems.innerHTML = '';
    cart.forEach(item => {
        const div = document.createElement('div');
        div.className = 'cart-item';
        
        // Build price display based on whether item is on sale
        let priceDisplay = '';
        if (item.isOnSale && item.regularPrice && item.salePrice) {
            priceDisplay = `
                <div class="cart-item-pricing">
                    <span class="cart-item-sale-price">R${(item.price * item.quantity).toFixed(2)}</span>
                    <span class="cart-item-original-price">R${(item.regularPrice * item.quantity).toFixed(2)}</span>
                </div>
            `;
        } else {
            priceDisplay = `<span>R${(item.price * item.quantity).toFixed(2)}</span>`;
        }
        
        div.innerHTML = `
            <div class="cart-item-info">
                <span class="cart-item-name">${item.product} x${item.quantity}</span>
                ${item.isOnSale ? '<span class="cart-item-sale-badge">SALE</span>' : ''}
            </div>
            ${priceDisplay}
            <button class="remove-btn" onclick="removeFromCart('${item.product}', ${item.price})">-</button>
        `;
        cartItems.appendChild(div);
    });
    document.getElementById('total').innerHTML = 'R' + total.toFixed(2);
    // Recalculate change when cart is updated
    calculateChange();
}

function calculateChange() {
    const cashReceived = parseFloat(document.getElementById('cash-received').value) || 0;
    const changeDisplay = document.getElementById('change-display');
    const changeAmount = document.getElementById('change-amount');
    
    if (cashReceived > 0 && total > 0) {
        const change = cashReceived - total;
        changeDisplay.style.display = 'block';
        changeAmount.textContent = change.toFixed(2);
        
        // Add visual feedback for change amount
        if (change >= 0) {
            changeDisplay.className = 'change-display positive';
        } else {
            changeDisplay.className = 'change-display negative';
        }
    } else {
        changeDisplay.style.display = 'none';
    }
}

function clearCart() {
    cart = [];
    total = 0;
    // Clear all form fields
    document.getElementById('cash-received').value = '';
    document.getElementById('customer-name').value = '';
    document.getElementById('customer-phone').value = '';
    document.getElementById('change-display').style.display = 'none';
    updateCart();
}

function saveOrder() {
    const customerName = document.getElementById('customer-name').value.trim();
    const customerPhone = document.getElementById('customer-phone').value.trim();
    
    // Validate customer information
    if (!customerName || !customerPhone) {
        alert("Customer name and phone number are required to save order.");
        if (!customerName) {
            document.getElementById('customer-name').focus();
        } else {
            document.getElementById('customer-phone').focus();
        }
        return;
    }
    
    // Validate phone number format
    const phoneRegex = /^[0-9]{10,15}$/;
    if (!phoneRegex.test(customerPhone)) {
        alert("Please enter a valid phone number (10-15 digits).");
        document.getElementById('customer-phone').focus();
        return;
    }
    
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    if (!csrfToken) {
        alert("Security token not found. Please refresh the page.");
        return;
    }
    
    // Send to server
    fetch('/save_order/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            customer_name: customerName,
            customer_phone: customerPhone,
            items: cart,
            total_amount: total
        })
    }).then(response => response.json())
    .then(data => {
        console.log('Save order response:', data);
        if (data.success) {
            alert("Order saved successfully!");
            clearCart();
        } else {
            alert("Failed to save order: " + (data.error || 'Unknown error'));
        }
    }).catch(error => {
        console.error('Error:', error);
        alert("An error occurred while saving the order: " + error.message);
    });
}

function checkoutOrder() {
    if (cart.length === 0) {
        alert("Cart is empty. Add items before checkout.");
        return;
    }
    
    const customerName = document.getElementById('customer-name').value.trim();
    const customerPhone = document.getElementById('customer-phone').value.trim();
    const cashReceived = parseFloat(document.getElementById('cash-received').value) || 0;
    
    // Validate customer information
    if (!customerName || !customerPhone) {
        alert("Customer name and phone number are required to complete the order.");
        if (!customerName) {
            document.getElementById('customer-name').focus();
        } else {
            document.getElementById('customer-phone').focus();
        }
        return;
    }
    
    // Validate phone number format
    const phoneRegex = /^[0-9]{10,15}$/;
    if (!phoneRegex.test(customerPhone)) {
        alert("Please enter a valid phone number (10-15 digits).");
        document.getElementById('customer-phone').focus();
        return;
    }
    
    // Validate payment
    if (cashReceived < total) {
        alert("Insufficient payment. Customer needs to pay at least R" + total.toFixed(2));
        document.getElementById('cash-received').focus();
        return;
    }
    
    const changeGiven = cashReceived - total;
    
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    if (!csrfToken) {
        alert("Security token not found. Please refresh the page.");
        return;
    }
    
    // Send to server as completed order
    fetch('/checkout_order/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            customer_name: customerName,
            customer_phone: customerPhone,
            items: cart,
            total: total,
            cashReceived: cashReceived,
            changeGiven: changeGiven
        })
    }).then(response => {
        console.log('Response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        if (data.status === 'success') {
            alert("Order completed successfully!\n\n" +
                  "Customer: " + customerName + "\n" +
                  "Total: R" + total.toFixed(2) + "\n" +
                  "Cash Received: R" + cashReceived.toFixed(2) + "\n" +
                  "Change: R" + changeGiven.toFixed(2));
            clearCart();
        } else {
            alert("Failed to complete order: " + (data.message || 'Unknown error'));
        }
    }).catch(error => {
        console.error('Error:', error);
        alert("An error occurred while processing the order: " + error.message);
    });
}

// Search functionality
function initializeSearch() {
    const searchInput = document.getElementById('product-search');
    const clearButton = document.getElementById('clear-search');
    const productsGrid = document.getElementById('products-grid');
    
    // Store all products initially
    const productCards = productsGrid.querySelectorAll('.product-card');
    allProducts = Array.from(productCards).map(card => ({
        element: card,
        name: card.querySelector('h3').textContent.toLowerCase(),
        price: card.querySelector('.product-price').textContent,
        category: card.querySelector('.product-category')?.textContent || ''
    }));
    
    // Search event listener
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase().trim();
        
        // Show/hide clear button
        if (searchTerm) {
            clearButton.style.display = 'block';
        } else {
            clearButton.style.display = 'none';
        }
        
        // Filter products
        filterProducts(searchTerm);
    });
    
    // Clear search event listener
    clearButton.addEventListener('click', function() {
        searchInput.value = '';
        this.style.display = 'none';
        filterProducts('');
        searchInput.focus();
    });
    
    // Clear search on Escape key
    searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            this.value = '';
            clearButton.style.display = 'none';
            filterProducts('');
        }
    });
}

function filterProducts(searchTerm) {
    const productsGrid = document.getElementById('products-grid');
    let hasResults = false;
    
    allProducts.forEach(product => {
        const matchesSearch = product.name.includes(searchTerm) || 
                             product.category.toLowerCase().includes(searchTerm);
        
        if (matchesSearch) {
            product.element.style.display = '';
            hasResults = true;
        } else {
            product.element.style.display = 'none';
        }
    });
    
    // Show "no results" message if needed
    let noResultsMsg = productsGrid.querySelector('.no-results');
    if (!hasResults) {
        if (!noResultsMsg) {
            noResultsMsg = document.createElement('div');
            noResultsMsg.className = 'no-results';
            noResultsMsg.innerHTML = `
                <div style="text-align: center; padding: 2rem; color: #718096;">
                    <i class="fas fa-search" style="font-size: 2rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                    <p>No products found matching "${searchTerm}"</p>
                </div>
            `;
            productsGrid.appendChild(noResultsMsg);
        }
    } else if (noResultsMsg) {
        noResultsMsg.remove();
    }
}

// Toggle barcode scan panel
function toggleBarcodeScan() {
    const panel = document.getElementById('barcode-scan-panel');
    const input = document.getElementById('barcode-scan-input');
    const button = document.querySelector('.btn-scan-barcode');
    
    if (panel.style.display === 'none' || !panel.style.display) {
        panel.style.display = 'flex';
        panel.style.flexDirection = 'column';
        panel.style.gap = '0.75rem';
        
        // Ensure button is visible and active
        button.classList.add('active');
        
        // Focus input with delay for mobile
        setTimeout(() => {
            input.focus();
            // For mobile, ensure input field is visible
            input.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 100);
        
        updateScanStatus('Ready to scan', 'ready');
    } else {
        panel.style.display = 'none';
        input.value = '';
        button.classList.remove('active');
    }
}

// Handle barcode scan input
function handleBarcodeScan(event) {
    const input = event.target;
    const barcode = input.value.trim();
    
    // Handle both Enter key and mobile "Go" button
    if (event.key === 'Enter' || event.key === 'Go' || event.type === 'search') {
        event.preventDefault();
        if (barcode) {
            findAndAddProductByBarcode(barcode);
        }
    } else if (barcode) {
        updateScanStatus('Scanning...', 'scanning');
    }
}

// Handle mobile-specific input events
function handleBarcodeInput(event) {
    const input = event.target;
    const barcode = input.value.trim();
    
    // For mobile, also check for reasonable barcode lengths
    if (barcode.length >= 8) {
        // Auto-submit for common barcode lengths (EAN-13, UPC-A, etc.)
        if (barcode.length >= 12 && barcode.length <= 13) {
            setTimeout(() => {
                if (input.value.trim() === barcode) {
                    findAndAddProductByBarcode(barcode);
                }
            }, 500);
        }
    } else if (barcode) {
        updateScanStatus('Scanning...', 'scanning');
    }
}

// Find and add product by barcode
function findAndAddProductByBarcode(barcode) {
    const productsGrid = document.getElementById('products-grid');
    const productCards = productsGrid.querySelectorAll('.product-card');
    
    let found = false;
    productCards.forEach(card => {
        // We need to add barcode data to the product cards
        // For now, we'll need to fetch product data from the server
        if (!found) {
            fetchProductByBarcode(barcode, card);
            found = true; // Prevent multiple requests
        }
    });
}

// Fetch product by barcode from server
function fetchProductByBarcode(barcode, fallbackCard = null) {
    updateScanStatus('Searching...', 'scanning');
    
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    const headers = {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
    };
    
    if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken.value;
    }
    
    fetch(`/api/get_product_by_barcode/?barcode=${encodeURIComponent(barcode)}`, {
        method: 'GET',
        headers: headers
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                const product = data.product;
                addToCart(
                    product.name,
                    parseFloat(product.price),
                    product.is_currently_on_sale,
                    parseFloat(product.regular_price),
                    product.sale_price ? parseFloat(product.sale_price) : null
                );
                updateScanStatus('Product added to cart!', 'success');
                
                // Clear input and hide panel after successful scan
                const input = document.getElementById('barcode-scan-input');
                if (input) {
                    input.value = '';
                }
                
                setTimeout(() => {
                    toggleBarcodeScan();
                }, 1500);
            } else {
                updateScanStatus(data.message || 'Product not found', 'error');
                setTimeout(() => {
                    updateScanStatus('Ready to scan', 'ready');
                    const input = document.getElementById('barcode-scan-input');
                    if (input) {
                        input.value = '';
                        input.focus();
                    }
                }, 2000);
            }
        })
        .catch(error => {
            console.error('Error fetching product:', error);
            updateScanStatus('Error scanning barcode', 'error');
            setTimeout(() => {
                updateScanStatus('Ready to scan', 'ready');
                const input = document.getElementById('barcode-scan-input');
                if (input) {
                    input.value = '';
                    input.focus();
                }
            }, 2000);
        });
}

// Update scan status
function updateScanStatus(message, status) {
    const statusDiv = document.getElementById('scan-status');
    statusDiv.innerHTML = `<i class="fas fa-${getScanStatusIcon(status)}"></i> ${message}`;
    statusDiv.className = `scan-status ${status}`;
}

// Get scan status icon
function getScanStatusIcon(status) {
    switch(status) {
        case 'ready': return 'camera';
        case 'scanning': return 'spinner fa-spin';
        case 'success': return 'check-circle';
        case 'error': return 'exclamation-triangle';
        default: return 'camera';
    }
}

// Export products to Excel
function exportProducts() {
    try {
        // Create a temporary anchor element
        const link = document.createElement('a');
        link.href = '/export/products/excel/';
        link.download = 'products_export.xlsx';
        link.click();
        
        // Optional: Show success message
        console.log('Export started successfully');
    } catch (error) {
        console.error('Error exporting products:', error);
        alert('Error exporting products. Please try again.');
    }
}

// Toggle shortcuts modal
function toggleShortcuts() {
    const modal = document.getElementById('shortcuts-modal');
    console.log('Toggle shortcuts called, modal:', modal); // Debug log
    if (modal) {
        if (modal.style.display === 'none' || !modal.style.display) {
            modal.style.display = 'flex';
            // Prevent body scroll when modal is open
            document.body.style.overflow = 'hidden';
            console.log('Modal opened'); // Debug log
        } else {
            modal.style.display = 'none';
            // Restore body scroll
            document.body.style.overflow = '';
            console.log('Modal closed'); // Debug log
        }
    } else {
        console.error('Shortcuts modal not found'); // Debug log
    }
}

// Keyboard shortcuts handler
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(event) {
        // Don't trigger shortcuts when typing in input fields
        if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
            return;
        }
        
        // Ctrl + C: Clear Cart
        if (event.ctrlKey && event.key === 'c') {
            event.preventDefault();
            clearCart();
        }
        
        // Ctrl + S: Save Order
        if (event.ctrlKey && event.key === 's') {
            event.preventDefault();
            saveOrder();
        }
        
        // Ctrl + F: Focus Search
        if (event.ctrlKey && event.key === 'f') {
            event.preventDefault();
            const searchInput = document.getElementById('product-search');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Ctrl + B: Toggle Barcode Scanner
        if (event.ctrlKey && event.key === 'b') {
            event.preventDefault();
            toggleBarcodeScan();
        }
        
        // Escape: Close modals and clear search
        if (event.key === 'Escape') {
            const shortcutsModal = document.getElementById('shortcuts-modal');
            if (shortcutsModal && shortcutsModal.style.display !== 'none') {
                toggleShortcuts();
            } else {
                const searchInput = document.getElementById('product-search');
                if (searchInput && searchInput.value) {
                    searchInput.value = '';
                    filterProducts('');
                    const clearButton = document.getElementById('clear-search');
                    if (clearButton) {
                        clearButton.style.display = 'none';
                    }
                }
            }
        }
    });
    
    // Special handling for Enter key on cart total
    const cartTotal = document.getElementById('total');
    if (cartTotal) {
        cartTotal.addEventListener('keydown', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                checkoutOrder();
            }
        });
    }
    
    // Arrow key handling for cash received input
    const cashReceived = document.getElementById('cash-received');
    if (cashReceived) {
        cashReceived.addEventListener('keydown', function(event) {
            let currentValue = parseFloat(this.value) || 0;
            let step = 1.00;
            
            if (event.shiftKey) {
                step = 10.00; // Shift + arrow for larger steps
            }
            
            if (event.key === 'ArrowUp') {
                event.preventDefault();
                this.value = (currentValue + step).toFixed(2);
                calculateChange();
            } else if (event.key === 'ArrowDown') {
                event.preventDefault();
                this.value = Math.max(0, currentValue - step).toFixed(2);
                calculateChange();
            }
        });
    }
}

// Close shortcuts modal when clicking outside
document.addEventListener('click', function(event) {
    const shortcutsModal = document.getElementById('shortcuts-modal');
    if (shortcutsModal && shortcutsModal.style.display !== 'none') {
        const modalContent = shortcutsModal.querySelector('.shortcuts-content');
        const shortcutsButton = document.getElementById('shortcuts-btn');
        if (!modalContent.contains(event.target) && event.target !== shortcutsButton && !shortcutsButton.contains(event.target)) {
            toggleShortcuts();
        }
    }
});

// Initialize everything when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded - Setting up home page');
    
    initializeSearch();
    
    // Initialize keyboard shortcuts
    setupKeyboardShortcuts();
    
    // Set up shortcuts button with multiple approaches to ensure it works
    const shortcutsButton = document.getElementById('shortcuts-btn');
    console.log('Shortcuts button found:', shortcutsButton);
    
    if (shortcutsButton) {
        // Create a wrapper function to handle all events
        const handleShortcutClick = function(e) {
            console.log('Shortcuts button click detected via:', e.type); // Debug log
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            
            // Visual feedback is already handled by inline events
            toggleShortcuts();
        };
        
        // Multiple event listeners for maximum compatibility
        shortcutsButton.addEventListener('click', handleShortcutClick, true); // Capture phase
        shortcutsButton.addEventListener('click', handleShortcutClick, false); // Bubble phase
        
        // Touch event support for mobile
        shortcutsButton.addEventListener('touchend', handleShortcutClick, { passive: false });
        
        // Mouse events for desktop
        shortcutsButton.addEventListener('mouseup', function(e) {
            e.preventDefault();
            handleShortcutClick.call(this, e);
        }, { passive: false });
        
        // Also add backup click handler
        shortcutsButton.onclick = function(e) {
            console.log('Shortcuts button clicked via onclick'); // Debug log
            handleShortcutClick.call(this, e);
            return false;
        };
        
        // Add keyboard support
        shortcutsButton.setAttribute('tabindex', '0');
        shortcutsButton.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                handleShortcutClick.call(this, e);
            }
        });
        
        console.log('Shortcuts button event listeners setup complete');
        
    } else {
        console.error('Shortcuts button not found'); // Debug log
        
        // Retry after delay
        setTimeout(() => {
            const retryButton = document.getElementById('shortcuts-btn');
            if (retryButton) {
                console.log('Shortcuts button found on retry - setting up events');
                // Trigger the setup again
                location.reload();
            } else {
                console.error('Shortcuts button still not found after retry');
            }
        }, 2000);
    }
    
    // Set up barcode scanner with mobile support
    const barcodeInput = document.getElementById('barcode-scan-input');
    const barcodeButton = document.querySelector('.btn-scan-barcode');
    
    if (barcodeInput && barcodeButton) {
        // Handle button clicks for both mouse and touch events
        barcodeButton.addEventListener('click', function(e) {
            e.preventDefault();
            toggleBarcodeScan();
        });
        
        // Touch event support for mobile
        barcodeButton.addEventListener('touchstart', function(e) {
            e.preventDefault();
            this.classList.add('touch-active');
        });
        
        barcodeButton.addEventListener('touchend', function(e) {
            e.preventDefault();
            this.classList.remove('touch-active');
            toggleBarcodeScan();
        });
        
        // Input event handlers
        barcodeInput.addEventListener('focus', function() {
            updateScanStatus('Ready to scan', 'ready');
        });
        
        barcodeInput.addEventListener('blur', function() {
            if (!this.value) {
                updateScanStatus('Ready to scan', 'ready');
            }
        });
        
        // Mobile keyboard handling
        barcodeInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleBarcodeScan(e);
            }
        });
        
        // Handle mobile input method changes
        barcodeInput.addEventListener('input', function(e) {
            handleBarcodeInput(e);
        });
        
        // Prevent zoom on iOS
        barcodeInput.addEventListener('touchstart', function(e) {
            if (e.touches.length > 1) {
                e.preventDefault();
            }
        });
    }
    
    // Add mobile menu toggle if needed
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (mobileMenuToggle && navMenu) {
        mobileMenuToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!mobileMenuToggle.contains(e.target) && !navMenu.contains(e.target)) {
                navMenu.classList.remove('active');
            }
        });
    }
});

// Backup initialization - run after a delay to ensure everything is loaded
setTimeout(function() {
    console.log('Backup initialization running...');
    const shortcutsButton = document.getElementById('shortcuts-btn');
    if (shortcutsButton) {
        console.log('Backup: Shortcuts button found, adding final backup handler');
        // Add a final backup click handler as last resort
        shortcutsButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Backup: Shortcuts button clicked via final backup');
            toggleShortcuts();
        }, { capture: true, passive: false });
        
        // Also add a direct onclick as ultimate backup
        shortcutsButton.setAttribute('onclick', 'toggleShortcuts(); return false;');
        console.log('Backup: All event handlers attached');
    } else {
        console.error('Backup: Shortcuts button still not found');
    }
}, 1000);
