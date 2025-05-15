/**
 * Custom JavaScript for Loras Boutique
 * Enhances user experience with smooth animations and improved interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeToasts();
    initializeQuantityButtons();
    initializeMobileMenu();
    initializeImageGalleries();
    initializeWishlistToggle();
    initializeAnimations();
    enhanceQuickView();
    
    // Add smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            if (this.getAttribute('href') !== '#') {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    window.scrollTo({
                        top: target.offsetTop - 80, // Offset for fixed header
                        behavior: 'smooth'
                    });
                }
            }
        });
    });
});

/**
 * Toast Notification System
 */
function initializeToasts() {
    // Create toast container if it doesn't exist
    if (!document.querySelector('.toast-container')) {
        const toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }
    
    // Global function to show toast messages
    window.showToast = function(message, type = 'info', duration = 3000) {
        const container = document.querySelector('.toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = message;
        
        container.appendChild(toast);
        
        // Force reflow before adding show class for animation
        toast.offsetHeight;
        toast.classList.add('show');
        
        // Auto remove after duration
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                toast.remove();
            }, 300); // Match transition duration
        }, duration);
    };
}

/**
 * Quantity Input Handlers
 */
function initializeQuantityButtons() {
    // Find all quantity input groups
    document.querySelectorAll('.quantity-input-group').forEach(group => {
        const input = group.querySelector('.quantity-input');
        const minusBtn = group.querySelector('.quantity-minus');
        const plusBtn = group.querySelector('.quantity-plus');
        
        if (input && minusBtn && plusBtn) {
            minusBtn.addEventListener('click', () => {
                const currentValue = parseInt(input.value);
                if (currentValue > 1) {
                    input.value = currentValue - 1;
                    // Trigger change event for cart updates
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });
            
            plusBtn.addEventListener('click', () => {
                const currentValue = parseInt(input.value);
                const max = input.getAttribute('max');
                if (!max || currentValue < parseInt(max)) {
                    input.value = currentValue + 1;
                    // Trigger change event for cart updates
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });
            
            // Validate input on change
            input.addEventListener('change', () => {
                let value = parseInt(input.value);
                if (isNaN(value) || value < 1) {
                    value = 1;
                }
                
                const max = input.getAttribute('max');
                if (max && value > parseInt(max)) {
                    value = parseInt(max);
                }
                
                input.value = value;
            });
        }
    });
}

/**
 * Mobile Menu Functionality
 */
function initializeMobileMenu() {
    const menuToggle = document.querySelector('.mobile-menu-toggle');
    const mobileMenu = document.querySelector('.mobile-menu');
    const closeBtn = document.querySelector('.mobile-menu-close');
    
    // Create overlay if it doesn't exist
    if (!document.querySelector('.mobile-menu-overlay')) {
        const overlay = document.createElement('div');
        overlay.className = 'mobile-menu-overlay';
        document.body.appendChild(overlay);
    }
    
    const overlay = document.querySelector('.mobile-menu-overlay');
    
    if (menuToggle && mobileMenu && closeBtn && overlay) {
        menuToggle.addEventListener('click', () => {
            mobileMenu.classList.add('open');
            overlay.classList.add('open');
            document.body.style.overflow = 'hidden'; // Prevent scrolling
        });
        
        closeBtn.addEventListener('click', closeMobileMenu);
        overlay.addEventListener('click', closeMobileMenu);
        
        function closeMobileMenu() {
            mobileMenu.classList.remove('open');
            overlay.classList.remove('open');
            document.body.style.overflow = ''; // Restore scrolling
        }
    }
}

/**
 * Image Gallery Functionality
 */
function initializeImageGalleries() {
    document.querySelectorAll('.gallery-container').forEach(gallery => {
        const images = gallery.querySelectorAll('.gallery-image');
        const indicators = gallery.querySelectorAll('.gallery-indicator');
        
        if (images.length > 1) {
            // Setup initial state
            images[0].classList.add('active');
            if (indicators.length > 0) {
                indicators[0].classList.add('active');
            }
            
            // Setup indicators
            indicators.forEach((indicator, index) => {
                indicator.addEventListener('click', () => {
                    // Remove active class from all
                    images.forEach(img => img.classList.remove('active'));
                    indicators.forEach(ind => ind.classList.remove('active'));
                    
                    // Add active class to selected
                    images[index].classList.add('active');
                    indicator.classList.add('active');
                });
            });
            
            // Auto rotate if gallery has data-auto attribute
            if (gallery.dataset.auto === 'true') {
                let currentIndex = 0;
                setInterval(() => {
                    currentIndex = (currentIndex + 1) % images.length;
                    
                    // Remove active class from all
                    images.forEach(img => img.classList.remove('active'));
                    indicators.forEach(ind => ind.classList.remove('active'));
                    
                    // Add active class to next
                    images[currentIndex].classList.add('active');
                    if (indicators.length > 0) {
                        indicators[currentIndex].classList.add('active');
                    }
                }, 5000); // Rotate every 5 seconds
            }
        }
    });
}

/**
 * Wishlist Toggle Functionality
 */
function initializeWishlistToggle() {
    document.querySelectorAll('.wishlist-toggle-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            const productId = this.getAttribute('data-product');
            if (!productId) return;
            
            // Add loading state
            this.classList.add('loading');
            
            // Send AJAX request to toggle wishlist
            fetch('/toggle-wishlist/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({ product_id: productId })
            })
            .then(response => response.json())
            .then(data => {
                // Remove loading state
                this.classList.remove('loading');
                
                // Update icon
                const icon = this.querySelector('i');
                if (data.is_in_wishlist) {
                    icon.className = 'fas fa-heart text-red-500';
                    showToast('تمت إضافة المنتج إلى المفضلة', 'success');
                } else {
                    icon.className = 'far fa-heart';
                    showToast('تمت إزالة المنتج من المفضلة', 'info');
                }
            })
            .catch(error => {
                console.error('Error toggling wishlist:', error);
                this.classList.remove('loading');
                showToast('حدث خطأ. يرجى المحاولة مرة أخرى', 'error');
            });
        });
    });
}

/**
 * Add smooth animations to elements
 */
function initializeAnimations() {
    // Fade in elements as they scroll into view
    const fadeElements = document.querySelectorAll('.fade-in');
    
    if (fadeElements.length > 0 && 'IntersectionObserver' in window) {
        const fadeObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    fadeObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.2 });
        
        fadeElements.forEach(element => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(20px)';
            element.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            fadeObserver.observe(element);
        });
        
        // Add CSS for visible class
        const style = document.createElement('style');
        style.textContent = `.fade-in.visible { opacity: 1 !important; transform: translateY(0) !important; }`;
        document.head.appendChild(style);
    }
}

/**
 * Enhance Quick View functionality
 */
function enhanceQuickView() {
    const originalQuickViewInit = window.initializeQuickView;
    
    // If quick view is already initialized
    if (typeof originalQuickViewInit === 'function') {
        window.initializeQuickView = function() {
            // Call original function first
            originalQuickViewInit();
            
            // Our enhancements
            const quickViewModal = document.getElementById('quick-view-modal');
            
            if (quickViewModal) {
                // Add transition class
                quickViewModal.classList.add('quick-view-modal');
                
                // Enhance content loading experience
                const content = document.getElementById('quick-view-content');
                if (content) {
                    content.classList.add('quick-view-content');
                }
            }
        };
        
        // Re-initialize with our enhancements
        window.initializeQuickView();
    }
    
    // Initialize quantity buttons in quick view after content loads
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('quick-view-btn')) {
            setTimeout(() => {
                const quickViewContent = document.getElementById('quick-view-content');
                if (quickViewContent) {
                    initializeQuantityButtons();
                }
            }, 500); // Wait for content to load
        }
    });
}

/**
 * Helper function to get CSRF token
 */
function getCsrfToken() {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith('csrftoken=')) {
            return cookie.substring('csrftoken='.length);
        }
    }
    return '';
}

/**
 * Product image zoom effect on hover
 */
function initializeImageZoom() {
    document.querySelectorAll('.product-detail-image').forEach(img => {
        img.addEventListener('mousemove', function(e) {
            const { left, top, width, height } = this.getBoundingClientRect();
            const x = (e.clientX - left) / width * 100;
            const y = (e.clientY - top) / height * 100;
            
            this.style.transformOrigin = `${x}% ${y}%`;
        });
        
        img.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.5)';
        });
        
        img.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
            this.style.transformOrigin = 'center center';
        });
    });
} 