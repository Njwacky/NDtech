class FoodScanner {
    constructor() {
        this.codeReader = null;
        this.currentDeviceId = null;
        this.isScanning = false;
        this.scanHistory = this.loadHistory();
        this.currentTab = 'scanner';
        
        this.initializeElements();
        this.bindEvents();
        this.displayHistory();
    }

    initializeElements() {
        this.elements = {
            // Scanner elements
            video: document.getElementById('video'),
            startBtn: document.getElementById('startScanner'),
            stopBtn: document.getElementById('stopScanner'),
            switchBtn: document.getElementById('switchCamera'),
            manualInput: document.getElementById('manualBarcode'),
            lookupBtn: document.getElementById('lookupBarcode'),
            statusMessage: document.getElementById('statusMessage'),
            scanningIndicator: document.getElementById('scanningIndicator'),
            
            // Results elements
            multipleResults: document.getElementById('multipleResults'),
            resultsContainer: document.getElementById('resultsContainer'),
            
            // Browser elements
            restaurantSelect: document.getElementById('restaurantSelect'),
            menuGrid: document.getElementById('menuGrid'),
            
            // History elements
            historyList: document.getElementById('historyList'),
            clearHistoryBtn: document.getElementById('clearHistory'),
            
            // Tab buttons
            tabButtons: document.querySelectorAll('.tab-button'),
            tabContents: document.querySelectorAll('.tab-content')
        };
    }

    bindEvents() {
        // Scanner events
        this.elements.startBtn.addEventListener('click', () => this.startScanning());
        this.elements.stopBtn.addEventListener('click', () => this.stopScanning());
        this.elements.switchBtn.addEventListener('click', () => this.switchCamera());
        this.elements.lookupBtn.addEventListener('click', () => this.manualLookup());
        
        // Allow Enter key for manual input
        this.elements.manualInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.manualLookup();
            }
        });
        
        // History events
        this.elements.clearHistoryBtn.addEventListener('click', () => this.clearHistory());
        
        // Tab switching
        this.elements.tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tabName = button.getAttribute('onclick').match(/switchTab\('(.+)'\)/)[1];
                this.switchTab(tabName);
            });
        });
    }

    switchTab(tabName) {
        // Update tab buttons
        this.elements.tabButtons.forEach(button => {
            button.classList.remove('active');
        });
        
        // Find and activate the clicked tab button
        this.elements.tabButtons.forEach(button => {
            if (button.getAttribute('onclick').includes(tabName)) {
                button.classList.add('active');
            }
        });
        
        // Update tab contents
        this.elements.tabContents.forEach(content => {
            content.classList.remove('active');
        });
        
        document.getElementById(`${tabName}-tab`).classList.add('active');
        this.currentTab = tabName;
        
        // Stop scanner when switching away from scanner tab
        if (tabName !== 'scanner' && this.isScanning) {
            this.stopScanning();
        }
    }

    async startScanning() {
        try {
            this.showStatus('Requesting camera access...', 'info');
            this.elements.scanningIndicator.classList.add('active');
            
            this.codeReader = new ZXing.BrowserMultiFormatReader();
            
            let devices = [];
            let deviceId = null;
            
            try {
                // Try to enumerate devices
                devices = await this.codeReader.listVideoInputDevices();
                console.log('Found devices:', devices);
                
                if (devices.length === 0) {
                    throw new Error('No camera devices found');
                }
                
                // Use the first camera or the previously selected one
                deviceId = this.currentDeviceId || devices[0].deviceId;
                
            } catch (enumerateError) {
                console.warn('Device enumeration failed, trying fallback:', enumerateError);
                
                // Fallback: Try to access camera without specific device ID
                try {
                    // Request camera permission first
                    const stream = await navigator.mediaDevices.getUserMedia({ 
                        video: { facingMode: 'environment' } 
                    });
                    stream.getTracks().forEach(track => track.stop());
                    
                    // If we got here, camera access is available
                    this.showStatus('Camera access granted, starting scanner...', 'info');
                    
                    // Try starting without device ID (let browser choose)
                    await this.codeReader.decodeFromVideoDevice(undefined, this.elements.video, (result, err) => {
                        if (result) {
                            this.handleBarcodeResult(result.text);
                        }
                    });
                    
                    this.currentDeviceId = null;
                    this.isScanning = true;
                    
                    this.elements.startBtn.disabled = true;
                    this.elements.stopBtn.disabled = false;
                    this.elements.switchBtn.disabled = true;
                    
                    this.showStatus('Scanner active - Point camera at barcode', 'success');
                    this.elements.scanningIndicator.classList.remove('active');
                    return;
                    
                } catch (cameraError) {
                    throw new Error('Camera access denied or not available: ' + cameraError.message);
                }
            }
            
            // If we got here, device enumeration worked
            await this.codeReader.decodeFromVideoDevice(deviceId, this.elements.video, (result, err) => {
                if (result) {
                    this.handleBarcodeResult(result.text);
                }
            });

            this.currentDeviceId = deviceId;
            this.isScanning = true;
            
            this.elements.startBtn.disabled = true;
            this.elements.stopBtn.disabled = false;
            this.elements.switchBtn.disabled = devices.length <= 1;
            
            this.showStatus('Scanner active - Point camera at barcode', 'success');
            this.elements.scanningIndicator.classList.remove('active');
            
        } catch (error) {
            console.error('Scanner error:', error);
            
            // Provide more specific error messages
            let errorMessage = error.message;
            if (error.message.includes('Permission denied')) {
                errorMessage = 'Camera permission denied. Please allow camera access in your browser settings.';
            } else if (error.message.includes('not found') || error.message.includes('enumerate')) {
                errorMessage = 'No camera devices found. Please ensure you have a camera connected.';
            } else if (error.message.includes('NotAllowedError')) {
                errorMessage = 'Camera access blocked. Please allow camera access and refresh the page.';
            } else if (error.message.includes('NotFoundError')) {
                errorMessage = 'No camera found. Please connect a camera and try again.';
            }
            
            this.showStatus('Failed to start scanner: ' + errorMessage, 'error');
            this.elements.scanningIndicator.classList.remove('active');
        }
    }

    stopScanning() {
        if (this.codeReader && this.isScanning) {
            this.codeReader.reset();
            this.isScanning = false;
            
            this.elements.startBtn.disabled = false;
            this.elements.stopBtn.disabled = true;
            this.elements.switchBtn.disabled = true;
            
            this.showStatus('Scanner stopped', 'info');
        }
    }

    async switchCamera() {
        if (!this.codeReader) return;
        
        try {
            const devices = await this.codeReader.listVideoInputDevices();
            if (devices.length <= 1) {
                this.showStatus('Only one camera available or camera enumeration not supported', 'info');
                return;
            }
            
            const currentIndex = devices.findIndex(d => d.deviceId === this.currentDeviceId);
            const nextIndex = (currentIndex + 1) % devices.length;
            const nextDeviceId = devices[nextIndex].deviceId;
            
            this.stopScanning();
            this.currentDeviceId = nextDeviceId;
            await this.startScanning();
            
        } catch (error) {
            console.error('Camera switch error:', error);
            this.showStatus('Camera switching not available - device enumeration failed', 'error');
        }
    }

    manualLookup() {
        const barcode = this.elements.manualInput.value.trim();
        if (!barcode) {
            this.showStatus('Please enter a barcode number', 'error');
            return;
        }
        
        this.handleBarcodeResult(barcode);
    }

    async handleBarcodeResult(barcode) {
        try {
            this.showStatus('Looking up barcode...', 'info');
            
            // Stop scanning while processing
            if (this.isScanning) {
                this.codeReader.reset();
            }
            
            // Use the integrated food scanner API
            const response = await fetch(`/api/food/scanner/lookup/${barcode}/`);
            const data = await response.json();
            
            if (data.success && data.results && data.results.length > 0) {
                this.displayMultipleResults(data.results, barcode);
                this.addToHistory(barcode, `Found ${data.total_found} items`);
                this.showStatus(`Found ${data.total_found} items!`, 'success');
            } else {
                this.showStatus(`No items found: ${data.message}`, 'error');
                this.hideResults();
                this.addToHistory(barcode, 'Not Found');
            }
            
        } catch (error) {
            console.error('Lookup error:', error);
            this.showStatus('Error looking up barcode', 'error');
            this.hideResults();
        }
    }

    displayMultipleResults(results, barcode) {
        const container = this.elements.resultsContainer;
        
        container.innerHTML = results.map(result => {
            const isPosSystem = result.source === 'pos_system';
            const cardClass = isPosSystem ? 'pos-system' : 'food-ordering';
            const sourceClass = isPosSystem ? 'source-pos' : 'source-food';
            const sourceText = isPosSystem ? 'POS System' : 'Food Ordering';
            
            let priceDisplay = '';
            if (result.is_on_sale && result.sale_price) {
                priceDisplay = `
                    <div>
                        <span style="text-decoration: line-through; color: #999;">R${result.price.toFixed(2)}</span>
                        <span style="color: #28a745; font-weight: bold; margin-left: 8px;">R${result.sale_price.toFixed(2)}</span>
                        <span style="background: #dc3545; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; margin-left: 8px;">-${result.discount_percentage}%</span>
                    </div>
                `;
            } else {
                priceDisplay = `<div style="color: #28a745; font-weight: bold;">R${result.price.toFixed(2)}</div>`;
            }
            
            let foodInfo = '';
            if (!isPosSystem) {
                foodInfo = `
                    <div class="food-info">
                        <div><strong>Restaurant:</strong> ${result.restaurant}</div>
                        <div><strong>Prep Time:</strong> ${result.preparation_time} mins</div>
                        ${result.is_vegetarian ? '<span class="badge badge-vegetarian">Vegetarian</span>' : ''}
                        ${result.is_vegan ? '<span class="badge badge-vegan">Vegan</span>' : ''}
                    </div>
                `;
            }
            
            let matchInfo = '';
            if (result.match_type) {
                matchInfo = `<div class="match-type">Match type: ${result.match_type}</div>`;
            }
            
            return `
                <div class="result-card ${cardClass}">
                    <div class="result-header">
                        <div>
                            <h4>${result.name}</h4>
                            <span class="result-source ${sourceClass}">${sourceText}</span>
                        </div>
                        <div>
                            ${priceDisplay}
                        </div>
                    </div>
                    
                    <div class="result-details">
                        <p>${result.description || 'No description available'}</p>
                        <div><strong>Category:</strong> ${result.category}</div>
                        ${isPosSystem ? `<div><strong>Stock:</strong> ${result.stock}</div>` : foodInfo}
                        ${matchInfo}
                    </div>
                    
                    <div class="result-actions">
                        ${isPosSystem ? 
                            `<button class="btn-add-to-cart" onclick="foodScanner.addToCart(${result.id}, '${result.name}', ${result.price}, '${result.source}')">
                                🛒 Add to Cart
                            </button>` :
                            `<button class="btn-create-pos-product" onclick="foodScanner.createPosProduct(${result.id}, '${result.name}', ${result.price}, '${barcode}')">
                                ➕ Add to POS
                            </button>`
                        }
                        <button class="btn btn-secondary" onclick="foodScanner.viewDetails('${result.source}', ${result.id})">
                            👁️ View Details
                        </button>
                    </div>
                </div>
            `;
        }).join('');
        
        this.elements.multipleResults.style.display = 'block';
    }

    hideResults() {
        this.elements.multipleResults.style.display = 'none';
    }

    async createPosProduct(menuItemId, itemName, price, barcode) {
        try {
            this.showStatus('Creating POS product...', 'info');
            
            const response = await fetch('/api/food/add-to-pos/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    menu_item_id: menuItemId,
                    barcode: barcode,
                    quantity: 1
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showStatus(`Added "${itemName}" to POS!`, 'success');
                this.addToHistory(barcode, `Added ${itemName} to POS`);
            } else {
                this.showStatus(`Error: ${data.error}`, 'error');
            }
            
        } catch (error) {
            console.error('Error creating POS product:', error);
            this.showStatus('Error creating POS product', 'error');
        }
    }

    addToCart(productId, productName, price, source) {
        // This would integrate with your POS cart system
        // For now, just show a success message
        this.showStatus(`Added "${productName}" to cart!`, 'success');
        this.addToHistory(`POS${productId}`, `Added ${productName} to cart`);
        
        // You could emit an event or call a global cart function here
        if (window.posCart) {
            window.posCart.addItem(productId, productName, price, 1);
        }
    }

    viewDetails(source, itemId) {
        if (source === 'pos_system') {
            window.open(`/upc/lookup/POS${itemId}/`, '_blank');
        } else {
            // For food ordering items, you might need to create a detail view
            this.showStatus('Food item details view not implemented yet', 'info');
        }
    }

    async loadRestaurantMenu() {
        const restaurantId = this.elements.restaurantSelect.value;
        
        if (!restaurantId) {
            this.elements.menuGrid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #7f8c8d;">Please select a restaurant</p>';
            return;
        }
        
        try {
            this.showStatus('Loading menu...', 'info');
            
            // This would need an API endpoint to get menu items
            // For now, we'll use the food ordering API
            const response = await fetch(`/food_ordering/api/v1/menu/?restaurant_id=${restaurantId}`);
            const data = await response.json();
            
            if (data.results && data.results.length > 0) {
                this.displayMenuItems(data.results);
            } else {
                this.elements.menuGrid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #7f8c8d;">No menu items available for this restaurant</p>';
            }
            
        } catch (error) {
            console.error('Error loading menu:', error);
            this.elements.menuGrid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #dc3545;">Error loading menu</p>';
        }
    }

    displayMenuItems(menuItems) {
        this.elements.menuGrid.innerHTML = menuItems.map(item => `
            <div class="menu-item-card">
                ${item.image ? `<img src="${item.image}" alt="${item.name}" class="menu-item-image">` : ''}
                <div class="menu-item-name">${item.name}</div>
                <div class="menu-item-price">R${parseFloat(item.price).toFixed(2)}</div>
                <div class="menu-item-restaurant">${item.restaurant || 'Restaurant'}</div>
                <p>${item.description || 'No description available'}</p>
                
                <div class="dietary-badges">
                    ${item.is_vegetarian ? '<span class="badge badge-vegetarian">Vegetarian</span>' : ''}
                    ${item.is_vegan ? '<span class="badge badge-vegan">Vegan</span>' : ''}
                </div>
                
                <div class="prep-time">⏱️ ${item.preparation_time || 15} mins</div>
                
                <div class="result-actions" style="margin-top: 15px;">
                    <button class="btn-create-pos-product" onclick="foodScanner.createPosProduct(${item.id}, '${item.name}', ${item.price}, 'MENU${item.id}')">
                        ➕ Add to POS
                    </button>
                </div>
            </div>
        `).join('');
    }

    showStatus(message, type) {
        // Use toast system if available
        if (window.toastManager) {
            window.toastManager.showToast(message, type);
        } else {
            // Fallback to inline status message
            const statusEl = this.elements.statusMessage;
            statusEl.textContent = message;
            statusEl.className = `status-message ${type} show`;
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                statusEl.classList.remove('show');
            }, 5000);
        }
    }

    addToHistory(barcode, result) {
        const timestamp = new Date().toLocaleString();
        this.scanHistory.unshift({
            barcode: barcode,
            result: result,
            timestamp: timestamp,
            tab: this.currentTab
        });
        
        // Keep only last 50 items
        if (this.scanHistory.length > 50) {
            this.scanHistory = this.scanHistory.slice(0, 50);
        }
        
        this.saveHistory();
        this.displayHistory();
    }

    displayHistory() {
        const historyList = this.elements.historyList;
        
        if (this.scanHistory.length === 0) {
            historyList.innerHTML = '<p style="text-align: center; color: #7f8c8d;">No scans yet</p>';
            return;
        }
        
        historyList.innerHTML = this.scanHistory.map(item => `
            <div class="history-item">
                <div>
                    <div class="history-barcode">${item.barcode}</div>
                    <div style="font-size: 12px; color: #7f8c8d;">${item.result}</div>
                    <div style="font-size: 11px; color: #999;">Tab: ${item.tab}</div>
                </div>
                <div class="history-time">${item.timestamp}</div>
            </div>
        `).join('');
    }

    saveHistory() {
        localStorage.setItem('foodScanHistory', JSON.stringify(this.scanHistory));
    }

    loadHistory() {
        const saved = localStorage.getItem('foodScanHistory');
        return saved ? JSON.parse(saved) : [];
    }

    clearHistory() {
        if (confirm('Are you sure you want to clear the scan history?')) {
            this.scanHistory = [];
            this.saveHistory();
            this.displayHistory();
            this.showStatus('History cleared', 'info');
        }
    }

    getCSRFToken() {
        // Get CSRF token from cookies
        const name = 'csrftoken';
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
}

// Global function for tab switching
function switchTab(tabName) {
    if (window.foodScanner) {
        window.foodScanner.switchTab(tabName);
    }
}

// Initialize the scanner when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.foodScanner = new FoodScanner();
});
