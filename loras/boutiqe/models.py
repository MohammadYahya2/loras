from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
import re
from django.db.models import Avg
from django.utils import timezone
from decimal import Decimal

# دالة مساعدة لترجمة الأحرف العربية إلى الإنجليزية في الـ slug
def arabic_slugify(str):
    str = str.replace(" ", "-")
    str = str.replace("ا", "a")
    str = str.replace("أ", "a")
    str = str.replace("إ", "e")
    str = str.replace("آ", "a")
    str = str.replace("ب", "b")
    str = str.replace("ت", "t")
    str = str.replace("ث", "th")
    str = str.replace("ج", "j")
    str = str.replace("ح", "h")
    str = str.replace("خ", "kh")
    str = str.replace("د", "d")
    str = str.replace("ذ", "th")
    str = str.replace("ر", "r")
    str = str.replace("ز", "z")
    str = str.replace("س", "s")
    str = str.replace("ش", "sh")
    str = str.replace("ص", "s")
    str = str.replace("ض", "d")
    str = str.replace("ط", "t")
    str = str.replace("ظ", "z")
    str = str.replace("ع", "a")
    str = str.replace("غ", "gh")
    str = str.replace("ف", "f")
    str = str.replace("ق", "q")
    str = str.replace("ك", "k")
    str = str.replace("ل", "l")
    str = str.replace("م", "m")
    str = str.replace("ن", "n")
    str = str.replace("ه", "h")
    str = str.replace("ة", "h")
    str = str.replace("و", "w")
    str = str.replace("ي", "y")
    str = str.replace("ى", "a")
    str = str.replace("ئ", "e")
    str = str.replace("ء", "a")
    
    # إزالة الرموز غير المرغوب فيها
    str = re.sub(r'[^\w\s-]', '', str)
    
    # تحويل إلى أحرف صغيرة وإزالة الشرطات المتكررة
    str = str.lower()
    while '--' in str:
        str = str.replace('--', '-')
    
    # إزالة الشرطات من البداية والنهاية
    str = str.strip('-')
    
    return str

class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name="اسم الفئة")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="الرابط المختصر")
    description = models.TextField(blank=True, null=True, verbose_name="وصف الفئة")
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name="صورة الفئة")
    is_active = models.BooleanField(default=True, verbose_name="فعالة")
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='children', verbose_name="الفئة الأم")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('boutiqe:product_list_by_category', args=[self.slug])
    
    class Meta:
        verbose_name = "فئة"
        verbose_name_plural = "الفئات"
        ordering = ['name']

class Color(models.Model):
    name = models.CharField(max_length=50, verbose_name="اسم اللون")
    code = models.CharField(max_length=10, verbose_name="كود اللون")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "لون"
        verbose_name_plural = "الألوان"

class Size(models.Model):
    name = models.CharField(max_length=20, verbose_name="المقاس")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "مقاس"
        verbose_name_plural = "المقاسات"

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="اسم المنتج")
    slug = models.SlugField(max_length=150, unique=True)
    description = models.TextField(verbose_name="وصف المنتج")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر")
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="سعر الخصم")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="الفئة")
    in_stock = models.BooleanField(default=True, verbose_name="متوفر")
    colors = models.ManyToManyField(Color, blank=True, verbose_name="الألوان المتاحة")
    sizes = models.ManyToManyField(Size, blank=True, verbose_name="المقاسات المتاحة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    is_featured = models.BooleanField(default=False, verbose_name="مميز")
    is_new = models.BooleanField(default=False, verbose_name="جديد")
    is_sale = models.BooleanField(default=False, verbose_name="عرض خاص")
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="رمز المنتج")
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name="الكمية المتوفرة")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = arabic_slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    def get_discount_percent(self):
        if self.discount_price:
            discount_amount = self.price - self.discount_price
            discount_percent = int((discount_amount / self.price) * 100)
            return discount_percent
        return 0
    
    def get_discount_amount(self):
        if self.discount_price:
            return self.price - self.discount_price
        return 0
    
    def get_main_image(self):
        main_image = self.images.filter(is_main=True).first()
        if not main_image:
            main_image = self.images.first()
        return main_image
    
    def get_average_rating(self):
        ratings = self.ratings.all()
        if not ratings:
            return 0
        return sum(rating.rating for rating in ratings) / ratings.count()
    
    def get_rating_count(self):
        return self.ratings.count()
    
    def get_absolute_url(self):
        return reverse('boutiqe:product_detail', args=[self.slug])
    
    class Meta:
        verbose_name = "منتج"
        verbose_name_plural = "المنتجات"
        ordering = ['-created_at']

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name="المنتج")
    image = models.ImageField(upload_to='products/', verbose_name="صورة المنتج")
    is_main = models.BooleanField(default=False, verbose_name="صورة رئيسية")
    
    def __str__(self):
        return f"صورة للمنتج {self.product.name}"
    
    class Meta:
        verbose_name = "صورة المنتج"
        verbose_name_plural = "صور المنتجات"

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="المستخدم")
    session_key = models.CharField(max_length=40, null=True, blank=True, verbose_name="مفتاح الجلسة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    def __str__(self):
        if self.user:
            return f"عربة {self.user.username}"
        return f"عربة زائر ({self.session_key})"
    
    class Meta:
        verbose_name = "عربة تسوق"
        verbose_name_plural = "عربات التسوق"
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(user__isnull=False),
                name='unique_user_cart'
            ),
            models.UniqueConstraint(
                fields=['session_key'],
                condition=models.Q(session_key__isnull=False),
                name='unique_session_cart'
            ),
            models.CheckConstraint(
                check=(
                    models.Q(user__isnull=False, session_key__isnull=True) |
                    models.Q(user__isnull=True, session_key__isnull=False)
                ),
                name='user_xor_session_cart'
            )
        ]

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name="عربة التسوق")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="المستخدم")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="المنتج")
    quantity = models.PositiveIntegerField(default=1, verbose_name="الكمية")
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="اللون")
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="المقاس")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    
    def get_total(self):
        if self.product.discount_price:
            return self.product.discount_price * self.quantity
        return self.product.price * self.quantity
    
    def __str__(self):
        return f"{self.quantity} من {self.product.name}"
    
    class Meta:
        verbose_name = "عنصر السلة"
        verbose_name_plural = "عناصر السلة"

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="المستخدم")
    session_key = models.CharField(max_length=40, null=True, blank=True, verbose_name="مفتاح الجلسة")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="المنتج")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    
    def __str__(self):
        if self.user:
            return f"{self.product.name} - قائمة مفضلة {self.user.username}"
        return f"{self.product.name} - قائمة مفضلة زائر"
    
    class Meta:
        verbose_name = "قائمة المفضلة"
        verbose_name_plural = "قوائم المفضلة"
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'product'],
                condition=models.Q(user__isnull=False),
                name='unique_user_product_wishlist'
            ),
            models.UniqueConstraint(
                fields=['session_key', 'product'],
                condition=models.Q(session_key__isnull=False),
                name='unique_session_product_wishlist'
            ),
            models.CheckConstraint(
                check=(
                    models.Q(user__isnull=False, session_key__isnull=True) |
                    models.Q(user__isnull=True, session_key__isnull=False)
                ),
                name='user_xor_session_wishlist'
            )
        ]

class Contact(models.Model):
    name = models.CharField(max_length=100, verbose_name="الاسم")
    email = models.EmailField(verbose_name="البريد الإلكتروني")
    subject = models.CharField(max_length=200, verbose_name="الموضوع", null=True, blank=True)
    message = models.TextField(verbose_name="الرسالة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإرسال")
    
    def __str__(self):
        return f"{self.subject} - {self.name}"
    
    class Meta:
        verbose_name = "نموذج تواصل"
        verbose_name_plural = "نماذج التواصل"
        ordering = ['-created_at']

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default="المملكة العربية السعودية")
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except User.profile.RelatedObjectDoesNotExist:
        # Create profile if it doesn't exist
        Profile.objects.create(user=instance)

class ProductVariation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variations', verbose_name="المنتج")
    color = models.ForeignKey(Color, on_delete=models.CASCADE, verbose_name="اللون")
    size = models.ForeignKey(Size, on_delete=models.CASCADE, verbose_name="المقاس")
    stock_count = models.PositiveIntegerField(default=0, verbose_name="الكمية المتوفرة")
    
    class Meta:
        verbose_name = "تنوع المنتج"
        verbose_name_plural = "تنوعات المنتج"
        unique_together = ('product', 'color', 'size')
    
    def __str__(self):
        return f"{self.product.name} - {self.color.name} - {self.size.name}"

class ProductRating(models.Model):
    RATING_CHOICES = (
        (1, '1 نجمة'),
        (2, '2 نجوم'),
        (3, '3 نجوم'),
        (4, '4 نجوم'),
        (5, '5 نجوم'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="المستخدم")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ratings', verbose_name="المنتج")
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, verbose_name="التقييم")
    comment = models.TextField(blank=True, null=True, verbose_name="التعليق")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ التقييم")
    
    class Meta:
        verbose_name = "تقييم المنتج"
        verbose_name_plural = "تقييمات المنتجات"
        unique_together = ('user', 'product')
    
    def __str__(self):
        return f"{self.product.name} - {self.user.username} - {self.rating} نجوم"

class TrendingCollection(models.Model):
    name = models.CharField(max_length=100, verbose_name="اسم المجموعة")
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(verbose_name="وصف المجموعة")
    image = models.ImageField(upload_to='collections/', verbose_name="صورة المجموعة")
    products = models.ManyToManyField(Product, related_name='collections', verbose_name="المنتجات")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    order_position = models.PositiveIntegerField(default=0, verbose_name="ترتيب العرض")
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = arabic_slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "مجموعة رائجة"
        verbose_name_plural = "المجموعات الرائجة"
        ordering = ['order_position', '-created_at']

class Discount(models.Model):
    """نموذج الخصومات"""
    name = models.CharField(max_length=100, verbose_name="اسم الخصم")
    description = models.TextField(blank=True, null=True, verbose_name="وصف الخصم")
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="نسبة الخصم (%)")
    start_date = models.DateTimeField(verbose_name="تاريخ البدء")
    end_date = models.DateTimeField(verbose_name="تاريخ الانتهاء")
    categories = models.ManyToManyField(Category, blank=True, verbose_name="الفئات المشمولة")
    products = models.ManyToManyField(Product, blank=True, verbose_name="المنتجات المشمولة")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    order_position = models.PositiveIntegerField(default=0, verbose_name="ترتيب العرض")
    image = models.ImageField(upload_to='discounts/', blank=True, null=True, verbose_name="صورة الخصم")
    
    class Meta:
        verbose_name = "خصم"
        verbose_name_plural = "الخصومات"
        ordering = ['order_position', '-created_at']
    
    def __str__(self):
        return self.name
    
class Coupon(models.Model):
    """نموذج كوبونات الخصم"""
    code = models.CharField(max_length=50, unique=True, verbose_name="كود الكوبون")
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="قيمة الخصم")
    discount_type = models.CharField(
        max_length=20,
        choices=[
            ('fixed', 'مبلغ ثابت'),
            ('percentage', 'نسبة مئوية')
        ],
        default='fixed',
        verbose_name="نوع الخصم"
    )
    minimum_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="الحد الأدنى للطلب")
    valid_from = models.DateTimeField(verbose_name="صالح من تاريخ")
    valid_to = models.DateTimeField(verbose_name="صالح حتى تاريخ")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    max_uses = models.PositiveIntegerField(default=1, verbose_name="أقصى عدد استخدامات")
    current_uses = models.PositiveIntegerField(default=0, verbose_name="عدد الاستخدامات الحالي")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    
    class Meta:
        verbose_name = "كوبون خصم"
        verbose_name_plural = "كوبونات الخصم"
    
    def __str__(self):
        if self.discount_type == 'fixed':
            return f"{self.code} ({self.discount_value} شيكل)"
        else:
            return f"{self.code} ({self.discount_value}%)"
    
    @property
    def is_valid(self):
        """التحقق مما إذا كان الكوبون صالحًا للاستخدام"""
        now = timezone.now()
        is_active = self.is_active
        in_valid_period = self.valid_from <= now <= self.valid_to
        not_maxed_out = self.current_uses < self.max_uses
        return is_active and in_valid_period and not_maxed_out
    
    def calculate_discount(self, order_total):
        """حساب قيمة الخصم بناءً على قيمة الطلب"""
        if not self.is_valid or order_total < self.minimum_order_value:
            return Decimal('0.00')
        
        if self.discount_type == 'fixed':
            return min(self.discount_value, order_total)  # لتجنب خصم أكبر من قيمة الطلب
        else:  # percentage
            percentage_discount = self.discount_value / Decimal('100')
            return round(order_total * percentage_discount, 2)

class CouponUsage(models.Model):
    """نموذج استخدام الكوبون"""
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, verbose_name="الكوبون")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="المستخدم")
    used_at = models.DateTimeField(auto_now_add=True, verbose_name="وقت الاستخدام")
    order_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="قيمة الطلب")
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="قيمة الخصم")
    
    class Meta:
        verbose_name = "استخدام كوبون"
        verbose_name_plural = "استخدامات الكوبونات"
        unique_together = ('coupon', 'user')  # يمكن للمستخدم استخدام الكوبون مرة واحدة فقط
    
    def __str__(self):
        return f"{self.user.username} - {self.coupon.code}"

# نسخة مؤقتة من Order لتجنب خطأ قاعدة البيانات
class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'بانتظار الدفع'),
        ('processing', 'قيد التحضير'),
        ('shipped', 'تم الشحن'),
        ('delivered', 'تم التوصيل'),
        ('cancelled', 'ملغي'),
    )
    
    CURRENCY_CHOICES = (
        ('SAR', 'ريال سعودي'),
        ('ILS', 'شيكل'),
    )
    
    # نموذج مبسط لتجنب خطأ قاعدة البيانات
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', null=True, blank=True, verbose_name="المستخدم")
    contact_info = models.ForeignKey('ContactInfo', on_delete=models.PROTECT, null=True, blank=True, related_name='orders', verbose_name="معلومات الاتصال")
    order_id = models.CharField(max_length=50, unique=True, verbose_name="رقم الطلب")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="حالة الطلب")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الطلب")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الدفع")
    session_key = models.CharField(max_length=40, null=True, blank=True, verbose_name="مفتاح الجلسة")
    
    # Guest fields
    email = models.EmailField(null=True, blank=True, verbose_name="البريد الإلكتروني")
    shipping_address = models.TextField(null=True, blank=True, verbose_name="عنوان الشحن")
    phone_number = models.CharField(max_length=20, null=True, blank=True, verbose_name="رقم الهاتف")
    
    def __str__(self):
        if self.user:
            return f"طلب #{self.order_id} ({self.user.username})"
        return f"طلب #{self.order_id} (زائر)"
    
    class Meta:
        verbose_name = "طلب"
        verbose_name_plural = "الطلبات"
        ordering = ['-created_at']

# نموذج طلبات إلغاء الطلب
class OrderCancellation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cancellation_requests', verbose_name="المستخدم", null=True, blank=True)
    order_id = models.CharField(max_length=50, verbose_name="رقم الطلب")
    reason = models.TextField(verbose_name="سبب الإلغاء")
    phone = models.CharField(max_length=20, verbose_name="رقم هاتف للتواصل")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الطلب")
    is_approved = models.BooleanField(default=False, verbose_name="تمت الموافقة")
    
    def __str__(self):
        return f"طلب إلغاء #{self.order_id} - {self.user.username if self.user else 'زائر'}"
    
    class Meta:
        verbose_name = "طلب إلغاء"
        verbose_name_plural = "طلبات الإلغاء"
        ordering = ['-created_at']

# نسخة مؤقتة من OrderItem لتجنب خطأ قاعدة البيانات
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="الطلب")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="المنتج")
    quantity = models.PositiveIntegerField(default=1, verbose_name="الكمية")
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="اللون")
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="المقاس")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="سعر الوحدة")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاريخ الإضافة")
    
    def __str__(self):
        return f"{self.quantity} من {self.product.name} في الطلب {self.order.order_id}"
    
    def get_total(self):
        if self.unit_price:
            return self.unit_price * self.quantity
        elif self.product.discount_price:
            return self.product.discount_price * self.quantity
        return self.product.price * self.quantity
    
    class Meta:
        verbose_name = "عنصر الطلب"
        verbose_name_plural = "عناصر الطلب"

# --- Guest checkout upgrade 2025/05/13 ---

class ContactInfo(models.Model):
    """
    نموذج لمعلومات الاتصال والشحن للعملاء الضيوف أو المسجلين
    يستخدم للحفاظ على معلومات العملاء الضيوف لعمليات الشراء المستقبلية
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='contacts', verbose_name="المستخدم")
    session_key = models.CharField(max_length=40, null=True, blank=True, verbose_name="مفتاح الجلسة")
    name = models.CharField(max_length=100, verbose_name="الاسم")
    phone = models.CharField(max_length=20, verbose_name="رقم الهاتف")
    address = models.TextField(verbose_name="العنوان")
    city = models.CharField(max_length=100, verbose_name="المدينة", null=True, blank=True)
    note = models.TextField(blank=True, null=True, verbose_name="ملاحظة")
    is_default = models.BooleanField(default=True, verbose_name="افتراضي")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    
    def __str__(self):
        return f"{self.name} ({self.phone})"
    
    class Meta:
        verbose_name = "معلومات الاتصال"
        verbose_name_plural = "معلومات الاتصال"
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'phone'],
                condition=models.Q(user__isnull=False),
                name='unique_user_phone_contact'
            ),
            models.UniqueConstraint(
                fields=['session_key', 'phone'],
                condition=models.Q(session_key__isnull=False),
                name='unique_session_phone_contact'
            ),
            models.CheckConstraint(
                check=(
                    models.Q(user__isnull=False, session_key__isnull=True) |
                    models.Q(user__isnull=True, session_key__isnull=False)
                ),
                name='user_xor_session_contact'
            )
        ]
