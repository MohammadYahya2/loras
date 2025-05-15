/**
 * Main JavaScript for Loras Boutique
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded');
    
    // Initialize components
    initializeComponents();
    
    // Explicitly check and initialize hero slider with a slight delay to ensure DOM is fully ready
    setTimeout(() => {
        if (document.querySelector('.hero-slider')) {
            console.log('Initializing hero slider');
            initHeroSlider();
        }
    }, 100);
    
    // Initialize product gallery if on product detail page
    if (document.getElementById('main-image')) {
        initProductGallery();
    }
    
    // Add event listeners
    addEventListeners();
});

/**
 * Initialize all site components
 */
function initializeComponents() {
    // Initialize mobile search toggle
    initMobileSearch();
    
    // Initialize search functionality
    initSearch();
    
    // Initialize dropdowns
    initDropdowns();
    
    // Initialize toast notifications
    initToasts();
    
    // Initialize quantity inputs
    initQuantityInputs();
    
    // Initialize mobile categories menu
    initMobileCategories();
    
    // Initialize product filters (if on product list page)
    if (document.getElementById('min-price-handle') || document.getElementById('mobile-min-price-handle')) {
        initProductFilters();
    }
    
    // Initialize cart sidebar
    initCartSidebar();
    
    // Lazy load images
    lazyLoadImages();
}

/**
 * Initialize mobile search toggle
 */
function initMobileSearch() {
    const searchToggle = document.getElementById('mobile-search-toggle');
    const searchBar = document.getElementById('mobile-search-bar');
    
    if (searchToggle && searchBar) {
        searchToggle.addEventListener('click', () => {
            searchBar.classList.toggle('hidden');
            // Focus search input when shown
            if (!searchBar.classList.contains('hidden')) {
                const searchInput = document.getElementById('mobile-search-input');
                if (searchInput) {
                    setTimeout(() => searchInput.focus(), 100);
                }
            }
        });
    }
}

/**
 * Initialize search functionality with AJAX
 */
function initSearch() {
    // Desktop search
    setupSearchInput('desktop-search-input', 'desktop-search-results');
    
    // Mobile search
    setupSearchInput('mobile-search-input', 'mobile-search-results');
    
    // Close search results when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-input') && !e.target.closest('.search-results')) {
            document.querySelectorAll('.search-results').forEach(results => {
                results.classList.remove('active');
            });
        }
    });
}

/**
 * Set up search input with AJAX functionality
 */
function setupSearchInput(inputId, resultsId) {
    const searchInput = document.getElementById(inputId);
    const searchResults = document.getElementById(resultsId);
    
    if (!searchInput || !searchResults) return;
    
    let searchTimeout;
    let lastQuery = '';
    
    // Input event for typing
    searchInput.addEventListener('input', () => {
        const query = searchInput.value.trim();
        
        // Don't search for empty queries or if query is the same as last one
        if (query === '' || query === lastQuery) {
            if (query === '') {
                searchResults.classList.remove('active');
                searchResults.innerHTML = '';
            }
            return;
        }
        
        // Show loading indicator
        searchInput.parentNode.querySelector('.search-loading').style.display = 'block';
        
        // Clear previous timeout
        clearTimeout(searchTimeout);
        
        // Set timeout to avoid sending requests on every keystroke
        searchTimeout = setTimeout(() => {
            lastQuery = query;
            fetchSearchResults(query, searchResults, searchInput);
        }, 300);
    });
    
    // Focus event
    searchInput.addEventListener('focus', () => {
        const query = searchInput.value.trim();
        if (query !== '' && searchResults.innerHTML !== '') {
            searchResults.classList.add('active');
        }
    });
    
    // Key navigation in search results
    searchInput.addEventListener('keydown', (e) => {
        // If Escape, close results
        if (e.key === 'Escape') {
            searchResults.classList.remove('active');
            searchInput.blur();
            return;
        }
        
        // If Enter and results are visible, go to first result
        if (e.key === 'Enter' && searchResults.classList.contains('active')) {
            const firstResult = searchResults.querySelector('.search-result-item a');
            if (firstResult) {
                e.preventDefault();
                window.location.href = firstResult.href;
            }
            return;
        }
        
        // Arrow navigation not implemented for simplicity, but could be added
    });
}

/**
 * Fetch search results via AJAX
 */
function fetchSearchResults(query, resultsContainer, inputElement) {
    fetch(`/search/ajax/?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            // Hide loading indicator
            inputElement.parentNode.querySelector('.search-loading').style.display = 'none';
            
            // Show results container
            resultsContainer.classList.add('active');
            
            // Process the results
            if (data.results && data.results.length > 0) {
                renderSearchResults(data.results, resultsContainer);
            } else {
                resultsContainer.innerHTML = `
                    <div class="p-4 text-center text-gray-500">
                        <i class="fas fa-search-minus mb-2 text-2xl"></i>
                        <p>لا توجد نتائج لـ "${query}"</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Search error:', error);
            inputElement.parentNode.querySelector('.search-loading').style.display = 'none';
            
            resultsContainer.classList.add('active');
            resultsContainer.innerHTML = `
                <div class="p-4 text-center text-gray-500">
                    <i class="fas fa-exclamation-triangle mb-2 text-2xl text-red-500"></i>
                    <p>حدث خطأ أثناء البحث، يرجى المحاولة مرة أخرى</p>
                </div>
            `;
        });
}

/**
 * Render search results in the container
 */
function renderSearchResults(results, container) {
    let html = '';
    
    results.forEach(product => {
        html += `
            <a href="${product.url}" class="search-result-item block border-b border-gray-100 hover:bg-gray-50">
                <div class="flex items-center p-3">
                    <div class="w-12 h-12 rounded-md overflow-hidden bg-gray-100 flex-shrink-0">
                        <img src="${product.image}" alt="${product.name}" class="w-full h-full object-cover">
                    </div>
                    <div class="mr-3 flex-1">
                        <h4 class="text-sm font-medium text-gray-900">${product.name}</h4>
                        <div class="flex justify-between items-center mt-1">
                            <span class="text-sm text-primary font-bold">${product.price} ₪</span>
                            <span class="text-xs text-gray-500">${product.category}</span>
                        </div>
                    </div>
                </div>
            </a>
        `;
    });
    
    // Add view all results link
    html += `
        <div class="p-3 border-t border-gray-100 bg-gray-50">
            <a href="/search/?q=${encodeURIComponent(document.getElementById('desktop-search-input').value || document.getElementById('mobile-search-input').value)}" class="block text-center text-primary hover:underline">
                عرض جميع النتائج <i class="fas fa-arrow-left mr-1"></i>
            </a>
        </div>
    `;
    
    container.innerHTML = html;
}

/**
 * Initialize cart sidebar
 */
function initCartSidebar() {
    const cartToggleDesktop = document.getElementById('cart-toggle-desktop');
    const cartToggleMobile = document.getElementById('cart-toggle-mobile');
    const cartSidebar = document.getElementById('cart-sidebar');
    const cartSidebarOverlay = document.getElementById('cart-sidebar-overlay');
    const closeCart = document.getElementById('close-cart');
    
    const openCartSidebar = (e) => {
        if (e) e.preventDefault();
        cartSidebar.classList.add('open');
        document.body.style.overflow = 'hidden';
        loadCartItems();
    };
    
    const closeCartSidebar = () => {
        cartSidebar.classList.remove('open');
        document.body.style.overflow = '';
    };
    
    if (cartToggleDesktop) {
        cartToggleDesktop.addEventListener('click', openCartSidebar);
    }
    
    if (cartToggleMobile) {
        cartToggleMobile.addEventListener('click', openCartSidebar);
    }
    
    if (cartSidebarOverlay) {
        cartSidebarOverlay.addEventListener('click', closeCartSidebar);
    }
    
    if (closeCart) {
        closeCart.addEventListener('click', closeCartSidebar);
    }
    
    // Close on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && cartSidebar.classList.contains('open')) {
            closeCartSidebar();
        }
    });
}

/**
 * Initialize dropdown menus
 */
function initDropdowns() {
    const dropdownButtons = document.querySelectorAll('.dropdown-toggle');
    
    dropdownButtons.forEach(button => {
        const dropdownContent = button.nextElementSibling;
        
        button.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdownContent.classList.toggle('hidden');
        });
    });
    
    // Close all dropdowns when clicking outside
    document.addEventListener('click', () => {
        document.querySelectorAll('.dropdown-content').forEach(dropdown => {
            dropdown.classList.add('hidden');
        });
    });
}

/**
 * Initialize hero slider
 */
function initHeroSlider() {
    const sliderContainer = document.querySelector('.slider-container');
    const sliderItems = document.querySelectorAll('.slider-item');
    const sliderDots = document.querySelectorAll('.slider-dot');
    let currentIndex = 0;
    let isAnimating = false; // Flag to prevent interaction during animation
    let sliderInterval; // Store interval reference so we can clear it if needed
    
    // Make sure elements exist before proceeding
    if (!sliderContainer || !sliderItems.length || !sliderDots.length) {
        console.error('Hero slider elements not found');
        return;
    }
    
    // Force initial styles - ensure first slide is visible
    sliderItems.forEach((item, index) => {
        // Reset any inline styles that might persist from previous page loads
        item.style.display = '';
        item.style.opacity = '';
        
        if (index !== 0) {
            item.style.display = 'none';
            item.style.opacity = '0';
        } else {
            item.style.display = 'block';
            item.style.opacity = '1';
            // Add animation classes to first slide
            addAnimationClasses(item);
        }
        
        // Ensure transition styles are applied
        item.style.transition = 'opacity 300ms ease';
    });
    
    // Initialize slider dots
    sliderDots.forEach((dot, index) => {
        // Clear any classes that might persist
        dot.classList.remove('active', 'bg-primary');
        dot.classList.add('bg-gray-300');
        
        // Set active state for first dot
        if (index === 0) {
            dot.classList.add('active', 'bg-primary');
            dot.classList.remove('bg-gray-300');
        }
    });
    
    // Set automatic slider interval (5 seconds)
    sliderInterval = setInterval(() => {
        if (document.hidden) return; // Don't advance if page is not visible
        nextSlide();
    }, 6000); // Increased to 6 seconds for better user experience
    
    // Slider Controls
    sliderDots.forEach(dot => {
        dot.addEventListener('click', () => {
            // Prevent click if animation is in progress
            if (isAnimating) return;
            
            // Clear auto-advance interval to prevent conflicts
            clearInterval(sliderInterval);
            
            const index = parseInt(dot.getAttribute('data-index'));
            
            // Don't do anything if clicking the current slide
            if (index === currentIndex) return;
            
            showSlide(index);
            
            // Restart interval after manual navigation
            sliderInterval = setInterval(() => {
                if (document.hidden) return;
                nextSlide();
            }, 6000);
        });
    });
    
    function showSlide(index) {
        if (index >= sliderItems.length || index < 0) {
            console.error('Invalid slide index:', index);
            return;
        }
        
        isAnimating = true;
        
        // Hide current slide (fade out)
        sliderItems[currentIndex].style.opacity = '0';
        sliderDots[currentIndex].classList.remove('active', 'bg-primary');
        sliderDots[currentIndex].classList.add('bg-gray-300');
        
        // Remove animation classes from current slide
        resetAnimationClasses(sliderItems[currentIndex]);
        
        // After fade out animation completes, show the new slide
        setTimeout(() => {
            sliderItems[currentIndex].style.display = 'none';
            
            // Update current index
            currentIndex = index;
            
            // Show new slide and apply animation classes
            sliderItems[currentIndex].style.display = 'block';
            
            // Force a layout reflow to make sure display:block takes effect
            sliderItems[currentIndex].offsetHeight;
            
            // Wait a tiny bit before fading in to ensure display:block takes effect
            setTimeout(() => {
                sliderItems[currentIndex].style.opacity = '1';
                
                // Add animation classes to new slide elements
                addAnimationClasses(sliderItems[currentIndex]);
                
                // Update slider dots
                sliderDots[currentIndex].classList.remove('bg-gray-300');
                sliderDots[currentIndex].classList.add('active', 'bg-primary');
                
                // Animation complete
                setTimeout(() => {
                    isAnimating = false;
                }, 1000); // Extended to match the longest animation duration
            }, 50); // Extended for better compatibility with different browsers
        }, 300); // Extended for smoother fade out
    }
    
    function nextSlide() {
        // Prevent automatic advancement if animation is in progress
        if (isAnimating) return;
        
        let nextIndex = currentIndex + 1;
        if (nextIndex >= sliderItems.length) {
            nextIndex = 0;
        }
        showSlide(nextIndex);
    }
    
    // Helper function to reset animation classes
    function resetAnimationClasses(slide) {
        if (!slide) return;
        
        const animElements = slide.querySelectorAll('.animate-fadeInUp, .animate-fadeInLeft, .animate-fadeInRight');
        animElements.forEach(el => {
            el.classList.remove('animate-fadeInUp', 'animate-fadeInLeft', 'animate-fadeInRight');
        });
    }
    
    // Helper function to add animation classes
    function addAnimationClasses(slide) {
        if (!slide) return;
        
        const fadeUpElements = slide.querySelectorAll('h1, p, .flex.flex-wrap, .flex.items-center, .grid.grid-cols-2');
        const fadeLeftElements = slide.querySelectorAll('.hero-divider, .hero-badge');
        
        fadeUpElements.forEach(el => {
            el.classList.add('animate-fadeInUp');
        });
        
        fadeLeftElements.forEach(el => {
            el.classList.add('animate-fadeInLeft');
        });
    }
    
    // Handle visibility change to prevent animation issues when tab is not active
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            // Page is hidden, clear interval
            clearInterval(sliderInterval);
        } else {
            // Page is visible again, restart interval
            clearInterval(sliderInterval); // Clear any existing interval first
            sliderInterval = setInterval(() => {
                nextSlide();
            }, 6000);
        }
    });
    
    // Cleanup when leaving the page
    window.addEventListener('beforeunload', () => {
        clearInterval(sliderInterval);
    });
}

/**
 * Initialize product image gallery
 */
function initProductGallery() {
    const mainImage = document.getElementById('main-image');
    const thumbnails = document.querySelectorAll('.product-thumbnail');
    
    thumbnails.forEach(thumb => {
        thumb.addEventListener('click', function() {
            const imgSrc = this.getAttribute('data-image');
            
            if (mainImage && imgSrc) {
                // Add fade transition
                mainImage.style.opacity = '0';
                
                setTimeout(() => {
                    mainImage.src = imgSrc;
                    mainImage.style.opacity = '1';
                }, 300);
                
                // Remove active class from all thumbnails
                thumbnails.forEach(t => t.classList.remove('ring-2', 'ring-primary'));
                
                // Add active class to clicked thumbnail
                this.classList.add('ring-2', 'ring-primary');
            }
        });
    });
}

/**
 * Initialize quantity input components
 */
function initQuantityInputs() {
    const decreaseButtons = document.querySelectorAll('.quantity-btn.decrease');
    const increaseButtons = document.querySelectorAll('.quantity-btn.increase');
    
    decreaseButtons.forEach(button => {
        button.addEventListener('click', function() {
            const input = this.parentNode.querySelector('input');
            const currentValue = parseInt(input.value);
            
            if (currentValue > 1) {
                input.value = currentValue - 1;
                input.dispatchEvent(new Event('change'));
            }
        });
    });
    
    increaseButtons.forEach(button => {
        button.addEventListener('click', function() {
            const input = this.parentNode.querySelector('input');
            const currentValue = parseInt(input.value);
            const max = parseInt(input.getAttribute('max') || 99);
            
            if (currentValue < max) {
                input.value = currentValue + 1;
                input.dispatchEvent(new Event('change'));
            }
        });
    });
}

/**
 * Initialize toast notifications
 */
function initToasts() {
    // Close buttons for existing toasts
    document.querySelectorAll('.toast .close').forEach(btn => {
        btn.addEventListener('click', function() {
            this.parentNode.classList.remove('show');
            setTimeout(() => {
                this.parentNode.remove();
            }, 300);
        });
    });
    
    // Auto-hide toasts after 5 seconds
    document.querySelectorAll('.toast').forEach(toast => {
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, 5000);
    });
}

/**
 * Add global event listeners
 */
function addEventListeners() {
    // Close message alerts
    document.querySelectorAll('.close-message').forEach(button => {
        button.addEventListener('click', function() {
            this.closest('.fade-in').classList.add('fade-out');
            setTimeout(() => {
                this.closest('.fade-in').remove();
            }, 300);
        });
    });
    
    // Handle active state for mobile bottom navigation
    const currentPath = window.location.pathname;
    document.querySelectorAll('.mobile-bottom-nav .nav-item').forEach(item => {
        const href = item.getAttribute('href');
        if (href && currentPath.includes(href)) {
            item.classList.add('active');
        }
    });
    
    // Handle add to cart buttons
    document.querySelectorAll('.add-to-cart-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            if (!this.getAttribute('data-url')) return;
            
            e.preventDefault();
            const productId = this.getAttribute('data-product-id');
            const url = this.getAttribute('data-url');
            
            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: `product_id=${productId}`
            })
            .then(response => response.json())
            .then(data => {
                showToast('تمت إضافة المنتج إلى السلة بنجاح', 'success');
                updateCartCounter(data.cart_count);
            })
            .catch(error => {
                showToast('حدث خطأ أثناء إضافة المنتج', 'error');
            });
        });
    });
    
    // زر المفضلة مدار بواسطة custom-toast.js
    // تم التعليق هنا لمنع ازدواجية الوظائف
    
    // Handle add to wishlist buttons
    document.querySelectorAll('.add-to-wishlist-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            if (!this.getAttribute('data-url')) return;
            
            e.preventDefault();
            const productId = this.getAttribute('data-product-id');
            const url = this.getAttribute('data-url');
            
            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: `product_id=${productId}`
            })
            .then(response => response.json())
            .then(data => {
                showToast('تمت الإضافة للمفضلة', 'success');
                updateWishlistCounter(data.wishlist_count);
                
                // Change button icon if needed
                const icon = this.querySelector('i');
                if (icon) {
                    icon.classList.remove('far');
                    icon.classList.add('fas', 'text-red-500');
                }
            })
            .catch(error => {
                showToast('حدث خطأ', 'error');
            });
        });
    });
    
    // Handle newsletter subscription
    const newsletterForm = document.querySelector('.newsletter-form');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const email = this.querySelector('input[type="email"]').value;
            
            if (validateEmail(email)) {
                showToast('تم الاشتراك في النشرة البريدية بنجاح', 'success');
                this.reset();
            } else {
                showToast('يرجى إدخال بريد إلكتروني صحيح', 'error');
            }
        });
    }
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    // قديماً كانت هذه الدالة تقوم بإظهار الإشعارات
    // الآن سنعتمد على التجاوز في base.html
    // سنحافظ على هذه الدالة لتوافق الكود القديم ولكنها ستستدعي الدالة الجديدة فقط
    if (window.showToast !== showToast) {
        // نستدعي الدالة المعرفة في base.html
        window.showToast(message, type);
    } else {
        // في حالة عدم وجود الدالة المعرفة في base.html (لسبب ما)
        // نستخدم النافذة المنبثقة الافتراضية للمتصفح
        console.warn('Toast function not overridden properly');
        alert(message);
    }
}

/**
 * Update cart counter
 */
function updateCartCounter(count) {
    document.querySelectorAll('.cart-count').forEach(counter => {
        counter.textContent = count;
    });
}

/**
 * Update wishlist counter
 */
function updateWishlistCounter(count) {
    const wishlistCounters = document.querySelectorAll('.wishlist-count, #wishlist-count');
    wishlistCounters.forEach(counter => {
        counter.textContent = count;
        
        // Add animation effect to the counter (optional bounce animation)
        counter.classList.add('animate-bounce');
        setTimeout(() => {
            counter.classList.remove('animate-bounce');
        }, 1000);
    });
}

/**
 * Load cart items for sidebar
 */
function loadCartItems() {
    const cartItemsContainer = document.getElementById('cart-items-container');
    const cartLoading = document.getElementById('cart-loading');
    const cartSidebarTotal = document.getElementById('cart-sidebar-total-amount');
    
    if (!cartItemsContainer || !cartLoading) return;
    
    // Show loading spinner
    cartLoading.style.display = 'flex';
    
    // Fetch cart data
    fetch('/cart/api/', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        // Hide loading spinner
        cartLoading.style.display = 'none';
        
        // Clear previous items
        cartItemsContainer.innerHTML = '';
        
        if (data.items && data.items.length > 0) {
            // Update total
            if (cartSidebarTotal) {
                cartSidebarTotal.textContent = data.total;
            }
            
            // Add items to the sidebar
            data.items.forEach(item => {
                const itemElement = document.createElement('div');
                itemElement.className = 'cart-item flex items-start space-x-4 space-x-reverse border-b border-gray-100 py-4';
                itemElement.innerHTML = `
                    <div class="w-20 h-20 flex-shrink-0 bg-gray-100 rounded-md overflow-hidden">
                        <img src="${item.image}" alt="${item.name}" class="w-full h-full object-cover">
                    </div>
                    <div class="flex-1 min-w-0">
                        <h4 class="text-sm font-medium text-gray-900 truncate">${item.name}</h4>
                        <p class="text-sm text-gray-500">${item.size || ''} ${item.color || ''}</p>
                        <div class="flex justify-between items-center mt-2">
                            <div class="flex items-center">
                                <button type="button" class="cart-item-decrease text-gray-500 hover:text-primary focus:outline-none" data-id="${item.id}">
                                    <i class="fas fa-minus-circle"></i>
                                </button>
                                <span class="mx-2 text-gray-700">${item.quantity}</span>
                                <button type="button" class="cart-item-increase text-gray-500 hover:text-primary focus:outline-none" data-id="${item.id}">
                                    <i class="fas fa-plus-circle"></i>
                                </button>
                            </div>
                            <span class="font-semibold">₪${item.total}</span>
                        </div>
                    </div>
                    <button type="button" class="cart-item-remove text-gray-400 hover:text-red-500 focus:outline-none" data-id="${item.id}">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                `;
                cartItemsContainer.appendChild(itemElement);
            });
            
            // Add event listeners to the quantity buttons after a small delay
            setTimeout(() => {
                addCartItemEventListeners();
            }, 100);
        } else {
            // Empty cart
            cartItemsContainer.innerHTML = `
                <div class="flex flex-col items-center justify-center py-8">
                    <i class="fas fa-shopping-cart text-gray-300 text-5xl mb-4"></i>
                    <p class="text-gray-500 text-center">عربة التسوق فارغة</p>
                    <a href="/product/list/" class="mt-4 px-4 py-2 bg-primary text-white rounded-md hover:bg-secondary transition">تسوق الآن</a>
                </div>
            `;
            
            // Update total to zero
            if (cartSidebarTotal) {
                cartSidebarTotal.textContent = '0.00';
            }
        }
    })
    .catch(error => {
        console.error('Error loading cart items:', error);
        cartLoading.style.display = 'none';
        cartItemsContainer.innerHTML = `
            <div class="flex flex-col items-center justify-center py-8">
                <i class="fas fa-exclamation-circle text-red-500 text-5xl mb-4"></i>
                <p class="text-gray-500 text-center">حدث خطأ أثناء تحميل العربة</p>
                <button id="retry-cart-load" class="mt-4 px-4 py-2 bg-primary text-white rounded-md hover:bg-secondary transition">
                    إعادة المحاولة
                </button>
            </div>
        `;
        
        // Add retry button listener
        document.getElementById('retry-cart-load')?.addEventListener('click', loadCartItems);
    });
}

/**
 * Add event listeners to cart item buttons
 */
function addCartItemEventListeners() {
    console.log('Adding cart item event listeners');
    
    // Increase quantity
    document.querySelectorAll('.cart-item-increase').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            const itemId = this.getAttribute('data-id');
            console.log('Increasing quantity for item:', itemId);
            updateCartItemQuantity(itemId, 1);
        });
    });
    
    // Decrease quantity
    document.querySelectorAll('.cart-item-decrease').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            const itemId = this.getAttribute('data-id');
            console.log('Decreasing quantity for item:', itemId);
            updateCartItemQuantity(itemId, -1);
        });
    });
    
    // Remove item
    document.querySelectorAll('.cart-item-remove').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            const itemId = this.getAttribute('data-id');
            console.log('Removing item:', itemId);
            removeCartItem(itemId);
        });
    });
}

/**
 * Show small notification popup
 * @param {string} message - The notification message
 * @param {string} type - The notification type (success, danger, warning, info)
 */
function showSmallNotification(message, type = 'success') {
    // إزالة أي إشعارات موجودة
    const existingNotifications = document.querySelectorAll('.notification-popup');
    existingNotifications.forEach(notification => notification.remove());
    
    // إنشاء الإشعار الجديد
    const notification = document.createElement('div');
    notification.className = `notification-popup notification-${type}`;
    
    // تعيين الأنماط الأساسية
    Object.assign(notification.style, {
        position: 'fixed',
        top: '20px',
        left: '50%',
        transform: 'translateX(-50%)',
        padding: '8px 14px',
        borderRadius: '30px',
        boxShadow: '0 3px 10px rgba(0, 0, 0, 0.15)',
        zIndex: '9999',
        fontSize: '0.8rem',
        maxWidth: '80%',
        textAlign: 'center',
        transition: 'all 0.3s ease',
        direction: 'rtl',
        display: 'flex',
        alignItems: 'center',
        backgroundColor: 'white',
        border: 'none'
    });
    
    // تحديد لون وأيقونة الإشعار حسب نوعه
    const colors = {
        'success': '#10B981',
        'danger': '#EF4444',
        'warning': '#F59E0B',
        'info': '#3B82F6'
    };
    
    const icons = {
        'success': '<i class="fas fa-check" style="color:white"></i>',
        'danger': '<i class="fas fa-times" style="color:white"></i>',
        'warning': '<i class="fas fa-exclamation" style="color:white"></i>',
        'info': '<i class="fas fa-info" style="color:white"></i>'
    };
    
    // إضافة المحتوى للإشعار
    notification.innerHTML = `
        <div style="background-color:${colors[type]}; width:20px; height:20px; border-radius:50%; display:flex; align-items:center; justify-content:center; margin-left:8px; flex-shrink:0">
            ${icons[type] || icons.info}
        </div>
        <span style="color:#333; font-weight:500">${message}</span>
    `;
    
    // تحسين العرض على الأجهزة المحمولة
    if (window.innerWidth <= 640) {
        notification.style.maxWidth = '90%';
        notification.style.fontSize = '0.75rem';
    }
    
    // إضافة الإشعار للصفحة
    document.body.appendChild(notification);
    
    // تطبيق تأثير ظهور محسن
    notification.style.opacity = '0';
    notification.style.transform = 'translate(-50%, -10px)';
    
    // إظهار الإشعار بتأثير انتقالي
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translate(-50%, 0)';
    }, 10);
    
    // تأثير التلاشي بعد فترة
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translate(-50%, -10px)';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 2000);
}

/**
 * Update cart item quantity
 */
function updateCartItemQuantity(itemId, change) {
    // العثور على العنصر وتحديثه بشكل فوري للتجربة المستخدم
    const quantityElement = document.querySelector(`.cart-item-increase[data-id="${itemId}"]`).parentNode.querySelector('span');
    const currentQuantity = parseInt(quantityElement.textContent);
    const newQuantity = currentQuantity + change;
    
    // إيجاد عنصر السعر الإجمالي للمنتج
    const itemElement = document.querySelector(`.cart-item-increase[data-id="${itemId}"]`).closest('.cart-item');
    const priceElement = itemElement.querySelector('.font-semibold');
    
    // تحديث القيمة بشكل مؤقت (تأثير بصري فوري)
    if (newQuantity > 0) {
        quantityElement.textContent = newQuantity;
        
        // تحديث سعر المنتج بشكل مؤقت (يفترض أن السعر الوحدوي ثابت)
        // استخراج سعر الوحدة من النص (يزيل رمز العملة والمسافات)
        const priceText = priceElement.textContent;
        const unitPrice = parseFloat(priceText.replace('₪', '').trim()) / currentQuantity;
        const newItemTotal = unitPrice * newQuantity;
        
        // تأثير بصري عند تغيير السعر
        priceElement.style.transition = 'color 0.3s ease';
        priceElement.style.color = change > 0 ? '#10B981' : '#EF4444';
        priceElement.textContent = `₪${newItemTotal.toFixed(2)}`;
        
        // إعادة اللون بعد فترة
        setTimeout(() => {
            priceElement.style.color = '';
        }, 1000);
        
        // تحديث إجمالي السلة بشكل مؤقت
        updateCartTotal();
    }
    
    // إرسال طلب التحديث إلى الخادم
    fetch('/cart/update/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            item_id: itemId,
            quantity_change: change
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // إذا كانت الكمية 0 أو أقل، يتم إزالة العنصر بشكل كامل
            if (newQuantity <= 0) {
                itemElement.style.transition = 'all 0.3s ease';
                itemElement.style.opacity = '0';
                setTimeout(() => {
                    itemElement.remove();
                }, 300);
            }
            
            // تحديث عداد السلة
            updateCartCounter(data.cart_count);
            
            // تحديث إجمالي السلة
            updateCartTotal();
            
            // إظهار رسالة نجاح
            showSmallNotification(data.message, 'success');
        } else {
            // إعادة تحميل السلة في حالة الخطأ لإعادة الحالة الصحيحة
            loadCartItems();
            showSmallNotification(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error updating cart item:', error);
        // إعادة تحميل السلة في حالة الخطأ
        loadCartItems();
        showSmallNotification('حدث خطأ أثناء تحديث العربة', 'danger');
    });
}

/**
 * تحديث إجمالي سعر السلة
 */
function updateCartTotal() {
    const cartItems = document.querySelectorAll('.cart-item');
    let total = 0;
    
    cartItems.forEach(item => {
        const itemPrice = parseFloat(item.querySelector('.font-semibold').textContent.replace('₪', '').trim());
        total += itemPrice;
    });
    
    // تحديث إجمالي السلة في الواجهة
    const totalElement = document.getElementById('cart-sidebar-total-amount');
    if (totalElement) {
        // تطبيق تأثير بصري عند تغيير المجموع
        totalElement.style.transition = 'all 0.3s ease';
        const oldTotal = parseFloat(totalElement.textContent);
        
        // تغيير لون السعر بناءً على ما إذا كان زيادة أو نقصان
        if (total < oldTotal) {
            totalElement.style.color = '#EF4444'; // أحمر عند النقصان
        } else if (total > oldTotal) {
            totalElement.style.color = '#10B981'; // أخضر عند الزيادة
        }
        
        // تطبيق تأثير النص
        totalElement.style.fontWeight = 'bold';
        totalElement.style.transform = 'scale(1.1)';
        totalElement.textContent = total.toFixed(2);
        
        // إعادة اللون والحجم بعد فترة
        setTimeout(() => {
            totalElement.style.color = '';
            totalElement.style.transform = 'scale(1)';
            totalElement.style.fontWeight = '';
        }, 1000);
    }
    
    // تحديث إجمالي السلة في صفحة السلة
    const subTotalElement = document.getElementById('subtotal');
    if (subTotalElement) {
        // تحديث النص مع مراعاة تنسيق العملة
        const currentText = subTotalElement.textContent;
        if (currentText.includes('ر.س')) {
            subTotalElement.textContent = `${total.toFixed(2)} ر.س`;
        } else {
            subTotalElement.textContent = total.toFixed(2);
        }
    }
    
    // تحديث الإجمالي النهائي في صفحة السلة
    const cartTotalElement = document.getElementById('cart-total');
    if (cartTotalElement) {
        // تحديث النص مع مراعاة تنسيق العملة
        const currentText = cartTotalElement.textContent;
        if (currentText.includes('ر.س')) {
            cartTotalElement.textContent = `${total.toFixed(2)} ر.س`;
        } else {
            cartTotalElement.textContent = total.toFixed(2);
        }
    }
    
    // تحديث الإجمالي الفرعي في لوحة السلة الجانبية
    const totalAmountElement = document.getElementById('cart-sidebar-total');
    if (totalAmountElement) {
        // حدد عنصر الرقم فقط داخل النص
        const amountSpan = totalAmountElement.querySelector('span');
        if (amountSpan) {
            amountSpan.textContent = total.toFixed(2);
        } else {
            // إذا لم يكن هناك عنصر span داخلي، قم بتحديث النص الكامل
            totalAmountElement.textContent = `₪${total.toFixed(2)}`;
        }
    }
}

/**
 * Remove item from cart
 */
function removeCartItem(itemId) {
    // العثور على عنصر السلة
    const itemElement = document.querySelector(`.cart-item-increase[data-id="${itemId}"]`).closest('.cart-item');
    
    // تطبيق تأثير التلاشي على العنصر نفسه
    itemElement.style.transition = 'all 0.5s ease';
    itemElement.style.opacity = '0.5';
    itemElement.style.transform = 'translateX(10px)';
    
    // إرسال طلب الإزالة إلى الخادم
    fetch('/cart/remove/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            item_id: itemId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // إزالة العنصر من DOM بشكل كامل بعد اكتمال التأثير
            setTimeout(() => {
                itemElement.remove();
                
                // تحديث عداد السلة
                updateCartCounter(data.cart_count);
                
                // تحديث إجمالي السلة
                updateCartTotal();
                
                // أظهر إشعارًا لفراغ السلة إذا كانت فارغة
                if (data.cart_count === 0) {
                    const cartContainer = document.querySelector('.cart-container');
                    if (cartContainer) {
                        const emptyMessage = document.createElement('div');
                        emptyMessage.className = 'text-center p-4';
                        emptyMessage.innerHTML = `
                            <div class="text-gray-400 text-5xl mb-4">
                                <i class="fas fa-shopping-cart"></i>
                            </div>
                            <h3 class="text-xl font-bold text-gray-700 mb-2">سلة التسوق فارغة</h3>
                            <p class="text-gray-600">لم تقم بإضافة أي منتج إلى سلة التسوق</p>
                        `;
                        
                        // تأثير ظهور تدريجي للرسالة
                        emptyMessage.style.opacity = '0';
                        emptyMessage.style.transition = 'opacity 0.5s ease';
                        cartContainer.innerHTML = '';
                        cartContainer.appendChild(emptyMessage);
                        
                        setTimeout(() => {
                            emptyMessage.style.opacity = '1';
                        }, 100);
                    }
                }
                
                // إظهار رسالة نجاح
                showSmallNotification(data.message, 'success');
            }, 500);
        } else {
            // إعادة تحميل السلة في حالة الخطأ لإعادة الحالة الصحيحة
            loadCartItems();
            showSmallNotification(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error removing cart item:', error);
        // إعادة تحميل السلة في حالة الخطأ
        loadCartItems();
        showSmallNotification('حدث خطأ أثناء تحديث العربة', 'danger');
    });
}

/**
 * Lazy load images
 */
function lazyLoadImages() {
    const lazyImages = document.querySelectorAll('img[data-src]');
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const image = entry.target;
                    image.src = image.dataset.src;
                    image.removeAttribute('data-src');
                    imageObserver.unobserve(image);
                }
            });
        });
        
        lazyImages.forEach(image => imageObserver.observe(image));
    } else {
        // Fallback for browsers that don't support IntersectionObserver
        lazyImages.forEach(image => {
            image.src = image.dataset.src;
            image.removeAttribute('data-src');
        });
    }
}

/**
 * Get CSRF cookie for Django
 */
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

/**
 * Validate email format
 */
function validateEmail(email) {
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
}

/**
 * Initialize mobile categories menu
 */
function initMobileCategories() {
    const categoriesToggle = document.getElementById('mobile-categories-toggle');
    const categoriesMenu = document.getElementById('mobile-categories-menu');
    const categoriesPanel = document.getElementById('mobile-categories-panel');
    const closeCategories = document.getElementById('close-categories');
    
    if (categoriesToggle && categoriesMenu && categoriesPanel) {
        // Open categories menu
        categoriesToggle.addEventListener('click', () => {
            document.body.style.overflow = 'hidden';
            categoriesMenu.classList.remove('hidden');
            
            // Use setTimeout to ensure CSS transition works
            setTimeout(() => {
                categoriesPanel.classList.remove('translate-y-full');
            }, 10);
        });
        
        // Close categories menu
        const closeMenu = () => {
            categoriesPanel.classList.add('translate-y-full');
            
            // Hide menu after transition completes
            setTimeout(() => {
                categoriesMenu.classList.add('hidden');
                document.body.style.overflow = '';
            }, 300);
        };
        
        if (closeCategories) {
            closeCategories.addEventListener('click', closeMenu);
        }
        
        // Close when clicking outside the panel
        categoriesMenu.addEventListener('click', (e) => {
            if (e.target === categoriesMenu) {
                closeMenu();
            }
        });
        
        // Close on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !categoriesMenu.classList.contains('hidden')) {
                closeMenu();
            }
        });
    }
}

/**
 * Initialize product filters on product list page
 */
function initProductFilters() {
    // Price range slider functionality
    initPriceRangeSlider(
        'min-price-handle', 
        'max-price-handle', 
        'min-price', 
        'max-price', 
        '.relative.h-1.bg-gray-200', 
        '.absolute.h-1.bg-primary'
    );
    
    // Mobile price range slider
    initPriceRangeSlider(
        'mobile-min-price-handle', 
        'mobile-max-price-handle', 
        'mobile-min-price', 
        'mobile-max-price', 
        '#mobile-filter-sidebar .relative.h-1.bg-gray-200', 
        '#mobile-price-range-highlight'
    );
    
    // Sort dropdown functionality
    const sortSelect = document.querySelector('select.appearance-none');
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            const sortValue = this.value;
            sortProducts(sortValue);
        });
    }
    
    // View switcher functionality
    const gridViewBtn = document.getElementById('grid-view');
    const listViewBtn = document.getElementById('list-view');
    const gridContainer = document.getElementById('grid-view-container');
    const listContainer = document.getElementById('list-view-container');
    
    if (gridViewBtn && listViewBtn && gridContainer && listContainer) {
        gridViewBtn.addEventListener('click', function() {
            gridContainer.classList.remove('hidden');
            listContainer.classList.add('hidden');
            
            gridViewBtn.classList.add('bg-primary', 'text-white');
            gridViewBtn.classList.remove('bg-gray-100', 'text-gray-700');
            
            listViewBtn.classList.add('bg-gray-100', 'text-gray-700');
            listViewBtn.classList.remove('bg-primary', 'text-white');
            
            // Save preference
            localStorage.setItem('productViewPreference', 'grid');
        });
        
        listViewBtn.addEventListener('click', function() {
            listContainer.classList.remove('hidden');
            gridContainer.classList.add('hidden');
            
            listViewBtn.classList.add('bg-primary', 'text-white');
            listViewBtn.classList.remove('bg-gray-100', 'text-gray-700');
            
            gridViewBtn.classList.add('bg-gray-100', 'text-gray-700');
            gridViewBtn.classList.remove('bg-primary', 'text-white');
            
            // Save preference
            localStorage.setItem('productViewPreference', 'list');
        });
        
        // Load saved preference
        const savedView = localStorage.getItem('productViewPreference');
        if (savedView === 'list') {
            listViewBtn.click();
        }
    }
}

/**
 * Initialize price range slider functionality
 * This is a reusable function for both desktop and mobile sliders
 */
function initPriceRangeSlider(minHandleId, maxHandleId, minDisplayId, maxDisplayId, rangeSelector, highlightSelector) {
    const minPriceHandle = document.getElementById(minHandleId);
    const maxPriceHandle = document.getElementById(maxHandleId);
    const minPriceDisplay = document.getElementById(minDisplayId);
    const maxPriceDisplay = document.getElementById(maxDisplayId);
    const priceRange = document.querySelector(rangeSelector);
    const priceRangeHighlight = document.querySelector(highlightSelector);
    const filterButton = document.querySelector(`#${minHandleId}`.includes('mobile') ? '#mobile-price-filter-btn' : '.bg-white.p-5 .bg-primary.hover\\:bg-secondary');
    
    if (minPriceHandle && maxPriceHandle && priceRange) {
        let isDraggingMin = false;
        let isDraggingMax = false;
        
        // Default price range values
        let minPrice = parseInt(minPriceDisplay.textContent) || 0;
        let maxPrice = parseInt(maxPriceDisplay.textContent) || 1000;
        
        // Functions to update price display and slider
        function updatePriceUI() {
            // Update price displays
            if (minPriceDisplay) minPriceDisplay.textContent = minPrice;
            if (maxPriceDisplay) maxPriceDisplay.textContent = maxPrice;
            
            // Calculate positions as percentages
            const maxPossiblePrice = 1000; // Default max range
            const minPos = (minPrice / maxPossiblePrice) * 100;
            const maxPos = (maxPrice / maxPossiblePrice) * 100;
            
            // Update slider UI
            minPriceHandle.style.left = `${minPos}%`;
            maxPriceHandle.style.left = `${maxPos}%`;
            
            // Update highlight bar position and width
            priceRangeHighlight.style.left = `${minPos}%`;
            priceRangeHighlight.style.width = `${maxPos - minPos}%`;
        }
        
        // Event listeners for mouse/touch interactions
        minPriceHandle.addEventListener('mousedown', (e) => {
            isDraggingMin = true;
            e.preventDefault();
        });
        
        maxPriceHandle.addEventListener('mousedown', (e) => {
            isDraggingMax = true;
            e.preventDefault();
        });
        
        document.addEventListener('mouseup', () => {
            isDraggingMin = false;
            isDraggingMax = false;
        });
        
        document.addEventListener('mousemove', function(e) {
            if (!isDraggingMin && !isDraggingMax) return;
            
            // Calculate position as percentage of slider width
            const rangeRect = priceRange.getBoundingClientRect();
            let posPercent = ((e.clientX - rangeRect.left) / rangeRect.width) * 100;
            
            // Constrain to slider bounds (0-100%)
            posPercent = Math.max(0, Math.min(100, posPercent));
            
            if (isDraggingMin) {
                // Ensure min handle doesn't go past max handle
                if (posPercent >= parseFloat(maxPriceHandle.style.left)) {
                    posPercent = parseFloat(maxPriceHandle.style.left) - 1;
                }
                
                // Update min price value
                minPrice = Math.round((posPercent / 100) * 1000);
                
                // Update UI
                updatePriceUI();
            }
            
            if (isDraggingMax) {
                // Ensure max handle doesn't go behind min handle
                if (posPercent <= parseFloat(minPriceHandle.style.left)) {
                    posPercent = parseFloat(minPriceHandle.style.left) + 1;
                }
                
                // Update max price value
                maxPrice = Math.round((posPercent / 100) * 1000);
                
                // Update UI
                updatePriceUI();
            }
        });
        
        // Mobile/touch support
        minPriceHandle.addEventListener('touchstart', (e) => {
            isDraggingMin = true;
            e.preventDefault();
        });
        
        maxPriceHandle.addEventListener('touchstart', (e) => {
            isDraggingMax = true;
            e.preventDefault();
        });
        
        document.addEventListener('touchend', () => {
            isDraggingMin = false;
            isDraggingMax = false;
        });
        
        document.addEventListener('touchmove', function(e) {
            if (!isDraggingMin && !isDraggingMax) return;
            
            // Get touch position
            const touch = e.touches[0];
            const rangeRect = priceRange.getBoundingClientRect();
            let posPercent = ((touch.clientX - rangeRect.left) / rangeRect.width) * 100;
            
            // Constrain to slider bounds (0-100%)
            posPercent = Math.max(0, Math.min(100, posPercent));
            
            if (isDraggingMin) {
                // Ensure min handle doesn't go past max handle
                if (posPercent >= parseFloat(maxPriceHandle.style.left)) {
                    posPercent = parseFloat(maxPriceHandle.style.left) - 1;
                }
                
                // Update min price value
                minPrice = Math.round((posPercent / 100) * 1000);
                
                // Update UI
                updatePriceUI();
            }
            
            if (isDraggingMax) {
                // Ensure max handle doesn't go behind min handle
                if (posPercent <= parseFloat(minPriceHandle.style.left)) {
                    posPercent = parseFloat(minPriceHandle.style.left) + 1;
                }
                
                // Update max price value
                maxPrice = Math.round((posPercent / 100) * 1000);
                
                // Update UI
                updatePriceUI();
            }
        });
        
        // Initialize slider positions
        updatePriceUI();
        
        // Filter button click event
        if (filterButton) {
            filterButton.addEventListener('click', function() {
                filterProducts(minPrice, maxPrice);
            });
        }
    }
}

/**
 * Filter products by price range
 */
function filterProducts(minPrice, maxPrice) {
    // Show loading overlay
    showFilterLoading(true);
    
    // Get current URL and params
    const url = new URL(window.location.href);
    const params = url.searchParams;
    
    // Update price filter params
    params.set('min_price', minPrice);
    params.set('max_price', maxPrice);
    
    // Redirect to filtered URL
    window.location.href = url.toString();
}

/**
 * Sort products based on selected option
 */
function sortProducts(sortValue) {
    // Show loading overlay
    showFilterLoading(true);
    
    // Get current URL and params
    const url = new URL(window.location.href);
    const params = url.searchParams;
    
    // Update sort param
    if (sortValue && sortValue !== 'default') {
        params.set('sort', sortValue);
    } else {
        params.delete('sort');
    }
    
    // Redirect to sorted URL
    window.location.href = url.toString();
}

/**
 * Show/hide loading overlay during filtering
 */
function showFilterLoading(show) {
    let loadingOverlay = document.getElementById('filter-loading-overlay');
    
    if (show) {
        if (!loadingOverlay) {
            loadingOverlay = document.createElement('div');
            loadingOverlay.id = 'filter-loading-overlay';
            loadingOverlay.className = 'fixed inset-0 bg-white bg-opacity-75 flex items-center justify-center z-50';
            loadingOverlay.innerHTML = `
                <div class="text-center">
                    <div class="inline-block w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mb-2"></div>
                    <p class="text-gray-700">جاري تطبيق التصفية...</p>
                </div>
            `;
            document.body.appendChild(loadingOverlay);
        } else {
            loadingOverlay.classList.remove('hidden');
        }
    } else if (loadingOverlay) {
        loadingOverlay.classList.add('hidden');
    }
} 