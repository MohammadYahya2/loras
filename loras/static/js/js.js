// Quick View Functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('تهيئة وظيفة المعاينة السريعة');
    
    // تهيئة عناصر المعاينة السريعة
    const quickViewButtons = document.querySelectorAll('.quick-view-btn');
    const quickViewModal = document.getElementById('quick-view-modal');
    const quickViewContent = document.getElementById('quick-view-content');
    
    if (quickViewButtons.length) {
        console.log(`تم العثور على ${quickViewButtons.length} أزرار للمعاينة السريعة`);
        
        // إضافة أحداث النقر لأزرار المعاينة السريعة
        quickViewButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const productId = this.getAttribute('data-product');
                console.log('طلب معاينة سريعة للمنتج:', productId);
                
                if (!productId) {
                    console.error('معرف المنتج غير موجود');
                    return;
                }
                
                // فتح نافذة المعاينة السريعة وعرض مؤشر التحميل
                if (quickViewModal) {
                    quickViewModal.classList.remove('hidden');
                    document.body.classList.add('overflow-hidden');
                    
                    if (quickViewContent) {
                        quickViewContent.innerHTML = `
                            <div class="bg-white p-6 rounded-xl shadow-lg">
                                <div class="flex justify-center">
                                    <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
                                    <p class="text-gray-500 mr-3">جاري التحميل...</p>
                                </div>
                            </div>
                        `;
                    }
                    
                    // إنشاء عنوان URL بشكل صحيح مع الاسلاش مطابق تماماً لما هو في urls.py
                    const baseUrl = window.location.origin; // الحصول على عنوان الموقع الأساسي
                    const url = `${baseUrl}/quick-view/${productId}/`;
                    console.log('جار طلب البيانات من:', url);
                    
                    // طلب بيانات المنتج
                    fetch(url, {
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                            'Accept': 'text/html'
                        }
                    })
                    .then(response => {
                        console.log('حالة الاستجابة:', response.status, response.statusText);
                        if (!response.ok) {
                            throw new Error(`خطأ في الطلب: ${response.status}`);
                        }
                        return response.text();
                    })
                    .then(html => {
                        console.log('تم استلام بيانات المنتج بنجاح، حجم البيانات:', html.length);
                        
                        if (html.trim() === '') {
                            throw new Error('تم استلام بيانات فارغة');
                        }
                        
                        if (quickViewContent) {
                            quickViewContent.innerHTML = html;
                            console.log('تم تحديث محتوى المعاينة السريعة');
                            setupQuickViewElements();
                        }
                    })
                    .catch(error => {
                        console.error('خطأ في جلب بيانات المنتج:', error.message);
                        
                        if (quickViewContent) {
                            quickViewContent.innerHTML = `
                                <div class="bg-white p-6 rounded-xl shadow-lg">
                                    <div class="flex flex-col items-center text-center">
                                        <div class="text-red-500 mb-4 text-6xl">
                                            <i class="fas fa-exclamation-circle"></i>
                                        </div>
                                        <h3 class="text-xl font-bold mb-2">تعذر الوصول للمنتج</h3>
                                        <p class="text-gray-600 mb-4">عذراً، لم نتمكن من تحميل بيانات المنتج</p>
                                        <p class="text-gray-400 mb-2 text-sm">السبب: ${error.message}</p>
                                        <button class="close-quick-view bg-primary hover:bg-secondary text-white px-6 py-2 rounded-lg transition duration-300">إغلاق</button>
                                    </div>
                                </div>
                            `;
                            
                            const closeBtn = quickViewContent.querySelector('.close-quick-view');
                            if (closeBtn) {
                                closeBtn.addEventListener('click', closeQuickView);
                            }
                        }
                    });
                }
            });
        });
        
        // إضافة مستمع لإغلاق النافذة عند النقر خارجها
        if (quickViewModal) {
            quickViewModal.addEventListener('click', function(e) {
                if (e.target === this) {
                    closeQuickView();
                }
            });
        }
        
        // إضافة مستمع لإغلاق النافذة باستخدام زر ESC
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && quickViewModal && !quickViewModal.classList.contains('hidden')) {
                closeQuickView();
            }
        });
    } else {
        console.log("لم يتم العثور على عناصر المعاينة السريعة المطلوبة");
    }
    
    // وظيفة إغلاق نافذة المعاينة السريعة
    function closeQuickView() {
        if (quickViewModal) {
            quickViewModal.classList.add('hidden');
            document.body.classList.remove('overflow-hidden');
        }
    }
    
    // إعداد العناصر الداخلية للمعاينة السريعة
    function setupQuickViewElements() {
        console.log('إعداد عناصر المعاينة السريعة الداخلية');
        
        // زر الإغلاق
        const closeBtn = document.querySelector('.close-quick-view');
        if (closeBtn) {
            closeBtn.addEventListener('click', closeQuickView);
        }
        
        // الصور المصغرة
        const thumbnails = document.querySelectorAll('.quick-view-thumbnail');
        const mainImage = document.querySelector('.main-image img');
        
        if (thumbnails.length && mainImage) {
            console.log('تم العثور على الصور المصغرة والصورة الرئيسية');
            thumbnails.forEach(thumb => {
                thumb.addEventListener('click', function() {
                    // إزالة الفئات النشطة من جميع الصور المصغرة
                    thumbnails.forEach(t => t.classList.remove('border-primary', 'shadow-lg'));
                    // إضافة الفئات النشطة إلى الصورة المصغرة المحددة
                    this.classList.add('border-primary', 'shadow-lg');
                    
                    // تغيير الصورة الرئيسية
                    const imgSrc = this.getAttribute('data-image');
                    if (imgSrc) {
                        mainImage.classList.add('opacity-50');
                        setTimeout(() => {
                            mainImage.src = imgSrc;
                            mainImage.classList.remove('opacity-50');
                        }, 200);
                    }
                });
            });
        } else {
            console.log('لم يتم العثور على الصور المصغرة أو الصورة الرئيسية');
        }
        
        // أزرار اللون والمقاس والكمية
        // أزرار الألوان
        const colorOptions = document.querySelectorAll('.quick-view-color');
        colorOptions.forEach(option => {
            option.addEventListener('click', function() {
                colorOptions.forEach(o => o.classList.remove('ring-2', 'ring-offset-2', 'ring-primary'));
                this.classList.add('ring-2', 'ring-offset-2', 'ring-primary');
            });
        });
        
        // أزرار المقاسات
        const sizeOptions = document.querySelectorAll('.quick-view-size');
        sizeOptions.forEach(option => {
            option.addEventListener('click', function() {
                sizeOptions.forEach(o => {
                    o.classList.remove('bg-primary', 'text-white', 'border-primary', 'shadow-md');
                    o.classList.add('border-gray-300');
                });
                this.classList.add('bg-primary', 'text-white', 'border-primary', 'shadow-md');
                this.classList.remove('border-gray-300');
            });
        });
        
        // أزرار الكمية
        const decreaseBtn = document.getElementById('quick-view-decrease');
        const increaseBtn = document.getElementById('quick-view-increase');
        const quantityInput = document.getElementById('quick-view-quantity');
        
        if (decreaseBtn && increaseBtn && quantityInput) {
            decreaseBtn.addEventListener('click', function() {
                let value = parseInt(quantityInput.value);
                if (value > 1) {
                    quantityInput.value = value - 1;
                }
            });
            
            increaseBtn.addEventListener('click', function() {
                let value = parseInt(quantityInput.value);
                quantityInput.value = value + 1;
            });
        }
        
        // زر إضافة للسلة
        const addToCartBtn = document.getElementById('quick-view-add-to-cart');
        if (addToCartBtn) {
            addToCartBtn.addEventListener('click', function() {
                const productId = this.getAttribute('data-product');
                const quantity = quantityInput ? parseInt(quantityInput.value) || 1 : 1;
                
                if (!productId) return;
                
                // تحضير رابط إضافة للسلة
                const baseUrl = window.location.origin;
                const url = `${baseUrl}/add_to_cart/${productId}/`;
                console.log('إضافة المنتج للسلة:', url);
                
                // إضافة المنتج للسلة
                fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `product_id=${productId}&quantity=${quantity}`
                })
                .then(response => {
                    if (!response.ok) throw new Error('فشل إضافة المنتج للسلة');
                    return response.json();
                })
                .then(data => {
                    // تحديث عداد السلة
                    const cartCount = document.querySelectorAll('.cart-count');
                    if (cartCount && data.cart_count) {
                        cartCount.forEach(count => {
                            count.textContent = data.cart_count;
                        });
                    }
                    
                    // عرض رسالة نجاح
                    if (typeof window.showToast === 'function') {
                        window.showToast('تمت إضافة المنتج للسلة', 'success');
                    }
                    
                    // إغلاق نافذة المعاينة السريعة
                    closeQuickView();
                })
                .catch(error => {
                    console.error('خطأ في إضافة المنتج للسلة:', error);
                    
                    if (typeof window.showToast === 'function') {
                        window.showToast('فشل إضافة المنتج للسلة', 'error');
                    }
                });
            });
        }
        
        // زر المفضلة
        const wishlistBtn = document.querySelector('.quick-view-wishlist-btn');
        if (wishlistBtn) {
            wishlistBtn.addEventListener('click', function() {
                const productId = this.getAttribute('data-product');
                const icon = this.querySelector('i');
                
                if (!productId) return;
                
                // إضافة/إزالة من المفضلة
                const requestBody = { product_id: parseInt(productId) };
                console.log('إرسال طلب toggle-wishlist من quick-view:', requestBody);
                
                // عرض مؤشر تحميل على الزر
                this.classList.add('opacity-50');
                
                fetch('/toggle-wishlist/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify(requestBody),
                    credentials: 'same-origin'
                })
                .then(response => {
                    // إزالة مؤشر التحميل
                    this.classList.remove('opacity-50');
                    
                    console.log('استجابة السيرفر:', response.status, response.statusText);
                    
                    if (!response.ok) {
                        return response.text().then(text => {
                            console.log('نص الخطأ:', text);
                            throw new Error('فشل في تبديل المفضلة: ' + response.status);
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        // تحديث الأيقونة
                        if (data.is_in_wishlist) {
                            icon.classList.remove('far');
                            icon.classList.add('fas', 'text-red-500');
                            
                            // عرض رسالة نجاح
                            if (typeof window.showToast === 'function') {
                                window.showToast('تمت الإضافة للمفضلة', 'success');
                            }
                        } else {
                            icon.classList.remove('fas', 'text-red-500');
                            icon.classList.add('far');
                            
                            // عرض رسالة الإزالة
                            if (typeof window.showToast === 'function') {
                                window.showToast('تمت الإزالة من المفضلة', 'info');
                            }
                        }
                        
                        // تحديث عداد المفضلة
                        if (window.updateWishlistCounter && typeof window.updateWishlistCounter === 'function') {
                            window.updateWishlistCounter(data.wishlist_count);
                        } else {
                            // احتياطي في حالة عدم وجود الدالة المحسنة
                            const wishlistCount = document.querySelectorAll('.wishlist-count, #wishlist-count');
                            if (wishlistCount && data.wishlist_count !== undefined) {
                                wishlistCount.forEach(count => {
                                    count.textContent = data.wishlist_count;
                                });
                            }
                        }
                    }
                })
                .catch(error => {
                    console.error('خطأ في تحديث المفضلة:', error);
                    
                    if (typeof window.showToast === 'function') {
                        window.showToast('فشل تحديث المفضلة', 'error');
                    }
                });
            });
        }
    }
    
    // دالة مساعدة للحصول على قيمة الكوكيز
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
}); 