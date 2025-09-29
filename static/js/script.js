// Marivor - JavaScript Functions

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Marivor app loaded successfully!');
    
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});

// Cart functionality - Enhanced version with stock checking
function addToCart(productId, productName = '') {
    // Show loading state
    const button = event.target.closest('button');
    const originalHTML = button.innerHTML;
    button.innerHTML = '<i class="bi bi-hourglass-split"></i> Checking...';
    button.disabled = true;
    
    // First, check stock availability
    fetch('/api/cart/check-stock', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: 1
        })
    })
    .then(response => response.json())
    .then(stockData => {
        if (!stockData.success) {
            // Stock check failed - show error and reset button
            button.innerHTML = originalHTML;
            button.disabled = false;
            showNotification(stockData.error || 'Product is out of stock', 'warning');
            return;
        }
        
        // Stock is available - proceed with adding to cart
        button.innerHTML = '<i class="bi bi-hourglass-split"></i> Adding...';
        
        // Make API call to add item to cart
        fetch('/api/cart/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                product_id: productId,
                quantity: 1
            })
        })
        .then(response => response.json())
        .then(data => {
            // Reset button
            button.innerHTML = originalHTML;
            button.disabled = false;
            
            if (data.success) {
                // Update cart count in navigation
                updateCartBadge(data.cart_count);
                
                // Show success message
                showNotification(data.message || `"${productName}" added to cart!`, 'success');
                
                // Briefly change button text to show success
                const successHTML = '<i class="bi bi-check2"></i> Added!';
                button.innerHTML = successHTML;
                button.classList.add('btn-success');
                button.classList.remove('btn-primary');
                
                setTimeout(() => {
                    button.innerHTML = originalHTML;
                    button.classList.remove('btn-success');
                    button.classList.add('btn-primary');
                }, 2000);
            } else {
                showNotification(data.error || 'Failed to add item to cart', 'danger');
            }
        })
        .catch(error => {
            // Reset button
            button.innerHTML = originalHTML;
            button.disabled = false;
            
            console.error('Error:', error);
            showNotification('Failed to add item to cart', 'danger');
        });
    })
    .catch(error => {
        // Stock check failed - reset button
        button.innerHTML = originalHTML;
        button.disabled = false;
        
        console.error('Stock check error:', error);
        showNotification('Failed to check product availability', 'danger');
    });
}

// Update cart badge in navigation
function updateCartBadge(cartCount) {
    // Update desktop cart badge
    const desktopBadge = document.querySelector('.navbar-nav .badge');
    if (desktopBadge) {
        if (cartCount > 0) {
            desktopBadge.textContent = cartCount;
            desktopBadge.style.display = 'inline';
        } else {
            desktopBadge.style.display = 'none';
        }
    }
    
    // Update mobile cart badge
    const mobileBadge = document.querySelector('.cart-badge');
    if (mobileBadge) {
        if (cartCount > 0) {
            mobileBadge.textContent = cartCount;
            mobileBadge.style.display = 'flex';
        } else {
            mobileBadge.style.display = 'none';
        }
    }
}

// Get current cart data
function getCartData() {
    return fetch('/api/cart/get')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                return data.cart;
            }
            throw new Error(data.error || 'Failed to get cart data');
        })
        .catch(error => {
            console.error('Error getting cart data:', error);
            return { items: [], total_items: 0, total_price: 0.0 };
        });
}

// Notification system
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 3000);
}

// Form validation helpers
function validatePhoneNumber(phone) {
    // Simple phone validation - can be enhanced
    const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
    return phoneRegex.test(phone.replace(/[\s\-\(\)]/g, ''));
}

function validateOTP(otp) {
    // OTP should be 6 digits
    const otpRegex = /^\d{6}$/;
    return otpRegex.test(otp);
}

// Search functionality (for future use)
function searchProducts(query) {
    console.log(`Searching for: ${query}`);
    // Will implement search functionality later
}

// Sort products (used in category pages)
function sortProducts(sortBy) {
    const grid = document.getElementById('products-grid');
    if (!grid) return;
    
    const cards = Array.from(grid.children);
    
    cards.sort((a, b) => {
        switch(sortBy) {
            case 'price-low':
                return parseFloat(a.dataset.price) - parseFloat(b.dataset.price);
            case 'price-high':
                return parseFloat(b.dataset.price) - parseFloat(a.dataset.price);
            case 'name':
                return a.dataset.name.localeCompare(b.dataset.name);
            case 'newest':
            default:
                return new Date(b.dataset.date) - new Date(a.dataset.date);
        }
    });
    
    // Re-append sorted cards with animation
    cards.forEach((card, index) => {
        setTimeout(() => {
            grid.appendChild(card);
        }, index * 50);
    });
}

// Utility functions
function formatPrice(price) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(price);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Loading states
function showLoading(element) {
    element.innerHTML = '<i class="bi bi-hourglass-split"></i> Loading...';
    element.disabled = true;
}

function hideLoading(element, originalText) {
    element.innerHTML = originalText;
    element.disabled = false;
}

// Error handling
function handleError(error, context = '') {
    console.error(`Error in ${context}:`, error);
    showNotification('Something went wrong. Please try again.', 'danger');
}