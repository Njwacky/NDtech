// Run comparison functionality
document.addEventListener('DOMContentLoaded', function() {
    const runComparisonBtn = document.getElementById('runComparisonBtn');
    if (runComparisonBtn) {
        runComparisonBtn.addEventListener('click', function() {
            runComparison();
        });
    }

    const runComparisonEmptyBtn = document.getElementById('runComparisonEmptyBtn');
    if (runComparisonEmptyBtn) {
        runComparisonEmptyBtn.addEventListener('click', function() {
            runComparison();
        });
    }
});

function runComparison() {
    const btn = event.target;
    const originalText = btn.innerHTML;
    
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running...';
    btn.disabled = true;

    fetch('/warehouse/run-comparison/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        if (data.success) {
            showNotification(data.message, 'success');
            setTimeout(function() {
                window.location.reload();
            }, 1500);
        } else {
            showNotification(data.error || 'Error running comparison', 'error');
        }
    })
    .catch(function(error) {
        console.error('Error:', error);
        showNotification('Error running comparison', 'error');
    })
    .finally(function() {
        btn.innerHTML = originalText;
        btn.disabled = false;
    });
}

// Show price comparison details
function showDetails(comparisonId) {
    fetch('/warehouse/price-comparison-details/' + comparisonId + '/')
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.success) {
                displayComparisonDetails(data.comparison);
            } else {
                showNotification(data.error || 'Error loading details', 'error');
            }
        })
        .catch(function(error) {
            console.error('Error:', error);
            showNotification('Error loading details', 'error');
        });
}

function displayComparisonDetails(comparison) {
    const modal = document.getElementById('detailsModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalContent = document.getElementById('modalContent');

    modalTitle.textContent = comparison.product_name;

    var pricesHtml = '';
    if (comparison.all_prices) {
        for (var warehouse in comparison.all_prices) {
            var price = comparison.all_prices[warehouse];
            var isLowest = warehouse === comparison.lowest_warehouse;
            pricesHtml += '<tr>' +
                '<td>' + warehouse + '</td>' +
                '<td style="font-weight: ' + (isLowest ? 'bold' : 'normal') + '; color: ' + (isLowest ? '#28a745' : '#333') + ';">' +
                    'R' + price +
                    (isLowest ? ' ✓' : '') +
                '</td>' +
                '</tr>';
        }
    }

    modalContent.innerHTML = `
        <div style="margin-bottom: 20px;">
            <p><strong>Barcode:</strong> ${comparison.barcode || 'N/A'}</p>
            <p><strong>Lowest Price:</strong> <span style="color: #28a745; font-weight: bold;">R${comparison.lowest_price}</span></p>
            <p><strong>Best Warehouse:</strong> ${comparison.lowest_warehouse}</p>
            <p><strong>Price Difference:</strong> R${comparison.price_difference}</p>
            <p><strong>Comparison Date:</strong> ${new Date(comparison.comparison_date).toLocaleString()}</p>
        </div>

        <h4>Price Breakdown</h4>
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="background-color: #f8f9fa;">
                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">Warehouse</th>
                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">Price</th>
                </tr>
            </thead>
            <tbody>
                ${pricesHtml}
            </tbody>
        </table>

        <div style="margin-top: 20px; text-align: right;">
            <button type="button" onclick="closeDetails()" class="btn btn-primary">Close</button>
        </div>
    `;

    modal.style.display = 'block';
}

function closeDetails() {
    document.getElementById('detailsModal').style.display = 'none';
}

// Utility functions
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 5px;
        color: white;
        font-weight: 500;
        z-index: 10000;
        max-width: 400px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transform: translateX(100%);
        transition: transform 0.3s ease;
    `;

    const colors = {
        success: '#28a745',
        error: '#dc3545',
        warning: '#ffc107',
        info: '#17a2b8'
    };

    notification.style.backgroundColor = colors[type] || colors.info;
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

// Close modal when clicking outside
window.addEventListener('click', function(event) {
    const modal = document.getElementById('detailsModal');
    if (event.target === modal) {
        closeDetails();
    }
});

// Auto-refresh every 5 minutes
setInterval(function() {
    window.location.reload();
}, 300000);
