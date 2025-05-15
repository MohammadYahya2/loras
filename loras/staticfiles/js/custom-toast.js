/**
 * إشعارات مخصصة بحجم أصغر ومظهر أكثر أناقة
 * خاص بإشعارات المفضلة والإشعارات الأخرى
 */

// دالة إظهار الإشعار المخصص - متوافقة مع showToast
function showCustomToast(message, type = 'success', duration = 3000) {
    // إزالة جميع الإشعارات الموجودة
    const allToasts = document.querySelectorAll('.toast, .toast-notification, .notification-popup, .notification-toast');
    allToasts.forEach(toast => {
        // حذف الإشعار مباشرة
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    });
    
    // إنشاء عنصر الإشعار
    const toast = document.createElement('div');
    toast.className = `notification-toast ${type}`;
    
    // جعل الرسالة مختصرة
    let shortMessage = message;
    if (message.includes('تمت إضافة المنتج إلى المفضلة')) {
        shortMessage = 'تمت الإضافة للمفضلة';
    } else if (message.includes('إزالة المنتج من المفضلة')) {
        shortMessage = 'تمت الإزالة من المفضلة';
    } else if (message.includes('حدث خطأ أثناء')) {
        shortMessage = 'حدث خطأ';
    }
    
    // الأيقونات حسب نوع الإشعار
    const icons = {
        'success': 'fa-check',
        'error': 'fa-times',
        'warning': 'fa-exclamation',
        'info': 'fa-info'
    };
    
    // إضافة محتوى الإشعار
    toast.innerHTML = `
        <div class="icon">
            <i class="fas ${icons[type] || icons.info}"></i>
        </div>
        <div class="message">${shortMessage}</div>
        <button class="close">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // إضافة الإشعار للصفحة
    document.body.appendChild(toast);
    
    // إظهار الإشعار بتأثير انتقالي
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    // إضافة حدث النقر لزر الإغلاق
    toast.querySelector('.close').addEventListener('click', function() {
        toast.classList.add('hide');
        setTimeout(() => toast.remove(), 300);
    });
    
    // إخفاء الإشعار تلقائيًا بعد المدة المحددة
    setTimeout(() => {
        if (document.body.contains(toast)) {
            toast.classList.add('hide');
            setTimeout(() => toast.remove(), 300);
        }
    }, duration);
}

// دالة تحديث عدادات المفضلة
function updateAllWishlistCounters(count) {
    // تحديث جميع العناصر التي تحتوي على id="wishlist-count" أو class="wishlist-count"
    const wishlistCounters = document.querySelectorAll('#wishlist-count, .wishlist-count');
    
    wishlistCounters.forEach(counter => {
        counter.textContent = count;
        // إضافة تأثير لجذب الانتباه
        counter.classList.add('scale-125', 'text-white', 'bg-secondary');
        setTimeout(() => {
            counter.classList.remove('scale-125', 'text-white', 'bg-secondary');
        }, 300);
    });
}

// دالة تحديث عدادات سلة التسوق
function updateAllCartCounters(count) {
    // تحديث جميع العناصر التي تحتوي على class="cart-count"
    const cartCounters = document.querySelectorAll('.cart-count');
    
    cartCounters.forEach(counter => {
        counter.textContent = count;
        // إضافة تأثير لجذب الانتباه
        counter.classList.add('scale-125', 'text-white', 'bg-secondary');
        setTimeout(() => {
            counter.classList.remove('scale-125', 'text-white', 'bg-secondary');
        }, 300);
    });
}

// تعريف الدالة الرئيسية في النافذة إذا لم تكن موجودة
document.addEventListener('DOMContentLoaded', function() {
    // التأكد من أن الدالة الرئيسية موجودة وتعمل بشكل صحيح
    if (typeof window.showToast !== 'function') {
        console.log("Toast function not overridden properly");
        window.showToast = showCustomToast;
    } else {
        // احتفظ بالدالة الأصلية
        const originalShowToast = window.showToast;
        
        // إعادة تعريف الدالة مع التوافق مع الدالة الأصلية
        window.showToast = function(message, type = 'success') {
            showCustomToast(message, type);
        };
    }
    
    // إضافة دالة تحديث عدادات المفضلة للنافذة
    window.updateWishlistCounter = updateAllWishlistCounters;
    
    // إضافة دالة تحديث عدادات سلة التسوق للنافذة
    window.updateCartCounter = updateAllCartCounters;
    
    // استبدال وظيفة إشعارات المفضلة الأصلية
    // منع ازدواجية المستمعين بإزالة المستمعين القديمة أولاً
    document.querySelectorAll('.wishlist-toggle-btn').forEach(button => {
        const oldClickEvent = button.onclick;
        if (oldClickEvent) {
            button.removeEventListener('click', oldClickEvent);
        }
        
        // إزالة جميع مستمعي الأحداث
        const newButton = button.cloneNode(true);
        button.parentNode.replaceChild(newButton, button);
    });
    
    // إضافة المستمعين الجدد
    document.querySelectorAll('.wishlist-toggle-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            // منع السلوك الافتراضي للنقرة
            e.preventDefault();
            e.stopPropagation();
            
            // الحصول على معرف المنتج
            const productId = this.getAttribute('data-product');
            if (!productId) return;
            
            // تأثير بصري عند النقر
            this.classList.add('scale-95');
            setTimeout(() => {
                this.classList.remove('scale-95');
            }, 100);
            
            // تعطيل الزر مؤقتًا لمنع النقرات المتكررة
            this.disabled = true;
            
            // إرسال طلب لإضافة/إزالة المنتج من المفضلة
            const requestBody = { product_id: parseInt(productId) };
            console.log('إرسال طلب toggle-wishlist:', requestBody);
            
            // عرض مؤشر تحميل على الزر
            this.classList.add('opacity-50');
            const icon = this.querySelector('i');
            
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
                    if (data.status === 'added') {
                        // تغيير الأيقونة للقلب الممتلئ باللون الأحمر
                        icon.classList.remove('far');
                        icon.classList.add('fas', 'text-red-500');
                        
                        // إضافة تأثير نبض للقلب
                        icon.classList.add('scale-125');
                        setTimeout(() => {
                            icon.classList.remove('scale-125');
                        }, 300);
                        
                        // إظهار إشعار النجاح
                        window.showToast('تمت الإضافة للمفضلة', 'success');
                    } else {
                        // تغيير الأيقونة للقلب الفارغ
                        icon.classList.remove('fas', 'text-red-500');
                        icon.classList.add('far');
                        
                        // إظهار إشعار الإزالة
                        window.showToast('تمت الإزالة من المفضلة', 'info');
                    }
                    
                    // استخدام الدالة المحسنة لتحديث جميع عدادات المفضلة
                    updateAllWishlistCounters(data.wishlist_count);
                }
                
                // إعادة تفعيل الزر بعد الانتهاء
                setTimeout(() => {
                    this.disabled = false;
                }, 500);
            })
            .catch(error => {
                console.error('خطأ في تبديل المفضلة:', error);
                window.showToast('حدث خطأ أثناء تحديث المفضلة', 'error');
                
                // إعادة تفعيل الزر في حالة الخطأ
                this.disabled = false;
            });
        });
    });
});

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