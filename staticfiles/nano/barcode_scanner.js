class BarcodeScanner {
    constructor() {
        this.codeReader = null;
        this.currentDeviceId = null;
        this.isScanning = false;
        this.scanHistory = this.loadHistory();
        
        this.initializeElements();
        this.bindEvents();
        this.displayHistory();
    }

    initializeElements() {
        this.elements = {
            video: document.getElementById('video'),
            startBtn: document.getElementById('startScanner'),
            stopBtn: document.getElementById('stopScanner'),
            switchBtn: document.getElementById('switchCamera'),
            manualInput: document.getElementById('manualBarcode'),
            lookupBtn: document.getElementById('lookupBarcode'),
            statusMessage: document.getElementById('statusMessage'),
            scanningIndicator: document.getElementById('scanningIndicator'),
            scanResult: document.getElementById('scanResult'),
            historyList: document.getElementById('historyList'),
            clearHistoryBtn: document.getElementById('clearHistory'),
            addToCartBtn: document.getElementById('addToCart'),
            viewDetailsBtn: document.getElementById('viewDetails'),
            scanAnotherBtn: document.getElementById('scanAnother')
        };
    }

    bindEvents() {
        this.elements.startBtn.addEventListener('click', () => this.startScanning());
        this.elements.stopBtn.addEventListener('click', () => this.stopScanning());
        this.elements.switchBtn.addEventListener('click', () => this.switchCamera());
        this.elements.lookupBtn.addEventListener('click', () => this.manualLookup());
        this.elements.clearHistoryBtn.addEventListener('click', () => this.clearHistory());
        this.elements.addToCartBtn.addEventListener('click', () => this.addToCart());
        this.elements.viewDetailsBtn.addEventListener('click', () => this.viewDetails());
        this.elements.scanAnotherBtn.addEventListener('click', () => this.scanAnother());
        
        // Allow Enter key for manual input
        this.elements.manualInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.manualLookup();
            }
        });
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
                    this.elements.switchBtn.disabled = true; // Disable switching if we can't enumerate
                    
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
            
            // Lookup barcode via API
            const response = await fetch(`/api/upc/lookup/${barcode}/`);
            const data = await response.json();
            
            if (data.success) {
                this.displayProductResult(data.product);
                this.addToHistory(barcode, data.product.name);
                this.showStatus('Product found successfully!', 'success');
            } else {
                this.showStatus(`Product not found: ${data.message}`, 'error');
                this.displayNoResult(barcode);
                this.addToHistory(barcode, 'Not Found');
            }
            
        } catch (error) {
            console.error('Lookup error:', error);
            this.showStatus('Error looking up barcode', 'error');
            this.displayNoResult(barcode);
        }
    }

    displayProductResult(product) {
        document.getElementById('resultBarcode').textContent = product.barcode || 'N/A';
        document.getElementById('resultName').textContent = product.name;
        document.getElementById('resultCategory').textContent = product.category || 'N/A';
        document.getElementById('resultPrice').textContent = `R${product.price?.toFixed(2) || '0.00'}`;
        document.getElementById('resultStock').textContent = product.stock || '0';
        document.getElementById('resultStatus').textContent = product.stock > 0 ? 'In Stock' : 'Out of Stock';
        
        this.elements.scanResult.classList.add('show');
    }

    displayNoResult(barcode) {
        document.getElementById('resultBarcode').textContent = barcode;
        document.getElementById('resultName').textContent = 'Product Not Found';
        document.getElementById('resultCategory').textContent = 'N/A';
        document.getElementById('resultPrice').textContent = 'N/A';
        document.getElementById('resultStock').textContent = 'N/A';
        document.getElementById('resultStatus').textContent = 'Not Available';
        
        this.elements.scanResult.classList.add('show');
    }

    showStatus(message, type) {
        // Use toast system instead of inline status messages
        if (window.toastManager) {
            window.toastManager.showToast(message, type);
        } else {
            // Fallback to original status message if toast not available
            const statusEl = this.elements.statusMessage;
            statusEl.textContent = message;
            statusEl.className = `status-message ${type} show`;
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                statusEl.classList.remove('show');
            }, 5000);
        }
    }

    addToHistory(barcode, productName) {
        const timestamp = new Date().toLocaleString();
        this.scanHistory.unshift({
            barcode: barcode,
            productName: productName,
            timestamp: timestamp
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
                    <div style="font-size: 12px; color: #7f8c8d;">${item.productName}</div>
                </div>
                <div class="history-time">${item.timestamp}</div>
            </div>
        `).join('');
    }

    saveHistory() {
        localStorage.setItem('barcodeScanHistory', JSON.stringify(this.scanHistory));
    }

    loadHistory() {
        const saved = localStorage.getItem('barcodeScanHistory');
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

    addToCart() {
        const barcode = document.getElementById('resultBarcode').textContent;
        if (barcode && barcode !== 'N/A') {
            // Implement add to cart functionality
            this.showStatus('Added to cart!', 'success');
            // You can redirect to cart or update cart state here
        }
    }

    viewDetails() {
        const barcode = document.getElementById('resultBarcode').textContent;
        if (barcode && barcode !== 'N/A') {
            // Redirect to product details page
            window.location.href = `/upc/lookup/${barcode}/`;
        }
    }

    scanAnother() {
        this.elements.scanResult.classList.remove('show');
        this.elements.manualInput.value = '';
        this.elements.manualInput.focus();
        
        if (this.isScanning) {
            this.startScanning(); // Restart scanning
        }
    }
}

// Initialize the scanner when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new BarcodeScanner();
});
