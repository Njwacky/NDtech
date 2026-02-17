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
