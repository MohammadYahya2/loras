from django.urls import path, re_path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'boutiqe'

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    re_path(r'^product/(?P<slug>[\w\d_\-\u0600-\u06FF]+)/$', views.product_detail, name='product_detail'),
    path('cart/', views.cart, name='cart'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart_by_id, name='add_to_cart_by_id'),
    path('remove_from_cart/<int:item_id>/', views.remove_from_cart_by_id, name='remove_from_cart_by_id'),
    path('update_cart_item/<int:item_id>/', views.update_cart_item_by_id, name='update_cart_item_by_id'),
    path('clear-cart/', views.clear_cart, name='clear_cart'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:wishlist_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/move-to-cart/<int:wishlist_id>/', views.move_to_cart, name='move_to_cart'),
    path('toggle-wishlist/', views.toggle_wishlist, name='toggle_wishlist'),
    path('get-cart-items/', views.get_cart_items, name='get_cart_items'),
    path('update-cart-item/', views.update_cart_item, name='update_cart_item'),
    path('remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    
    # Search routes
    path('search/', views.search, name='search'),
    path('search/ajax/', views.search_ajax, name='search_ajax'),
    path('cart/api/', views.cart_api, name='cart_api'),
    path('cart/update/', views.cart_update, name='cart_update'),
    path('cart/remove/', views.cart_remove, name='cart_remove'),
    
    path('checkout/', views.checkout, name='checkout'),
    path('place-order/', views.place_order, name='place_order'),
    path('contact/', views.contact, name='contact'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('orders/', views.orders_view, name='orders'),
    path('cancel-order/', views.cancel_order, name='cancel_order'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    
    # المسارات الجديدة
    path('quick-view/<int:product_id>/', views.quick_view, name='quick_view'),

    # مسارات لوحة تحكم الأدمن
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/products/', views.admin_products, name='admin_products'),
    path('admin/product/create/', views.admin_product_create, name='admin_product_create'),
    path('admin/product/edit/<int:product_id>/', views.admin_product_edit, name='admin_product_edit'),
    path('admin/product/delete/<int:product_id>/', views.admin_product_delete, name='admin_product_delete'),
    path('admin/categories/', views.admin_categories, name='admin_categories'),
    path('admin/users/', views.admin_users, name='admin_users'),
    
    # مسارات المجموعات الرائجة
    path('admin/trending-collections/', views.admin_trending_collections, name='admin_trending_collections'),
    path('admin/trending-collection/create/', views.admin_trending_collection_create, name='admin_trending_collection_create'),
    path('admin/trending-collection/edit/<int:collection_id>/', views.admin_trending_collection_edit, name='admin_trending_collection_edit'),
    path('admin/trending-collection/delete/<int:collection_id>/', views.admin_trending_collection_delete, name='admin_trending_collection_delete'),
    
    # مسارات الخصومات
    path('admin/discounts/', views.admin_discounts, name='admin_discounts'),
    path('admin/discounts/create/', views.admin_discount_create, name='admin_discount_create'),
    path('admin/discounts/<int:discount_id>/edit/', views.admin_discount_edit, name='admin_discount_edit'),
    path('admin/discounts/<int:discount_id>/delete/', views.admin_discount_delete, name='admin_discount_delete'),
    
    # Admin - Coupons
    path('admin/coupons/', views.admin_coupons, name='admin_coupons'),
    path('admin/coupons/create/', views.admin_coupon_create, name='admin_coupon_create'),
    path('admin/coupons/<int:coupon_id>/edit/', views.admin_coupon_edit, name='admin_coupon_edit'),
    path('admin/coupons/<int:coupon_id>/delete/', views.admin_coupon_delete, name='admin_coupon_delete'),
    path('admin/coupons/<int:coupon_id>/usage/', views.admin_coupon_usage, name='admin_coupon_usage'),
    
    # Coupon
    path('cart/apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('cart/remove-coupon/', views.remove_coupon, name='remove_coupon'),
    
    # Ratings
    path('product/<int:product_id>/submit-rating/', views.submit_rating, name='submit_rating'),

    # API endpoints
    path('api/cart-count/', views.cart_count, name='cart_count'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 