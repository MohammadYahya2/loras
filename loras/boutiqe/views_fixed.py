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
        
        # Check if contact_info was created successfully
        if not contact_info:
            messages.error(request, 'حدث خطأ أثناء حفظ معلومات الاتصال')
            return redirect('boutiqe:checkout')
            
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