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