import os
import random
import requests
import time
from io import BytesIO
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.text import slugify
from django.conf import settings
from PIL import Image
from boutiqe.models import Product, ProductImage, Category, TrendingCollection, Discount

class Command(BaseCommand):
    help = 'تنزيل صور ملابس حقيقية من Pexels API وتعيينها للمنتجات والفئات'

    # رابط API ومفتاح الوصول
    PEXELS_API_URL = "https://api.pexels.com/v1/search"
    
    # مفتاح API تجريبي (يمكنك استبداله بمفتاح حقيقي)
    API_KEY = "YOUR_PEXELS_API_KEY"  # قم بتعديل هذا المفتاح
    
    # قواميس للبحث عن الصور حسب نوع المنتج
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
    
    # قواميس أكثر تحديداً للمنتجات
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
    
    # مصطلحات تجميعية
    COLLECTION_SEARCH_TERMS = {
        'مجموعة الصيف': ['summer fashion', 'summer collection', 'summer outfit'],
        'مجموعة العيد': ['eid fashion', 'festive outfit', 'celebration outfit'],
        'مجموعة السهرات': ['evening fashion', 'party outfit', 'formal wear']
    }
    
    def handle(self, *args, **kwargs):
        self.stdout.write('بدء تنزيل الصور الحقيقية للمنتجات والفئات...')
        
        if self.API_KEY == "YOUR_PEXELS_API_KEY":
            self.stdout.write(self.style.WARNING('تحذير: أنت تستخدم مفتاح API افتراضي. يرجى تعيين مفتاح API حقيقي قبل الاستمرار.'))
            self.stdout.write('يمكنك الحصول على مفتاح API مجاني من: https://www.pexels.com/api/')
            return
        
        # تحديث صور الفئات
        self.update_category_images()
        
        # تحديث صور المنتجات
        self.update_product_images()
        
        # تحديث صور المجموعات والخصومات
        self.update_collection_images()
        self.update_discount_images()
        
        self.stdout.write(self.style.SUCCESS('تم تنزيل وتعيين الصور بنجاح!'))
    
    def fetch_image_from_pexels(self, query, per_page=1, orientation='portrait'):
        """تنزيل صور من Pexels API"""
        headers = {
            'Authorization': self.API_KEY
        }
        
        params = {
            'query': query,
            'per_page': per_page,
            'orientation': orientation
        }
        
        response = requests.get(self.PEXELS_API_URL, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            photos = data.get('photos', [])
            
            if not photos:
                self.stdout.write(self.style.WARNING(f'لم يتم العثور على صور لـ "{query}"'))
                return []
            
            return photos
        else:
            self.stdout.write(self.style.ERROR(f'خطأ في طلب Pexels API: {response.status_code}'))
            self.stdout.write(self.style.ERROR(response.text))
            return []
    
    def download_image(self, url, image_name):
        """تنزيل صورة من URL وحفظها"""
        try:
            response = requests.get(url)
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
            file_path = os.path.join(folder, f"{safe_name}.jpg")
            
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
            
            photos = self.fetch_image_from_pexels(search_term, per_page=3)
            
            if photos:
                photo = random.choice(photos)
                image_url = photo['src']['large']
                
                self.stdout.write(f'تنزيل صورة من {image_url}')
                image_data = self.download_image(image_url, category.name)
                
                if image_data:
                    file_path = self.process_and_save_image(image_data, 'categories', category.name)
                    if file_path:
                        category.image = file_path
                        category.save()
                        self.stdout.write(self.style.SUCCESS(f'تم تحديث صورة الفئة: {category.name}'))
            
            # انتظار لتجنب تجاوز حدود طلبات API
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
            photos = self.fetch_image_from_pexels(search_term, per_page=5)
            
            if photos:
                # صورة رئيسية
                main_photo = random.choice(photos)
                image_url = main_photo['src']['large']
                
                self.stdout.write(f'تنزيل الصورة الرئيسية من {image_url}')
                image_data = self.download_image(image_url, product.name)
                
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
                remaining_photos = [p for p in photos if p['id'] != main_photo['id']]
                
                for i, photo in enumerate(remaining_photos[:2]):
                    if photo:
                        image_url = photo['src']['large']
                        self.stdout.write(f'تنزيل صورة إضافية {i+1} من {image_url}')
                        image_data = self.download_image(image_url, f"{product.name}-{i+1}")
                        
                        if image_data:
                            file_path = self.process_and_save_image(image_data, 'products', f"{product.name}-{i+1}")
                            if file_path:
                                ProductImage.objects.create(
                                    product=product,
                                    image=file_path,
                                    is_main=False
                                )
                                self.stdout.write(self.style.SUCCESS(f'تم تحديث صورة إضافية للمنتج: {product.name}'))
            
            # انتظار لتجنب تجاوز حدود طلبات API
            time.sleep(1)
    
    def update_collection_images(self):
        """تحديث صور المجموعات"""
        collections = TrendingCollection.objects.all()
        self.stdout.write(f'تحديث صور لـ {collections.count()} مجموعة...')
        
        for collection in collections:
            search_terms = self.COLLECTION_SEARCH_TERMS.get(collection.name, [collection.name, 'fashion collection'])
            search_term = random.choice(search_terms)
            
            self.stdout.write(f'البحث عن صور لمجموعة "{collection.name}" باستخدام "{search_term}"...')
            
            photos = self.fetch_image_from_pexels(search_term, per_page=3, orientation='landscape')
            
            if photos:
                photo = random.choice(photos)
                image_url = photo['src']['large']
                
                self.stdout.write(f'تنزيل صورة من {image_url}')
                image_data = self.download_image(image_url, collection.name)
                
                if image_data:
                    file_path = self.process_and_save_image(image_data, 'collections', collection.name, max_size=(1200, 800))
                    if file_path:
                        collection.image = file_path
                        collection.save()
                        self.stdout.write(self.style.SUCCESS(f'تم تحديث صورة المجموعة: {collection.name}'))
            
            # انتظار لتجنب تجاوز حدود طلبات API
            time.sleep(0.5)
    
    def update_discount_images(self):
        """تحديث صور الخصومات"""
        discounts = Discount.objects.all()
        self.stdout.write(f'تحديث صور لـ {discounts.count()} خصم...')
        
        for discount in discounts:
            # استخدام بعض الصور من المنتجات ذات الصلة
            related_products = discount.products.all()
            if related_products.exists():
                related_product = random.choice(related_products)
                main_image = related_product.get_main_image()
                
                if main_image:
                    discount.image = main_image.image
                    discount.save()
                    self.stdout.write(self.style.SUCCESS(f'تم تعيين صورة للخصم: {discount.name}'))
                    continue
            
            # إذا لم يكن هناك منتجات مرتبطة أو صور، نبحث عن صور جديدة
            search_term = f"sale {discount.name}" if discount.name else "fashion sale"
            
            self.stdout.write(f'البحث عن صور للخصم "{discount.name}" باستخدام "{search_term}"...')
            
            photos = self.fetch_image_from_pexels(search_term, per_page=3, orientation='landscape')
            
            if photos:
                photo = random.choice(photos)
                image_url = photo['src']['large']
                
                self.stdout.write(f'تنزيل صورة من {image_url}')
                image_data = self.download_image(image_url, discount.name)
                
                if image_data:
                    file_path = self.process_and_save_image(image_data, 'discounts', discount.name, max_size=(1200, 800))
                    if file_path:
                        discount.image = file_path
                        discount.save()
                        self.stdout.write(self.style.SUCCESS(f'تم تحديث صورة الخصم: {discount.name}'))
            
            # انتظار لتجنب تجاوز حدود طلبات API
            time.sleep(0.5) 