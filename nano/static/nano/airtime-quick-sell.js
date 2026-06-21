/**
 * Airtime Quick Sell Interactive Logic
 * Handles mode selection, network/template selection, and sale processing.
 */

$(document).ready(function() {
    console.log("Airtime Quick Sell Page Loading...");

    // State Management
    let state = {
        mode: null, // 'inventory', 'quick', 'custom'
        network: null,
        amount: 0,
        price: 0,
        type: 'airtime',
        productName: '',
        selectedProductId: null
    };

    // Mode Selection
    $('.action-card').on('click', function() {
        const modeId = $(this).attr('id');
        $('.action-card').removeClass('active');
        $(this).addClass('active');

        // Reset state
        resetSections();

        if (modeId === 'sellFromInventoryCard') {
            state.mode = 'inventory';
            $('#inventorySection').fadeIn();
            loadInventoryProducts();
        } else if (modeId === 'managerQuickSellCard' || modeId === 'useCreditCard') {
            state.mode = 'quick';
            $('#networkSelector').fadeIn();
        } else if (modeId === 'customAmountCard') {
            state.mode = 'custom';
            $('#networkSelector').fadeIn();
        }
    });

    // Network Selection
    $('.network-btn').on('click', function() {
        state.network = $(this).data('network');
        $('.network-btn').removeClass('selected');
        $(this).addClass('selected');

        if (state.mode === 'quick') {
            $('#amountSelector').fadeIn();
            $('.template-grid').show();
            $('.custom-amount-form').hide();
        } else if (state.mode === 'custom') {
            $('#amountSelector').fadeIn();
            $('.template-grid').hide();
            $('.custom-amount-form').show();
            updateCustomPrice();
        }
    });

    // Template Selection
    $('.template-btn').on('click', function() {
        state.amount = $(this).data('amount');
        state.type = $(this).data('type');
        state.price = parseFloat($(this).find('.template-price').text().replace('R', ''));
        state.productName = `${state.network.toUpperCase()} ${state.amount} ${state.type}`;

        $('.template-btn').removeClass('selected');
        $(this).addClass('selected');

        showCustomerDetails();
    });

    // Custom Amount Logic
    $('#customAmount, #customType').on('input change', function() {
        updateCustomPrice();
    });

    function updateCustomPrice() {
        const amount = parseFloat($('#customAmount').val()) || 0;
        const type = $('#customType').val();
        const markup = type === 'airtime' ? 2 : 3;
        const price = amount > 0 ? amount + markup : 0;

        $('#calculatedPrice').text(`R${price.toFixed(2)}`);
        
        state.amount = amount;
        state.type = type;
        state.price = price;
        state.productName = `${state.network.toUpperCase()} ${state.amount} ${state.type} (Custom)`;
    }

    $('#useCustomAmount').on('click', function() {
        if (state.amount <= 0) {
            alert("Please enter a valid amount.");
            return;
        }
        showCustomerDetails();
    });

    // Inventory Selection
    $(document).on('click', '.inventory-product-card', function() {
        state.selectedProductId = $(this).data('product-id');
        state.productName = $(this).find('.inventory-product-name').text();
        state.price = parseFloat($(this).data('price'));
        state.network = $(this).data('network');
        state.amount = parseFloat($(this).data('value'));
        state.type = $(this).data('type');

        $('.inventory-product-card').removeClass('selected');
        $(this).addClass('selected');

        showCustomerDetails();
    });

    // Customer Details
    function showCustomerDetails() {
        $('#selectedNetwork').text(state.network.toUpperCase());
        $('#selectedType').text(state.type.charAt(0).toUpperCase() + state.type.slice(1));
        $('#selectedAmount').text(`R${state.amount}`);
        $('#selectedPrice').text(`R${state.price.toFixed(2)}`);

        $('#customerDetails').fadeIn();
        // Scroll to customer details
        $('html, body').animate({
            scrollTop: $("#customerDetails").offset().top - 20
        }, 500);
    }

    $('#backToAmount').on('click', function() {
        $('#customerDetails').hide();
    });

    // Process Sale
    $('#processQuickSell').on('click', async function() {
        const phone = $('#customerPhone').val().trim();
        if (!phone || phone.length < 10) {
            alert("Please enter a valid phone number.");
            return;
        }

        const $btn = $(this);
        $btn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Processing...');

        const payload = {
            network: state.network,
            amount: state.amount,
            type: state.type,
            price: state.price,
            customer_phone: phone,
            product_name: state.productName,
            product_id: state.selectedProductId,
            use_credit: state.mode === 'quick'
        };

        try {
            const response = await fetch('/api/airtime/cashier-process/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val()
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (data.success) {
                alert(data.message || "Sale completed successfully!");
                window.location.href = "/airtime/history-review/";
            } else {
                alert("Error: " + (data.error || "Unknown error occurred"));
                $btn.prop('disabled', false).html('<i class="fas fa-shopping-cart"></i> Process Sale');
            }
        } catch (error) {
            console.error("Sale Error:", error);
            alert("An error occurred. Please check your connection.");
            $btn.prop('disabled', false).html('<i class="fas fa-shopping-cart"></i> Process Sale');
        }
    });

    // Helper Functions
    function resetSections() {
        $('#inventorySection, #networkSelector, #amountSelector, #customerDetails').hide();
        $('.network-btn, .template-btn, .inventory-product-card').removeClass('selected');
        $('#customerPhone').val('');
    }

    async function loadInventoryProducts() {
        const $grid = $('#inventoryGrid');
        $grid.html('<div class="col-12 text-center p-5"><i class="fas fa-spinner fa-spin fa-2x"></i><p>Loading products...</p></div>');

        try {
            const response = await fetch('/api/airtime/product-status/');
            const data = await response.json();

            if (data.success && data.products.length > 0) {
                let html = '';
                data.products.forEach(p => {
                    html += `
                        <div class="inventory-product-card" 
                             data-product-id="${p.id}" 
                             data-price="${p.price}" 
                             data-network="${p.network}" 
                             data-value="${p.value}"
                             data-type="${p.airtime_type}">
                            <div class="inventory-product-header">
                                <span class="inventory-network-badge ${p.network}">${p.network.toUpperCase()}</span>
                                <span class="inventory-stock-status ${p.stock > 0 ? 'in-stock' : 'out-of-stock'}">
                                    ${p.stock > 0 ? 'In Stock' : 'Out of Stock'}
                                </span>
                            </div>
                            <div class="inventory-product-name">${p.name}</div>
                            <div class="inventory-product-details">
                                <div class="inventory-detail-item">
                                    <span class="inventory-detail-label">Type</span>
                                    <span class="inventory-detail-value">${p.airtime_type}</span>
                                </div>
                                <div class="inventory-detail-item">
                                    <span class="inventory-detail-label">Value</span>
                                    <span class="inventory-detail-value">R${p.value}</span>
                                </div>
                            </div>
                            <div class="inventory-price-row">
                                <div class="inventory-price">R${p.price}</div>
                            </div>
                        </div>
                    `;
                });
                $grid.html(html);
            } else {
                $grid.html('<div class="inventory-no-products"><i class="fas fa-info-circle"></i><h4>No Products Available</h4><p>No active airtime products found in inventory.</p></div>');
            }
        } catch (error) {
            $grid.html('<div class="alert alert-danger">Failed to load products.</div>');
        }
    }
});
