import os
import random
import requests
import time
from io import BytesIO
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.conf import settings
from PIL import Image
from boutiqe.models import Product, ProductImage, Category, TrendingCollection, Discount

class Command(BaseCommand):
    help = 'تنزيل صور ملابس حقيقية من Unsplash وتعيينها للمنتجات والفئات'

    # قاموس للبحث عن الصور حسب نوع المنتج
    CATEGORY_SEARCH_TERMS = {
        'فساتين': ['dress', 'fashion dress', 'elegant dress'],
        'بلوزات': ['blouse', 'women top', 'fashion top'],
        'تنانير': ['skirt', 'fashion skirt'],
        'بناطيل': ['pants', 'trousers', 'fashion pants'],
        'عبايات': ['abaya', 'cloak', 'modest fashion'],
        'إكسسوارات': ['jewelry', 'accessories', 'fashion accessories'],
        'أحذية': ['shoes', 'heels', 'women shoes'],
        'حقائب': ['handbag', 'purse', 'fashion bag']
    }
    
    # مصطلحات أكثر تحديداً للمنتجات
    PRODUCT_SEARCH_TERMS = {
        'فستان سهرة أنيق': ['elegant evening dress', 'gown'],
        'بلوزة كاجوال': ['casual blouse', 'casual top'],
        'تنورة قصيرة': ['mini skirt', 'short skirt'],
        'بنطلون جينز': ['jeans', 'denim pants'],
        'عباية سوداء فاخرة': ['black abaya', 'luxury abaya'],
        'عقد ذهبي': ['gold necklace', 'jewelry'],
        'حذاء كعب عالي': ['high heels', 'stiletto'],
        'حقيبة يد فاخرة': ['luxury handbag', 'designer bag'],
        'فستان زفاف أبيض': ['wedding dress', 'white gown'],
        'عباية مطرزة': ['embroidered abaya', 'embroidered cloak'],
        'حذاء رياضي': ['sneakers', 'sport shoes'],
        'حقيبة ظهر': ['backpack', 'fashion backpack'],
        'فستان صيفي': ['summer dress', 'light dress'],
        'سوار ذهبي': ['gold bracelet', 'fashion bracelet'],
        'صندل صيفي': ['summer sandals', 'women sandals']
    }
    
    # مصطلحات للمجموعات
    COLLECTION_SEARCH_TERMS = {
        'مجموعة الصيف': ['summer fashion', 'summer collection', 'summer outfit'],
        'مجموعة العيد': ['eid fashion', 'festive outfit', 'celebration outfit'],
        'مجموعة السهرات': ['evening fashion', 'party outfit', 'formal wear']
    }
    
    def handle(self, *args, **kwargs):
        self.stdout.write('بدء تنزيل الصور الحقيقية للمنتجات والفئات من Unsplash...')
        
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
    
    def fetch_image_from_unsplash(self, query, count=1):
        """تنزيل صور من Unsplash Source API (لا يتطلب مفتاح API)"""
        # تنسيق مصطلح البحث للاستخدام في URL
        formatted_query = query.replace(' ', '-')
        
        # قائمة URLs للصور
        image_urls = []
        
        for i in range(count):
            # إضافة رقم عشوائي لتجنب تكرار نفس الصورة
            random_number = random.randint(1, 1000)
            # بناء URL للصورة باستخدام Unsplash Source
            # يمكن تحديد الحجم والموضوع
            image_url = f"https://source.unsplash.com/featured/800x600?{formatted_query}&sig={random_number}"
            image_urls.append(image_url)
            # انتظار لتجنب تكرار نفس الصورة
            time.sleep(0.2)
        
        return image_urls
    
    def download_image(self, url, image_name):
        """تنزيل صورة من URL"""
        try:
            response = requests.get(url, allow_redirects=True)
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
            
            return file_path
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'خطأ أثناء معالجة الصورة: {str(e)}'))
            return None
    
    def update_category_images(self):
        """تحديث صور الفئات"""
        categories = Category.objects.all()
        self.stdout.write(f'تحديث صور لـ {categories.count()} فئة...')
        
        for category in categories:
            search_terms = self.CATEGORY_SEARCH_TERMS.get(category.name, [category.name])
            search_term = random.choice(search_terms)
            
            self.stdout.write(f'البحث عن صور لفئة "{category.name}" باستخدام "{search_term}"...')
            
            image_urls = self.fetch_image_from_unsplash(search_term, count=1)
            
            if image_urls:
                image_url = image_urls[0]
                self.stdout.write(f'تنزيل صورة من {image_url}')
                image_data = self.download_image(image_url, category.name)
                
                if image_data:
                    file_path = self.process_and_save_image(image_data, 'categories', category.name)
                    if file_path:
                        category.image = file_path
                        category.save()
                        self.stdout.write(self.style.SUCCESS(f'تم تحديث صورة الفئة: {category.name}'))
            
            # انتظار قليلاً
            time.sleep(0.5)
    
    def update_product_images(self):
        """تحديث صور المنتجات"""
        products = Product.objects.all()
        self.stdout.write(f'تحديث صور لـ {products.count()} منتج...')
        
        for product in products:
            # حذف الصور القديمة
            ProductImage.objects.filter(product=product).delete()
            
            # البحث عن مصطلح البحث المناسب للمنتج
            if product.name in self.PRODUCT_SEARCH_TERMS:
                search_terms = self.PRODUCT_SEARCH_TERMS[product.name]
            else:
                search_terms = self.CATEGORY_SEARCH_TERMS.get(product.category.name, [product.category.name])
            
            search_term = random.choice(search_terms)
            
            self.stdout.write(f'البحث عن صور للمنتج "{product.name}" باستخدام "{search_term}"...')
            
            # تنزيل 3 صور لكل منتج
            image_urls = self.fetch_image_from_unsplash(search_term, count=3)
            
            # صورة رئيسية
            if image_urls:
                main_url = image_urls[0]
                self.stdout.write(f'تنزيل الصورة الرئيسية من {main_url}')
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
            
                # صور إضافية
                for i, url in enumerate(image_urls[1:]):
                    self.stdout.write(f'تنزيل صورة إضافية {i+1} من {url}')
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
            
            # انتظار بين المنتجات
            time.sleep(1)
    
    def update_collection_images(self):
        """تحديث صور المجموعات"""
        collections = TrendingCollection.objects.all()
        self.stdout.write(f'تحديث صور لـ {collections.count()} مجموعة...')
        
        for collection in collections:
            search_terms = self.COLLECTION_SEARCH_TERMS.get(collection.name, [collection.name, 'fashion collection'])
            search_term = random.choice(search_terms)
            
            self.stdout.write(f'البحث عن صور لمجموعة "{collection.name}" باستخدام "{search_term}"...')
            
            image_urls = self.fetch_image_from_unsplash(search_term, count=1)
            
            if image_urls:
                image_url = image_urls[0]
                self.stdout.write(f'تنزيل صورة من {image_url}')
                image_data = self.download_image(image_url, collection.name)
                
                if image_data:
                    file_path = self.process_and_save_image(image_data, 'collections', collection.name, max_size=(1200, 800))
                    if file_path:
                        collection.image = file_path
                        collection.save()
                        self.stdout.write(self.style.SUCCESS(f'تم تحديث صورة المجموعة: {collection.name}'))
            
            # انتظار قليلاً
            time.sleep(0.5)
    
    def update_discount_images(self):
        """تحديث صور الخصومات"""
        discounts = Discount.objects.all()
        self.stdout.write(f'تحديث صور لـ {discounts.count()} خصم...')
        
        for discount in discounts:
            search_term = f"sale {discount.name}" if discount.name else "fashion sale"
            
            self.stdout.write(f'البحث عن صور للخصم "{discount.name}" باستخدام "{search_term}"...')
            
            image_urls = self.fetch_image_from_unsplash(search_term, count=1)
            
            if image_urls:
                image_url = image_urls[0]
                self.stdout.write(f'تنزيل صورة من {image_url}')
                image_data = self.download_image(image_url, discount.name)
                
                if image_data:
                    file_path = self.process_and_save_image(image_data, 'discounts', discount.name, max_size=(1200, 800))
                    if file_path:
                        discount.image = file_path
                        discount.save()
                        self.stdout.write(self.style.SUCCESS(f'تم تحديث صورة الخصم: {discount.name}'))
            
            # انتظار قليلاً
            time.sleep(0.5) 