@login_required
def orders_view(request):
    """
    عرض صفحة طلبات المستخدم (استخدام بيانات وهمية مؤقتاً)
    """
    # عرض طلبات وهمية بدلاً من الوصول إلى قاعدة البيانات
    orders = [
        {
            'id': 'ORD-2023-8745',
            'date': '12/08/2023',
            'status': 'pending',
            'status_text': 'بانتظار الدفع',
            'items': [
                {'name': 'فستان سهرة مطرز باللون الأسود', 'price': 730, 'quantity': 1, 'image': 'images/product-1.jpg', 'size': 'M', 'color': 'أسود'},
                {'name': 'حقيبة يد نسائية فاخرة', 'price': 450, 'quantity': 1, 'image': 'images/product-2.jpg', 'color': 'بني'}
            ],
            'shipping': 50,
            'discount': 100,
            'subtotal': 1180,
            'total': 1130
        },
        {
            'id': 'ORD-2023-7652',
            'date': '05/08/2023',
            'status': 'processing',
            'status_text': 'قيد التحضير',
            'items': [
                {'name': 'بلوزة كاجوال بأكمام طويلة', 'price': 250, 'quantity': 2, 'image': 'images/product-3.jpg', 'size': 'L', 'color': 'أزرق'}
            ],
            'shipping': 35,
            'discount': 0,
            'subtotal': 500,
            'total': 535
        },
        {
            'id': 'ORD-2023-6574',
            'date': '25/07/2023',
            'status': 'delivered',
            'status_text': 'تم التوصيل',
            'items': [
                {'name': 'عباية مطرزة فاخرة', 'price': 850, 'quantity': 1, 'image': 'images/product-4.jpg', 'size': 'XL', 'color': 'أسود'}
            ],
            'shipping': 50,
            'discount': 0,
            'subtotal': 850,
            'total': 900
        }
    ]
    
    # فلترة الطلبات حسب الحالة إذا تم تحديد فلتر
    status_filter = request.GET.get('status')
    if status_filter:
        filtered_orders = [order for order in orders if order['status'] == status_filter]
    else:
        filtered_orders = orders
    
    # استخدام العملة المفضلة (شيكل أو ريال)
    selected_currency = request.GET.get('currency', 'SAR')
    
    # سعر الصرف الحالي للشيكل (1 ريال = X شيكل)
    shekel_exchange_rate = 0.94
    
    # تحويل الأسعار إلى الشيكل إذا تم اختيار الشيكل كعملة
    if selected_currency == 'ILS':
        for order in filtered_orders:
            order['shipping'] = round(order['shipping'] * shekel_exchange_rate, 2)
            order['discount'] = round(order['discount'] * shekel_exchange_rate, 2)
            order['subtotal'] = round(order['subtotal'] * shekel_exchange_rate, 2)
            order['total'] = round(order['total'] * shekel_exchange_rate, 2)
            
            for item in order['items']:
                item['price'] = round(item['price'] * shekel_exchange_rate, 2)
    
    # إعداد إحصائيات الطلبات
    order_stats = {
        'all': len(orders),
        'pending': len([order for order in orders if order['status'] == 'pending']),
        'processing': len([order for order in orders if order['status'] == 'processing']),
        'shipped': len([order for order in orders if order['status'] == 'shipped']), 
        'delivered': len([order for order in orders if order['status'] == 'delivered']),
        'cancelled': len([order for order in orders if order['status'] == 'cancelled']),
    }
    
    context = {
        'orders': filtered_orders,
        'order_stats': order_stats,
        'selected_currency': selected_currency,
        'shekel_exchange_rate': shekel_exchange_rate,
    }
    return render(request, 'boutiqe/orders.html', context)

def place_order(request):
    # ... existing code ...
    try:
        # ... existing code ...
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

def serve_media(request, path):
    """
    Serve media files manually when MEDIA_URL doesn't work properly
    """
    import os, io
    from django.conf import settings
    from django.http import FileResponse, Http404
    from PIL import Image, ImageDraw, ImageFont
    
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    
    # If the file doesn't exist, create a dynamic placeholder
    if not os.path.exists(file_path):
        # Determine what type of placeholder to create based on the path
        parts = path.split('/')
        placeholder_type = "صورة غير متوفرة"
        bg_color = (240, 240, 240)  # light gray
        text_color = (100, 100, 100)  # dark gray
        
        if len(parts) > 1:
            folder = parts[0]
            if folder == 'categories':
                placeholder_type = "فئة غير متوفرة"
                bg_color = (255, 240, 240)  # light red
                text_color = (220, 100, 100)  # dark red
            elif folder == 'products':
                placeholder_type = "منتج غير متوفر"
                bg_color = (240, 255, 240)  # light green
                text_color = (100, 200, 100)  # dark green
        
        # Create a simple image with text
        img = Image.new('RGB', (400, 300), color=bg_color)
        d = ImageDraw.Draw(img)
        # Use a simple font since custom fonts might not be available
        d.text((150, 150), placeholder_type, fill=text_color)
        
        # Convert image to a file-like object
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        
        # Return the image
        return FileResponse(img_io, content_type='image/jpeg')
    
    return FileResponse(open(file_path, 'rb'))

def checkout(request):
    # ... existing code ...
    
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
            
        # ... rest of the code 

def save_contact_info(request, name, phone, address, city='', note=''):
    """
    حفظ معلومات الاتصال للمستخدم أو الزائر وإرجاع كائن ContactInfo
    """
    from .models import ContactInfo
    
    # إنشاء كائن ContactInfo جديد
    if request.user.is_authenticated:
        # للمستخدمين المسجلين
        contact_info = ContactInfo.objects.create(
            user=request.user,
            name=name,
            phone=phone,
            address=address,
            city=city,
            note=note,
            is_default=True
        )
    else:
        # للزوار
        if not request.session.session_key:
            request.session.create()
            
        contact_info = ContactInfo.objects.create(
            session_key=request.session.session_key,
            name=name,
            phone=phone,
            address=address,
            city=city,
            note=note,
            is_default=True
        )
    
    # حفظ في الجلسة أيضًا (للتوافق مع الكود القديم)
    contact_info_dict = {
        'name': name,
        'phone': phone,
        'address': address,
        'city': city,
        'note': note
    }
    request.session['contact_info'] = contact_info_dict
    
    return contact_info 