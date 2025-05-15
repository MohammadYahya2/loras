from django.contrib import admin
from .models import (
    Category, Color, Size, Product, ProductImage, CartItem, Wishlist, Contact, TrendingCollection, Discount, ProductVariation, Profile, ProductRating,
    Coupon, CouponUsage, Cart, Order, OrderItem, OrderCancellation, ContactInfo
)
# OrderCancellation is not imported to avoid database errors

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3

class ProductVariationInline(admin.TabularInline):
    model = ProductVariation
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'in_stock', 'is_featured', 'is_new')
    list_filter = ('category', 'in_stock', 'is_featured', 'is_new')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVariationInline]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_key', 'created_at', 'updated_at', 'items_count')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'session_key')
    
    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'عدد العناصر'

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'user_display', 'product', 'quantity', 'color', 'size', 'added_at')
    list_filter = ('added_at', 'cart__user')
    search_fields = ('product__name', 'cart__user__username', 'cart__session_key')
    
    def user_display(self, obj):
        if obj.cart.user:
            return obj.cart.user.username
        return f"زائر ({obj.cart.session_key[:10]}...)"
    user_display.short_description = 'المستخدم'

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user_display', 'product', 'added_at')
    list_filter = ('user', 'added_at')
    search_fields = ('product__name', 'user__username', 'session_key')
    
    def user_display(self, obj):
        if obj.user:
            return obj.user.username
        return f"زائر ({obj.session_key[:10]}...)"
    user_display.short_description = 'المستخدم'

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'email', 'message')

@admin.register(TrendingCollection)
class TrendingCollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'order_position', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    list_editable = ('order_position', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('products',)

@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('name', 'discount_percent', 'order_position', 'is_active', 'start_date', 'end_date')
    list_filter = ('is_active', 'start_date', 'end_date')
    list_editable = ('order_position', 'is_active')
    search_fields = ('name', 'description')
    filter_horizontal = ('products', 'categories')

@admin.register(ProductVariation)
class ProductVariationAdmin(admin.ModelAdmin):
    list_display = ('product', 'color', 'size', 'stock_count')
    list_filter = ('product', 'color', 'size')
    search_fields = ('product__name',)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'city', 'country')
    search_fields = ('user__username', 'user__email', 'phone', 'city', 'country')

@admin.register(ProductRating)
class ProductRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'product__name')

# إعادة تسجيل الكوبونات بطريقة بسيطة
admin.site.register(Coupon)
admin.site.register(CouponUsage)

# Add OrderCancellation registration
@admin.register(OrderCancellation)
class OrderCancellationAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user', 'created_at', 'is_approved']
    list_filter = ['is_approved', 'created_at']
    search_fields = ['order_id', 'user__username', 'reason', 'phone']
    readonly_fields = ['created_at']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'color', 'size', 'unit_price']
    fields = ['product', 'quantity', 'color', 'size', 'unit_price']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'get_customer_name', 'status', 'created_at', 'get_total']
    list_filter = ['status', 'created_at']
    search_fields = ['order_id', 'contact_info__name', 'contact_info__phone']
    readonly_fields = ['order_id', 'created_at', 'paid_at', 'session_key']
    inlines = [OrderItemInline]
    
    def get_customer_name(self, obj):
        if obj.user:
            return obj.user.username
        elif obj.contact_info:
            return f"{obj.contact_info.name} (ضيف)"
        return "ضيف"
    get_customer_name.short_description = "العميل"
    
    def get_total(self, obj):
        return sum(item.get_total() for item in obj.items.all())
    get_total.short_description = "الإجمالي"

@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'user_display', 'is_default', 'created_at']
    list_filter = ['is_default', 'created_at']
    search_fields = ['name', 'phone', 'user__username']
    
    def user_display(self, obj):
        if obj.user:
            return obj.user.username
        return "ضيف"
    user_display.short_description = "المستخدم"
