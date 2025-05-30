from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from .models import Category, Product, ProductImage, CartItem, Wishlist, Color, Size, Contact, Profile, ProductVariation, TrendingCollection, Discount, ProductRating, OrderCancellation, Coupon, CouponUsage, Order, OrderItem, Cart, ContactInfo
from .utils.cart import get_or_create_cart, get_cart_or_error, save_contact_info
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django import forms
import logging
from django.views.decorators.http import require_POST, require_GET
from django.contrib.admin.views.decorators import staff_member_required
import json
from django.db.models import Count, Sum, Q, Min, Max
from django.db.models.functions import Coalesce
from .forms import ProductForm, CategoryForm, ProductImageFormSet, ProductVariationFormSet, TrendingCollectionForm, DiscountForm, CouponForm
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from django.utils.text import slugify
import uuid
from django.db.utils import OperationalError
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import FileResponse, Http404
import os
from django.conf import settings
from django.utils import timezone

# إعداد logger خاص بالتطبيق
logger = logging.getLogger(__name__)

# إضافة context processor لجلب الفئات في جميع الصفحات
def categories_processor(request):
    try:
        categories = Category.objects.all()
        return {'categories': categories}
    except:
        return {'categories': []}

def home(request):
    # عرض جميع الفئات بدون تصفية
    categories = Category.objects.all()[:6]
    featured_products = Product.objects.filter(is_featured=True, in_stock=True)[:8]
    new_arrivals = Product.objects.filter(is_new=True, in_stock=True).order_by('-created_at')[:8]
    
    # إضافة المجموعات الرائجة
    trending_collections = TrendingCollection.objects.filter(is_active=True).order_by('order_position', '-created_at')[:3]
    
    # إضافة الخصومات النشطة
    active_discounts = Discount.objects.filter(
        is_active=True,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).order_by('order_position', '-created_at')[:4]
    
    wishlist_products = []
    if request.user.is_authenticated:
        wishlist_products = [item.product for item in Wishlist.objects.filter(user=request.user)]
    
    context = {
        'categories': categories,
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'trending_collections': trending_collections,
        'active_discounts': active_discounts,
        'wishlist_products': wishlist_products,
    }
    return render(request, 'boutiqe/home.html', context)

def product_list(request, category_slug=None):
    category = None
    collection = None
    categories = Category.objects.all()
    products = Product.objects.filter(in_stock=True)
    
    # Apply category filter if provided
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    # Apply trending collection filter if provided
    collection_slug = request.GET.get('collection')
    if collection_slug:
        collection = get_object_or_404(TrendingCollection, slug=collection_slug, is_active=True)
        products = products.filter(collections=collection)
    
    # Apply price range filter if provided
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    if min_price:
        try:
            min_price = float(min_price)
            # For products with discount_price, filter on the actual price shown to customer
            products = products.filter(
                Q(discount_price__gte=min_price) | 
                Q(discount_price__isnull=True, price__gte=min_price)
            )
        except (ValueError, TypeError):
            pass  # Invalid min_price parameter, ignore
    
    if max_price:
        try:
            max_price = float(max_price)
            # For products with discount_price, filter on the actual price shown to customer
            products = products.filter(
                Q(discount_price__lte=max_price, discount_price__isnull=False) | 
                Q(price__lte=max_price)
            )
        except (ValueError, TypeError):
            pass  # Invalid max_price parameter, ignore
    
    # Apply sorting if provided
    sort = request.GET.get('sort')
    if sort:
        if sort == 'price_low':
            # Sort by actual displayed price (discount_price if available, otherwise price)
            products = products.annotate(
                display_price=Coalesce('discount_price', 'price')
            ).order_by('display_price')
        elif sort == 'price_high':
            # Sort by actual displayed price in descending order
            products = products.annotate(
                display_price=Coalesce('discount_price', 'price')
            ).order_by('-display_price')
        elif sort == 'newest':
            products = products.order_by('-created_at')
    
    # Get min and max prices for range slider
    price_range = products.aggregate(
        min_price=Min('price'),
        max_price=Max('price')
    )
    
    min_product_price = price_range['min_price'] if price_range['min_price'] is not None else 0
    max_product_price = price_range['max_price'] if price_range['max_price'] is not None else 1000
    
    # Round to nearest 10s for cleaner UI
    min_product_price = int(max(0, min_product_price - (min_product_price % 10)))
    max_product_price = int(max_product_price + (10 - (max_product_price % 10)) if max_product_price % 10 else max_product_price)
    
    context = {
        'category': category,
        'collection': collection,
        'categories': categories,
        'products': products,
        'min_product_price': min_product_price,
        'max_product_price': max_product_price,
        'current_min_price': int(min_price) if min_price else min_product_price,
        'current_max_price': int(max_price) if max_price else max_product_price,
        'current_sort': sort or 'default',
    }
    return render(request, 'boutiqe/product_list.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, in_stock=True)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    is_in_wishlist = False
    
    if request.user.is_authenticated:
        is_in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
    
    # Get product ratings with newest first
    product_ratings = product.ratings.all().order_by('-created_at')
    
    context = {
        'product': product,
        'related_products': related_products,
        'is_in_wishlist': is_in_wishlist,
        'product_ratings': product_ratings,
    }
    return render(request, 'boutiqe/product_detail.html', context)

def cart(request):
    # Get cart for the current user or session
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()
    
    # سعر الصرف الحالي للشيكل (1 ريال = 0.94 شيكل)
    shekel_exchange_rate = Decimal('0.94')
    
    # Calculate total
    total = sum(item.get_total() for item in cart_items)
    # حساب المجموع بالشيكل
    total_ils = round(total * shekel_exchange_rate, 2)
    
    # إضافة السعر بالشيكل لكل منتج
    for item in cart_items:
        # حساب السعر الإفرادي بالشيكل
        if item.product.discount_price:
            item.price_ils = round(item.product.discount_price * shekel_exchange_rate, 2)
        else:
            item.price_ils = round(item.product.price * shekel_exchange_rate, 2)
        
        # حساب الإجمالي بالشيكل
        item.total_price_ils = round(item.get_total() * shekel_exchange_rate, 2)
    
    # استرجاع معلومات الكوبون من الجلسة إذا كان موجودًا
    coupon_code = request.session.get('coupon_code', None)
    coupon_discount = request.session.get('coupon_discount', 0)
    coupon_discount_ils = round(Decimal(coupon_discount) * shekel_exchange_rate, 2)
    
    # حساب المجموع النهائي بعد الخصم
    final_total = total - Decimal(coupon_discount)
    if final_total < 0:
        final_total = Decimal('0.00')
    final_total_ils = round(final_total * shekel_exchange_rate, 2)
    
    context = {
        'cart_items': cart_items,
        'total': total,
        'total_ils': total_ils,
        'shekel_exchange_rate': shekel_exchange_rate,
        'coupon_code': coupon_code,
        'coupon_discount': coupon_discount,
        'coupon_discount_ils': coupon_discount_ils,
        'final_total': final_total,
        'final_total_ils': final_total_ils,
    }
    
    return render(request, 'boutiqe/cart.html', context)

def get_cart_items(request):
    # Get cart for the current user or session
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()
    
    # Prepare data for JSON response
    items_data = []
    total = 0
    
    for item in cart_items:
        # Get the first image or a placeholder
        image_url = None
        if item.product.images.exists():
            for image in item.product.images.all():
                if image.is_main:
                    image_url = image.image.url
                    break
            
            if not image_url and item.product.images.first():
                image_url = item.product.images.first().image.url
        
        # Calculate subtotal for this item
        subtotal = item.get_total()
        total += subtotal
        
        items_data.append({
            'id': item.id,
            'name': item.product.name,
            'price': item.product.price,
            'quantity': item.quantity,
            'image': image_url,
            'subtotal': subtotal,
        })
    
    # Return JSON response
    return JsonResponse({
        'items': items_data,
        'total': total,
        'count': len(items_data),
    })

def add_to_cart(request):
    # Handle both GET and POST requests
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            quantity = int(data.get('quantity', 1))
            color_id = data.get('color_id')
            size_id = data.get('size_id')
        except:
            # For form submissions
            product_id = request.POST.get('product_id')
            quantity = int(request.POST.get('quantity', 1))
            color_id = request.POST.get('color_id')
            size_id = request.POST.get('size_id')
            
        if product_id:
            product = get_object_or_404(Product, id=product_id)
            
            # Get color and size if specified
            color = None
            size = None
            if color_id:
                color = get_object_or_404(Color, id=color_id)
            if size_id:
                size = get_object_or_404(Size, id=size_id)
            
            # Get or create cart for current user/session
            cart = get_or_create_cart(request)
            
            # Check cart limit (30 items total)
            total_quantity = get_cart_items_total_quantity(request)
            remaining_capacity = 30 - total_quantity
            
            # If quantity would exceed limit, adjust it
            if quantity > remaining_capacity:
                quantity = max(0, remaining_capacity)
                # If no capacity left, return error
                if quantity <= 0:
                    message = 'عذراً، لا يمكن إضافة المزيد من المنتجات. الحد الأقصى هو 30 قطعة.'
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Content-Type', ''):
                        return JsonResponse({
                            'success': False,
                            'message': message,
                            'cart_count': total_quantity,
                        })
                    messages.error(request, message)
                    return redirect('boutiqe:cart')
            
            # Check if product already in cart
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                color=color,
                size=size,
                defaults={'quantity': quantity}
            )
            
            # If not created, increment quantity within limits
            if not created:
                # Calculate how much we can add without exceeding limit
                max_to_add = 30 - (total_quantity - cart_item.quantity)
                add_quantity = min(quantity, max_to_add)
                
                if add_quantity > 0:
                    cart_item.quantity += add_quantity
                    cart_item.save()
                else:
                    message = 'عذراً، لا يمكن إضافة المزيد من المنتجات. الحد الأقصى هو 30 قطعة.'
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Content-Type', ''):
                        return JsonResponse({
                            'success': False,
                            'message': message,
                            'cart_count': total_quantity,
                        })
                    messages.error(request, message)
                    return redirect('boutiqe:cart')
            
            # Get new total count for response
            new_count = get_cart_items_total_quantity(request)
            
            # If AJAX request, return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Content-Type', ''):
                return JsonResponse({
                    'success': True,
                    'message': 'تمت إضافة المنتج إلى سلة التسوق',
                    'cart_count': new_count,
                })
            
            # Else redirect to cart page
            messages.success(request, 'تمت إضافة المنتج إلى سلة التسوق')
            return redirect('boutiqe:cart')
    
    # Default response for non-POST requests
    return render(request, 'boutiqe/cart.html')

@require_POST
def remove_from_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            
            if item_id:
                # Get cart for current user or session
                cart = get_or_create_cart(request)
                
                # Ensure the item belongs to the current cart
                try:
                    cart_item = CartItem.objects.get(id=item_id, cart=cart)
                    cart_item.delete()
                    
                    # Get updated count
                    cart_count = cart.items.count()
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'تمت إزالة المنتج من السلة',
                        'count': cart_count,
                    })
                except CartItem.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'المنتج غير موجود في السلة',
                    }, status=404)
        except json.JSONDecodeError:
            pass
            
    return JsonResponse({
        'success': False,
        'message': 'طلب غير صالح',
    }, status=400)

@require_POST
def update_cart_item(request):
    """
    API endpoint to update cart item quantity
    """
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'يرجى تسجيل الدخول أولاً'})
    
    data = json.loads(request.body)
    item_id = data.get('item_id')
    quantity_change = data.get('quantity_change', 0)
    
    try:
        cart_item = CartItem.objects.get(id=item_id, user=request.user)
        
        # Update quantity
        new_quantity = cart_item.quantity + quantity_change
        
        if new_quantity <= 0:
            # If quantity becomes 0 or negative, remove the item
            cart_item.delete()
            message = 'تم إزالة المنتج من العربة'
        else:
            # Check if there's enough stock
            if cart_item.product.stock_quantity >= new_quantity:
                cart_item.quantity = new_quantity
                cart_item.save()
                message = 'تم تحديث كمية المنتج في العربة'
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'لا يوجد كمية كافية من المنتج'
                })
        
        # Get updated cart count
        cart_count = CartItem.objects.filter(user=request.user).count()
        
        return JsonResponse({
            'success': True,
            'message': message,
            'cart_count': cart_count
        })
        
    except CartItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'المنتج غير موجود في العربة'
        })

def save_contact_info(request, name, phone, address, city='', note=''):
    """
    حفظ معلومات الاتصال للمستخدم أو الزائر في الجلسة
    """
    # تخزين معلومات الاتصال في جلسة المستخدم
    contact_info = {
        'name': name,
        'phone': phone,
        'address': address,
        'city': city,
        'note': note
    }
    
    # حفظ في الجلسة
    request.session['contact_info'] = contact_info
    
    return contact_info

def checkout(request):
    """
    Display checkout page and process order submission.
    """
    # Get cart for the current user or session
    cart_items, cart = get_cart_or_error(request)
    
    if not cart_items.exists():
        messages.error(request, 'عفواً، السلة فارغة!')
        return redirect('boutiqe:cart')
    
    # Calculate totals
    cart_total = sum(item.get_total() for item in cart_items)
    
    # Apply coupon if present
    coupon_code = request.session.get('coupon_code', None)
    coupon_discount = Decimal('0.00')
    
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code, active=True)
            
            # Check if coupon is still valid
            if (coupon.valid_from and coupon.valid_from > timezone.now()) or \
               (coupon.valid_to and coupon.valid_to < timezone.now()) or \
               (coupon.max_uses > 0 and coupon.current_uses >= coupon.max_uses):
                # Remove expired coupon
                request.session.pop('coupon_code', None)
                request.session.pop('coupon_discount', None)
                messages.warning(request, 'انتهت صلاحية الكوبون أو تم استخدامه')
            else:
                # Apply coupon discount
                if coupon.discount_type == 'percentage':
                    coupon_discount = (cart_total * coupon.discount_value) / 100
                else:
                    coupon_discount = min(coupon.discount_value, cart_total)
                
                # Store the calculated discount in the session
                request.session['coupon_discount'] = str(coupon_discount)
        except Coupon.DoesNotExist:
            # Remove invalid coupon
            request.session.pop('coupon_code', None)
            request.session.pop('coupon_discount', None)
    
    # Calculate final totals
    final_total = max(cart_total - coupon_discount, Decimal('0.00'))
    
    # Calculate shekel values for display
    shekel_exchange_rate = Decimal('5.00')  # Placeholder exchange rate
    cart_total_ils = round(cart_total * shekel_exchange_rate, 2)
    final_total_ils = round(final_total * shekel_exchange_rate, 2)
    
    if request.method == 'POST':
        # Process the order
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city', '')
        note = request.POST.get('note', '')
        
        # Validate required fields
        if not all([name, phone, address]):
            messages.error(request, 'يرجى ملء جميع الحقول المطلوبة')
            return redirect('boutiqe:checkout')
        
        # Validate phone number format (must start with 05)
        if not phone.startswith('05'):
            messages.error(request, 'يجب أن يبدأ رقم الهاتف بـ 05')
            return redirect('boutiqe:checkout')
        
        # Save contact info
        contact_info = save_contact_info(request, name, phone, address, city, note)
        
        # Create unique order ID
        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        
        # Create the order
        if request.user.is_authenticated:
            # For authenticated users
            order = Order.objects.create(
                user=request.user,
                order_id=order_id,
                status='pending',
                shipping_address=address,
                phone_number=phone,
                contact_info=contact_info
            )
        else:
            # For guest users
            order = Order.objects.create(
                order_id=order_id,
                status='pending',
                shipping_address=address,
                phone_number=phone,
                session_key=request.session.session_key,
                contact_info=contact_info
            )
        
        # Add items to the order
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                color=item.color,
                size=item.size
            )
        
        # Clear cart after successful order
        cart_items.delete()
        
        # Store order_id in session for thank you page
        request.session['last_order_id'] = order_id
        
        # Add success message
        if request.user.is_authenticated:
            messages.success(request, 'تم إنشاء طلبك بنجاح! يمكنك متابعة حالة طلبك من صفحة طلباتي.')
        else:
            messages.success(request, 'تم إنشاء طلبك بنجاح! سيتم التواصل معك قريباً.')
        
        # Redirect to orders page instead of order confirmation
        if request.user.is_authenticated:
            return redirect('boutiqe:orders')
        else:
            # For guest users, still show the order confirmation page
            return redirect('boutiqe:order_confirmation')
    
    # Prepare context for the template
    context = {
        'cart_items': cart_items,
        'total_ils': cart_total_ils,
        'coupon_code': coupon_code,
        'coupon_discount': coupon_discount,
        'coupon_discount_ils': round(coupon_discount * shekel_exchange_rate, 2) if coupon_discount else 0,
        'final_total_ils': final_total_ils,
        'shipping_cost': Decimal('0.00'),  # Placeholder for shipping cost calculation
        'total_with_shipping': final_total_ils,  # Add shipping when implemented
        'is_authenticated': request.user.is_authenticated,
    }
    
    # Add user's contact info if authenticated
    if request.user.is_authenticated:
        try:
            contact = ContactInfo.objects.filter(user=request.user).order_by('-is_default', '-created_at').first()
            if contact:
                context['contact'] = contact
        except:
            pass
    
    return render(request, 'boutiqe/checkout.html', context)

def order_confirmation(request):
    """
    Order confirmation page showing order details after successful checkout.
    """
    order_id = request.session.get('last_order_id')
    
    if not order_id:
        messages.error(request, 'لم يتم العثور على معلومات الطلب')
        return redirect('boutiqe:home')
    
    # Get the order
    try:
        if request.user.is_authenticated:
            order = get_object_or_404(Order, order_id=order_id, user=request.user)
        else:
            # For guest users
            order = get_object_or_404(Order, order_id=order_id, session_key=request.session.session_key)
        
        # Add a success message if not already present
        messages.success(request, 'تم تقديم طلبك بنجاح! سيتم التواصل معك قريبًا لتأكيد الطلب.')
        
        context = {
            'order': order,
            'items': order.items.all(),
        }
        
        return render(request, 'boutiqe/order_confirmation.html', context)
    except:
        messages.error(request, 'حدث خطأ أثناء استرجاع معلومات الطلب')
        return redirect('boutiqe:home')

@login_required
def place_order(request):
    """
    إنشاء طلب جديد (باستخدام الجلسة بدلاً من قاعدة البيانات)
    """
    if request.method == 'POST':
        # الحصول على عناصر السلة للمستخدم الحالي
        cart_items = CartItem.objects.filter(user=request.user)
        
        if not cart_items.exists():
            messages.error(request, 'لا يمكن إتمام الطلب. السلة فارغة.')
            return redirect('boutiqe:cart')
        
        # حساب إجمالي الطلب
        total = sum(item.get_total() for item in cart_items)
        
        # إنشاء رقم طلب
        import datetime
        import random
        order_id = f"ORD-{datetime.datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        
        try:
            # إعداد بيانات الطلب
            order_info = {
                'order_id': order_id,
                'date': datetime.datetime.now().strftime('%d/%m/%Y'),
                'status': 'processing',
                'status_text': 'قيد التحضير',
                'items': [],
            }
            
            # إضافة عناصر الطلب
            for item in cart_items:
                product = item.product
                order_info['items'].append({
                    'name': product.name,
                    'price': float(product.discount_price or product.price),
                    'quantity': item.quantity,
                    'image': product.get_main_image().image.url if product.get_main_image() else None,
                    'size': item.size.name if hasattr(item, 'size') and item.size else None,
                    'color': item.color.name if hasattr(item, 'color') and item.color else None,
                })
            
            # إضافة المجاميع
            subtotal = float(total)
            shipping = 40.00  # قيمة افتراضية للشحن
            discount = 0.00  # قيمة افتراضية للخصم
            
            # التحقق من وجود كوبون خصم مطبق
            coupon_id = request.session.get('coupon_id', None)
            coupon_discount = request.session.get('coupon_discount', '0.00')
            
            if coupon_id:
                try:
                    coupon = Coupon.objects.get(id=coupon_id)
                    discount = float(coupon_discount)
                    
                    # تسجيل استخدام الكوبون
                    try:
                        # إنشاء سجل استخدام الكوبون - تصحيح أسماء الحقول
                        coupon_usage = CouponUsage(
                            coupon=coupon,
                            user=request.user,
                            discount_value=Decimal(coupon_discount),
                            order_value=total
                        )
                        coupon_usage.save()
                        
                        # زيادة عدد مرات استخدام الكوبون
                        coupon.current_uses += 1
                        coupon.save()
                    except Exception as e:
                        # توثيق الخطأ دون توقف العملية
                        logger.error(f"Error recording coupon usage: {str(e)}")
                    
                    # حذف معلومات الكوبون من الجلسة
                    if 'coupon_code' in request.session:
                        del request.session['coupon_code']
                    if 'coupon_discount' in request.session:
                        del request.session['coupon_discount']
                    if 'coupon_id' in request.session:
                        del request.session['coupon_id']
                except Exception as e:
                    # توثيق الخطأ دون توقف العملية
                    logger.error(f"Error applying coupon: {str(e)}")
            
            # استكمال معلومات الطلب
            order_info['shipping'] = shipping
            order_info['discount'] = discount
            order_info['subtotal'] = subtotal
            order_info['total'] = subtotal + shipping - discount
            
            # حفظ معلومات الطلب في جلسة المستخدم
            if 'orders' not in request.session:
                request.session['orders'] = []
            
            # إضافة الطلب الجديد في بداية القائمة
            orders = request.session.get('orders', [])
            orders.insert(0, order_info)
            request.session['orders'] = orders
            
            # تخزين المعرف في الجلسة لاستخدامه في صفحة الطلبات
            request.session['new_order_id'] = order_id
            
            # حذف عناصر السلة بعد إتمام الطلب
            cart_items.delete()
            
            messages.success(request, f'تم إنشاء طلبك بنجاح. رقم الطلب هو {order_id}')
            return redirect('boutiqe:orders')
        
        except Exception as e:
            # توثيق الخطأ وإعلام المستخدم
            logger.error(f"Error creating order: {str(e)}")
            messages.error(request, 'حدث خطأ أثناء إنشاء الطلب. يرجى المحاولة مرة أخرى لاحقًا.')
            return redirect('boutiqe:checkout')
    
    return redirect('boutiqe:checkout')

def wishlist(request):
    """
    View for displaying items in the wishlist.
    """
    # Get wishlist items for current user or session
    if request.user.is_authenticated:
        wishlist_items = Wishlist.objects.filter(user=request.user)
    elif request.session.session_key:
        wishlist_items = Wishlist.objects.filter(session_key=request.session.session_key)
    else:
        # No session yet, create one
        request.session.save()
        wishlist_items = Wishlist.objects.none()
    
    context = {
        'wishlist_items': wishlist_items,
    }
    return render(request, 'boutiqe/wishlist.html', context)

def add_to_wishlist(request, product_id):
    """
    Add a product to the wishlist.
    """
    product = get_object_or_404(Product, id=product_id)
    
    # Create wishlist item based on authentication status
    if request.user.is_authenticated:
        # For authenticated users
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )
    else:
        # For anonymous users
        if not request.session.session_key:
            request.session.save()
        
        session_key = request.session.session_key
        wishlist_item, created = Wishlist.objects.get_or_create(
            session_key=session_key,
            product=product
        )
    
    if created:
        messages.success(request, f'تمت إضافة {product.name} إلى قائمة المفضلة')
    else:
        messages.info(request, 'هذا المنتج موجود بالفعل في قائمة المفضلة')
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Count wishlist items based on authentication status
        if request.user.is_authenticated:
            wishlist_count = Wishlist.objects.filter(user=request.user).count()
        else:
            wishlist_count = Wishlist.objects.filter(session_key=request.session.session_key).count()
        
        return JsonResponse({'wishlist_count': wishlist_count})
    
    return redirect('boutiqe:product_detail', slug=product.slug)

def remove_from_wishlist(request, wishlist_id):
    """
    Remove an item from the wishlist.
    """
    # Get wishlist item based on authentication status
    if request.user.is_authenticated:
        wishlist_item = get_object_or_404(Wishlist, id=wishlist_id, user=request.user)
    else:
        wishlist_item = get_object_or_404(
            Wishlist, 
            id=wishlist_id, 
            session_key=request.session.session_key
        )
    
    wishlist_item.delete()
    
    messages.success(request, 'تم حذف المنتج من قائمة المفضلة')
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Count wishlist items based on authentication status
        if request.user.is_authenticated:
            wishlist_count = Wishlist.objects.filter(user=request.user).count()
        else:
            wishlist_count = Wishlist.objects.filter(session_key=request.session.session_key).count()
        
        return JsonResponse({'wishlist_count': wishlist_count})
    
    return redirect('boutiqe:wishlist')

@login_required
def move_to_cart(request, wishlist_id):
    """
    Move item from wishlist to cart for both authenticated and guest users
    """
    # Get the wishlist item
    try:
        if request.user.is_authenticated:
            wishlist_item = WishlistItem.objects.get(id=wishlist_id, user=request.user)
        else:
            # For anonymous users
            if not request.session.session_key:
                request.session.create()
            wishlist_item = WishlistItem.objects.get(id=wishlist_id, session_key=request.session.session_key)
        
        # Get cart
        cart = get_or_create_cart(request)
        
        # Check if product is already in cart
        product = wishlist_item.product
        existing_item = cart.items.filter(product=product).first()
        
        if existing_item:
            # Increment quantity if already in cart
            existing_item.quantity += 1
            existing_item.save()
            message = 'تم زيادة الكمية في السلة'
        else:
            # Add to cart
            CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=1
            )
            message = 'تم إضافة المنتج إلى السلة'
        
        # Remove from wishlist
        wishlist_item.delete()
        
        messages.success(request, message)
    except WishlistItem.DoesNotExist:
        messages.error(request, 'العنصر غير موجود في المفضلة')
    
    return redirect('boutiqe:wishlist')

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message_text = request.POST.get('message')
        
        contact = Contact(
            name=name,
            email=email,
            phone=phone,
            message=message_text
        )
        contact.save()
        
        messages.success(request, 'تم إرسال رسالتك بنجاح. سنتواصل معك قريبًا.')
        return redirect('boutiqe:contact')
    
    return render(request, 'boutiqe/contact.html')

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    phone = forms.CharField(max_length=20, required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'مرحبًا {username}! تم تسجيل دخولك بنجاح.')
                next_url = request.POST.get('next', '')
                if next_url:
                    return redirect(next_url)
                else:
                    return redirect('boutiqe:home')
            else:
                messages.error(request, 'خطأ في اسم المستخدم أو كلمة المرور!')
        else:
            messages.error(request, 'خطأ في اسم المستخدم أو كلمة المرور!')
    else:
        form = AuthenticationForm()
    
    return render(request, 'boutiqe/login.html', {'form': form})

def user_logout(request):
    logout(request)
    messages.success(request, 'تم تسجيل خروجك بنجاح.')
    return redirect('boutiqe:home')

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Add additional profile information if needed
            username = form.cleaned_data.get('username')
            login(request, user)
            messages.success(request, f'مرحبًا {username}! تم إنشاء حسابك بنجاح.')
            return redirect('boutiqe:home')
    else:
        form = UserRegisterForm()
    
    return render(request, 'boutiqe/register.html', {'form': form})

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary', 'readonly': 'readonly'})
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary'})
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary'})
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def clean_email(self):
        # إعادة البريد الإلكتروني الحالي فقط بدون تغيير
        return self.instance.email

class ProfileUpdateForm(forms.ModelForm):
    phone = forms.CharField(
        max_length=20, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary'})
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary', 'rows': '3'})
    )
    city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary'})
    )
    country = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary'})
    )
    
    class Meta:
        model = Profile
        fields = ['phone', 'address', 'city', 'country', 'profile_image']
        widgets = {
            'profile_image': forms.FileInput(attrs={'class': 'hidden absolute inset-0 opacity-0 cursor-pointer', 'id': 'profile_image_upload'})
        }

@login_required
def profile_view(request):
    """
    عرض صفحة الملف الشخصي للمستخدم
    """
    # التأكد من وجود ملف شخصي للمستخدم
    if not hasattr(request.user, 'profile'):
        Profile.objects.create(user=request.user)
    
    if request.method == 'POST':
        logger.debug("تم استلام طلب POST لتحديث الملف الشخصي")
        
        # طباعة محتوى request.FILES للتنقيح
        if request.FILES:
            logger.debug(f"الملفات المرفقة: {request.FILES}")
        else:
            logger.debug("لا توجد ملفات مرفقة في الطلب")
        
        # إنشاء نماذج مع البيانات المرسلة
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        # التحقق من صلاحية النماذج
        u_valid = u_form.is_valid()
        p_valid = p_form.is_valid()
        
        logger.debug(f"صلاحية نموذج المستخدم: {u_valid}, صلاحية نموذج الملف الشخصي: {p_valid}")
        
        if p_form.is_valid():
            logger.debug(f"بيانات نموذج الملف الشخصي (cleaned_data): {p_form.cleaned_data}")
            if 'profile_image' in p_form.cleaned_data and p_form.cleaned_data['profile_image']:
                logger.debug(f"تم تحميل صورة جديدة: {p_form.cleaned_data['profile_image']}")
        
        # إذا كان كلا النموذجين صالحين، قم بحفظهما
        if u_valid and p_valid:
            try:
                # حفظ نموذج المستخدم أولاً
                user = u_form.save()
                logger.debug(f"تم حفظ بيانات المستخدم: {user.username}")
                
                # التعامل مع الصورة وحفظ نموذج الملف الشخصي بشكل منفصل
                profile = p_form.save(commit=False)
                
                # معالجة تحميل الصورة - طباعة معلومات للتنقيح
                if 'profile_image' in request.FILES:
                    logger.debug(f"تم تحميل صورة ملف شخصي: {request.FILES['profile_image']}")
                    profile.profile_image = request.FILES['profile_image']
                
                # حفظ الملف الشخصي
                profile.user = user  # تأكيد ربط الملف الشخصي بالمستخدم
                profile.save()
                logger.debug(f"تم حفظ الملف الشخصي للمستخدم: {user.username}")
                
                messages.success(request, 'تم تحديث الملف الشخصي بنجاح!')
                return redirect('boutiqe:profile')
            except Exception as e:
                logger.error(f"خطأ أثناء حفظ الملف الشخصي: {str(e)}")
                messages.error(request, f'حدث خطأ أثناء الحفظ: {str(e)}')
        else:
            # عرض أخطاء التحقق من الصحة إذا وجدت
            if not u_valid:
                logger.debug(f"أخطاء نموذج المستخدم: {u_form.errors}")
            if not p_valid:
                logger.debug(f"أخطاء نموذج الملف الشخصي: {p_form.errors}")
            
            # إضافة رسالة خطأ للمستخدم
            messages.error(request, 'الرجاء تصحيح الأخطاء أدناه.')
    else:
        # إذا كان الطلب ليس POST، قم بإنشاء نماذج فارغة باستخدام البيانات الحالية
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    # الحصول على عناصر سلة التسوق وعناصر المفضلة للمستخدم الحالي
    cart_items = CartItem.objects.filter(user=request.user)
    wishlist_items = Wishlist.objects.filter(user=request.user)
    
    context = {
        'u_form': u_form,
        'p_form': p_form,
        'cart_items': cart_items,
        'wishlist_items': wishlist_items,
    }
    return render(request, 'boutiqe/profile.html', context)

@login_required
def orders_view(request):
    """
    عرض صفحة طلبات المستخدم (باستخدام الجلسة بدلاً من قاعدة البيانات)
    """
    # استرجاع الطلبات من جلسة المستخدم
    orders = request.session.get('orders', [])
    
    # إعداد إحصائيات فارغة للطلبات (افتراضي)
    order_stats = {
        'all': len(orders),
        'delivered': len([order for order in orders if order.get('status') == 'delivered']),
        'cancelled': len([order for order in orders if order.get('status') == 'cancelled']),
    }
    
    # عرض الطلب الذي تم تشكيله للتو إذا كان موجوداً في الجلسة وغير موجود في الطلبات
    new_order_id = request.session.get('new_order_id')
    if new_order_id and not any(order.get('order_id') == new_order_id for order in orders):
        # إنشاء بيانات وهمية للطلب الجديد
        import datetime
        
        new_order = {
            'order_id': new_order_id,
            'date': datetime.datetime.now().strftime('%d/%m/%Y'),
            'status': 'processing',
            'status_text': 'قيد التحضير',
            'items': [],
            'shipping': 40.00,
            'discount': 0.00,
            'subtotal': 0.00,
            'total': 40.00
        }
        
        # إضافة الطلب الجديد إلى قائمة الطلبات في بداية القائمة
        orders.insert(0, new_order)
        
        # تحديث إحصائيات الطلبات
        order_stats['all'] = len(orders)
        
        # حفظ القائمة المحدثة في الجلسة
        request.session['orders'] = orders
        
        # إزالة الطلب الجديد من الجلسة بعد عرضه
        request.session.pop('new_order_id', None)
    
    # فلترة الطلبات حسب الحالة إذا تم تحديد فلتر
    status_filter = request.GET.get('status')
    if status_filter and orders:
        filtered_orders = [order for order in orders if order.get('status') == status_filter]
    else:
        filtered_orders = orders
    
    # دائما استخدام الشيكل كعملة
    selected_currency = 'ILS'
    
    # سعر الصرف الحالي للشيكل (1 ريال = X شيكل)
    shekel_exchange_rate = Decimal('0.94')
    
    context = {
        'orders': filtered_orders,
        'order_stats': order_stats,
        'selected_currency': selected_currency,
        'shekel_exchange_rate': shekel_exchange_rate,
    }
    return render(request, 'boutiqe/orders.html', context)

class CancelOrderForm(forms.Form):
    """نموذج طلب إلغاء طلب"""
    order_id = forms.CharField(widget=forms.HiddenInput(), required=True)
    reason = forms.CharField(
        label='سبب الإلغاء',
        widget=forms.Select(
            choices=[
                ('', '-- اختر سبب الإلغاء --'),
                ('تغيير رأيي في الطلب', 'تغيير رأيي في الطلب'),
                ('وجدت سعر أفضل في مكان آخر', 'وجدت سعر أفضل في مكان آخر'),
                ('تأخر في الشحن', 'تأخر في الشحن'),
                ('مشكلة في الدفع', 'مشكلة في الدفع'),
                ('أخرى', 'أخرى')
            ],
            attrs={'class': 'w-full border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary p-2'}
        ),
        required=True
    )
    phone = forms.CharField(
        label='رقم الهاتف للتواصل',
        widget=forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary p-2', 'placeholder': '05xxxxxxxx'}),
        required=True
    )

def cancel_order(request):
    """
    طلب إلغاء طلب من قبل المستخدم
    """
    if request.method == 'POST':
        form = CancelOrderForm(request.POST)
        if form.is_valid():
            order_id = form.cleaned_data['order_id']
            reason = form.cleaned_data['reason']
            phone = form.cleaned_data['phone']
            
            # إضافة معلومات تأكيد نجاح المعاملة للمستخدم
            messages.success(request, 'تم استلام طلب الإلغاء بنجاح. سنتواصل معك قريباً على الرقم المقدم.')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # إعادة JSON response للطلبات AJAX
                return JsonResponse({'status': 'success'})
            else:
                # إعادة التوجيه لصفحة الطلبات
                return redirect('boutiqe:orders')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'errors': form.errors})
    else:
        form = CancelOrderForm()
    
    context = {
        'form': form
    }
    return render(request, 'boutiqe/parts/cancel_order_form.html', context)

@require_POST
def toggle_wishlist(request):
    """
    دالة بسيطة لإضافة/إزالة منتج من المفضلة
    تعمل مع المستخدمين المسجلين والزوار
    """
    print("تم استلام طلب toggle-wishlist")
    print("نوع المحتوى:", request.content_type)
    print("الرؤوس:", dict(request.headers))
    
    # استخدام محاولة/استثناء لمعالجة أي خطأ محتمل
    try:
        # فك ترميز البيانات المستلمة
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                print("البيانات المستلمة (JSON):", data)
            else:
                data = request.POST
                print("البيانات المستلمة (POST):", dict(data))
        except json.JSONDecodeError as e:
            print("خطأ في فك ترميز JSON:", str(e))
            return JsonResponse(
                {'success': False, 'error': 'صيغة البيانات غير صحيحة'}, 
                status=400
            )
        
        # الحصول على معرف المنتج
        product_id = data.get('product_id')
        print("معرف المنتج المستلم:", product_id, "النوع:", type(product_id))
        
        if not product_id:
            print("معرف المنتج مفقود")
            return JsonResponse(
                {'success': False, 'error': 'معرف المنتج مطلوب'}, 
                status=400
            )
        
        # تحويل معرف المنتج إلى رقم صحيح
        try:
            product_id = int(product_id)
            print("معرف المنتج بعد التحويل:", product_id)
        except (ValueError, TypeError) as e:
            print("خطأ في تحويل معرف المنتج:", str(e))
            return JsonResponse(
                {'success': False, 'error': 'معرف المنتج يجب أن يكون رقماً'}, 
                status=400
            )
        
        # البحث عن المنتج
        try:
            product = Product.objects.get(id=product_id)
            print("تم العثور على المنتج:", product.name)
        except Product.DoesNotExist:
            print("المنتج غير موجود")
            return JsonResponse(
                {'success': False, 'error': 'المنتج غير موجود'}, 
                status=404
            )
        
        # معالجة المستخدمين المسجلين
        if request.user.is_authenticated:
            try:
                # البحث عن المنتج في المفضلة
                wishlist_item = Wishlist.objects.filter(
                    user=request.user,
                    product=product
                ).first()
                
                if wishlist_item:
                    # إذا كان موجوداً، قم بحذفه
                    wishlist_item.delete()
                    is_in_wishlist = False
                    print("تمت إزالة المنتج من المفضلة للمستخدم:", request.user.username)
                else:
                    # إذا لم يكن موجوداً، قم بإضافته
                    Wishlist.objects.create(
                        user=request.user,
                        product=product
                    )
                    is_in_wishlist = True
                    print("تمت إضافة المنتج للمفضلة للمستخدم:", request.user.username)
                
                # حساب عدد عناصر المفضلة
                wishlist_count = Wishlist.objects.filter(user=request.user).count()
                
            except Exception as e:
                print("خطأ أثناء معالجة المستخدم المسجل:", str(e))
                return JsonResponse(
                    {'success': False, 'error': 'خطأ في معالجة الطلب'}, 
                    status=500
                )
        
        # معالجة الزوار
        else:
            try:
                # التأكد من وجود جلسة
                if not request.session.session_key:
                    request.session.create()
                
                session_key = request.session.session_key
                print("مفتاح الجلسة للزائر:", session_key)
                
                # البحث عن المنتج في المفضلة
                wishlist_item = Wishlist.objects.filter(
                    session_key=session_key,
                    product=product
                ).first()
                
                if wishlist_item:
                    # إذا كان موجوداً، قم بحذفه
                    wishlist_item.delete()
                    is_in_wishlist = False
                    print("تمت إزالة المنتج من المفضلة للزائر")
                else:
                    # إذا لم يكن موجوداً، قم بإضافته
                    Wishlist.objects.create(
                        session_key=session_key,
                        product=product
                    )
                    is_in_wishlist = True
                    print("تمت إضافة المنتج للمفضلة للزائر")
                
                # حساب عدد عناصر المفضلة
                wishlist_count = Wishlist.objects.filter(session_key=session_key).count()
                
            except Exception as e:
                print("خطأ أثناء معالجة الزائر:", str(e))
                return JsonResponse(
                    {'success': False, 'error': 'خطأ في معالجة الطلب'}, 
                    status=500
                )
        
        # إرجاع الاستجابة
        response = {
            'success': True,
            'is_in_wishlist': is_in_wishlist,
            'wishlist_count': wishlist_count
        }
        print("الاستجابة النهائية:", response)
        return JsonResponse(response)
        
    except Exception as e:
        print("خطأ عام غير متوقع:", str(e))
        return JsonResponse(
            {'success': False, 'error': str(e)}, 
            status=500
        )

def quick_view(request, product_id):
    """
    Show a quick view modal for a product.
    Supports both authenticated and guest users.
    """
    product = get_object_or_404(Product, id=product_id)
    
    # Check if the product is in the user's wishlist
    is_in_wishlist = False
    if request.user.is_authenticated:
        is_in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
    elif request.session.session_key:
        try:
            is_in_wishlist = Wishlist.objects.filter(session_key=request.session.session_key, product=product).exists()
        except Exception:
            # Handle case where session_key field might not exist yet
            pass
    
    context = {
        'product': product,
        'is_in_wishlist': is_in_wishlist,
    }
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'boutiqe/parts/quick_view_modal.html', context)
    
    # Always use quick_view_modal.html instead of quick_view.html
    return render(request, 'boutiqe/parts/quick_view_modal.html', context)

# ===== لوحة تحكم الأدمن =====

def is_admin(user):
    """Check if user is an admin or staff"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin dashboard view showing statistics and recent items"""
    # Get counts for basic stats
    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_users = User.objects.count()
    
    # Get count of featured products
    featured_products = Product.objects.filter(is_featured=True).count()
    
    # Get new products (added in the last 7 days)
    from datetime import timedelta
    from django.utils import timezone
    new_products = Product.objects.filter(created_at__gte=timezone.now() - timedelta(days=7)).count()
    
    # Get products with special offers
    special_offers = Product.objects.filter(discount_price__isnull=False).count()
    
    # Get products out of stock
    out_of_stock = Product.objects.filter(stock_count=0).count()
    
    # Get recent products
    recent_products = Product.objects.order_by('-created_at')[:5]
    
    context = {
        'total_products': total_products,
        'total_categories': total_categories,
        'total_users': total_users,
        'featured_products': featured_products,
        'new_products': new_products,
        'special_offers': special_offers,
        'out_of_stock': out_of_stock,
        'recent_products': recent_products,
    }
    
    return render(request, 'boutiqe/admin/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_products(request):
    """Admin products list view"""
    products = Product.objects.all().order_by('-created_at')
    
    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
    
    # Handle category filter
    category_id = request.GET.get('category', '')
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Get all categories for the filter dropdown
    categories = Category.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
    }
    
    return render(request, 'boutiqe/admin/products.html', context)

@login_required
@user_passes_test(is_admin)
def admin_product_create(request):
    """Admin create product view"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'تم إضافة المنتج "{product.name}" بنجاح')
            return redirect('boutiqe:admin_products')
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'title': 'إضافة منتج جديد',
        'submit_text': 'إضافة',
    }
    
    return render(request, 'boutiqe/admin/product_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_product_edit(request, product_id):
    """Admin edit product view"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'تم تحديث المنتج "{product.name}" بنجاح')
            return redirect('boutiqe:admin_products')
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
        'title': f'تعديل المنتج: {product.name}',
        'submit_text': 'حفظ التغييرات',
    }
    
    return render(request, 'boutiqe/admin/product_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_product_delete(request, product_id):
    """Admin delete product view"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'تم حذف المنتج "{product_name}" بنجاح')
        return redirect('boutiqe:admin_products')
    
    context = {
        'product': product,
    }
    
    return render(request, 'boutiqe/admin/product_confirm_delete.html', context)

@login_required
@user_passes_test(is_admin)
def admin_categories(request):
    """Admin categories view"""
    categories = Category.objects.annotate(product_count=Count('product'))
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'تم إضافة الفئة "{category.name}" بنجاح')
            return redirect('boutiqe:admin_categories')
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = CategoryForm()
    
    context = {
        'categories': categories,
        'form': form,
    }
    
    return render(request, 'boutiqe/admin/categories.html', context)

@login_required
@user_passes_test(is_admin)
def admin_users(request):
    """Admin users view"""
    users = User.objects.all().order_by('-date_joined')
    
    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) | 
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    context = {
        'users': users,
        'search_query': search_query,
    }
    
    return render(request, 'boutiqe/admin/users.html', context)

@login_required
@user_passes_test(is_admin)
def admin_trending_collections(request):
    """Admin trending collections list view"""
    collections = TrendingCollection.objects.all().order_by('order_position', '-created_at')
    
    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        collections = collections.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    context = {
        'collections': collections,
        'search_query': search_query,
    }
    
    return render(request, 'boutiqe/admin/trending_collections.html', context)

@login_required
@user_passes_test(is_admin)
def admin_trending_collection_create(request):
    """Admin create trending collection view"""
    if request.method == 'POST':
        form = TrendingCollectionForm(request.POST, request.FILES)
        if form.is_valid():
            collection = form.save()
            messages.success(request, f'تم إضافة المجموعة "{collection.name}" بنجاح')
            return redirect('boutiqe:admin_trending_collections')
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = TrendingCollectionForm()
    
    context = {
        'form': form,
        'title': 'إضافة مجموعة رائجة جديدة',
        'submit_text': 'إضافة',
    }
    
    return render(request, 'boutiqe/admin/trending_collection_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_trending_collection_edit(request, collection_id):
    """Admin edit trending collection view"""
    collection = get_object_or_404(TrendingCollection, id=collection_id)
    
    if request.method == 'POST':
        form = TrendingCollectionForm(request.POST, request.FILES, instance=collection)
        if form.is_valid():
            form.save()
            messages.success(request, f'تم تحديث المجموعة "{collection.name}" بنجاح')
            return redirect('boutiqe:admin_trending_collections')
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = TrendingCollectionForm(instance=collection)
    
    context = {
        'form': form,
        'title': f'تعديل المجموعة: {collection.name}',
        'submit_text': 'تحديث',
        'collection': collection,
    }
    
    return render(request, 'boutiqe/admin/trending_collection_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_trending_collection_delete(request, collection_id):
    """Admin delete trending collection view"""
    collection = get_object_or_404(TrendingCollection, id=collection_id)
    
    if request.method == 'POST':
        collection_name = collection.name
        collection.delete()
        messages.success(request, f'تم حذف المجموعة "{collection_name}" بنجاح')
        return redirect('boutiqe:admin_trending_collections')
    
    context = {
        'collection': collection,
    }
    
    return render(request, 'boutiqe/admin/trending_collection_delete.html', context)

@login_required
@user_passes_test(is_admin)
def admin_discounts(request):
    """Admin discounts list view"""
    discounts = Discount.objects.all().order_by('order_position', '-created_at')
    
    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        discounts = discounts.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    context = {
        'discounts': discounts,
        'search_query': search_query,
    }
    
    return render(request, 'boutiqe/admin/discounts.html', context)

@login_required
@user_passes_test(is_admin)
def admin_discount_create(request):
    """Admin create discount view"""
    if request.method == 'POST':
        form = DiscountForm(request.POST, request.FILES)
        if form.is_valid():
            discount = form.save()
            messages.success(request, f'تم إضافة الخصم "{discount.name}" بنجاح')
            return redirect('boutiqe:admin_discounts')
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = DiscountForm()
    
    context = {
        'form': form,
        'title': 'إضافة خصم جديد',
        'submit_text': 'إضافة',
    }
    
    return render(request, 'boutiqe/admin/discount_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_discount_edit(request, discount_id):
    """Admin edit discount view"""
    discount = get_object_or_404(Discount, id=discount_id)
    
    if request.method == 'POST':
        form = DiscountForm(request.POST, request.FILES, instance=discount)
        if form.is_valid():
            form.save()
            messages.success(request, f'تم تحديث الخصم "{discount.name}" بنجاح')
            return redirect('boutiqe:admin_discounts')
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = DiscountForm(instance=discount)
    
    context = {
        'form': form,
        'title': f'تعديل الخصم: {discount.name}',
        'submit_text': 'تحديث',
        'discount': discount,
    }
    
    return render(request, 'boutiqe/admin/discount_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_discount_delete(request, discount_id):
    """Admin delete discount view"""
    discount = get_object_or_404(Discount, id=discount_id)
    
    if request.method == 'POST':
        discount_name = discount.name
        discount.delete()
        messages.success(request, f'تم حذف الخصم "{discount_name}" بنجاح')
        return redirect('boutiqe:admin_discounts')
    
    context = {
        'discount': discount,
    }
    
    return render(request, 'boutiqe/admin/discount_delete.html', context)

@login_required
def add_to_cart_by_id(request, product_id):
    """
    Add a product to cart using the URL parameter method
    """
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.GET.get('quantity', 1))
    color_id = request.GET.get('color')
    size_id = request.GET.get('size')
    
    # Get color and size if specified
    color = None
    size = None
    if color_id:
        color = get_object_or_404(Color, id=color_id)
    if size_id:
        size = get_object_or_404(Size, id=size_id)
    
    # Get or create cart for current user/session
    cart = get_or_create_cart(request)
    
    # التأكد من حفظ السلة في قاعدة البيانات
    if not cart.pk:
        cart.save()
    
    # Check if product already in cart
    try:
        cart_item = CartItem.objects.get(
            cart=cart,
            product=product,
            color=color,
            size=size,
        )
        # If item exists, increment quantity
        cart_item.quantity += quantity
        created = False
    except CartItem.DoesNotExist:
        # Create new cart item
        cart_item = CartItem(
            cart=cart,
            product=product,
            color=color,
            size=size,
            quantity=quantity
        )
        if request.user.is_authenticated:
            cart_item.user = request.user
        created = True
    
    cart_item.save()
    
    # If AJAX request, return JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'تمت إضافة المنتج إلى سلة التسوق',
            'cart_count': cart.items.aggregate(total=Sum('quantity'))['total'] or 0,
        })
    
    # Redirect based on the 'next' parameter or default to cart
    next_url = request.GET.get('next', 'boutiqe:cart')
    
    messages.success(request, f'تم إضافة {product.name} إلى سلة التسوق.')
    
    # If next_url is a full URL, redirect to that
    if next_url.startswith('http'):
        return redirect(next_url)
    
    # Otherwise, treat it as a named URL
    return redirect(next_url)

@login_required
def remove_from_cart_by_id(request, item_id):
    """
    Remove an item from the cart using the URL parameter method
    """
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    product_name = cart_item.product.name
    cart_item.delete()
    
    # سعر الصرف الحالي للشيكل
    shekel_exchange_rate = Decimal('0.94')
    
    # Get the cart's new total
    cart_total = sum(item.get_total() for item in request.user.cartitem_set.all())
    cart_total_ils = round(cart_total * shekel_exchange_rate, 2)
    
    # If AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'تم حذف المنتج من سلة التسوق',
            'cart_total': cart_total,
            'cart_total_ils': cart_total_ils,
            'cart_count': request.user.cartitem_set.count(),
        })
    
    messages.success(request, f'تم حذف {product_name} من سلة التسوق.')
    
    # Redirect based on the 'next' parameter or default to cart
    next_url = request.GET.get('next', 'boutiqe:cart')
    
    # If next_url is a full URL, redirect to that
    if next_url.startswith('http'):
        return redirect(next_url)
    
    # Otherwise, treat it as a named URL
    return redirect(next_url)

@login_required
def update_cart_item_by_id(request, item_id):
    """
    Update cart item quantity using the URL parameter method
    """
    # Get cart for current user or session
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    shekel_exchange_rate = Decimal('0.94')
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        # Ensure quantity is at least 1
        if quantity < 1:
            quantity = 1
        
        cart_item.quantity = quantity
        cart_item.save()
        
        # Get the item's new total
        item_total = cart_item.get_total()
        item_total_ils = round(item_total * shekel_exchange_rate, 2)
        
        # Get the cart's new total
        cart_total = sum(item.get_total() for item in cart.items.all())
        cart_total_ils = round(cart_total * shekel_exchange_rate, 2)
        
        
        # If AJAX request, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'تم تحديث كمية المنتج في سلة التسوق.',
                'item_total': item_total,
                'item_total_ils': item_total_ils,
                'cart_total': cart_total,
                'cart_total_ils': cart_total_ils,
                'cart_count': request.user.cartitem_set.count(),
            })
        
        messages.success(request, 'تم تحديث كمية المنتج في سلة التسوق.')
    
    # Redirect based on the 'next' parameter or default to cart
    next_url = request.GET.get('next', 'boutiqe:cart')
    
    # If next_url is a full URL, redirect to that
    if next_url.startswith('http'):
        return redirect(next_url)
    
    # Otherwise, treat it as a named URL
    return redirect(next_url)

@require_POST
def clear_cart(request):
    """Clear all items from the user's cart"""
    try:
        # Get cart for current user or session
        cart = get_or_create_cart(request)
        
        # Delete all items in the cart
        cart.items.all().delete()
        
        # سعر الصرف الحالي للشيكل
        shekel_exchange_rate = Decimal('0.94')
        
        # Return success response with zeros for totals (since cart is now empty)
        return JsonResponse({
            'success': True,
            'message': 'تم إفراغ السلة بنجاح',
            'cart_total': 0,
            'cart_total_ils': 0,
            'cart_count': 0
        })
    except Exception as e:
        # Log the error
        logger.error(f"Error clearing cart: {str(e)}")
        
        # Return error response
        return JsonResponse({
            'success': False,
            'message': 'حدث خطأ أثناء إفراغ السلة'
        }, status=400)

"""
Search views
"""
@require_GET
def search(request):
    """
    Regular search view that renders a page with search results
    """
    query = request.GET.get('q', '')
    
    if not query:
        # If there's no query, show an empty search page with categories
        categories = Category.objects.all()
        return render(request, 'boutiqe/search.html', {
            'query': '',
            'products': [],
            'count': 0,
            'categories': categories,
        })
    
    # Base query
    products = Product.objects.filter(
        Q(name__icontains=query) | 
        Q(description__icontains=query) |
        Q(category__name__icontains=query)
    ).distinct()
    
    # Filter by category if specified
    category_ids = request.GET.getlist('category')
    if category_ids:
        products = products.filter(category__id__in=category_ids)
    
    # Filter by price range if specified
    min_price = request.GET.get('min_price')
    if min_price and min_price.isdigit():
        products = products.filter(Q(price__gte=min_price) | Q(discount_price__gte=min_price))
    
    max_price = request.GET.get('max_price')
    if max_price and max_price.isdigit():
        # First check if discount_price exists and is less than max_price
        # If not, check if regular price is less than max_price
        products = products.filter(
            Q(discount_price__lte=max_price, discount_price__isnull=False) | 
            Q(price__lte=max_price)
        )
    
    # Sorting
    sort = request.GET.get('sort', 'relevance')
    if sort == 'price_asc':
        # Sort by price (taking into account discount_price if available)
        products = products.annotate(
            final_price=Coalesce('discount_price', 'price')
        ).order_by('final_price')
    elif sort == 'price_desc':
        products = products.annotate(
            final_price=Coalesce('discount_price', 'price')
        ).order_by('-final_price')
    elif sort == 'newest':
        products = products.order_by('-created_at')
    # Default is relevance, which is the default order from the search
    
    # Count all results before pagination
    total_count = products.count()
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(products, 12)  # 12 products per page
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    # Get all categories for filter sidebar
    all_categories = Category.objects.all()
    
    # Return search results page
    return render(request, 'boutiqe/search.html', {
        'query': query,
        'products': products,
        'count': total_count,
        'all_categories': all_categories,
    })

@require_GET
def search_ajax(request):
    """
    AJAX search view that returns JSON results for real-time search
    """
    query = request.GET.get('q', '')
    
    if not query:
        return JsonResponse({'results': []})
    
    # Search in products - limit to 5 for quick display
    products = Product.objects.filter(
        Q(name__icontains=query) | 
        Q(description__icontains=query) |
        Q(category__name__icontains=query)
    ).distinct()[:5]
    
    # Format results
    results = []
    for product in products:
        # Get product image
        image = product.get_main_image()
        image_url = image.image.url if image else '/static/images/no-image.jpg'
        
        # Get the current price (discounted or regular)
        price = product.discount_price if product.discount_price else product.price
        
        # Get category name
        category_name = product.category.name if product.category else ''
        
        results.append({
            'id': product.id,
            'name': product.name,
            'price': str(price),
            'image': image_url,
            'category': category_name,
            'url': product.get_absolute_url()
        })
    
    return JsonResponse({'results': results})

"""
Cart API views
"""
@require_GET
def cart_api(request):
    """
    API endpoint to get cart items for the sidebar
    """
    # Get cart for current user or session
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()
    
    # Format cart items
    items = []
    total = 0
    
    for item in cart_items:
        # Get product image
        image = item.product.get_main_image()
        image_url = image.image.url if image else '/static/images/no-image.jpg'
        
        # Get item price
        price = item.product.discount_price if item.product.discount_price else item.product.price
        item_total = price * item.quantity
        total += item_total
        
        # Get size and color
        size = item.size.name if item.size else ''
        color = item.color.name if item.color else ''
        
        items.append({
            'id': item.id,
            'name': item.product.name,
            'price': str(price),
            'total': str(item_total),
            'quantity': item.quantity,
            'image': image_url,
            'size': size,
            'color': color
        })
    
    return JsonResponse({
        'items': items,
        'total': str(total)
    })

@require_POST
def cart_update(request):
    """
    API endpoint to update cart item quantity
    """
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'يرجى تسجيل الدخول أولاً'})
    
    data = json.loads(request.body)
    item_id = data.get('item_id')
    quantity_change = data.get('quantity_change', 0)
    
    try:
        cart_item = CartItem.objects.get(id=item_id, user=request.user)
        
        # Update quantity
        new_quantity = cart_item.quantity + quantity_change
        
        if new_quantity <= 0:
            # If quantity becomes 0 or negative, remove the item
            cart_item.delete()
            message = 'تم إزالة المنتج من العربة'
        else:
            # Check if there's enough stock
            if cart_item.product.stock_quantity >= new_quantity:
                cart_item.quantity = new_quantity
                cart_item.save()
                message = 'تم تحديث كمية المنتج في العربة'
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'لا يوجد كمية كافية من المنتج'
                })
        
        # Get updated cart count
        cart_count = CartItem.objects.filter(user=request.user).count()
        
        return JsonResponse({
            'success': True,
            'message': message,
            'cart_count': cart_count
        })
        
    except CartItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'المنتج غير موجود في العربة'
        })

@require_POST
def cart_remove(request):
    """
    API endpoint to remove an item from the cart
    """
    data = json.loads(request.body)
    item_id = data.get('item_id')
    
    try:
        # Get cart for current user or session
        cart = get_or_create_cart(request)
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
        cart_item.delete()
        
        # Get updated cart count
        cart_count = cart.items.count()
        
        return JsonResponse({
            'success': True,
            'message': 'تم إزالة المنتج من العربة',
            'cart_count': cart_count
        })
        
    except CartItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'المنتج غير موجود في العربة'
        })

@require_POST
@login_required
def clear_cart(request):
    """Clear all items from the user's cart"""
    try:
        # Delete all cart items for the current user
        CartItem.objects.filter(user=request.user).delete()
        
        # سعر الصرف الحالي للشيكل
        shekel_exchange_rate = Decimal('0.94')
        
        # Return success response with zeros for totals (since cart is now empty)
        return JsonResponse({
            'success': True,
            'message': 'تم إفراغ السلة بنجاح',
            'cart_total': 0,
            'cart_total_ils': 0,
            'cart_count': 0
        })
    except Exception as e:
        # Log the error
        logger.error(f"Error clearing cart: {str(e)}")
        
        # Return error response
        return JsonResponse({
            'success': False,
            'message': 'حدث خطأ أثناء إفراغ السلة'
        }, status=400)

@require_POST
@login_required
def apply_coupon(request):
    """تطبيق كوبون الخصم على سلة التسوق"""
    code = request.POST.get('coupon_code', '').strip().upper()
    
    if not code:
        return JsonResponse({
            'success': False,
            'message': 'يرجى إدخال كود الكوبون'
        })
    
    try:
        coupon = Coupon.objects.get(code=code, is_active=True)
        
        # التحقق من صلاحية الكوبون
        if not coupon.is_valid:
            return JsonResponse({
                'success': False,
                'message': 'هذا الكوبون غير صالح أو منتهي الصلاحية'
            })
        
        # التحقق من عدد مرات استخدام الكوبون للمستخدم
        if CouponUsage.objects.filter(coupon=coupon, user=request.user).exists():
            return JsonResponse({
                'success': False,
                'message': 'لقد استخدمت هذا الكوبون من قبل'
            })
        
        # حساب إجمالي سلة التسوق
        cart_items = request.user.cartitem_set.all()
        cart_total = sum(item.get_total() for item in cart_items)
        
        # التحقق من الحد الأدنى للطلب
        if cart_total < coupon.minimum_order_value:
            return JsonResponse({
                'success': False,
                'message': f'الحد الأدنى للطلب هو {coupon.minimum_order_value} ريال'
            })
        
        # حساب قيمة الخصم
        discount_amount = coupon.calculate_discount(cart_total)
        
        # سعر الصرف الحالي للشيكل
        shekel_exchange_rate = Decimal('0.94')
        
        # تحويل القيم إلى شيكل
        cart_total_ils = round(cart_total * shekel_exchange_rate, 2)
        discount_amount_ils = round(discount_amount * shekel_exchange_rate, 2)
        final_total = cart_total - discount_amount
        final_total_ils = round(final_total * shekel_exchange_rate, 2)
        
        # حفظ معلومات الكوبون في جلسة المستخدم
        request.session['coupon_code'] = code
        request.session['coupon_discount'] = str(discount_amount)
        request.session['coupon_id'] = coupon.id
        
        # تنسيق الرسالة حسب نوع الخصم
        if coupon.discount_type == 'fixed':
            message = f'تم تطبيق خصم بقيمة {discount_amount} ريال ({discount_amount_ils} شيكل)'
        else:
            message = f'تم تطبيق خصم بنسبة {coupon.discount_value}% (توفير {discount_amount} ريال - {discount_amount_ils} شيكل)'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'discount_amount': str(discount_amount),
            'discount_amount_ils': str(discount_amount_ils),
            'cart_total': str(cart_total),
            'cart_total_ils': str(cart_total_ils),
            'final_total': str(final_total),
            'final_total_ils': str(final_total_ils)
        })
    
    except Coupon.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'كود الكوبون غير صالح'
        })
    except Exception as e:
        logger.error(f"Error applying coupon: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'حدث خطأ أثناء تطبيق الكوبون'
        })

@require_POST
@login_required
def remove_coupon(request):
    """إزالة كوبون الخصم من سلة التسوق"""
    # حذف معلومات الكوبون من جلسة المستخدم
    if 'coupon_code' in request.session:
        del request.session['coupon_code']
    if 'coupon_discount' in request.session:
        del request.session['coupon_discount']
    if 'coupon_id' in request.session:
        del request.session['coupon_id']
    
    # حساب إجمالي سلة التسوق
    cart_items = request.user.cartitem_set.all()
    cart_total = sum(item.get_total() for item in cart_items)
    
    # سعر الصرف الحالي للشيكل
    shekel_exchange_rate = Decimal('0.94')
    cart_total_ils = round(cart_total * shekel_exchange_rate, 2)
    
    return JsonResponse({
        'success': True,
        'message': 'تم إزالة الكوبون',
        'cart_total': str(cart_total),
        'cart_total_ils': str(cart_total_ils),
        'final_total': str(cart_total),
        'final_total_ils': str(cart_total_ils)
    })

@login_required
@user_passes_test(is_admin)
def admin_coupons(request):
    """عرض قائمة الكوبونات في لوحة التحكم"""
    coupons = Coupon.objects.all().order_by('-created_at')
    
    # فلترة بالبحث
    search_query = request.GET.get('search', '')
    if search_query:
        coupons = coupons.filter(code__icontains=search_query)
    
    # فلترة بالحالة
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        coupons = coupons.filter(is_active=True)
    elif status_filter == 'inactive':
        coupons = coupons.filter(is_active=False)
    elif status_filter == 'expired':
        from django.utils import timezone
        coupons = coupons.filter(valid_to__lt=timezone.now())
    
    context = {
        'coupons': coupons,
        'search_query': search_query,
        'status_filter': status_filter
    }
    
    return render(request, 'boutiqe/admin/coupons.html', context)

@login_required
@user_passes_test(is_admin)
def admin_coupon_create(request):
    """إضافة كوبون خصم جديد"""
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            coupon = form.save()
            messages.success(request, f'تم إضافة الكوبون "{coupon.code}" بنجاح')
            return redirect('boutiqe:admin_coupons')
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = CouponForm()
    
    context = {
        'form': form,
        'title': 'إضافة كوبون خصم جديد',
        'submit_text': 'إضافة'
    }
    
    return render(request, 'boutiqe/admin/coupon_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_coupon_edit(request, coupon_id):
    """تعديل كوبون خصم"""
    coupon = get_object_or_404(Coupon, id=coupon_id)
    
    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            messages.success(request, f'تم تحديث الكوبون "{coupon.code}" بنجاح')
            return redirect('boutiqe:admin_coupons')
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = CouponForm(instance=coupon)
    
    context = {
        'form': form,
        'coupon': coupon,
        'title': f'تعديل الكوبون: {coupon.code}',
        'submit_text': 'تحديث'
    }
    
    return render(request, 'boutiqe/admin/coupon_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_coupon_delete(request, coupon_id):
    """حذف كوبون خصم"""
    coupon = get_object_or_404(Coupon, id=coupon_id)
    
    if request.method == 'POST':
        coupon_code = coupon.code
        coupon.delete()
        messages.success(request, f'تم حذف الكوبون "{coupon_code}" بنجاح')
        return redirect('boutiqe:admin_coupons')
    
    context = {
        'coupon': coupon
    }
    
    return render(request, 'boutiqe/admin/coupon_delete.html', context)

@login_required
@user_passes_test(is_admin)
def admin_coupon_usage(request, coupon_id):
    """عرض استخدامات الكوبون"""
    coupon = get_object_or_404(Coupon, id=coupon_id)
    usages = CouponUsage.objects.filter(coupon=coupon).order_by('-used_at')
    
    context = {
        'coupon': coupon,
        'usages': usages,
    }
    
    return render(request, 'boutiqe/admin/coupon_usage.html', context)

@login_required
@require_POST
def submit_rating(request, product_id):
    """Submit or update a product rating and comment"""
    product = get_object_or_404(Product, id=product_id)
    
    # Get rating and comment from request
    rating = request.POST.get('rating')
    comment = request.POST.get('comment', '')
    
    if not rating or not rating.isdigit() or int(rating) < 1 or int(rating) > 5:
        messages.error(request, 'يرجى تقديم تقييم صالح من 1 إلى 5')
        return redirect('boutiqe:product_detail', slug=product.slug)
    
    # Create or update the rating
    rating_obj, created = ProductRating.objects.update_or_create(
        user=request.user,
        product=product,
        defaults={
            'rating': int(rating),
            'comment': comment
        }
    )
    
    if created:
        messages.success(request, 'شكراً لك على تقييمك للمنتج')
    else:
        messages.success(request, 'تم تحديث تقييمك بنجاح')
    
    return redirect('boutiqe:product_detail', slug=product.slug)

def placfwishliste_order(request):
    """
    إنشاء طلب جديد (باستخدام الجلسة بدلاً من قاعدة البيانات)
    """
    if request.method == 'POST':
        # الحصول على عناصر السلة للمستخدم الحالي
        cart_items = CartItem.objects.filter(user=request.user)
        
        if not cart_items.exists():
            messages.error(request, 'لا يمكن إتمام الطلب. السلة فارغة.')
            return redirect('boutiqe:cart')
        
        # حساب إجمالي الطلب
        total = sum(item.get_total() for item in cart_items)
        
        # إنشاء رقم طلب
        import datetime
        import random
        order_id = f"ORD-{datetime.datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        
        try:
            # إعداد بيانات الطلب
            order_info = {
                'order_id': order_id,
                'date': datetime.datetime.now().strftime('%d/%m/%Y'),
                'status': 'processing',
                'status_text': 'قيد التحضير',
                'items': [],
            }
            
            # إضافة عناصر الطلب
            for item in cart_items:
                product = item.product
                order_info['items'].append({
                    'name': product.name,
                    'price': float(product.discount_price or product.price),
                    'quantity': item.quantity,
                    'image': product.get_main_image().image.url if product.get_main_image() else None,
                    'size': item.size.name if hasattr(item, 'size') and item.size else None,
                    'color': item.color.name if hasattr(item, 'color') and item.color else None,
                })
            
            # إضافة المجاميع
            subtotal = float(total)
            shipping = 40.00  # قيمة افتراضية للشحن
            discount = 0.00  # قيمة افتراضية للخصم
            
            # التحقق من وجود كوبون خصم مطبق
            coupon_id = request.session.get('coupon_id', None)
            coupon_discount = request.session.get('coupon_discount', '0.00')
            
            if coupon_id:
                try:
                    coupon = Coupon.objects.get(id=coupon_id)
                    discount = float(coupon_discount)
                    
                    # تسجيل استخدام الكوبون
                    try:
                        # إنشاء سجل استخدام الكوبون - تصحيح أسماء الحقول
                        coupon_usage = CouponUsage(
                            coupon=coupon,
                            user=request.user,
                            discount_value=Decimal(coupon_discount),
                            order_value=total
                        )
                        coupon_usage.save()
                        
                        # زيادة عدد مرات استخدام الكوبون
                        coupon.current_uses += 1
                        coupon.save()
                    except Exception as e:
                        # توثيق الخطأ دون توقف العملية
                        logger.error(f"Error recording coupon usage: {str(e)}")
                    
                    # حذف معلومات الكوبون من الجلسة
                    if 'coupon_code' in request.session:
                        del request.session['coupon_code']
                    if 'coupon_discount' in request.session:
                        del request.session['coupon_discount']
                    if 'coupon_id' in request.session:
                        del request.session['coupon_id']
                except Exception as e:
                    # توثيق الخطأ دون توقف العملية
                    logger.error(f"Error applying coupon: {str(e)}")
            
            # استكمال معلومات الطلب
            order_info['shipping'] = shipping
            order_info['discount'] = discount
            order_info['subtotal'] = subtotal
            order_info['total'] = subtotal + shipping - discount
            
            # حفظ معلومات الطلب في جلسة المستخدم
            if 'orders' not in request.session:
                request.session['orders'] = []
            
            # إضافة الطلب الجديد في بداية القائمة
            orders = request.session.get('orders', [])
            orders.insert(0, order_info)
            request.session['orders'] = orders
            
            # تخزين المعرف في الجلسة لاستخدامه في صفحة الطلبات
            request.session['new_order_id'] = order_id
            
            # حذف عناصر السلة بعد إتمام الطلب
            cart_items.delete()
            
            messages.success(request, f'تم إنشاء طلبك بنجاح. رقم الطلب هو {order_id}')
            return redirect('boutiqe:orders')
        
        except Exception as e:
            # توثيق الخطأ وإعلام المستخدم
            logger.error(f"Error creating order: {str(e)}")
            messages.error(request, 'حدث خطأ أثناء إنشاء الطلب. يرجى المحاولة مرة أخرى لاحقًا.')
            return redirect('boutiqe:checkout')
    
    return redirect('boutiqe:checkout')



def cart_count(request):
    """
    API endpoint to get the current cart count for AJAX requests.
    Returns the count as JSON.
    """
    from django.http import JsonResponse
    from .utils.cart import get_cart_items_total_quantity
    
    # Get the total quantity of items in the cart
    total_quantity = get_cart_items_total_quantity(request)
    
    # Return as JSON
    return JsonResponse({'cart_count': total_quantity})
