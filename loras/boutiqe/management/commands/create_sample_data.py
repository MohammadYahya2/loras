import random
import os
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from django.conf import settings
from boutiqe.models import (
    Category, Color, Size, Product, ProductImage, 
    TrendingCollection, Discount, ProductVariation, Profile
)

class Command(BaseCommand):
    help = 'يقوم بإنشاء بيانات نموذجية للموقع'

    def handle(self, *args, **kwargs):
        self.stdout.write('جاري إنشاء البيانات النموذجية...')
        
        # إنشاء مجلدات الصور إذا لم تكن موجودة
        self.create_media_folders()
        
        # حذف البيانات الموجودة (اختياري)
        self.clear_data()
        
        # إنشاء البيانات
        self.create_users()
        self.create_categories()
        self.create_colors()
        self.create_sizes()
        self.create_products()
        self.create_trending_collections()
        self.create_discounts()
        
        self.stdout.write(self.style.SUCCESS('تم إنشاء البيانات النموذجية بنجاح!'))
    
    def create_media_folders(self):
        """إنشاء مجلدات الوسائط إذا لم تكن موجودة"""
        media_folders = [
            os.path.join(settings.MEDIA_ROOT, 'products'),
            os.path.join(settings.MEDIA_ROOT, 'categories'),
            os.path.join(settings.MEDIA_ROOT, 'collections'),
            os.path.join(settings.MEDIA_ROOT, 'discounts'),
            os.path.join(settings.MEDIA_ROOT, 'profile_images'),
        ]
        
        for folder in media_folders:
            if not os.path.exists(folder):
                os.makedirs(folder)
                self.stdout.write(f'تم إنشاء المجلد: {folder}')
    
    def create_placeholder_image(self, folder, name, color='#cccccc'):
        """إنشاء صورة وهمية باستخدام لون محدد والاحتفاظ بمسارها"""
        from PIL import Image, ImageDraw, ImageFont
        
        # إنشاء مسار المجلد إذا لم يكن موجوداً
        folder_path = os.path.join(settings.MEDIA_ROOT, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        # إنشاء صورة بحجم 600x600 بلون محدد
        img = Image.new('RGB', (600, 600), color=color)
        d = ImageDraw.Draw(img)
        
        # محاولة تحميل الخط، وإذا فشل استخدم الخط الافتراضي
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except IOError:
            font = ImageFont.load_default()
        
        # إضافة نص للصورة
        text = name
        
        # التعامل مع خصائص النص حسب إصدار PIL
        if hasattr(d, 'textsize'):
            textwidth, textheight = d.textsize(text, font=font)
        else:
            # استخدام طريقة بديلة للإصدارات الأحدث من PIL
            try:
                left, top, right, bottom = d.textbbox((0, 0), text, font=font)
                textwidth, textheight = right - left, bottom - top
            except AttributeError:
                # إذا فشلت كل الطرق، استخدم قيم تقريبية
                textwidth, textheight = 300, 50
        
        x = (600 - textwidth) / 2
        y = (600 - textheight) / 2
        d.text((x, y), text, fill="white", font=font)
        
        # إنشاء اسم ملف آمن
        safe_name = slugify(name) if slugify(name) else f"image-{random.randint(1000, 9999)}"
        
        # حفظ الصورة بامتداد واضح
        file_path = os.path.join(settings.MEDIA_ROOT, folder, f"{safe_name}.jpg")
        img.save(file_path, format='JPEG')
        
        # إرجاع المسار النسبي للاستخدام في نموذج Django
        return f"{folder}/{safe_name}.jpg"
    
    # جدول تحويل الأحرف العربية إلى اللاتينية
    def transliterate_arabic(self, arabic_text):
        transliteration_dict = {
            'ا': 'a', 'أ': 'a', 'إ': 'e', 'آ': 'a',
            'ب': 'b', 'ت': 't', 'ث': 'th',
            'ج': 'j', 'ح': 'h', 'خ': 'kh',
            'د': 'd', 'ذ': 'th',
            'ر': 'r', 'ز': 'z',
            'س': 's', 'ش': 'sh',
            'ص': 's', 'ض': 'd',
            'ط': 't', 'ظ': 'z',
            'ع': 'a', 'غ': 'gh',
            'ف': 'f', 'ق': 'q',
            'ك': 'k', 'ل': 'l',
            'م': 'm', 'ن': 'n',
            'ه': 'h', 'ة': 'h',
            'و': 'w', 'ي': 'y', 'ى': 'a',
            'ئ': 'e', 'ء': 'a',
            ' ': '-', '_': '-'
        }
        
        result = ''
        for char in arabic_text:
            if char in transliteration_dict:
                result += transliteration_dict[char]
            elif char.isalnum() or char in '-_':
                result += char
            else:
                result += '-'
        
        # تجنب التكرار المتتالي للشرطات
        while '--' in result:
            result = result.replace('--', '-')
        
        # إزالة الشرطات من البداية والنهاية
        result = result.strip('-')
        
        return result

    def clear_data(self):
        self.stdout.write('جاري حذف البيانات الموجودة...')
        # لا نحذف حساب المشرف
        User.objects.exclude(is_superuser=True).delete()
        ProductImage.objects.all().delete()
        ProductVariation.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        Color.objects.all().delete()
        Size.objects.all().delete()
        TrendingCollection.objects.all().delete()
        Discount.objects.all().delete()
        self.stdout.write('تم حذف البيانات القديمة')
    
    def create_users(self):
        # إنشاء 5 مستخدمين
        for i in range(1, 6):
            username = f'user{i}'
            email = f'user{i}@example.com'
            
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='password123',
                    first_name=f'مستخدم{i}',
                    last_name=f'عائلة{i}'
                )
                
                # إنشاء ملف شخصي للمستخدم
                Profile.objects.update_or_create(
                    user=user,
                    defaults={
                        'phone': f'05{random.randint(10000000, 99999999)}',
                        'address': f'عنوان المستخدم رقم {i}',
                        'city': random.choice(['الرياض', 'جدة', 'الدمام', 'مكة', 'المدينة']),
                        'country': 'المملكة العربية السعودية'
                    }
                )
                self.stdout.write(f'تم إنشاء المستخدم: {username}')
    
    def create_categories(self):
        # إنشاء فئات المنتجات
        categories = [
            {'name': 'فساتين', 'slug': 'dresses', 'color': '#FF6B6B'},
            {'name': 'بلوزات', 'slug': 'blouses', 'color': '#4ECDC4'},
            {'name': 'تنانير', 'slug': 'skirts', 'color': '#FFD166'},
            {'name': 'بناطيل', 'slug': 'pants', 'color': '#06D6A0'},
            {'name': 'عبايات', 'slug': 'abayas', 'color': '#118AB2'},
            {'name': 'إكسسوارات', 'slug': 'accessories', 'color': '#073B4C'},
            {'name': 'أحذية', 'slug': 'shoes', 'color': '#EF476F'},
            {'name': 'حقائب', 'slug': 'bags', 'color': '#6D597A'}
        ]
        
        for cat in categories:
            # إنشاء صورة وهمية للفئة
            image_path = self.create_placeholder_image('categories', cat['name'], cat['color'])
            
            Category.objects.update_or_create(
                slug=cat['slug'],
                defaults={
                    'name': cat['name'],
                    'image': image_path
                }
            )
            self.stdout.write(f'تم إنشاء الفئة: {cat["name"]}')
    
    def create_colors(self):
        # إنشاء الألوان
        colors = [
            {'name': 'أسود', 'code': '#000000'},
            {'name': 'أبيض', 'code': '#FFFFFF'},
            {'name': 'أحمر', 'code': '#FF0000'},
            {'name': 'أزرق', 'code': '#0000FF'},
            {'name': 'أخضر', 'code': '#00FF00'},
            {'name': 'أصفر', 'code': '#FFFF00'},
            {'name': 'وردي', 'code': '#FFC0CB'},
            {'name': 'بنفسجي', 'code': '#800080'},
            {'name': 'رمادي', 'code': '#808080'},
            {'name': 'بني', 'code': '#A52A2A'}
        ]
        
        for color in colors:
            Color.objects.update_or_create(
                name=color['name'],
                defaults={
                    'code': color['code']
                }
            )
            self.stdout.write(f'تم إنشاء اللون: {color["name"]}')
    
    def create_sizes(self):
        # إنشاء المقاسات
        sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL', '38', '39', '40', '41', '42']
        
        for size in sizes:
            Size.objects.update_or_create(name=size)
            self.stdout.write(f'تم إنشاء المقاس: {size}')
    
    def create_products(self):
        # استيراد الفئات والألوان والمقاسات
        categories = list(Category.objects.all())
        colors = list(Color.objects.all())
        sizes = list(Size.objects.all())
        
        # قائمة المنتجات النموذجية
        products_data = [
            {
                'name': 'فستان سهرة أنيق',
                'description': 'فستان سهرة أنيق مناسب للمناسبات الخاصة، مصنوع من أجود أنواع الأقمشة بتصميم عصري وراقي.',
                'category': 'فساتين',
                'price': 899.99,
                'discount_price': 699.99,
                'is_featured': True,
                'is_new': True,
                'color': '#FF6B6B'
            },
            {
                'name': 'بلوزة كاجوال',
                'description': 'بلوزة كاجوال مناسبة للاستخدام اليومي، مريحة وعملية بتصميم بسيط وأنيق.',
                'category': 'بلوزات',
                'price': 199.99,
                'discount_price': None,
                'is_featured': True,
                'is_new': False,
                'color': '#4ECDC4'
            },
            {
                'name': 'تنورة قصيرة',
                'description': 'تنورة قصيرة بتصميم عصري، مناسبة للإطلالات الكاجوال والرسمية.',
                'category': 'تنانير',
                'price': 249.99,
                'discount_price': 199.99,
                'is_featured': False,
                'is_new': True,
                'color': '#FFD166'
            },
            {
                'name': 'بنطلون جينز',
                'description': 'بنطلون جينز عالي الجودة، مريح وعملي مناسب للاستخدام اليومي.',
                'category': 'بناطيل',
                'price': 299.99,
                'discount_price': None,
                'is_featured': False,
                'is_new': False,
                'color': '#06D6A0'
            },
            {
                'name': 'عباية سوداء فاخرة',
                'description': 'عباية سوداء فاخرة بتطريز مميز، مصنوعة من أجود أنواع الأقمشة.',
                'category': 'عبايات',
                'price': 750.00,
                'discount_price': 650.00,
                'is_featured': True,
                'is_new': True,
                'color': '#118AB2'
            },
            {
                'name': 'عقد ذهبي',
                'description': 'عقد ذهبي فاخر بتصميم أنيق، مناسب للمناسبات الخاصة.',
                'category': 'إكسسوارات',
                'price': 1200.00,
                'discount_price': None,
                'is_featured': True,
                'is_new': False,
                'color': '#073B4C'
            },
            {
                'name': 'حذاء كعب عالي',
                'description': 'حذاء بكعب عالي أنيق، مريح ومناسب للمناسبات الرسمية.',
                'category': 'أحذية',
                'price': 450.00,
                'discount_price': 399.99,
                'is_featured': False,
                'is_new': True,
                'color': '#EF476F'
            },
            {
                'name': 'حقيبة يد فاخرة',
                'description': 'حقيبة يد فاخرة بتصميم عصري، مناسبة للاستخدام اليومي والمناسبات.',
                'category': 'حقائب',
                'price': 599.99,
                'discount_price': 499.99,
                'is_featured': True,
                'is_new': True,
                'color': '#6D597A'
            },
            {
                'name': 'فستان زفاف أبيض',
                'description': 'فستان زفاف أبيض فاخر بتصميم كلاسيكي، مناسب ليوم الزفاف المميز.',
                'category': 'فساتين',
                'price': 3500.00,
                'discount_price': 2999.99,
                'is_featured': True,
                'is_new': True,
                'color': '#FF6B6B'
            },
            {
                'name': 'بلوزة رسمية',
                'description': 'بلوزة رسمية أنيقة مناسبة للعمل والمناسبات الرسمية.',
                'category': 'بلوزات',
                'price': 249.99,
                'discount_price': None,
                'is_featured': False,
                'is_new': False,
                'color': '#4ECDC4'
            },
            {
                'name': 'تنورة طويلة',
                'description': 'تنورة طويلة بتصميم أنيق، مناسبة للإطلالات الرسمية والكاجوال.',
                'category': 'تنانير',
                'price': 299.99,
                'discount_price': 249.99,
                'is_featured': True,
                'is_new': False,
                'color': '#FFD166'
            },
            {
                'name': 'بنطلون قماش',
                'description': 'بنطلون قماش أنيق مناسب للعمل والمناسبات الرسمية.',
                'category': 'بناطيل',
                'price': 349.99,
                'discount_price': 299.99,
                'is_featured': False,
                'is_new': True,
                'color': '#06D6A0'
            },
            {
                'name': 'عباية مطرزة',
                'description': 'عباية مطرزة بتصميم عصري، مناسبة للمناسبات الخاصة.',
                'category': 'عبايات',
                'price': 850.00,
                'discount_price': None,
                'is_featured': True,
                'is_new': True,
                'color': '#118AB2'
            },
            {
                'name': 'أقراط فضية',
                'description': 'أقراط فضية بتصميم أنيق، مناسبة للاستخدام اليومي والمناسبات.',
                'category': 'إكسسوارات',
                'price': 199.99,
                'discount_price': 149.99,
                'is_featured': False,
                'is_new': True,
                'color': '#073B4C'
            },
            {
                'name': 'حذاء رياضي',
                'description': 'حذاء رياضي مريح وعملي، مناسب للاستخدام اليومي والرياضة.',
                'category': 'أحذية',
                'price': 299.99,
                'discount_price': 249.99,
                'is_featured': True,
                'is_new': False,
                'color': '#EF476F'
            },
            {
                'name': 'حقيبة ظهر',
                'description': 'حقيبة ظهر عملية ومريحة، مناسبة للاستخدام اليومي والرحلات.',
                'category': 'حقائب',
                'price': 199.99,
                'discount_price': None,
                'is_featured': False,
                'is_new': True,
                'color': '#6D597A'
            },
            {
                'name': 'فستان صيفي',
                'description': 'فستان صيفي خفيف وأنيق، مناسب للإطلالات الصيفية.',
                'category': 'فساتين',
                'price': 349.99,
                'discount_price': 299.99,
                'is_featured': True,
                'is_new': True,
                'color': '#FF6B6B'
            },
            {
                'name': 'بلوزة مطرزة',
                'description': 'بلوزة مطرزة بتصميم تقليدي، مناسبة للمناسبات الخاصة.',
                'category': 'بلوزات',
                'price': 299.99,
                'discount_price': 249.99,
                'is_featured': True,
                'is_new': False,
                'color': '#4ECDC4'
            },
            {
                'name': 'تنورة جينز',
                'description': 'تنورة جينز بتصميم عصري، مناسبة للإطلالات الكاجوال.',
                'category': 'تنانير',
                'price': 199.99,
                'discount_price': None,
                'is_featured': False,
                'is_new': True,
                'color': '#FFD166'
            },
            {
                'name': 'بنطلون واسع',
                'description': 'بنطلون واسع بتصميم عصري، مريح ومناسب للإطلالات الكاجوال.',
                'category': 'بناطيل',
                'price': 249.99,
                'discount_price': 199.99,
                'is_featured': True,
                'is_new': True,
                'color': '#06D6A0'
            },
            {
                'name': 'عباية كاجوال',
                'description': 'عباية كاجوال مناسبة للاستخدام اليومي، مريحة وعملية.',
                'category': 'عبايات',
                'price': 550.00,
                'discount_price': 499.99,
                'is_featured': False,
                'is_new': False,
                'color': '#118AB2'
            },
            {
                'name': 'سوار ذهبي',
                'description': 'سوار ذهبي بتصميم أنيق، مناسب للمناسبات الخاصة.',
                'category': 'إكسسوارات',
                'price': 850.00,
                'discount_price': 799.99,
                'is_featured': True,
                'is_new': True,
                'color': '#073B4C'
            },
            {
                'name': 'صندل صيفي',
                'description': 'صندل صيفي مريح وأنيق، مناسب للإطلالات الصيفية.',
                'category': 'أحذية',
                'price': 199.99,
                'discount_price': None,
                'is_featured': True,
                'is_new': True,
                'color': '#EF476F'
            },
            {
                'name': 'حقيبة سفر',
                'description': 'حقيبة سفر عملية وواسعة، مناسبة للرحلات والسفر.',
                'category': 'حقائب',
                'price': 699.99,
                'discount_price': 599.99,
                'is_featured': False,
                'is_new': False,
                'color': '#6D597A'
            }
        ]
        
        # إنشاء المنتجات
        for p_data in products_data:
            # البحث عن الفئة
            category = next((c for c in categories if c.name == p_data['category']), None)
            if not category:
                self.stdout.write(self.style.WARNING(f'لم يتم العثور على الفئة: {p_data["category"]}'))
                continue
            
            # إنشاء اسم slug من اسم المنتج (استخدام اللاتينية للـ slug)
            arabic_name = p_data['name']
            latin_slug = self.transliterate_arabic(arabic_name)
            
            # استخدام Django slugify لضمان سلامة الـ slug
            slug = slugify(latin_slug)
            
            product_sku = f'SKU-{random.randint(10000, 99999)}'
            
            # إنشاء المنتج
            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': p_data['name'],
                    'description': p_data['description'],
                    'price': p_data['price'],
                    'discount_price': p_data['discount_price'],
                    'category': category,
                    'in_stock': True,
                    'is_featured': p_data['is_featured'],
                    'is_new': p_data['is_new'],
                    'is_sale': p_data['discount_price'] is not None,
                    'sku': product_sku,
                    'stock_quantity': random.randint(10, 100)
                }
            )
            
            # إضافة ألوان ومقاسات عشوائية للمنتج
            product_colors = random.sample(colors, min(3, len(colors)))
            product_sizes = random.sample(sizes, min(4, len(sizes)))
            
            product.colors.set(product_colors)
            product.sizes.set(product_sizes)
            
            # إنشاء متغيرات المنتج (ProductVariation)
            for color in product_colors:
                for size in product_sizes:
                    ProductVariation.objects.update_or_create(
                        product=product,
                        color=color,
                        size=size,
                        defaults={
                            'stock_count': random.randint(5, 30)
                        }
                    )
            
            # إنشاء صورة للمنتج
            product_color = p_data.get('color', '#cccccc')
            image_path = self.create_placeholder_image('products', product.name, product_color)
            
            ProductImage.objects.update_or_create(
                product=product,
                is_main=True,
                defaults={
                    'image': image_path
                }
            )
            
            # إنشاء صور إضافية للمنتج (2-3 صور)
            for i in range(random.randint(1, 2)):
                alt_color = f"#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}"
                alt_image_path = self.create_placeholder_image('products', f"{product.name}-{i+1}", alt_color)
                
                ProductImage.objects.create(
                    product=product,
                    is_main=False,
                    image=alt_image_path
                )
            
            self.stdout.write(f'تم إنشاء المنتج: {product.name} (slug: {slug})')
    
    def create_trending_collections(self):
        # إنشاء المجموعات الرائجة
        collections_data = [
            {
                'name': 'مجموعة الصيف',
                'description': 'أحدث تشكيلة صيفية بتصاميم عصرية وألوان زاهية',
                'is_active': True,
                'color': '#FFD166'
            },
            {
                'name': 'مجموعة العيد',
                'description': 'تشكيلة خاصة لمناسبة العيد بتصاميم فاخرة',
                'is_active': True,
                'color': '#06D6A0'
            },
            {
                'name': 'مجموعة السهرات',
                'description': 'تشكيلة مميزة من أزياء السهرات والمناسبات الخاصة',
                'is_active': True,
                'color': '#118AB2'
            }
        ]
        
        products = list(Product.objects.all())
        
        for c_data in collections_data:
            # إنشاء slug من اسم المجموعة (استخدام اللاتينية للـ slug)
            arabic_name = c_data['name']
            latin_slug = self.transliterate_arabic(arabic_name)
            slug = slugify(latin_slug)
            
            # إنشاء صورة للمجموعة
            image_path = self.create_placeholder_image('collections', c_data['name'], c_data['color'])
            
            # إنشاء المجموعة
            collection, created = TrendingCollection.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': c_data['name'],
                    'description': c_data['description'],
                    'is_active': c_data['is_active'],
                    'image': image_path
                }
            )
            
            # إضافة منتجات عشوائية للمجموعة
            collection_products = random.sample(products, min(8, len(products)))
            collection.products.set(collection_products)
            
            self.stdout.write(f'تم إنشاء المجموعة: {collection.name} (slug: {slug})')
    
    def create_discounts(self):
        # إنشاء خصومات متنوعة
        discounts_data = [
            {
                'name': 'خصم الصيف',
                'description': 'خصم 20% على جميع المنتجات الصيفية',
                'discount_percent': 20,
                'is_active': True,
            },
            {
                'name': 'خصم العيد',
                'description': 'خصم 15% على مجموعة العيد',
                'discount_percent': 15,
                'is_active': True,
            },
            {
                'name': 'خصم الحقائب',
                'description': 'خصم 10% على جميع الحقائب',
                'discount_percent': 10,
                'is_active': False,
            }
        ]
        
        categories = list(Category.objects.all())
        products = list(Product.objects.all())
        
        for d_data in discounts_data:
            # تواريخ البداية والنهاية
            start_date = timezone.now() - timedelta(days=random.randint(1, 5))
            end_date = timezone.now() + timedelta(days=random.randint(10, 30))
            
            # إنشاء الخصم
            discount, created = Discount.objects.update_or_create(
                name=d_data['name'],
                defaults={
                    'description': d_data['description'],
                    'discount_percent': d_data['discount_percent'],
                    'is_active': d_data['is_active'],
                    'start_date': start_date,
                    'end_date': end_date,
                }
            )
            
            # إضافة منتجات وفئات عشوائية للخصم
            discount_products = random.sample(products, min(6, len(products)))
            discount_categories = random.sample(categories, min(2, len(categories)))
            
            discount.products.set(discount_products)
            discount.categories.set(discount_categories)
            
            self.stdout.write(f'تم إنشاء الخصم: {discount.name}') 