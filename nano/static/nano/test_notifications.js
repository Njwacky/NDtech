// Test Notifications Page JavaScript

// Test results tracking
let testResults = {};

function updateStatus(indicatorId, status) {
    const indicator = document.getElementById(indicatorId);
    if (indicator) {
        indicator.className = `status-indicator ${status}`;
    }
}

function addResult(containerId, message, type = 'info') {
    const container = document.getElementById(containerId);
    if (container) {
        const result = document.createElement('div');
        result.className = `test-result ${type}`;
        result.innerHTML = `<strong>${new Date().toLocaleTimeString()}</strong><br>${message}`;
        container.appendChild(result);
        
        // Keep only last 5 results
        while (container.children.length > 5) {
            container.removeChild(container.firstChild);
        }
    }
}

function checkAuth() {
    fetch('/api/check_role/', {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        updateStatus('authStatus', 'online');
        const authInfo = document.getElementById('authInfo');
        authInfo.innerHTML = `
            <div class="test-result success">
                <strong>Authenticated User:</strong> {{ user.username }}<br>
                <strong>User Role:</strong> ${data.user_role || 'N/A'}<br>
                <strong>Is Admin:</strong> {{ user.is_superuser|yesno:"Yes,No" }}<br>
                <strong>Session Valid:</strong> Yes
            </div>
        `;
        testResults.auth = 'success';
    })
    .catch(error => {
        updateStatus('authStatus', 'offline');
        addResult('authInfo', `Auth check failed: ${error.message}`, 'error');
        testResults.auth = 'failed';
    });
}

function testNotificationsAPI() {
    fetch('/api/notifications/', {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        updateStatus('apiStatus', 'online');
        addResult('apiResults', `Notifications API working. Found ${data.notifications.length} notifications.`, 'success');
        testResults.notificationsAPI = 'success';
    })
    .catch(error => {
        updateStatus('apiStatus', 'offline');
        addResult('apiResults', `Notifications API failed: ${error.message}`, 'error');
        testResults.notificationsAPI = 'failed';
    });
}

function testCashierRequestAPI() {
    fetch('/api/cashier_request/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            request_type: 'system_problem',
            message: 'Test message from notification test page',
            urgent: false
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            addResult('apiResults', `Cashier request API working. Created ${data.data.admin_count} notifications.`, 'success');
            testResults.cashierRequestAPI = 'success';
        } else {
            addResult('apiResults', `Cashier request API error: ${data.error}`, 'error');
            testResults.cashierRequestAPI = 'failed';
        }
    })
    .catch(error => {
        addResult('apiResults', `Cashier request API failed: ${error.message}`, 'error');
        testResults.cashierRequestAPI = 'failed';
    });
}

function testLowStockAPI() {
    fetch('/api/check_low_stock/', {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        addResult('apiResults', `Low stock API working. Found ${data.low_stock_products.length} low stock items.`, 'success');
        testResults.lowStockAPI = 'success';
    })
    .catch(error => {
        addResult('apiResults', `Low stock API failed: ${error.message}`, 'error');
        testResults.lowStockAPI = 'failed';
    });
}

function loadNotifications() {
    if (window.notificationSystem) {
        window.notificationSystem.loadNotifications();
        updateStatus('displayStatus', 'online');
        addResult('displayResults', 'Notifications loaded via notification system', 'success');
        testResults.display = 'success';
    } else {
        updateStatus('displayStatus', 'offline');
        addResult('displayResults', 'Notification system not available', 'error');
        testResults.display = 'failed';
    }
}

function createTestNotification() {
    fetch('/api/cashier_request/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            request_type: 'other',
            message: 'This is a test notification from the test page',
            urgent: false
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            addResult('displayResults', 'Test notification created successfully', 'success');
            setTimeout(() => loadNotifications(), 1000);
        } else {
            addResult('displayResults', `Failed to create test notification: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        addResult('displayResults', `Error creating test notification: ${error.message}`, 'error');
    });
}

function createLowStockNotification() {
    fetch('/api/check_low_stock/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        addResult('displayResults', 'Low stock check triggered', 'success');
        setTimeout(() => loadNotifications(), 1000);
    })
    .catch(error => {
        addResult('displayResults', `Error triggering low stock check: ${error.message}`, 'error');
    });
}

let isClearingNotifications = false;

function clearAllNotifications() {
    // Prevent multiple simultaneous calls
    if (isClearingNotifications) {
        console.log('Clear notifications already in progress...');
        return;
    }
    
    isClearingNotifications = true;
    
    fetch('/api/notifications/', {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        // Clear notifications in batches to avoid overwhelming the server
        const batchSize = 10;
        const batches = [];
        
        for (let i = 0; i < data.notifications.length; i += batchSize) {
            batches.push(data.notifications.slice(i, i + batchSize));
        }
        
        // Process batches sequentially
        return batches.reduce((promise, batch) => {
            return promise.then(() => {
                const batchPromises = batch.map(notification => 
                    fetch(`/api/notifications/${notification.id}/dismiss/`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                        }
                    })
                );
                
                return Promise.all(batchPromises);
            });
        }, Promise.resolve());
    })
    .then(() => {
        addResult('displayResults', 'All notifications cleared', 'success');
        setTimeout(() => {
            loadNotifications();
            isClearingNotifications = false;
        }, 1000);
    })
    .catch(error => {
        addResult('displayResults', `Error clearing notifications: ${error.message}`, 'error');
        isClearingNotifications = false;
    });
}

function testBadgeCount() {
    if (window.notificationSystem) {
        const badge = document.getElementById('notificationBadge');
        const mobileBadge = document.getElementById('mobileNotificationBadge');
        
        addResult('badgeResults', `Desktop badge: ${badge ? badge.textContent : 'Not found'}, Mobile badge: ${mobileBadge ? mobileBadge.textContent : 'Not found'}`, 'info');
        updateStatus('badgeStatus', 'online');
        testResults.badge = 'success';
    } else {
        updateStatus('badgeStatus', 'offline');
        addResult('badgeResults', 'Notification system not available for badge test', 'error');
        testResults.badge = 'failed';
    }
}

function markAllAsRead() {
    fetch('/api/notifications/', {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        const readPromises = data.notifications.filter(n => !n.is_read).map(notification => 
            fetch(`/api/notifications/${notification.id}/read/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
        );
        
        Promise.all(readPromises)
        .then(() => {
            addResult('badgeResults', 'All notifications marked as read', 'success');
            setTimeout(() => loadNotifications(), 1000);
        })
        .catch(error => {
            addResult('badgeResults', `Error loading notifications to mark as read: ${error.message}`, 'error');
        });
    })
    .catch(error => {
        addResult('badgeResults', `Error marking notifications as read: ${error.message}`, 'error');
    });
}

function testFloatingButton() {
    const floatingBtn = document.getElementById('floatingMessageBtn');
    if (floatingBtn) {
        updateStatus('floatingStatus', 'online');
        addResult('floatingResults', 'Floating button found and accessible', 'success');
        testResults.floatingButton = 'success';
    } else {
        updateStatus('floatingStatus', 'offline');
        addResult('floatingResults', 'Floating button not found', 'error');
        testResults.floatingButton = 'failed';
    }
}

function simulateFloatingButtonClick() {
    const floatingBtn = document.getElementById('floatingMessageBtn');
    if (floatingBtn) {
        floatingBtn.click();
        addResult('floatingResults', 'Floating button clicked programmatically', 'success');
    } else {
        addResult('floatingResults', 'Cannot click floating button - not found', 'error');
    }
}

function createManualNotification() {
    const title = document.getElementById('manualTitle').value;
    const message = document.getElementById('manualMessage').value;
    const type = document.getElementById('manualType').value;
    
    if (!title || !message) {
        addResult('manualResults', 'Please fill in both title and message', 'error');
        return;
    }
    
    fetch('/api/cashier_request/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            request_type: type,
            message: `${title}: ${message}`,
            urgent: false
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            addResult('manualResults', 'Manual notification created successfully', 'success');
            // Clear form
            document.getElementById('manualTitle').value = '';
            document.getElementById('manualMessage').value = '';
            setTimeout(() => loadNotifications(), 1000);
        } else {
            addResult('manualResults', `Failed to create manual notification: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        addResult('manualResults', `Error creating manual notification: ${error.message}`, 'error');
    });
}

function refreshDebugInfo() {
    const debugInfo = {
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        currentUrl: window.location.href,
        csrfToken: document.querySelector('[name=csrfmiddlewaretoken]') ? 'Present' : 'Missing',
        notificationSystem: window.notificationSystem ? 'Initialized' : 'Not initialized',
        floatingButton: document.getElementById('floatingMessageBtn') ? 'Present' : 'Missing',
        notificationBell: document.getElementById('notificationBell') ? 'Present' : 'Missing',
        notificationDropdown: document.getElementById('notificationDropdown') ? 'Present' : 'Missing',
        testResults: testResults
    };
    
    document.getElementById('debugInfo').textContent = JSON.stringify(debugInfo, null, 2);
}

// Initialize tests on page load
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        checkAuth();
        testNotificationsAPI();
        testFloatingButton();
        refreshDebugInfo();
        
        // Update status indicators based on results
        setTimeout(() => {
            if (testResults.auth === 'success' && testResults.notificationsAPI === 'success') {
                updateStatus('displayStatus', 'online');
                updateStatus('badgeStatus', 'online');
            }
        }, 2000);
    }, 100);
});

// Monitor notification system changes
const originalLoadNotifications = window.notificationSystem?.loadNotifications;
if (originalLoadNotifications) {
    window.notificationSystem.loadNotifications = function() {
        const result = originalLoadNotifications.call(this);
        setTimeout(() => refreshDebugInfo(), 500);
        return result;
    };
}
