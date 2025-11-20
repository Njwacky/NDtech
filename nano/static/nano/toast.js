class ToastManager {
    constructor() {
        this.container = null;
        this.toasts = [];
        this.init();
    }

    init() {
        // Create toast container if it doesn't exist
        if (!document.querySelector('.toast-container')) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        } else {
            this.container = document.querySelector('.toast-container');
        }

        // Convert existing Django messages to toasts
        this.convertDjangoMessages();
        
        // Listen for dynamic messages
        this.observeMessages();
    }

    convertDjangoMessages() {
        const messages = document.querySelectorAll('.messages .message');
        messages.forEach(message => {
            const messageText = message.textContent.trim();
            const messageType = this.getMessageType(message);
            
            if (messageText) {
                this.showToast(messageText, messageType);
                // Remove the original message to avoid duplication
                message.style.display = 'none';
            }
        });
    }

    getMessageType(messageElement) {
        if (messageElement.classList.contains('success')) return 'success';
        if (messageElement.classList.contains('error')) return 'error';
        if (messageElement.classList.contains('warning')) return 'warning';
        if (messageElement.classList.contains('info')) return 'info';
        return 'info'; // default
    }

    showToast(message, type = 'info', duration = 5000) {
        const toast = this.createToast(message, type);
        this.container.appendChild(toast);
        this.toasts.push(toast);

        // Animate in
        setTimeout(() => {
            toast.style.animation = 'slideInRight 0.3s ease-out';
        }, 10);

        // Auto remove after duration
        setTimeout(() => {
            this.removeToast(toast);
        }, duration);

        return toast;
    }

    createToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        toast.innerHTML = `
            <div class="toast-icon"></div>
            <div class="toast-content">${this.escapeHtml(message)}</div>
            <button class="toast-close" aria-label="Close">×</button>
        `;

        // Add close functionality
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => {
            this.removeToast(toast);
        });

        return toast;
    }

    removeToast(toast) {
        if (!toast || !toast.parentNode) return;

        toast.classList.add('hiding');
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
            
            const index = this.toasts.indexOf(toast);
            if (index > -1) {
                this.toasts.splice(index, 1);
            }
        }, 300);
    }

    observeMessages() {
        // Observe for dynamically added messages
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        // Check if this is a new message container
                        if (node.classList && node.classList.contains('messages')) {
                            this.convertDjangoMessages();
                        }
                        
                        // Check for new message elements
                        if (node.classList && node.classList.contains('message')) {
                            const messageText = node.textContent.trim();
                            const messageType = this.getMessageType(node);
                            
                            if (messageText) {
                                this.showToast(messageText, messageType);
                                node.style.display = 'none';
                            }
                        }
                        
                        // Check child nodes for messages
                        const messages = node.querySelectorAll && node.querySelectorAll('.message');
                        if (messages) {
                            messages.forEach(message => {
                                const messageText = message.textContent.trim();
                                const messageType = this.getMessageType(message);
                                
                                if (messageText) {
                                    this.showToast(messageText, messageType);
                                    message.style.display = 'none';
                                }
                            });
                        }
                    }
                });
            });
        });

        // Start observing the entire document
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Static methods for easy access
    static success(message, duration) {
        window.toastManager.showToast(message, 'success', duration);
    }

    static error(message, duration) {
        window.toastManager.showToast(message, 'error', duration);
    }

    static warning(message, duration) {
        window.toastManager.showToast(message, 'warning', duration);
    }

    static info(message, duration) {
        window.toastManager.showToast(message, 'info', duration);
    }

    static show(message, type = 'info', duration) {
        window.toastManager.showToast(message, type, duration);
    }
}

// Initialize toast manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.toastManager = new ToastManager();
    
    // Make static methods available globally
    window.showToast = ToastManager.show;
    window.showSuccessToast = ToastManager.success;
    window.showErrorToast = ToastManager.error;
    window.showWarningToast = ToastManager.warning;
    window.showInfoToast = ToastManager.info;
});

// Also initialize immediately if DOM is already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.toastManager = new ToastManager();
    });
} else {
    window.toastManager = new ToastManager();
}
