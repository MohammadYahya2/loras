/**
 * Wishlist functionality for Loras Boutique
 * This file handles all wishlist-related operations
 */

// Store initialized buttons to prevent duplicate listeners
const initializedButtons = new Set();

// Get CSRF token from cookies for AJAX requests
function getCSRFToken() {
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

// Update wishlist counter in the UI
function updateWishlistCounter(count) {
    const wishlistCounterElements = document.querySelectorAll('.wishlist-counter');
    wishlistCounterElements.forEach(element => {
        element.textContent = count;
        
        // Only show if count > 0
        if (count > 0) {
            element.classList.remove('hidden');
        } else {
            element.classList.add('hidden');
        }
    });
    console.log(`Wishlist counter updated to: ${count}`);
}

// Fetch current wishlist items to initialize button states
async function fetchWishlistItems() {
    try {
        const response = await fetch('/api/wishlist-items/');
        if (!response.ok) {
            throw new Error(`Error fetching wishlist items: ${response.status}`);
        }
        const data = await response.json();
        console.log('Fetched wishlist items:', data);
        return data.product_ids || [];
    } catch (error) {
        console.error('Error fetching wishlist items:', error);
        return [];
    }
}

// Toggle wishlist item (add or remove)
async function toggleWishlistItem(productId, button) {
    console.log(`Toggling wishlist for product ID: ${productId}`);
    
    try {
        // Disable the button during the request
        button.disabled = true;
        
        const response = await fetch('/toggle-wishlist/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCSRFToken()
            },
            body: `product_id=${productId}`,
            credentials: 'same-origin'
        });
        
        if (!response.ok) {
            throw new Error(`Server responded with status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Wishlist toggle response:', data);
        
        // Update button appearance
        const icon = button.querySelector('i');
        
        if (data.is_in_wishlist) {
            icon.classList.remove('far');
            icon.classList.add('fas', 'text-red-500');
            
            if (window.showCustomToast) {
                window.showCustomToast('تمت الإضافة إلى المفضلة', 'success');
            } else {
                window.showNotification('تمت الإضافة إلى المفضلة', 'success');
            }
        } else {
            icon.classList.remove('fas', 'text-red-500');
            icon.classList.add('far');
            
            if (window.showCustomToast) {
                window.showCustomToast('تمت الإزالة من المفضلة', 'warning');
            } else {
                window.showNotification('تمت الإزالة من المفضلة', 'warning');
            }
        }
        
        // Update the wishlist counter
        if (data.wishlist_count !== undefined) {
            updateWishlistCounter(data.wishlist_count);
        }
        
    } catch (error) {
        console.error('Error toggling wishlist item:', error);
        window.showNotification('حدث خطأ أثناء تحديث المفضلة', 'error');
    } finally {
        // Re-enable the button
        button.disabled = false;
    }
}

// Setup wishlist buttons with proper event listeners
async function initializeWishlistButtons() {
    console.log('Initializing wishlist buttons...');
    
    // Get current wishlist items
    const wishlistItems = await fetchWishlistItems();
    console.log('Current wishlist items:', wishlistItems);
    
    // Select all wishlist buttons
    const buttons = document.querySelectorAll('.wishlist-button');
    console.log(`Found ${buttons.length} wishlist buttons`);
    
    buttons.forEach(button => {
        // Skip already initialized buttons
        if (initializedButtons.has(button)) {
            return;
        }
        
        const productId = button.dataset.productId;
        if (!productId) {
            console.warn('Wishlist button missing product ID:', button);
            return;
        }
        
        // Set initial state based on wishlist data
        const icon = button.querySelector('i');
        if (wishlistItems.includes(parseInt(productId))) {
            icon.classList.remove('far');
            icon.classList.add('fas', 'text-red-500');
        } else {
            icon.classList.remove('fas', 'text-red-500');
            icon.classList.add('far');
        }
        
        // Add click event listener
        button.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            toggleWishlistItem(productId, button);
        });
        
        // Mark button as initialized
        initializedButtons.add(button);
    });
}

// Initialize on DOM content loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded - setting up wishlist functionality');
    initializeWishlistButtons();
    
    // Also run when new content is loaded via AJAX
    document.addEventListener('contentLoaded', function() {
        console.log('New content loaded - refreshing wishlist buttons');
        initializeWishlistButtons();
    });
});

// Re-initialize on page changes when using Turbo or similar frameworks
document.addEventListener('turbo:load', function() {
    console.log('Turbo load - refreshing wishlist buttons');
    initializedButtons.clear(); // Clear cache on new page
    initializeWishlistButtons();
});

// Export functions for external use
window.wishlistFunctions = {
    initializeWishlistButtons,
    toggleWishlistItem,
    updateWishlistCounter
}; 