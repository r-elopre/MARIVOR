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

// Cart functionality (placeholder for now)
function addToCart(productId, productName = '') {
    // Show loading state
    const button = event.target.closest('button');
    const originalHTML = button.innerHTML;
    button.innerHTML = '<i class="bi bi-hourglass-split"></i> Adding...';
    button.disabled = true;
    
    // Simulate API call delay
    setTimeout(() => {
        // Reset button
        button.innerHTML = originalHTML;
        button.disabled = false;
        
        // Show success message
        showNotification(`"${productName}" added to cart!`, 'success');
        
        // In the future, this will make an actual API call
        console.log(`Adding product ${productId} to cart`);
    }, 1000);
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