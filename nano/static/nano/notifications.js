// Notification System JavaScript

class NotificationSystem {
    constructor() {
        this.notifications = [];
        this.dropdownVisible = false;
        this.unreadCount = 0;
        this.reminderInterval = null;
        // Always try to initialize the floating button for authenticated users
        this.initFloatingButton();
        // Only initialize full notification system if elements exist
        if (this.isUserAuthenticated() && this.notificationElementsExist()) {
            this.init();
        } else {
            console.log('NotificationSystem not fully initialized:', {
                authenticated: this.isUserAuthenticated(),
                elementsExist: this.notificationElementsExist(),
                notificationBell: !!document.getElementById('notificationBell'),
                notificationDropdown: !!document.getElementById('notificationDropdown')
            });
        }
    }

    isUserAuthenticated() {
        // Check if user is authenticated by looking for CSRF token or user indicators
        return document.querySelector('[name=csrfmiddlewaretoken]') !== null || 
               document.getElementById('notificationBell') !== null ||
               document.body.classList.contains('authenticated-user');
    }

    notificationElementsExist() {
        return document.getElementById('notificationBell') && 
               document.getElementById('notificationDropdown');
    }

    initFloatingButton() {
        // Create floating message button for all authenticated users
        if (this.isUserAuthenticated()) {
            this.createFloatingMessageButton();
            // Set up event listeners for the floating button
            setTimeout(() => {
                this.setupFloatingButtonListeners();
            }, 100);
        }
    }

    init() {
        this.setupEventListeners();
        this.startPolling();
        this.startReminderSystem();
        this.checkLowStock();
        this.updateNavbarBadge();
    }

    createFloatingMessageButton() {
        // Remove existing button if any
        const existingBtn = document.getElementById('floatingMessageBtn');
        if (existingBtn) {
            existingBtn.remove();
        }

        // Create floating message button for all authenticated users
        const floatingBtn = document.createElement('div');
        floatingBtn.className = 'floating-message-btn';
        floatingBtn.innerHTML = '<i class="fas fa-comment-dots"></i>';
        floatingBtn.id = 'floatingMessageBtn';
        floatingBtn.title = 'Send Message';
        floatingBtn.style.cssText = `
            position: fixed !important;
            bottom: 20px !important;
            right: 20px !important;
            width: 60px !important;
            height: 60px !important;
            background: #007bff !important;
            border-radius: 50% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            color: white !important;
            font-size: 1.5rem !important;
            cursor: pointer !important;
            box-shadow: 0 4px 20px rgba(0, 123, 255, 0.3) !important;
            transition: all 0.3s ease !important;
            z-index: 9999 !important;
            border: none !important;
            outline: none !important;
            text-decoration: none !important;
        `;
        document.body.appendChild(floatingBtn);

        // Create message modal
        this.createMessageModal();
        
        console.log('Floating message button created');
    }

    createMessageModal() {
        const modal = document.createElement('div');
        modal.className = 'message-modal';
        modal.id = 'messageModal';
        modal.innerHTML = `
            <div class="message-modal-content">
                <div class="message-modal-header">
                    <h3>Send Message</h3>
                    <button class="close-modal" id="closeModal">&times;</button>
                </div>
                <div class="message-modal-body">
                    <div class="form-group">
                        <label for="requestType">Request Type</label>
                        <select id="requestType" required>
                            <option value="">Select a request type</option>
                            <option value="password_reset">Password Reset</option>
                            <option value="order_issue">Order Issue</option>
                            <option value="system_problem">System Problem</option>
                            <option value="stock_issue">Stock Issue</option>
                            <option value="customer_complaint">Customer Complaint</option>
                            <option value="payment_issue">Payment Issue</option>
                            <option value="other">Other</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="requestMessage">Message</label>
                        <textarea id="requestMessage" placeholder="Describe your request in detail..." required></textarea>
                    </div>
                </div>
                <div class="message-modal-footer">
                    <button class="btn btn-secondary" id="cancelRequest">Cancel</button>
                    <button class="btn btn-primary" id="sendRequest">Send Request</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    setupFloatingButtonListeners() {
        console.log('Setting up floating button listeners');
        
        // Floating message button
        const floatingBtn = document.getElementById('floatingMessageBtn');
        if (floatingBtn) {
            // Remove any existing listeners to avoid duplicates
            floatingBtn.replaceWith(floatingBtn.cloneNode(true));
            const newFloatingBtn = document.getElementById('floatingMessageBtn');
            
            newFloatingBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Floating button clicked');
                this.showMessageModal();
            });
            
            console.log('Floating button listener attached');
        } else {
            console.error('Floating button not found for listener setup');
        }

        // Modal controls
        const closeModal = document.getElementById('closeModal');
        const cancelRequest = document.getElementById('cancelRequest');
        const sendRequest = document.getElementById('sendRequest');

        if (closeModal) {
            closeModal.addEventListener('click', (e) => {
                e.preventDefault();
                this.hideMessageModal();
            });
        }

        if (cancelRequest) {
            cancelRequest.addEventListener('click', (e) => {
                e.preventDefault();
                this.hideMessageModal();
            });
        }

        if (sendRequest) {
            sendRequest.addEventListener('click', (e) => {
                e.preventDefault();
                this.sendCashierRequest();
            });
        }

        // Close modal when clicking outside
        const modal = document.getElementById('messageModal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.hideMessageModal();
                }
            });
        }
    }

    setupEventListeners() {
        // Floating message button
        const floatingBtn = document.getElementById('floatingMessageBtn');
        if (floatingBtn) {
            floatingBtn.addEventListener('click', () => this.showMessageModal());
        }

        // Modal controls
        const closeModal = document.getElementById('closeModal');
        const cancelRequest = document.getElementById('cancelRequest');
        const sendRequest = document.getElementById('sendRequest');

        if (closeModal) closeModal.addEventListener('click', () => this.hideMessageModal());
        if (cancelRequest) cancelRequest.addEventListener('click', () => this.hideMessageModal());
        if (sendRequest) sendRequest.addEventListener('click', () => this.sendCashierRequest());

        // Close modal when clicking outside
        const modal = document.getElementById('messageModal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.hideMessageModal();
                }
            });
        }
    }


    showMessageModal() {
        const modal = document.getElementById('messageModal');
        if (modal) {
            modal.style.display = 'flex';
            modal.classList.add('show');
            const requestType = document.getElementById('requestType');
            if (requestType) {
                requestType.focus();
            }
        }
    }

    hideMessageModal() {
        const modal = document.getElementById('messageModal');
        if (modal) {
            modal.style.display = 'none';
            modal.classList.remove('show');
            // Reset form
            const requestType = document.getElementById('requestType');
            const requestMessage = document.getElementById('requestMessage');
            if (requestType) requestType.value = '';
            if (requestMessage) requestMessage.value = '';
        }
    }

    sendCashierRequest() {
        const requestType = document.getElementById('requestType').value;
        const message = document.getElementById('requestMessage').value;
        const urgent = document.getElementById('requestUrgent')?.checked || false;

        if (!requestType || !message) {
            alert('Please fill in all fields');
            return;
        }

        fetch('/api/cashier_request/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                request_type: requestType,
                message: message,
                urgent: urgent
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success === true || data.status === 'success') {
                this.hideMessageModal();
                this.showSuccessMessage('Your message has been sent successfully');
                // Refresh notifications after a short delay
                setTimeout(() => this.loadNotifications(), 1000);
            } else {
                alert('Error sending request: ' + (data.message || data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error sending request:', error);
            alert('Error sending request. Please try again.');
        });
    }

    showSuccessMessage(message) {
        // Create a temporary success message
        const successDiv = document.createElement('div');
        successDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 15px 20px;
            border-radius: 6px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            z-index: 3000;
            animation: slideInRight 0.3s ease;
        `;
        successDiv.textContent = message;
        document.body.appendChild(successDiv);

        setTimeout(() => {
            successDiv.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => successDiv.remove(), 300);
        }, 3000);
    }

    loadNotifications() {
        fetch('/api/notifications/', {
            method: 'GET',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            this.notifications = data.notifications;
            this.updateBadge();
        })
        .catch(error => console.error('Error loading notifications:', error));
    }

    isPasswordRelatedNotification(notification) {
        // Check if notification is related to password change
        if (notification.notification_type === 'cashier_request' && notification.request_type === 'password_reset') {
            return true;
        }
        
        // Also check title and message for password-related keywords
        const passwordKeywords = ['password', 'pwd', 'reset', 'change password'];
        const title = (notification.title || '').toLowerCase();
        const message = (notification.message || '').toLowerCase();
        
        return passwordKeywords.some(keyword => 
            title.includes(keyword) || message.includes(keyword)
        );
    }

    isLowStockNotification(notification) {
        // Check if notification is related to low stock
        if (notification.notification_type === 'low_stock') {
            return true;
        }
        
        // Also check title and message for low stock keywords
        const lowStockKeywords = ['low stock', 'stock alert', 'running low', 'inventory'];
        const title = (notification.title || '').toLowerCase();
        const message = (notification.message || '').toLowerCase();
        
        return lowStockKeywords.some(keyword => 
            title.includes(keyword) || message.includes(keyword)
        );
    }

    isSuggestionNotification(notification) {
        // Check if notification is just a suggestion (no action needed)
        if (notification.notification_type === 'system_alert' && notification.request_type === 'message_confirmation') {
            return true;
        }
        
        // Also check title and message for suggestion keywords
        const suggestionKeywords = ['suggestion', 'info', 'fyi', 'for your information', 'sent successfully'];
        const title = (notification.title || '').toLowerCase();
        const message = (notification.message || '').toLowerCase();
        
        return suggestionKeywords.some(keyword => 
            title.includes(keyword) || message.includes(keyword)
        );
    }

    handleNotificationAction(notificationId) {
        const notification = this.notifications.find(n => n.id === notificationId);
        if (!notification) return;

        // Mark as read first
        this.markAsRead(notificationId);

        // Handle different notification types
        if (this.isPasswordRelatedNotification(notification)) {
            // Redirect to edit user page
            setTimeout(() => {
                this.redirectToEditUser(notificationId);
            }, 500);
        } else if (this.isLowStockNotification(notification)) {
            // Redirect to warehouse/add stock page
            setTimeout(() => {
                window.location.href = '/add_stock/';
            }, 500);
        } else if (this.isSuggestionNotification(notification)) {
            // Just mark as read, no redirect needed
            console.log('Suggestion notification marked as read, no redirect needed');
        } else {
            // For other notifications, you might want to go to notifications page
            setTimeout(() => {
                window.location.href = '/notifications_page/';
            }, 500);
        }
    }

    redirectToEditUser(notificationId) {
        const notification = this.notifications.find(n => n.id === notificationId);
        if (!notification) return;

        // Extract user information from notification
        let userId = null;
        
        // Try to get user from created_by field (the user who requested the reset)
        if (notification.created_by_id) {
            userId = notification.created_by_id;
        } else if (notification.request_data && notification.request_data.user_id) {
            // Try to get user_id from request_data
            userId = notification.request_data.user_id;
        } else {
            // Try to extract username from message and find the user
            const messageMatch = notification.message.match(/Password reset requested for user:\s+(\w+)/);
            if (messageMatch) {
                const username = messageMatch[1];
                // Make an API call to find the user ID
                fetch(`/api/get_user_by_username/?username=${username}`, {
                    method: 'GET',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success === true && data.user && data.user.id) {
                        window.location.href = `/edit_user/${data.user.id}/`;
                    } else {
                        alert('Could not find the user to edit. Please go to Manage Users manually.');
                        window.location.href = '/manage_users/';
                    }
                })
                .catch(error => {
                    console.error('Error finding user:', error);
                    alert('Error finding user. Please go to Manage Users manually.');
                    window.location.href = '/manage_users/';
                });
                return;
            }
        }

        if (userId) {
            window.location.href = `/edit_user/${userId}/`;
        } else {
            // Fallback to manage users page
            alert('Could not determine which user to edit. Redirecting to Manage Users.');
            window.location.href = '/manage_users/';
        }
    }

    getNotificationIcon(type) {
        const icons = {
            'low_stock': '<i class="fas fa-box" style="color: #ffc107;"></i>',
            'cashier_request': '<i class="fas fa-user" style="color: #17a2b8;"></i>',
            'system_alert': '<i class="fas fa-exclamation-triangle" style="color: #dc3545;"></i>'
        };
        return icons[type] || '<i class="fas fa-info-circle"></i>';
    }

    formatNotificationType(type) {
        return type.replace('_', ' ');
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        return date.toLocaleDateString();
    }

    updateBadge() {
        const badge = document.getElementById('notificationBadge');
        const mobileBadge = document.getElementById('mobileNotificationBadge');
        
        const unreadCount = this.notifications.filter(n => !n.is_read).length;
        
        // Update desktop badge with count text
        if (badge) {
            if (unreadCount > 0) {
                badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
                badge.style.display = 'flex';
                // Add title attribute to show full count
                badge.title = `${unreadCount} unread notification${unreadCount !== 1 ? 's' : ''}`;
            } else {
                badge.style.display = 'none';
                badge.title = '';
            }
        }
        
        // Update mobile badge with count text
        if (mobileBadge) {
            if (unreadCount > 0) {
                mobileBadge.textContent = unreadCount > 99 ? '99+' : unreadCount;
                mobileBadge.style.display = 'flex';
                // Add title attribute to show full count
                mobileBadge.title = `${unreadCount} unread notification${unreadCount !== 1 ? 's' : ''}`;
            } else {
                mobileBadge.style.display = 'none';
                mobileBadge.title = '';
            }
        }

        this.unreadCount = unreadCount;
    }

    markAsRead(notificationId) {
        fetch(`/api/notifications/${notificationId}/read/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const notification = this.notifications.find(n => n.id === notificationId);
                if (notification) {
                    notification.is_read = true;
                    this.renderNotifications();
                    this.updateBadge();
                }
            }
        })
        .catch(error => console.error('Error marking notification as read:', error));
    }

    dismiss(notificationId) {
        fetch(`/api/notifications/${notificationId}/dismiss/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                this.notifications = this.notifications.filter(n => n.id !== notificationId);
                this.renderNotifications();
                this.updateBadge();
            }
        })
        .catch(error => console.error('Error dismissing notification:', error));
    }

    markAllAsRead() {
        const unreadNotifications = this.notifications.filter(n => !n.is_read);
        
        unreadNotifications.forEach(notification => {
            this.markAsRead(notification.id);
        });
    }

    startPolling() {
        // Poll for new notifications every 30 seconds
        setInterval(() => {
            this.loadNotifications();
        }, 30000);
    }

    startReminderSystem() {
        // Check for reminders every 5 minutes
        this.reminderInterval = setInterval(() => {
            this.checkReminders();
        }, 300000); // 5 minutes
    }

    checkReminders() {
        // This would be handled by the backend, but we can trigger a refresh
        this.loadNotifications();
        
        // Show browser notification if there are reminders
        const reminders = this.notifications.filter(n => n.can_remind && !n.is_read);
        if (reminders.length > 0) {
            this.showBrowserNotification(reminders[0]);
        }
    }

    showBrowserNotification(notification) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(notification.title, {
                body: notification.message,
                icon: '/static/favicon.ico'
            });
        } else if ('Notification' in window && Notification.permission !== 'denied') {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    new Notification(notification.title, {
                        body: notification.message,
                        icon: '/static/favicon.ico'
                    });
                }
            });
        }
    }

    checkLowStock() {
        // Check for low stock products
        fetch('/api/check_low_stock/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Refresh notifications after checking low stock
                setTimeout(() => this.loadNotifications(), 1000);
            }
        })
        .catch(error => console.error('Error checking low stock:', error));
    }
}

// Notifications Page Class
class NotificationsPage {
    constructor() {
        this.notifications = [];
        this.filteredNotifications = [];
        this.init();
    }

    init() {
        this.loadNotifications();
        this.setupEventListeners();
        this.startAutoRefresh();
    }

    setupEventListeners() {
        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.loadNotifications();
        });

        // Mark all as read
        document.getElementById('markAllReadBtn').addEventListener('click', () => {
            this.markAllAsRead();
        });

        // Filters
        document.getElementById('typeFilter').addEventListener('change', () => {
            this.applyFilters();
        });

        document.getElementById('statusFilter').addEventListener('change', () => {
            this.applyFilters();
        });

        document.getElementById('dateFilter').addEventListener('change', () => {
            this.applyFilters();
        });

        // Modal close buttons
        document.getElementById('closeModalBtn').addEventListener('click', () => {
            this.closeModal();
        });

        document.getElementById('modalCloseBtn').addEventListener('click', () => {
            this.closeModal();
        });

        // Close modal when clicking outside
        document.getElementById('notificationDetailModal').addEventListener('click', (e) => {
            if (e.target.id === 'notificationDetailModal') {
                this.closeModal();
            }
        });
    }

    async loadNotifications() {
        try {
            const response = await fetch('/api/notifications/', {
                method: 'GET',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });

            const data = await response.json();
            this.notifications = data.notifications || [];
            this.filteredNotifications = [...this.notifications];
            
            this.renderNotifications();
            this.updateStats();
            this.updateNavbarBadge();
        } catch (error) {
            console.error('Error loading notifications:', error);
            this.showError('Failed to load notifications');
        }
    }

    renderNotifications() {
        const container = document.getElementById('notificationsList');
        
        if (this.filteredNotifications.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-bell-slash"></i>
                    <h3>No notifications found</h3>
                    <p>Check back later for new notifications</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.filteredNotifications.map(notification => `
            <div class="notification-item ${notification.is_read ? 'read' : 'unread'}" data-id="${notification.id}">
                <div class="notification-header-info">
                    <div class="notification-title">
                        ${this.getNotificationIcon(notification.notification_type)}
                        ${notification.title}
                        ${this.isPasswordRelatedNotification(notification) ? '<span class="password-badge"><i class="fas fa-key"></i> Password</span>' : ''}
                    </div>
                    <div class="notification-time">${this.formatTime(notification.created_at)}</div>
                </div>
                <div class="notification-message">${notification.message}</div>
                <div class="notification-meta">
                    <div class="notification-type ${notification.notification_type}">
                        ${this.formatNotificationType(notification.notification_type)}
                    </div>
                    <div class="notification-actions">
                        ${this.isPasswordRelatedNotification(notification) ? `<button class="notification-btn btn-edit-user" onclick="notificationsPage.handleNotificationAction(${notification.id})">Edit User</button>` : ''}
                        ${this.isLowStockNotification(notification) ? `<button class="notification-btn btn-add-stock" onclick="notificationsPage.handleNotificationAction(${notification.id})">Add Stock</button>` : ''}
                        ${!this.isSuggestionNotification(notification) && !notification.is_read ? `<button class="notification-btn btn-mark-read" onclick="notificationsPage.markAsRead(${notification.id})">Mark as read</button>` : ''}
                        <button class="notification-btn btn-dismiss" onclick="notificationsPage.dismiss(${notification.id})">Dismiss</button>
                    </div>
                </div>
            </div>
        `).join('');

        // Add click listeners for notification items
        container.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.notification-actions')) {
                    const notificationId = parseInt(item.dataset.id);
                    this.showNotificationDetail(notificationId);
                }
            });
        });
    }

    updateStats() {
        const total = this.notifications.length;
        const unread = this.notifications.filter(n => !n.is_read).length;
        const today = this.notifications.filter(n => {
            const notificationDate = new Date(n.created_at);
            const today = new Date();
            return notificationDate.toDateString() === today.toDateString();
        }).length;

        document.getElementById('totalCount').textContent = total;
        document.getElementById('unreadCount').textContent = unread;
        document.getElementById('todayCount').textContent = today;
    }

    updateNavbarBadge() {
        const badge = document.getElementById('notificationBadge');
        const mobileBadge = document.getElementById('mobileNotificationBadge');
        
        const unreadCount = this.notifications.filter(n => !n.is_read).length;
        
        if (badge) {
            if (unreadCount > 0) {
                badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        }
        
        if (mobileBadge) {
            if (unreadCount > 0) {
                mobileBadge.textContent = unreadCount > 99 ? '99+' : unreadCount;
                mobileBadge.style.display = 'flex';
            } else {
                mobileBadge.style.display = 'none';
            }
        }
    }

    applyFilters() {
        const typeFilter = document.getElementById('typeFilter').value;
        const statusFilter = document.getElementById('statusFilter').value;
        const dateFilter = document.getElementById('dateFilter').value;

        this.filteredNotifications = this.notifications.filter(notification => {
            // Type filter
            if (typeFilter && notification.notification_type !== typeFilter) {
                return false;
            }

            // Status filter
            if (statusFilter === 'unread' && notification.is_read) {
                return false;
            }
            if (statusFilter === 'read' && !notification.is_read) {
                return false;
            }

            // Date filter
            if (dateFilter) {
                const notificationDate = new Date(notification.created_at);
                const today = new Date();
                
                switch (dateFilter) {
                    case 'today':
                        if (notificationDate.toDateString() !== today.toDateString()) {
                            return false;
                        }
                        break;
                    case 'week':
                        const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
                        if (notificationDate < weekAgo) {
                            return false;
                        }
                        break;
                    case 'month':
                        const monthAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);
                        if (notificationDate < monthAgo) {
                            return false;
                        }
                        break;
                }
            }

            return true;
        });

        this.renderNotifications();
    }

    async markAsRead(notificationId) {
        try {
            const response = await fetch(`/api/notifications/${notificationId}/read/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });

            const data = await response.json();
            if (data.status === 'success') {
                const notification = this.notifications.find(n => n.id === notificationId);
                if (notification) {
                    notification.is_read = true;
                    this.applyFilters();
                    this.updateStats();
                    this.updateNavbarBadge();
                }
            } else {
                this.showError('Failed to mark notification as read');
            }
        } catch (error) {
            console.error('Error marking notification as read:', error);
            this.showError('Failed to mark notification as read');
        }
    }

    async dismiss(notificationId) {
        try {
            const response = await fetch(`/api/notifications/${notificationId}/dismiss/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });

            const data = await response.json();
            if (data.status === 'success') {
                this.notifications = this.notifications.filter(n => n.id !== notificationId);
                this.applyFilters();
                this.updateStats();
                this.updateNavbarBadge();
            } else {
                this.showError('Failed to dismiss notification');
            }
        } catch (error) {
            console.error('Error dismissing notification:', error);
            this.showError('Failed to dismiss notification');
        }
    }

    async markAllAsRead() {
        try {
            const unreadNotifications = this.notifications.filter(n => !n.is_read);
            
            for (const notification of unreadNotifications) {
                await this.markAsRead(notification.id);
            }
        } catch (error) {
            console.error('Error marking all as read:', error);
            this.showError('Failed to mark all notifications as read');
        }
    }

    showNotificationDetail(notificationId) {
        const notification = this.notifications.find(n => n.id === notificationId);
        if (!notification) return;

        const modal = document.getElementById('notificationDetailModal');
        const modalTitle = document.getElementById('modalTitle');
        const modalContent = document.getElementById('notificationDetailContent');
        const modalActionBtn = document.getElementById('modalActionBtn');

        modalTitle.textContent = notification.title;
        modalContent.innerHTML = `
            <div class="notification-detail">
                <div class="detail-row">
                    <strong>Type:</strong> ${this.formatNotificationType(notification.notification_type)}
                </div>
                <div class="detail-row">
                    <strong>Time:</strong> ${new Date(notification.created_at).toLocaleString()}
                </div>
                <div class="detail-row">
                    <strong>Status:</strong> ${notification.is_read ? 'Read' : 'Unread'}
                </div>
                ${notification.sender_username ? `
                <div class="detail-row">
                    <strong>From:</strong> ${notification.sender_username}
                </div>
                ` : ''}
                <div class="detail-message">
                    <strong>Message:</strong>
                    <div class="message-content">${notification.message}</div>
                </div>
            </div>
        `;

        // Show action button for password-related notifications
        if (this.isPasswordRelatedNotification(notification)) {
            modalActionBtn.style.display = 'block';
            modalActionBtn.textContent = 'Edit User';
            modalActionBtn.onclick = () => this.editUser(notificationId);
        } else {
            modalActionBtn.style.display = 'none';
        }

        modal.classList.add('show');
    }

    closeModal() {
        const modal = document.getElementById('notificationDetailModal');
        modal.classList.remove('show');
    }

    editUser(notificationId) {
        const notification = this.notifications.find(n => n.id === notificationId);
        if (!notification) return;

        // Extract user information from notification
        let userId = null;
        
        if (notification.created_by_id) {
            userId = notification.created_by_id;
        } else if (notification.request_data && notification.request_data.user_id) {
            userId = notification.request_data.user_id;
        } else {
            // Try to extract username from message
            const messageMatch = notification.message.match(/Password reset requested for user:\s+(\w+)/);
            if (messageMatch) {
                const username = messageMatch[1];
                // Make an API call to find the user ID
                fetch(`/api/get_user_by_username/?username=${username}`, {
                    method: 'GET',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success === true && data.user && data.user.id) {
                        window.location.href = `/edit_user/${data.user.id}/`;
                    } else {
                        alert('Could not find the user to edit. Please go to Manage Users manually.');
                        window.location.href = '/manage_users/';
                    }
                })
                .catch(error => {
                    console.error('Error finding user:', error);
                    alert('Error finding user. Please go to Manage Users manually.');
                    window.location.href = '/manage_users/';
                });
                return;
            }
        }

        if (userId) {
            window.location.href = `/edit_user/${userId}/`;
        } else {
            alert('Could not determine which user to edit. Redirecting to Manage Users.');
            window.location.href = '/manage_users/';
        }
    }

    getNotificationIcon(type) {
        const icons = {
            'low_stock': '<i class="fas fa-box" style="color: #ffc107;"></i>',
            'cashier_request': '<i class="fas fa-user" style="color: #17a2b8;"></i>',
            'system_alert': '<i class="fas fa-exclamation-triangle" style="color: #dc3545;"></i>'
        };
        return icons[type] || '<i class="fas fa-info-circle"></i>';
    }

    formatNotificationType(type) {
        return type.replace('_', ' ');
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        return date.toLocaleDateString();
    }

    isPasswordRelatedNotification(notification) {
        // Check if notification is related to password change
        if (notification.notification_type === 'cashier_request' && notification.request_type === 'password_reset') {
            return true;
        }
        
        // Also check title and message for password-related keywords
        const passwordKeywords = ['password', 'pwd', 'reset', 'change password'];
        const title = (notification.title || '').toLowerCase();
        const message = (notification.message || '').toLowerCase();
        
        return passwordKeywords.some(keyword => 
            title.includes(keyword) || message.includes(keyword)
        );
    }

    isLowStockNotification(notification) {
        // Check if notification is related to low stock
        if (notification.notification_type === 'low_stock') {
            return true;
        }
        
        // Also check title and message for low stock keywords
        const lowStockKeywords = ['low stock', 'stock alert', 'running low', 'inventory'];
        const title = (notification.title || '').toLowerCase();
        const message = (notification.message || '').toLowerCase();
        
        return lowStockKeywords.some(keyword => 
            title.includes(keyword) || message.includes(keyword)
        );
    }

    isSuggestionNotification(notification) {
        // Check if notification is just a suggestion (no action needed)
        if (notification.notification_type === 'system_alert' && notification.request_type === 'message_confirmation') {
            return true;
        }
        
        // Also check title and message for suggestion keywords
        const suggestionKeywords = ['suggestion', 'info', 'fyi', 'for your information', 'sent successfully'];
        const title = (notification.title || '').toLowerCase();
        const message = (notification.message || '').toLowerCase();
        
        return suggestionKeywords.some(keyword => 
            title.includes(keyword) || message.includes(keyword)
        );
    }

    handleNotificationAction(notificationId) {
        const notification = this.notifications.find(n => n.id === notificationId);
        if (!notification) return;

        // Mark as read first
        this.markAsRead(notificationId);

        // Handle different notification types
        if (this.isPasswordRelatedNotification(notification)) {
            // Redirect to edit user page
            setTimeout(() => {
                this.editUser(notificationId);
            }, 500);
        } else if (this.isLowStockNotification(notification)) {
            // Redirect to warehouse/add stock page
            setTimeout(() => {
                window.location.href = '/add_stock/';
            }, 500);
        } else if (this.isSuggestionNotification(notification)) {
            // Just mark as read, no redirect needed
            console.log('Suggestion notification marked as read, no redirect needed');
        } else {
            // For other notifications, you might want to go to notifications page
            setTimeout(() => {
                window.location.href = '/notifications_page/';
            }, 500);
        }
    }

    showError(message) {
        // Create a temporary error message
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #dc3545;
            color: white;
            padding: 15px 20px;
            border-radius: 6px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            z-index: 3000;
            animation: slideInRight 0.3s ease;
        `;
        errorDiv.textContent = message;
        document.body.appendChild(errorDiv);

        setTimeout(() => {
            errorDiv.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => errorDiv.remove(), 300);
        }, 3000);
    }

    startAutoRefresh() {
        // Auto-refresh notifications every 30 seconds
        setInterval(() => {
            this.loadNotifications();
        }, 30000);
    }
}

// Initialize notification system when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    try {
        window.notificationSystem = new NotificationSystem();
        
        // Initialize NotificationsPage if we're on the notifications page
        if (document.getElementById('notificationsList')) {
            window.notificationsPage = new NotificationsPage();
        }
        
        // Request notification permission
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    } catch (error) {
        console.error('Error initializing notification system:', error);
        // Fallback: ensure notification elements are hidden if system fails
        const notificationElements = document.querySelectorAll('.notification-bell, .notification-dropdown');
        notificationElements.forEach(el => {
            if (el) el.style.display = 'none';
        });
    }
});

// Additional initialization fallback for dynamically loaded content
window.addEventListener('load', function() {
    // Retry initialization if notification elements exist but system wasn't initialized
    if (!window.notificationSystem && document.getElementById('notificationBell')) {
        try {
            window.notificationSystem = new NotificationSystem();
        } catch (error) {
            console.error('Error in fallback notification system initialization:', error);
        }
    }
    
    // Fallback: Create floating button independently if it doesn't exist
    if (!document.getElementById('floatingMessageBtn') && document.querySelector('[name=csrfmiddlewaretoken]')) {
        try {
            createStandaloneFloatingButton();
        } catch (error) {
            console.error('Error creating standalone floating button:', error);
        }
    }
});

// Standalone floating button creation as fallback
function createStandaloneFloatingButton() {
    console.log('Creating standalone floating button');
    
    // Remove existing button if any
    const existingBtn = document.getElementById('floatingMessageBtn');
    if (existingBtn) {
        existingBtn.remove();
    }
    
    // Create floating button
    const floatingBtn = document.createElement('div');
    floatingBtn.className = 'floating-message-btn';
    floatingBtn.innerHTML = '<i class="fas fa-comment-dots"></i>';
    floatingBtn.id = 'floatingMessageBtn';
    floatingBtn.title = 'Send Message';
    floatingBtn.style.cssText = `
        position: fixed;
        bottom: ${window.innerWidth <= 768 ? '80px' : '20px'};
        right: 20px;
        width: 60px;
        height: 60px;
        background: #007bff;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 1.5rem;
        cursor: pointer;
        box-shadow: 0 4px 20px rgba(0, 123, 255, 0.3);
        transition: all 0.3s ease;
        z-index: 999;
    `;
    
    document.body.appendChild(floatingBtn);
    
    // Create modal
    createStandaloneModal();
    
    // Add event listener with proper error handling
    floatingBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log('Standalone floating button clicked');
        
        const modal = document.getElementById('messageModal');
        if (modal) {
            modal.style.display = 'flex';
            modal.classList.add('show');
            const requestType = document.getElementById('requestType');
            if (requestType) {
                requestType.focus();
            }
            console.log('Modal opened successfully');
        } else {
            console.error('Modal not found when button clicked');
        }
    });

    // Add hover effects
    floatingBtn.addEventListener('mouseenter', function() {
        this.style.transform = 'scale(1.1)';
        this.style.background = '#0056b3';
    });

    floatingBtn.addEventListener('mouseleave', function() {
        this.style.transform = 'scale(1)';
        this.style.background = '#007bff';
    });
    
    console.log('Standalone floating button created successfully');
}

function createStandaloneModal() {
    // Remove existing modal if any
    const existingModal = document.getElementById('messageModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    const modal = document.createElement('div');
    modal.className = 'message-modal';
    modal.id = 'messageModal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: none;
        align-items: center;
        justify-content: center;
        z-index: 2000;
    `;
    
    modal.innerHTML = `
        <div style="background: white; border-radius: 12px; width: 90%; max-width: 500px; max-height: 80vh; overflow-y: auto;">
            <div style="padding: 20px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center;">
                <h3 style="margin: 0; color: #333;">Send Message</h3>
                <button class="close-modal" id="closeModal" style="background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #666;">&times;</button>
            </div>
            <div style="padding: 20px;">
                <div style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px; font-weight: 500; color: #333;">Request Type</label>
                    <select id="requestType" required style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px;">
                        <option value="">Select a request type</option>
                        <option value="password_reset">Password Reset</option>
                        <option value="order_issue">Order Issue</option>
                        <option value="system_problem">System Problem</option>
                        <option value="stock_issue">Stock Issue</option>
                        <option value="customer_complaint">Customer Complaint</option>
                        <option value="payment_issue">Payment Issue</option>
                        <option value="other">Other</option>
                    </select>
                </div>
                <div style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px; font-weight: 500; color: #333;">Message</label>
                    <textarea id="requestMessage" placeholder="Describe your request in detail..." required style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; min-height: 100px; resize: vertical;"></textarea>
                </div>
                <div style="margin-bottom: 15px;">
                    <label style="display: inline-flex; align-items: center; color: #333; cursor: pointer;">
                        <input type="checkbox" id="requestUrgent" style="margin-right: 8px;">
                        Mark as urgent
                    </label>
                </div>
            </div>
            <div style="padding: 20px; border-top: 1px solid #eee; display: flex; justify-content: flex-end; gap: 10px;">
                <button class="btn btn-secondary" id="cancelRequest" style="padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; background: #6c757d; color: white;">Cancel</button>
                <button class="btn btn-primary" id="sendRequest" style="padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; background: #007bff; color: white;">Send Request</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add event listeners for modal
    const closeModal = document.getElementById('closeModal');
    const cancelRequest = document.getElementById('cancelRequest');
    const sendRequest = document.getElementById('sendRequest');
    
    if (closeModal) {
        closeModal.addEventListener('click', function() {
            modal.style.display = 'none';
            resetForm();
        });
    }
    
    if (cancelRequest) {
        cancelRequest.addEventListener('click', function() {
            modal.style.display = 'none';
            resetForm();
        });
    }
    
    if (sendRequest) {
        sendRequest.addEventListener('click', function() {
            sendStandaloneMessage();
        });
    }
    
    // Close modal when clicking outside
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.style.display = 'none';
            resetForm();
        }
    });
    
    console.log('Standalone modal created successfully');
}

function resetForm() {
    const requestType = document.getElementById('requestType');
    const requestMessage = document.getElementById('requestMessage');
    if (requestType) requestType.value = '';
    if (requestMessage) requestMessage.value = '';
}

function sendStandaloneMessage() {
    const requestType = document.getElementById('requestType').value;
    const message = document.getElementById('requestMessage').value;
    const urgent = document.getElementById('requestUrgent')?.checked || false;

    if (!requestType || !message) {
        alert('Please fill in all fields');
        return;
    }

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!csrfToken) {
        alert('Security token not found. Please refresh the page and try again.');
        return;
    }

    fetch('/api/cashier_request/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken.value
        },
        body: JSON.stringify({
            request_type: requestType,
            message: message,
            urgent: urgent
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success === true || data.status === 'success') {
            const modal = document.getElementById('messageModal');
            if (modal) {
                modal.style.display = 'none';
            }
            resetForm();
            showStandaloneSuccessMessage('Your message has been sent successfully');
        } else {
            alert('Error sending request: ' + (data.message || data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error sending request:', error);
        alert('Error sending request. Please try again.');
    });
}

function showStandaloneSuccessMessage(message) {
    const successDiv = document.createElement('div');
    successDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #28a745;
        color: white;
        padding: 15px 20px;
        border-radius: 6px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        z-index: 3000;
        animation: slideInRight 0.3s ease;
    `;
    successDiv.textContent = message;
    document.body.appendChild(successDiv);

    setTimeout(() => {
        successDiv.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => successDiv.remove(), 300);
    }, 3000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
