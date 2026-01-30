// TypeScript implementation for home page functionality
// This file addresses shortcut button issues and provides robust functionality

interface CartItem {
    product: string;
    price: number;
    regularPrice: number;
    salePrice?: number;
    isOnSale: boolean;
    quantity: number;
}

interface Product {
    element: HTMLElement;
    name: string;
    price: string;
    regular_price: number;
    sale_price?: number;
    is_currently_on_sale: boolean;
    category: string;
}

interface CustomerInfo {
    name: string;
    phone: string;
}

class HomePageManager {
    private cart: CartItem[] = [];
    private total: number = 0;
    private allProducts: Product[] = [];


    constructor() {
        this.initializePage();
    }

    private initializePage(): void {
        console.log('🚀 TypeScript: Initializing home page...');
        
        // Wait for DOM to be fully loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupEventListeners());
        } else {
            this.setupEventListeners();
        }
    }

    private setupEventListeners(): void {
        console.log('🔧 TypeScript: Setting up event listeners...');
        
        // Setup search functionality
        this.setupSearch();
        
        // Setup barcode scanner
        this.setupBarcodeScanner();
        
        // Setup mobile menu
        this.setupMobileMenu();
        
        console.log('✅ TypeScript: All event listeners setup complete');
    }


    private setupSearch(): void {
        const searchInput = document.getElementById('product-search') as HTMLInputElement;
        const clearButton = document.getElementById('clear-search') as HTMLElement;
        const productsGrid = document.getElementById('products-grid');
        
        if (!searchInput || !clearButton || !productsGrid) {
            console.warn('⚠️ TypeScript: Search elements not found');
            return;
        }

        // Store all products
        const productCards = productsGrid.querySelectorAll('.product-card');
        this.allProducts = Array.from(productCards).map(card => ({
            element: card as HTMLElement,
            name: card.querySelector('h3')?.textContent?.toLowerCase() || '',
            price: card.querySelector('.product-price')?.textContent || '',
            regular_price: 0,
            is_currently_on_sale: false,
            category: card.querySelector('.product-category')?.textContent || ''
        }));

        // Search event listener
        searchInput.addEventListener('input', () => {
            const searchTerm = searchInput.value.toLowerCase().trim();
            
            if (searchTerm) {
                clearButton.style.display = 'block';
            } else {
                clearButton.style.display = 'none';
            }
            
            this.filterProducts(searchTerm);
        });

        // Clear search event listener
        clearButton.addEventListener('click', () => {
            searchInput.value = '';
            clearButton.style.display = 'none';
            this.filterProducts('');
            searchInput.focus();
        });

        // Escape key to clear search
        searchInput.addEventListener('keydown', (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                searchInput.value = '';
                clearButton.style.display = 'none';
                this.filterProducts('');
            }
        });
    }

    private filterProducts(searchTerm: string): void {
        const productsGrid = document.getElementById('products-grid');
        if (!productsGrid) return;

        let hasResults = false;
        
        this.allProducts.forEach(product => {
            const matchesSearch = product.name.includes(searchTerm) || 
                                 product.category.toLowerCase().includes(searchTerm);
            
            if (matchesSearch) {
                product.element.style.display = '';
                hasResults = true;
            } else {
                product.element.style.display = 'none';
            }
        });

        // Show/hide no results message
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

    private setupKeyboardShortcuts(): void {
        document.addEventListener('keydown', (e: KeyboardEvent) => {
            // Enhanced keyboard shortcuts with better UX
            const isInputField = e.target instanceof HTMLInputElement || 
                                e.target instanceof HTMLTextAreaElement;
            
            // Don't trigger shortcuts when typing in input fields (except for specific shortcuts)
            if (isInputField && !e.altKey) {
                return;
            }
            
            // Improved shortcut combinations
            const shortcuts = [
                { keys: ['c', 'C'], action: () => this.clearCart(), description: 'Clear Cart' },
                { keys: ['s', 'S'], action: () => this.saveOrder(), description: 'Save Order' },
                { keys: ['f', 'F'], action: () => this.focusSearch(), description: 'Focus Search' },
                { keys: ['b', 'B'], action: () => this.toggleBarcodeScan(), description: 'Toggle Barcode Scanner' }
            ];
            
            for (const shortcut of shortcuts) {
                if (e.ctrlKey && shortcut.keys.includes(e.key)) {
                    e.preventDefault();
                    shortcut.action();
                    console.log(`⌨️ TypeScript: Keyboard shortcut activated - ${shortcut.description}`);
                    break;
                }
            }
            
            // Enhanced Escape handling
            if (e.key === 'Escape') {
                if (!isInputField) {
                    this.clearSearchAndFocus();
                }
            }
        });
    }
    
    // Helper method for search focus
    private focusSearch(): void {
        const searchInput = document.getElementById('product-search') as HTMLInputElement;
        if (searchInput) {
            searchInput.focus();
            searchInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
    
    // Helper method for clearing search
    private clearSearchAndFocus(): void {
        const searchInput = document.getElementById('product-search') as HTMLInputElement;
        if (searchInput) {
            searchInput.value = '';
            this.filterProducts('');
            const clearButton = document.getElementById('clear-search');
            if (clearButton) clearButton.style.display = 'none';
            searchInput.focus();
        }
    }

    private setupBarcodeScanner(): void {
        const barcodeInput = document.getElementById('barcode-scan-input') as HTMLInputElement;
        const barcodeButton = document.querySelector('.btn-scan-barcode') as HTMLElement;
        
        if (!barcodeInput || !barcodeButton) {
            console.warn('⚠️ TypeScript: Barcode scanner elements not found');
            return;
        }

        // Button click/touch events
        barcodeButton.addEventListener('click', (e: Event) => {
            e.preventDefault();
            this.toggleBarcodeScan();
        });
        
        barcodeButton.addEventListener('touchstart', (e: TouchEvent) => {
            e.preventDefault();
            barcodeButton.classList.add('touch-active');
        });
        
        barcodeButton.addEventListener('touchend', (e: TouchEvent) => {
            e.preventDefault();
            barcodeButton.classList.remove('touch-active');
            this.toggleBarcodeScan();
        });

        // Input events
        barcodeInput.addEventListener('focus', () => {
            this.updateScanStatus('Ready to scan', 'ready');
        });
        
        barcodeInput.addEventListener('keydown', (e: KeyboardEvent) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.handleBarcodeScan(e);
            }
        });
        
        barcodeInput.addEventListener('input', (e: Event) => {
            this.handleBarcodeInput(e);
        });
    }

    public toggleBarcodeScan(): void {
        const panel = document.getElementById('barcode-scan-panel');
        const input = document.getElementById('barcode-scan-input') as HTMLInputElement;
        const button = document.querySelector('.btn-scan-barcode') as HTMLElement;
        
        if (!panel || !input || !button) return;
        
        if (panel.style.display === 'none' || !panel.style.display) {
            panel.style.display = 'flex';
            panel.style.flexDirection = 'column';
            panel.style.gap = '0.75rem';
            button.classList.add('active');
            
            setTimeout(() => {
                input.focus();
                input.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 100);
            
            this.updateScanStatus('Ready to scan', 'ready');
        } else {
            panel.style.display = 'none';
            input.value = '';
            button.classList.remove('active');
        }
    }

    public handleBarcodeScan(event: KeyboardEvent): void {
        const input = event.target as HTMLInputElement;
        const barcode = input.value.trim();
        
        if (event.key === 'Enter' || event.key === 'Go') {
            event.preventDefault();
            if (barcode) {
                this.findAndAddProductByBarcode(barcode);
            }
        } else if (barcode) {
            this.updateScanStatus('Scanning...', 'scanning');
        }
    }

    public handleBarcodeInput(event: Event): void {
        const input = event.target as HTMLInputElement;
        const barcode = input.value.trim();
        
        if (barcode.length >= 8) {
            if (barcode.length >= 12 && barcode.length <= 13) {
                setTimeout(() => {
                    if (input.value.trim() === barcode) {
                        this.findAndAddProductByBarcode(barcode);
                    }
                }, 500);
            }
        } else if (barcode) {
            this.updateScanStatus('Scanning...', 'scanning');
        }
    }

    private async findAndAddProductByBarcode(barcode: string): Promise<void> {
        this.updateScanStatus('Searching...', 'scanning');
        
        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]') as HTMLMetaElement;
            const headers: { [key: string]: string } = {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            };
            
            if (csrfToken) {
                headers['X-CSRFToken'] = csrfToken.content;
            }
            
            const response = await fetch(`/api/get_product_by_barcode/?barcode=${encodeURIComponent(barcode)}`, {
                method: 'GET',
                headers
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'success') {
                const product = data.product;
                this.addToCart(
                    product.name,
                    parseFloat(product.price),
                    product.is_currently_on_sale,
                    parseFloat(product.regular_price),
                    product.sale_price ? parseFloat(product.sale_price) : null
                );
                this.updateScanStatus('Product added to cart!', 'success');
                
                const input = document.getElementById('barcode-scan-input') as HTMLInputElement;
                if (input) input.value = '';
                
                setTimeout(() => {
                    this.toggleBarcodeScan();
                }, 1500);
            } else {
                this.updateScanStatus(data.message || 'Product not found', 'error');
                setTimeout(() => {
                    this.updateScanStatus('Ready to scan', 'ready');
                    const input = document.getElementById('barcode-scan-input') as HTMLInputElement;
                    if (input) {
                        input.value = '';
                        input.focus();
                    }
                }, 2000);
            }
        } catch (error) {
            console.error('Error fetching product:', error);
            this.updateScanStatus('Error scanning barcode', 'error');
            setTimeout(() => {
                this.updateScanStatus('Ready to scan', 'ready');
                const input = document.getElementById('barcode-scan-input') as HTMLInputElement;
                if (input) {
                    input.value = '';
                    input.focus();
                }
            }, 2000);
        }
    }

    private updateScanStatus(message: string, status: string): void {
        const statusDiv = document.getElementById('scan-status');
        if (!statusDiv) return;
        
        const iconMap: { [key: string]: string } = {
            'ready': 'camera',
            'scanning': 'spinner fa-spin',
            'success': 'check-circle',
            'error': 'exclamation-triangle'
        };
        
        statusDiv.innerHTML = `<i class="fas fa-${iconMap[status] || 'camera'}"></i> ${message}`;
        statusDiv.className = `scan-status ${status}`;
    }

    private setupMobileMenu(): void {
        const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
        const navMenu = document.querySelector('.nav-menu');
        
        if (!mobileMenuToggle || !navMenu) return;

        mobileMenuToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', (e: Event) => {
            if (!mobileMenuToggle?.contains(e.target as Node) && !navMenu?.contains(e.target as Node)) {
                navMenu.classList.remove('active');
            }
        });
    }

    private setupModalClickOutside(): void {
        document.addEventListener('click', (e: Event) => {
            const shortcutsModal = document.getElementById('shortcuts-modal');
            if (!shortcutsModal) return;
            
            const modalContent = shortcutsModal.querySelector('.shortcuts-content');
            const shortcutsButton = document.getElementById('shortcuts-btn');
            
            if (modalContent && shortcutsModal.style.display === 'flex') {
                if (!modalContent?.contains(e.target as Node) && 
                    e.target !== shortcutsButton && 
                    !shortcutsButton?.contains(e.target as Node)) {
                    // Close modal if clicked outside
                    shortcutsModal.style.display = 'none';
                    document.body.style.overflow = '';
                }
            }
        });
    }

    private showNotification(message: string, type: 'success' | 'error' | 'warning' | 'info'): void {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${this.getNotificationIcon(type)}"></i>
            <span>${message}</span>
        `;
        
        // Style the notification
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '1rem 1.5rem',
            borderRadius: '0.5rem',
            color: 'white',
            fontWeight: '600',
            zIndex: '10001',
            opacity: '0',
            transform: 'translateX(100%)',
            transition: 'all 0.3s ease'
        });
        
        // Set background color based on type
        const bgColors: { [key: string]: string } = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };
        notification.style.background = bgColors[type] || bgColors.info;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    private getNotificationIcon(type: string): string {
        const icons: { [key: string]: string } = {
            success: 'check-circle',
            error: 'exclamation-triangle',
            warning: 'exclamation-circle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    // Cart Management Methods
    public addToCart(product: string, price: number, isOnSale: boolean = false, regularPrice: number | null = null, salePrice: number | null = null): void {
        const existingItem = this.cart.find(item => item.product === product);
        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            this.cart.push({ 
                product, 
                price, 
                regularPrice: regularPrice || price,
                salePrice: salePrice || undefined,
                isOnSale,
                quantity: 1 
            });
        }
        this.total += price;
        this.updateCart();
    }

    public removeFromCart(product: string, price: number): void {
        const existingItem = this.cart.find(item => item.product === product);
        if (existingItem) {
            if (existingItem.quantity > 1) {
                existingItem.quantity -= 1;
                this.total -= price;
            } else {
                // Remove the item completely if quantity is 1
                const index = this.cart.indexOf(existingItem);
                this.cart.splice(index, 1);
                this.total -= price;
            }
            this.updateCart();
        }
    }

    private updateCart(): void {
        const cartItems = document.getElementById('cart-items');
        if (!cartItems) return;

        cartItems.innerHTML = '';
        this.cart.forEach(item => {
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
                <button class="remove-btn" onclick="homePageManager.removeFromCart('${item.product}', ${item.price})">-</button>
            `;
            cartItems.appendChild(div);
        });
        
        const totalElement = document.getElementById('total');
        if (totalElement) {
            totalElement.innerHTML = 'R' + this.total.toFixed(2);
        }
        
        // Recalculate change when cart is updated
        this.calculateChange();
    }

    public calculateChange(): void {
        const cashReceivedElement = document.getElementById('cash-received') as HTMLInputElement;
        const changeDisplay = document.getElementById('change-display');
        const changeAmount = document.getElementById('change-amount');
        
        if (!cashReceivedElement || !changeDisplay || !changeAmount) return;
        
        const cashReceived = parseFloat(cashReceivedElement.value) || 0;
        
        if (cashReceived > 0 && this.total > 0) {
            const change = cashReceived - this.total;
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

    public clearCart(): void {
        this.cart = [];
        this.total = 0;
        
        // Clear all form fields
        const cashReceivedElement = document.getElementById('cash-received') as HTMLInputElement;
        const customerNameElement = document.getElementById('customer-name') as HTMLInputElement;
        const customerPhoneElement = document.getElementById('customer-phone') as HTMLInputElement;
        const changeDisplay = document.getElementById('change-display');
        
        if (cashReceivedElement) cashReceivedElement.value = '';
        if (customerNameElement) customerNameElement.value = '';
        if (customerPhoneElement) customerPhoneElement.value = '';
        if (changeDisplay) changeDisplay.style.display = 'none';
        
        this.updateCart();
        this.showNotification('Cart cleared', 'info');
    }

    public async saveOrder(): Promise<void> {
        const customerNameElement = document.getElementById('customer-name') as HTMLInputElement;
        const customerPhoneElement = document.getElementById('customer-phone') as HTMLInputElement;
        
        if (!customerNameElement || !customerPhoneElement) {
            this.showNotification('Customer form elements not found', 'error');
            return;
        }
        
        const customerName = customerNameElement.value.trim();
        const customerPhone = customerPhoneElement.value.trim();
        
        // Validate customer information
        if (!customerName || !customerPhone) {
            this.showNotification('Customer name and phone number are required', 'error');
            if (!customerName) {
                customerNameElement.focus();
            } else {
                customerPhoneElement.focus();
            }
            return;
        }
        
        // Validate phone number format
        const phoneRegex = /^[0-9]{10,15}$/;
        if (!phoneRegex.test(customerPhone)) {
            this.showNotification('Please enter a valid phone number (10-15 digits)', 'error');
            customerPhoneElement.focus();
            return;
        }
        
        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]') as HTMLInputElement;
        if (!csrfToken) {
            this.showNotification('Security token not found. Please refresh the page.', 'error');
            return;
        }
        
        try {
            const response = await fetch('/save_order/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken.value
                },
                body: JSON.stringify({
                    customer_name: customerName,
                    customer_phone: customerPhone,
                    items: this.cart,
                    total_amount: this.total
                })
            });
            
            const data = await response.json();
            console.log('Save order response:', data);
            
            if (data.success) {
                this.showNotification('Order saved successfully!', 'success');
                this.clearCart();
            } else {
                this.showNotification('Failed to save order: ' + (data.error || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showNotification('An error occurred while saving the order: ' + (error as Error).message, 'error');
        }
    }

    public async checkoutOrder(): Promise<void> {
        if (this.cart.length === 0) {
            this.showNotification('Cart is empty. Add items before checkout.', 'error');
            return;
        }
        
        const customerNameElement = document.getElementById('customer-name') as HTMLInputElement;
        const customerPhoneElement = document.getElementById('customer-phone') as HTMLInputElement;
        const cashReceivedElement = document.getElementById('cash-received') as HTMLInputElement;
        
        if (!customerNameElement || !customerPhoneElement || !cashReceivedElement) {
            this.showNotification('Form elements not found', 'error');
            return;
        }
        
        const customerName = customerNameElement.value.trim();
        const customerPhone = customerPhoneElement.value.trim();
        const cashReceived = parseFloat(cashReceivedElement.value) || 0;
        
        // Validate customer information
        if (!customerName || !customerPhone) {
            this.showNotification('Customer name and phone number are required to complete the order.', 'error');
            if (!customerName) {
                customerNameElement.focus();
            } else {
                customerPhoneElement.focus();
            }
            return;
        }
        
        // Validate phone number format
        const phoneRegex = /^[0-9]{10,15}$/;
        if (!phoneRegex.test(customerPhone)) {
            this.showNotification('Please enter a valid phone number (10-15 digits)', 'error');
            customerPhoneElement.focus();
            return;
        }
        
        // Validate payment
        if (cashReceived < this.total) {
            this.showNotification(`Insufficient payment. Customer needs to pay at least R${this.total.toFixed(2)}`, 'error');
            cashReceivedElement.focus();
            return;
        }
        
        const changeGiven = cashReceived - this.total;
        
        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]') as HTMLInputElement;
        if (!csrfToken) {
            this.showNotification('Security token not found. Please refresh the page.', 'error');
            return;
        }
        
        try {
            const response = await fetch('/checkout_order/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken.value
                },
                body: JSON.stringify({
                    customer_name: customerName,
                    customer_phone: customerPhone,
                    items: this.cart,
                    total: this.total,
                    cashReceived: cashReceived,
                    changeGiven: changeGiven
                })
            });
            
            console.log('Response status:', response.status);
            const data = await response.json();
            console.log('Response data:', data);
            
            if (data.status === 'success') {
                this.showNotification('Order completed successfully!', 'success');
                this.clearCart();
            } else {
                this.showNotification('Failed to complete order: ' + (data.message || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showNotification('An error occurred while processing the order: ' + (error as Error).message, 'error');
        }
    }

    // Public method to initialize from global scope
    public initialize(): void {
        console.log('🎯 TypeScript: HomePageManager initialized');
    }
}

// Create global instance
let homePageManager: HomePageManager;

// Initialize when DOM is ready
function initializeHomePage(): void {
    homePageManager = new HomePageManager();
    (window as any).homePageManager = homePageManager; // Make it globally accessible
    
    // Expose key methods for inline event handlers
    (window as any).clearCart = () => homePageManager.clearCart();
    (window as any).saveOrder = () => homePageManager.saveOrder();
    (window as any).checkoutOrder = () => homePageManager.checkoutOrder();
    (window as any).addToCartFromData = (element: HTMLElement) => {
        const productName = element.dataset.productName || '';
        const currentPrice = parseFloat(element.dataset.currentPrice || '0');
        const isOnSale = element.dataset.isOnSale === 'true';
        const regularPrice = parseFloat(element.dataset.regularPrice || '0');
        const salePrice = element.dataset.salePrice ? parseFloat(element.dataset.salePrice) : null;
        
        homePageManager.addToCart(productName, currentPrice, isOnSale, regularPrice, salePrice);
    };
    (window as any).toggleBarcodeScan = () => homePageManager.toggleBarcodeScan();
    (window as any).handleBarcodeScan = (event: KeyboardEvent) => homePageManager.handleBarcodeScan(event);
    (window as any).handleBarcodeInput = (event: Event) => homePageManager.handleBarcodeInput(event);
    (window as any).calculateChange = () => homePageManager.calculateChange();
    
    console.log('🌐 TypeScript: Global methods exposed and ready');
}

// Auto-initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeHomePage);
} else {
    initializeHomePage();
}

// Export for TypeScript modules
export { HomePageManager };
