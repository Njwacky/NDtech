// Marketing Dashboard JavaScript for Price Comparisons
let charts = {};

// Initialize the marketing dashboard
function initializeMarketingDashboard() {
    showLoadingState();
    
    // Fetch comparison data for marketing analytics
    fetch('/warehouse/marketing-analytics-data')
        .then(response => response.json())
        .then(data => {
            hideLoadingState();
            if (data.success) {
                renderMarketingCharts(data.data);
                populateTopProducts(data.data.top_products || []);
                populateWarehousePerformance(data.data.warehouse_performance || []);
                updateInsights(data.data.insights || {});
            } else {
                showNotification('Error loading marketing analytics', 'error');
            }
        })
        .catch(error => {
            hideLoadingState();
            console.error('Error:', error);
            showNotification('Error loading marketing analytics', 'error');
        });
}

// Render all marketing charts
function renderMarketingCharts(analytics) {
    // Top Savings Chart
    renderTopSavingsChart(analytics.top_savings);
    
    // Category Distribution Chart
    renderCategoryChart(analytics.category_distribution);
    
    // Savings Distribution Chart
    renderSavingsDistributionChart(analytics.savings_distribution);
}

// Render Top Savings Bar Chart
function renderTopSavingsChart(data) {
    const ctx = document.getElementById('topSavingsChart').getContext('2d');
    
    if (charts.topSavings) {
        charts.topSavings.destroy();
    }
    
    charts.topSavings = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => item.product_name),
            datasets: [{
                label: 'Savings (R)',
                data: data.map(item => item.savings),
                backgroundColor: 'rgba(102, 126, 234, 0.8)',
                borderColor: 'rgba(102, 126, 234, 1)',
                borderWidth: 2,
                borderRadius: 8,
                hoverBackgroundColor: 'rgba(118, 75, 162, 0.9)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Savings: R${context.parsed.y.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return 'R' + value.toFixed(0);
                        }
                    }
                },
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            },
            animation: {
                duration: 1500,
                easing: 'easeInOutQuart'
            }
        }
    });
}

// Render Category Distribution Pie Chart
function renderCategoryChart(data) {
    const ctx = document.getElementById('categoryChart').getContext('2d');
    
    if (charts.category) {
        charts.category.destroy();
    }
    
    const colors = [
        'rgba(102, 126, 234, 0.8)',
        'rgba(118, 75, 162, 0.8)',
        'rgba(40, 167, 69, 0.8)',
        'rgba(255, 193, 7, 0.8)',
        'rgba(220, 53, 69, 0.8)',
        'rgba(23, 162, 184, 0.8)'
    ];
    
    charts.category = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(item => item.category),
            datasets: [{
                data: data.map(item => item.savings),
                backgroundColor: colors,
                borderColor: colors.map(color => color.replace('0.8', '1')),
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return `${context.label}: R${context.parsed.toFixed(2)} (${percentage}%)`;
                        }
                    }
                }
            },
            animation: {
                animateRotate: true,
                animateScale: true,
                duration: 1500,
                easing: 'easeInOutQuart'
            }
        }
    });
}

// Render Savings Distribution Chart
function renderSavingsDistributionChart(data) {
    const ctx = document.getElementById('savingsDistributionChart').getContext('2d');
    
    if (charts.savingsDistribution) {
        charts.savingsDistribution.destroy();
    }
    
    charts.savingsDistribution = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(item => item.range),
            datasets: [{
                label: 'Number of Products',
                data: data.map(item => item.count),
                borderColor: 'rgba(102, 126, 234, 1)',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: 'rgba(102, 126, 234, 1)',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Products: ${context.parsed.y}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Products'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Savings Range (R)'
                    }
                }
            },
            animation: {
                duration: 2000,
                easing: 'easeInOutQuart'
            }
        }
    });
}

// Populate top products grid
function populateTopProducts(products) {
    const grid = document.getElementById('topProductsGrid');
    grid.innerHTML = '';
    
    products.forEach((product, index) => {
        const card = document.createElement('div');
        card.className = 'comparison-card';
        card.style.animationDelay = `${index * 0.1}s`;
        
        const savingsPercentage = ((product.price_difference / product.highest_price) * 100).toFixed(1);
        
        card.innerHTML = `
            <div class="comparison-product">${product.product_name}</div>
            <div class="comparison-savings">Save R${product.price_difference.toFixed(2)} (${savingsPercentage}%)</div>
            <div style="margin-bottom: 15px;">
                <span class="visual-indicator indicator-${savingsPercentage > 30 ? 'high' : savingsPercentage > 15 ? 'medium' : 'low'}"></span>
                <strong>Best Price:</strong> R${product.lowest_price.toFixed(2)} at ${product.lowest_warehouse}
            </div>
            <div class="price-breakdown">
                ${Object.entries(product.all_prices).map(([warehouse, price]) => `
                    <div class="price-item ${warehouse === product.lowest_warehouse ? 'best-price' : ''}">
                        ${warehouse}: R${price.toFixed(2)}
                    </div>
                `).join('')}
            </div>
        `;
        
        grid.appendChild(card);
    });
}

// Populate warehouse performance
function populateWarehousePerformance(warehouses) {
    const container = document.getElementById('warehousePerformance');
    container.innerHTML = '';
    
    const maxCount = Math.max(...warehouses.map(w => w.best_price_count));
    
    warehouses.forEach((warehouse, index) => {
        const percentage = (warehouse.best_price_count / maxCount) * 100;
        
        const item = document.createElement('div');
        item.className = 'warehouse-item';
        item.style.animationDelay = `${index * 0.1}s`;
        
        item.innerHTML = `
            <div class="warehouse-name">${warehouse.name}</div>
            <div class="warehouse-bar">
                <div class="warehouse-fill" style="width: 0%;" data-width="${percentage}%">
                    ${warehouse.best_price_count} products
                </div>
            </div>
        `;
        
        container.appendChild(item);
        
        // Animate the bar after a short delay
        setTimeout(() => {
            const fill = item.querySelector('.warehouse-fill');
            fill.style.width = fill.dataset.width;
        }, 100 + (index * 100));
    });
}

// Update insights section
function updateInsights(insights) {
    // Update key insight percentage
    const keyInsightValue = document.querySelector('.insight-value');
    if (keyInsightValue && insights.saving_percentage) {
        keyInsightValue.textContent = `${insights.saving_percentage}%`;
    }
    
    // Update best warehouse
    const bestWarehouseElements = document.querySelectorAll('.insight-value');
    if (bestWarehouseElements[1] && insights.best_warehouse) {
        bestWarehouseElements[1].textContent = insights.best_warehouse;
    }
    
    // Update last update time
    const lastUpdateElements = document.querySelectorAll('.insight-value');
    if (lastUpdateElements[2] && insights.last_update) {
        lastUpdateElements[2].textContent = insights.last_update;
    }
}

// Refresh marketing data
function refreshMarketingData() {
    const btn = document.getElementById('refreshDataBtn');
    const originalText = btn.innerHTML;
    
    btn.innerHTML = '🔄 Refreshing...';
    btn.disabled = true;
    
    fetch('/warehouse/marketing-analytics-data')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderMarketingCharts(data.data);
                populateTopProducts(data.data.top_products || []);
                populateWarehousePerformance(data.data.warehouse_performance || []);
                updateInsights(data.data.insights || {});
                showNotification('Analytics refreshed successfully!', 'success');
            } else {
                showNotification('Error refreshing analytics', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error refreshing analytics', 'error');
        })
        .finally(() => {
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
}

// Export marketing report
function exportMarketingReport() {
    const btn = document.getElementById('exportReportBtn');
    const originalText = btn.innerHTML;
    
    btn.innerHTML = '📊 Generating...';
    btn.disabled = true;
    
    fetch('/warehouse/export-marketing-report/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Create downloadable report
            downloadReport(data.report_data, data.filename);
            showNotification('Marketing report exported successfully!', 'success');
        } else {
            showNotification(data.error || 'Error exporting report', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error exporting report', 'error');
    })
    .finally(() => {
        btn.innerHTML = originalText;
        btn.disabled = false;
    });
}

// Download report as JSON file
function downloadReport(data, filename) {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || `marketing-report-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// Show loading state
function showLoadingState() {
    document.getElementById('loadingState').style.display = 'block';
}

// Hide loading state
function hideLoadingState() {
    document.getElementById('loadingState').style.display = 'none';
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 10px;
        color: white;
        font-weight: 500;
        z-index: 10000;
        max-width: 400px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        transform: translateX(100%);
        transition: transform 0.3s ease;
        background: linear-gradient(135deg, ${type === 'success' ? '#28a745, #20c997' : type === 'error' ? '#dc3545, #c82333' : '#17a2b8, #138496'});
    `;

    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);

    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 5000);
}

// Get CSRF token
function getCookie(name) {
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

// Auto-refresh every 5 minutes
setInterval(() => {
    refreshMarketingData();
}, 300000);

// Add keyboard shortcuts
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey || e.metaKey) {
        switch(e.key) {
            case 'r':
                e.preventDefault();
                refreshMarketingData();
                break;
            case 'e':
                e.preventDefault();
                exportMarketingReport();
                break;
        }
    }
});

// Add print functionality
function printMarketingReport() {
    window.print();
}

// Add share functionality
function shareMarketingReport() {
    if (navigator.share) {
        navigator.share({
            title: 'Price Comparison Marketing Analytics',
            text: 'Check out our latest price comparison insights and savings opportunities!',
            url: window.location.href
        }).catch(err => console.log('Error sharing:', err));
    } else {
        // Fallback - copy link to clipboard
        navigator.clipboard.writeText(window.location.href).then(() => {
            showNotification('Link copied to clipboard!', 'success');
        });
    }
}
