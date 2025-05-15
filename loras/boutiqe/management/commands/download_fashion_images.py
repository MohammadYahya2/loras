import os
import random
import requests
import time
import base64
from io import BytesIO
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.conf import settings
from PIL import Image
from boutiqe.models import Product, ProductImage, Category, TrendingCollection, Discount

class Command(BaseCommand):
    help = 'تنزيل صور ملابس حقيقية من مصادر محددة وتعيينها للمنتجات والفئات'

    # قائمة روابط لصور في مختلف فئات الملابس
    FASHION_IMAGES = {
        'فساتين': [
            'https://images.pexels.com/photos/1755428/pexels-photo-1755428.jpeg',
            'https://images.pexels.com/photos/985635/pexels-photo-985635.jpeg',
            'https://images.pexels.com/photos/1462637/pexels-photo-1462637.jpeg',
            'https://images.pexels.com/photos/291759/pexels-photo-291759.jpeg',
        ],
        'بلوزات': [
            'https://images.pexels.com/photos/7679454/pexels-photo-7679454.jpeg',
            'https://images.pexels.com/photos/10054513/pexels-photo-10054513.jpeg',
            'https://images.pexels.com/photos/6311475/pexels-photo-6311475.jpeg',
        ],
        'تنانير': [
            'https://images.pexels.com/photos/6046226/pexels-photo-6046226.jpeg',
            'https://images.pexels.com/photos/6311650/pexels-photo-6311650.jpeg',
            'https://images.pexels.com/photos/7290864/pexels-photo-7290864.jpeg',
        ],
        'بناطيل': [
            'https://images.pexels.com/photos/4937229/pexels-photo-4937229.jpeg',
            'https://images.pexels.com/photos/3962294/pexels-photo-3962294.jpeg',
            'https://images.pexels.com/photos/2343661/pexels-photo-2343661.jpeg',
        ],
        'عبايات': [
            'https://images.pexels.com/photos/6103188/pexels-photo-6103188.jpeg',
            'https://images.pexels.com/photos/6749910/pexels-photo-6749910.jpeg',
            'https://images.pexels.com/photos/7139188/pexels-photo-7139188.jpeg',
        ],
        'إكسسوارات': [
            'https://images.pexels.com/photos/1191531/pexels-photo-1191531.jpeg',
            'https://images.pexels.com/photos/1534293/pexels-photo-1534293.jpeg',
            'https://images.pexels.com/photos/2735970/pexels-photo-2735970.jpeg',
        ],
        'أحذية': [
            'https://images.pexels.com/photos/2300334/pexels-photo-2300334.jpeg',
            'https://images.pexels.com/photos/134064/pexels-photo-134064.jpeg',
            'https://images.pexels.com/photos/1478442/pexels-photo-1478442.jpeg',
        ],
        'حقائب': [
            'https://images.pexels.com/photos/1152077/pexels-photo-1152077.jpeg',
            'https://images.pexels.com/photos/2081199/pexels-photo-2081199.jpeg',
            'https://images.pexels.com/photos/1214212/pexels-photo-1214212.jpeg',
        ],
    }
    
    # صور محددة للمنتجات
    PRODUCT_IMAGES = {
        'فستان سهرة أنيق': [
            'https://images.pexels.com/photos/1755428/pexels-photo-1755428.jpeg',
            'https://images.pexels.com/photos/1537671/pexels-photo-1537671.jpeg',
        ],
        'فستان زفاف أبيض': [
            'https://images.pexels.com/photos/291759/pexels-photo-291759.jpeg',
            'https://images.pexels.com/photos/997525/pexels-photo-997525.jpeg',
        ],
        'بلوزة كاجوال': [
            'https://images.pexels.com/photos/6311475/pexels-photo-6311475.jpeg',
            'https://images.pexels.com/photos/6311650/pexels-photo-6311650.jpeg',
        ],
        'عباية سوداء فاخرة': [
            'https://images.pexels.com/photos/6103188/pexels-photo-6103188.jpeg',
            'https://images.pexels.com/photos/6749910/pexels-photo-6749910.jpeg',
        ],
        'حذاء كعب عالي': [
            'https://images.pexels.com/photos/336372/pexels-photo-336372.jpeg',
            'https://images.pexels.com/photos/2300334/pexels-photo-2300334.jpeg',
        ],
        'حقيبة يد فاخرة': [
            'https://images.pexels.com/photos/1152077/pexels-photo-1152077.jpeg',
            'https://images.pexels.com/photos/2081199/pexels-photo-2081199.jpeg',
        ],
    }
    
    # صور للمجموعات
    COLLECTION_IMAGES = {
        'مجموعة الصيف': [
            'https://images.pexels.com/photos/5886041/pexels-photo-5886041.jpeg',
            'https://images.pexels.com/photos/6776717/pexels-photo-6776717.jpeg',
        ],
        'مجموعة العيد': [
            'https://images.pexels.com/photos/6103188/pexels-photo-6103188.jpeg',
            'https://images.pexels.com/photos/6749910/pexels-photo-6749910.jpeg',
        ],
        'مجموعة السهرات': [
            'https://images.pexels.com/photos/1755428/pexels-photo-1755428.jpeg',
            'https://images.pexels.com/photos/985635/pexels-photo-985635.jpeg',
        ],
    }
    
    # صور للخصومات
    DISCOUNT_IMAGES = [
        'https://images.pexels.com/photos/3951880/pexels-photo-3951880.jpeg',
        'https://images.pexels.com/photos/5872363/pexels-photo-5872363.jpeg',
        'https://images.pexels.com/photos/1078973/pexels-photo-1078973.jpeg',
    ]
    
    def handle(self, *args, **kwargs):
        self.stdout.write('بدء تنزيل الصور الحقيقية للمنتجات والفئات...')
        
        # تأكد من وجود المجلدات المطلوبة
        self.create_media_folders()
        
        # تحديث صور الفئات
        self.update_category_images()
        
        # تحديث صور المنتجات
        self.update_product_images()
        
        # تحديث صور المجموعات والخصومات
        self.update_collection_images()
        self.update_discount_images()
        
        self.stdout.write(self.style.SUCCESS('تم تنزيل وتعيين الصور بنجاح!'))
    
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
    
    def download_image(self, url, image_name):
        """تنزيل صورة من URL"""
        try:
            self.stdout.write(f'تنزيل صورة من {url}')
            response = requests.get(url, allow_redirects=True, timeout=10)
            if response.status_code == 200:
                return response.content
            else:
                self.stdout.write(self.style.ERROR(f'فشل في تنزيل الصورة: {response.status_code}'))
                return None
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'خطأ أثناء تنزيل الصورة: {str(e)}'))
            return None
    
    def process_and_save_image(self, image_data, folder, name, max_size=(800, 800)):
        """معالجة وحفظ الصورة المنزلة"""
        if not image_data:
            return None
        
        try:
            # إنشاء صورة من البيانات المنزلة
            img = Image.open(BytesIO(image_data))
            
            # تغيير حجم الصورة إذا كانت أكبر من الحجم المطلوب
            if max(img.size) > max(max_size):
                img.thumbnail(max_size, Image.LANCZOS)
            
            # إنشاء اسم ملف آمن
            safe_name = slugify(name) if slugify(name) else f"image-{random.randint(1000, 9999)}"
            file_path = os.path.join(folder, f"{safe_name}-{random.randint(1000, 9999)}.jpg")
            
            # حفظ الصورة محلياً
            full_path = os.path.join(settings.MEDIA_ROOT, file_path)
            
            # التأكد من وجود المجلد
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # حفظ الصورة
            img.save(full_path, format='JPEG', quality=85)
            
            self.stdout.write(self.style.SUCCESS(f'تم حفظ الصورة بنجاح: {file_path}'))
            return file_path
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'خطأ أثناء معالجة الصورة: {str(e)}'))
            return None
    
    def update_category_images(self):
        """تحديث صور الفئات"""
        categories = Category.objects.all()
        self.stdout.write(f'تحديث صور لـ {categories.count()} فئة...')
        
        for category in categories:
            # الحصول على قائمة الصور المناسبة للفئة
            image_urls = self.FASHION_IMAGES.get(category.name)
            
            if not image_urls:
                self.stdout.write(self.style.WARNING(f'لم يتم العثور على صور لفئة: {category.name}'))
                continue
            
            image_url = random.choice(image_urls)
            image_data = self.download_image(image_url, category.name)
            
            if image_data:
                file_path = self.process_and_save_image(image_data, 'categories', category.name)
                if file_path:
                    category.image = file_path
                    category.save()
                    self.stdout.write(self.style.SUCCESS(f'تم تحديث صورة الفئة: {category.name}'))
    
    def update_product_images(self):
        """تحديث صور المنتجات"""
        products = Product.objects.all()
        self.stdout.write(f'تحديث صور لـ {products.count()} منتج...')
        
        for product in products:
            # حذف الصور القديمة
            ProductImage.objects.filter(product=product).delete()
            
            # اختيار الصور المناسبة
            if product.name in self.PRODUCT_IMAGES:
                image_urls = self.PRODUCT_IMAGES[product.name]
            else:
                # إذا لم يكن هناك صور محددة للمنتج، استخدم صور الفئة
                image_urls = self.FASHION_IMAGES.get(product.category.name, [])
            
            if not image_urls:
                self.stdout.write(self.style.WARNING(f'لم يتم العثور على صور للمنتج: {product.name}'))
                continue
            
            # تنزيل الصورة الرئيسية
            main_url = image_urls[0] if image_urls else None
            if main_url:
                image_data = self.download_image(main_url, product.name)
                
                if image_data:
                    file_path = self.process_and_save_image(image_data, 'products', product.name)
                    if file_path:
                        ProductImage.objects.create(
                            product=product,
                            image=file_path,
                            is_main=True
                        )
                        self.stdout.write(self.style.SUCCESS(f'تم تحديث الصورة الرئيسية للمنتج: {product.name}'))
            
            # تنزيل صور إضافية
            for i, url in enumerate(image_urls[1:]):
                image_data = self.download_image(url, f"{product.name}-{i+1}")
                
                if image_data:
                    file_path = self.process_and_save_image(image_data, 'products', f"{product.name}-{i+1}")
                    if file_path:
                        ProductImage.objects.create(
                            product=product,
                            image=file_path,
                            is_main=False
                        )
                        self.stdout.write(self.style.SUCCESS(f'تم تحديث صورة إضافية للمنتج: {product.name}'))
    
    def update_collection_images(self):
        """تحديث صور المجموعات"""
        collections = TrendingCollection.objects.all()
        self.stdout.write(f'تحديث صور لـ {collections.count()} مجموعة...')
        
        for collection in collections:
            # اختيار الصور المناسبة
            image_urls = self.COLLECTION_IMAGES.get(collection.name, [])
            
            if not image_urls:
                self.stdout.write(self.style.WARNING(f'لم يتم العثور على صور للمجموعة: {collection.name}'))
                continue
            
            image_url = random.choice(image_urls)
            image_data = self.download_image(image_url, collection.name)
            
            if image_data:
                file_path = self.process_and_save_image(image_data, 'collections', collection.name, max_size=(1200, 800))
                if file_path:
                    collection.image = file_path
                    collection.save()
                    self.stdout.write(self.style.SUCCESS(f'تم تحديث صورة المجموعة: {collection.name}'))
    
    def update_discount_images(self):
        """تحديث صور الخصومات"""
        discounts = Discount.objects.all()
        self.stdout.write(f'تحديث صور لـ {discounts.count()} خصم...')
        
        for discount in discounts:
            if not self.DISCOUNT_IMAGES:
                self.stdout.write(self.style.WARNING(f'لم يتم العثور على صور للخصومات'))
                continue
            
            image_url = random.choice(self.DISCOUNT_IMAGES)
            image_data = self.download_image(image_url, discount.name)
            
            if image_data:
                file_path = self.process_and_save_image(image_data, 'discounts', discount.name, max_size=(1200, 800))
                if file_path:
                    discount.image = file_path
                    discount.save()
                    self.stdout.write(self.style.SUCCESS(f'تم تحديث صورة الخصم: {discount.name}')) 