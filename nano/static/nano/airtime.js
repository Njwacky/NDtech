/**
 * Airtime Pages JavaScript Enhancement
 * Provides interactive functionality for all airtime-related pages
 */

// Global state management
const AirtimeApp = {
    currentMode: null,
    selectedProduct: null,
    selectedNetwork: null,
    selectedAmount: null,
    selectedType: null,
    availableCredit: 0,
    inventoryProducts: [],
    
    // Initialize the app
    init() {
        this.bindEvents();
        this.loadInventoryProducts();
        this.initializeModeHandlers();
        this.setupKeyboardShortcuts();
        this.setupNotifications();
        this.initializeTooltips();
    },

    // Bind global events
    bindEvents() {
        // Product card clicks
        document.addEventListener('click', (e) => {
            if (e.target.closest('.sell-btn')) {
                this.handleProductSell(e.target.closest('.sell-btn'));
            }
            if (e.target.closest('.product-card')) {
                this.handleProductCardClick(e.target.closest('.product-card'));
            }
            if (e.target.closest('.status-toggle-btn')) {
                this.handleStatusToggle(e.target.closest('.status-toggle-btn'));
            }
        });

        // Quick sell action cards
        const actionCards = document.querySelectorAll('.action-card');
        actionCards.forEach(card => {
            card.addEventListener('click', () => this.handleActionCard(card));
        });

        // Network selection
        document.addEventListener('click', (e) => {
            if (e.target.closest('.network-btn')) {
                this.handleNetworkSelection(e.target.closest('.network-btn'));
            }
        });

        // Amount templates
        document.addEventListener('click', (e) => {
            if (e.target.closest('.template-btn')) {
                this.handleAmountSelection(e.target.closest('.template-btn'));
            }
        });

        // Form inputs
        document.addEventListener('input', (e) => {
            if (e.target.id === 'customAmount') {
                this.calculateCustomPrice();
            }
            if (e.target.id === 'quickQuantity') {
                this.updateQuickTotal();
            }
        });

        // Phone number validation
        document.addEventListener('input', (e) => {
            if (e.target.id === 'customerPhone' || e.target.id === 'quickCustomerPhone') {
                this.validatePhoneNumber(e.target);
            }
        });

        // Button actions
        this.bindButtonActions();
    },

    // Handle product card sell button
    handleProductSell(button) {
        const productId = button.dataset.productId;
        const productName = button.dataset.productName;
        const productPrice = button.dataset.productPrice;
        
        if (button.classList.contains('disabled')) {
            this.showNotification('This product is out of stock', 'error');
            return;
        }

        this.selectedProduct = {
            id: productId,
            name: productName,
            price: parseFloat(productPrice)
        };

        this.showQuickSaleForm();
    },

    // Handle product card selection (for inventory mode)
    handleProductCardClick(card) {
        if (event.target.closest('.sell-btn') || event.target.closest('.status-toggle-btn')) {
            return;
        }

        // Remove previous selection
        document.querySelectorAll('.product-card').forEach(c => c.classList.remove('selected'));
        
        // Add selection to clicked card
        card.classList.add('selected');
        
        // Extract product data
        const productId = card.querySelector('.sell-btn')?.dataset.productId;
        if (productId) {
            this.loadProductDetails(productId);
        }
    },

    // Handle status toggle for products
    async handleStatusToggle(button) {
        const productId = button.dataset.productId;
        const currentStatus = button.dataset.currentStatus;
        const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
        
        // Show loading state
        button.classList.add('loading');
        button.disabled = true;

        try {
            const response = await this.updateProductStatus(productId, newStatus);
            
            if (response.success) {
                // Update button state
                button.dataset.currentStatus = newStatus;
                button.className = `status-toggle-btn ${newStatus}`;
                
                if (newStatus === 'active') {
                    button.innerHTML = '<i class="fas fa-check-circle"></i><span>Active</span>';
                    this.showNotification('Product activated successfully', 'success');
                } else {
                    button.innerHTML = '<i class="fas fa-pause-circle"></i><span>Inactive</span>';
                    this.showNotification('Product deactivated', 'info');
                }
            } else {
                this.showNotification(response.message || 'Failed to update status', 'error');
            }
        } catch (error) {
            this.showNotification('Error updating product status', 'error');
        } finally {
            button.classList.remove('loading');
            button.disabled = false;
        }
    },

    // Update product status via API
    async updateProductStatus(productId, status) {
        const csrfToken = this.getCSRFToken();
        
        try {
            const response = await fetch('/api/airtime/product-status/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({
                    product_id: productId,
                    status: status
                })
            });
            
            return await response.json();
        } catch (error) {
            console.error('Error updating product status:', error);
            return { success: false, message: 'Network error' };
        }
    },

    // Handle quick action cards
    handleActionCard(card) {
        const cardId = card.id;
        
        // Remove active state from all cards
        document.querySelectorAll('.action-card').forEach(c => c.classList.remove('active'));
        card.classList.add('active');

        // Hide all sections first
        this.hideAllSections();

        switch(cardId) {
            case 'sellFromInventoryCard':
                this.showInventorySection();
                break;
            case 'useCreditCard':
                this.showNetworkSelector();
                this.currentMode = 'credit';
                break;
            case 'managerQuickSellCard':
                this.showNetworkSelector();
                this.currentMode = 'manager';
                break;
            case 'customAmountCard':
                this.showNetworkSelector();
                this.currentMode = 'custom';
                break;
            default:
                break;
        }
    },

    hideAllSections() {
        ['inventorySection', 'networkSelector', 'amountSelector', 'customerDetails'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });
    },

    showInventorySection() {
        this.hideAllSections();
        const el = document.getElementById('inventorySection');
        if (el) el.style.display = 'block';
    },

    showNetworkSelector() {
        this.hideAllSections();
        const el = document.getElementById('networkSelector');
        if (el) el.style.display = 'block';
    },

    showAmountSelector() {
        this.hideAllSections();
        const el = document.getElementById('amountSelector');
        if (el) el.style.display = 'block';
    },

    showQuickSaleForm() {
        const el = document.getElementById('customerDetails');
        if (el) el.style.display = 'block';
    },

    handleNetworkSelection(btn) {
        if (!btn) return;
        this.selectedNetwork = btn.dataset.network;
        document.querySelectorAll('.network-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        this.showAmountSelector();
    },

    handleAmountSelection(btn) {
        if (!btn) return;
        this.selectedAmount = parseFloat(btn.dataset.amount) || 0;
        this.selectedType = btn.dataset.type || 'airtime';
        document.querySelectorAll('.template-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        document.getElementById('customerDetails').style.display = 'block';
    },

    calculateCustomPrice() {
        const input = document.getElementById('customAmount');
        if (!input) return;
        const amount = parseFloat(input.value) || 0;
        const typeSelect = document.getElementById('customType');
        const type = typeSelect ? typeSelect.value : 'airtime';
        const markup = type === 'airtime' ? 2 : 3;
        const price = amount + markup;
        const priceEl = document.getElementById('calculatedPrice');
        if (priceEl) priceEl.textContent = 'R' + price.toFixed(2);
    },

    updateQuickTotal() {},
    validatePhoneNumber(input) {
        if (!input) return;
        const val = input.value.replace(/\D/g, '');
        input.value = val;
    },

    loadProductDetails(productId) {},
    loadInventoryProducts() {
        const grid = document.getElementById('inventoryGrid');
        if (!grid) return;
        fetch('/airtime/?fetch_products=true')
            .then(r => r.json())
            .then(data => {
                if (data.products && data.products.length) {
                    grid.innerHTML = data.products.map(p => `
                        <div class="inventory-product-card product-card" data-product-id="${p.id}">
                            <div class="product-name">${p.name}</div>
                            <div class="product-price">R${p.price.toFixed(2)}</div>
                            <button class="sell-btn action-btn" data-product-id="${p.id}" data-product-name="${p.name}" data-product-price="${p.price}" ${p.stock < 1 ? 'disabled class="disabled"' : ''}>
                                <i class="fas fa-shopping-cart"></i> Sell
                            </button>
                        </div>
                    `).join('');
                } else {
                    grid.innerHTML = '<p>No products available</p>';
                }
            })
            .catch(() => { grid.innerHTML = '<p>Error loading products</p>'; });
    },

    bindButtonActions() {
        const processBtn = document.getElementById('processQuickSell');
        const useCustomBtn = document.getElementById('useCustomAmount');
        const backBtn = document.getElementById('backToAmount');
        if (processBtn) {
            processBtn.addEventListener('click', () => this.processQuickSale());
        }
        if (useCustomBtn) {
            useCustomBtn.addEventListener('click', () => {
                const amount = parseFloat(document.getElementById('customAmount')?.value) || 0;
                const typeSelect = document.getElementById('customType');
                const type = typeSelect ? typeSelect.value : 'airtime';
                if (amount > 0) {
                    this.selectedAmount = amount;
                    this.selectedType = type;
                    this.selectedNetwork = this.selectedNetwork || 'mtn';
                    this.selectedProduct = { price: amount + (type === 'airtime' ? 2 : 3) };
                    this.showQuickSaleForm();
                }
            });
        }
        if (backBtn) backBtn.addEventListener('click', () => this.showAmountSelector());
    },

    async processQuickSale() {
        const phoneInput = document.getElementById('customerPhone') || document.getElementById('quickCustomerPhone');
        const phone = phoneInput ? phoneInput.value.replace(/\D/g, '') : '';
        if (!phone || phone.length < 10) {
            this.showNotification('Please enter a valid phone number', 'error');
            return;
        }
        const productId = this.selectedProduct?.id;
        const price = this.selectedProduct?.price || (this.selectedAmount + 2);
        const productName = this.selectedProduct?.name || `${this.selectedNetwork} R${this.selectedAmount} ${this.selectedType}`;
        if (!productId && !this.selectedAmount) {
            this.showNotification('Please select a product or amount', 'error');
            return;
        }
        const csrfToken = this.getCSRFToken();
        const url = productId ? '/airtime/process/' : '/api/airtime/cashier-process/';
        const body = productId ? {
            product_id: productId,
            customer_phone: phone,
            quantity: 1
        } : {
            network: this.selectedNetwork || 'mtn',
            amount: this.selectedAmount || 0,
            type: this.selectedType || 'airtime',
            price: price,
            customer_phone: phone,
            product_name: productName
        };
        try {
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify(body)
            });
            const data = await res.json();
            if (data.success) {
                this.showNotification('Sale completed successfully!', 'success');
                setTimeout(() => location.reload(), 1500);
            } else {
                this.showNotification(data.error || 'Sale failed', 'error');
            }
        } catch (e) {
            this.showNotification('Network error', 'error');
        }
    },

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || '';
    },

    showNotification(message, type) {
        if (typeof showToast === 'function') showToast(message, type);
        else if (typeof alert !== 'undefined') alert(message);
    },

    initializeModeHandlers() {},
    setupKeyboardShortcuts() {},
    setupNotifications() {},
    initializeTooltips() {}
};

document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.airtime-container, .cashier-airtime-container, .action-card')) {
        try { AirtimeApp.init(); } catch (e) { console.warn('AirtimeApp init:', e); }
    }
});
