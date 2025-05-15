import os
import random
import requests
import io
from PIL import Image
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils import timezone
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.conf import settings
from django.db import transaction
from boutiqe.models import (
    Category, Color, Size, Product, ProductImage, 
    TrendingCollection, Discount, ProductVariation, Profile
)

class Command(BaseCommand):
    help = 'Populate database with products, categories, and images from Unsplash'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before importing',
        )
        parser.add_argument(
            '--products',
            type=int,
            default=20,
            help='Number of products to create per category',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database population...'))
        
        # Create media folders if they don't exist
        self.create_media_folders()
        
        # Optionally clear existing data
        if options['clear']:
            self.clear_data()
        
        # Create basic data
        self.create_users()
        self.create_colors()
        self.create_sizes()
        
        # Create categories with Unsplash images
        self.create_categories_with_images()
        
        # Create products with Unsplash images
        self.create_products_with_images(num_products=options['products'])
        
        # Create collections and discounts
        self.create_trending_collections()
        self.create_discounts()
        
        self.stdout.write(self.style.SUCCESS('Database population completed successfully!'))
    
    def create_media_folders(self):
        """Create media folders if they don't exist"""
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
                self.stdout.write(f'Created folder: {folder}')
    
    def clear_data(self):
        self.stdout.write('Clearing existing data...')
        try:
            # Don't delete admin user
            User.objects.exclude(is_superuser=True).delete()
            ProductImage.objects.all().delete()
            ProductVariation.objects.all().delete()
            Product.objects.all().delete()
            Category.objects.all().delete()
            Color.objects.all().delete()
            Size.objects.all().delete()
            TrendingCollection.objects.all().delete()
            Discount.objects.all().delete()
            self.stdout.write('Existing data cleared')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Error clearing data: {e}'))
            self.stdout.write('Continuing with database population...')

    def download_image_from_url(self, url, folder, filename):
        """Download an image from URL and save it to the specified folder"""
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            
            # Create full path
            folder_path = os.path.join(settings.MEDIA_ROOT, folder)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            
            file_path = os.path.join(folder_path, filename)
            
            # Process image with PIL for validation and possible resizing
            img = Image.open(io.BytesIO(response.content))
            
            # Resize if needed (e.g., for thumbnails or large images)
            if folder == 'products' and (img.width > 1200 or img.height > 1200):
                img.thumbnail((1200, 1200))
            
            img.save(file_path, format=img.format or 'JPEG')
            
            # Return relative path for Django model
            return f"{folder}/{filename}"
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error downloading image: {e}'))
            return None

    def get_unsplash_image(self, query, folder, filename):
        """Get an image from Unsplash based on query"""
        url = f"https://source.unsplash.com/random/800x800/?{query}"
        return self.download_image_from_url(url, folder, filename)

    def create_users(self):
        """Create sample users"""
        arabic_first_names = ['أحمد', 'محمد', 'سارة', 'فاطمة', 'عبدالله', 'نورة', 'علي', 'ريم', 'خالد', 'مريم']
        arabic_last_names = ['العلي', 'الأحمد', 'محمد', 'السالم', 'الخالد', 'العمر', 'الناصر', 'الحسن', 'السعيد', 'الحربي']
        
        # Create 5 users
        for i in range(1, 6):
            username = f'user{i}'
            email = f'user{i}@example.com'
            
            if not User.objects.filter(username=username).exists():
                first_name = random.choice(arabic_first_names)
                last_name = random.choice(arabic_last_names)
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='password123',
                    first_name=first_name,
                    last_name=last_name
                )
                
                # Create user profile
                Profile.objects.update_or_create(
                    user=user,
                    defaults={
                        'phone': f'05{random.randint(10000000, 99999999)}',
                        'address': f'شارع {random.randint(1, 50)}، حي {random.choice(["النرجس", "النخيل", "الياسمين", "العليا", "المروج"])}',
                        'city': random.choice(['الرياض', 'جدة', 'الدمام', 'مكة', 'المدينة']),
                        'country': 'المملكة العربية السعودية'
                    }
                )
                self.stdout.write(f'Created user: {username} ({first_name} {last_name})')

    def create_colors(self):
        """Create color options"""
        colors = [
            {'name': 'أسود', 'code': '#000000'},
            {'name': 'أبيض', 'code': '#FFFFFF'},
            {'name': 'أحمر', 'code': '#FF0000'},
            {'name': 'أزرق', 'code': '#0000FF'},
            {'name': 'أخضر', 'code': '#008000'},
            {'name': 'أصفر', 'code': '#FFFF00'},
            {'name': 'وردي', 'code': '#FFC0CB'},
            {'name': 'بنفسجي', 'code': '#800080'},
            {'name': 'برتقالي', 'code': '#FFA500'},
            {'name': 'بني', 'code': '#A52A2A'},
            {'name': 'رمادي', 'code': '#808080'},
            {'name': 'ذهبي', 'code': '#FFD700'},
            {'name': 'فضي', 'code': '#C0C0C0'},
        ]
        
        for color_data in colors:
            Color.objects.get_or_create(
                name=color_data['name'],
                defaults={'code': color_data['code']}
            )
        
        self.stdout.write(f'Created {len(colors)} colors')

    def create_sizes(self):
        """Create size options"""
        sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL', '36', '38', '40', '42', '44', '46']
        
        for size_name in sizes:
            Size.objects.get_or_create(name=size_name)
        
        self.stdout.write(f'Created {len(sizes)} sizes')

    def create_categories_with_images(self):
        """Create categories with Unsplash images"""
        categories = [
            {'name': 'فساتين', 'slug': 'dresses', 'query': 'dress,fashion'},
            {'name': 'بلوزات', 'slug': 'blouses', 'query': 'blouse,top,fashion'},
            {'name': 'تنانير', 'slug': 'skirts', 'query': 'skirt,fashion'},
            {'name': 'بناطيل', 'slug': 'pants', 'query': 'pants,fashion'},
            {'name': 'عبايات', 'slug': 'abayas', 'query': 'abaya,modest,fashion'},
            {'name': 'إكسسوارات', 'slug': 'accessories', 'query': 'jewelry,accessories'},
            {'name': 'أحذية', 'slug': 'shoes', 'query': 'shoes,womens,fashion'},
            {'name': 'حقائب', 'slug': 'bags', 'query': 'bags,handbag,fashion'}
        ]
        
        for cat in categories:
            filename = f"{cat['slug']}.jpg"
            image_path = self.get_unsplash_image(cat['query'], 'categories', filename)
            
            Category.objects.update_or_create(
                slug=cat['slug'],
                defaults={
                    'name': cat['name'],
                    'image': image_path
                }
            )
            self.stdout.write(f"Created category: {cat['name']} with image")
    
    def generate_arabic_description(self, category_name):
        """Generate an Arabic description based on category name"""
        descriptions = {
            'فساتين': [
                f"فستان أنيق بتصميم عصري مناسب لجميع المناسبات. يتميز بقصة مريحة وخامة فاخرة تمنحكِ إطلالة مميزة.",
                f"فستان راقٍ بأحدث صيحات الموضة، قصة أنيقة تبرز جمال قوامك. مصنوع من أفضل الأقمشة المستوردة.",
                f"فستان فاخر بتصميم حديث ومميز، مناسب للحفلات والمناسبات الخاصة. يتميز بتطريزات يدوية راقية."
            ],
            'بلوزات': [
                f"بلوزة أنيقة بقصة عصرية مريحة، مصنوعة من أجود أنواع الأقمشة. مناسبة للإطلالات اليومية والرسمية.",
                f"بلوزة بتصميم فريد وخامة ممتازة، تضيف لمسة أناقة لإطلالتك. متوفرة بألوان متعددة تناسب جميع الأذواق.",
                f"بلوزة راقية بقصة مميزة، سهلة التنسيق مع مختلف القطع. تتميز بتفاصيل عصرية تواكب أحدث صيحات الموضة."
            ],
            'تنانير': [
                f"تنورة أنيقة بقصة مميزة تناسب مختلف المناسبات. مصنوعة من أجود الخامات لراحة فائقة طوال اليوم.",
                f"تنورة عصرية بتصميم راقٍ، مناسبة للإطلالات اليومية والرسمية. تتميز بخامة عالية الجودة وألوان ثابتة.",
                f"تنورة بقصة أنيقة تبرز جمال قوامك. مصممة بعناية لتمنحكِ إطلالة مثالية في جميع مناسباتك."
            ],
            'بناطيل': [
                f"بنطلون عصري بقصة مريحة، مصنوع من أفضل الخامات. يمنحكِ إطلالة أنيقة مع راحة طوال اليوم.",
                f"بنطلون أنيق يجمع بين الراحة والأناقة. مناسب للعمل والمناسبات المختلفة، سهل التنسيق مع عدة قطع.",
                f"بنطلون بتصميم مميز وخامة فاخرة، قصة عصرية تناسب مختلف الأجسام. متوفر بألوان متعددة."
            ],
            'عبايات': [
                f"عباءة أنيقة بتصميم عصري مميز، مصنوعة من أجود أنواع الأقمشة. تتميز بتطريزات راقية وقصة مريحة.",
                f"عباءة فاخرة بلمسات عصرية، مناسبة لجميع المناسبات. تتميز بخامة عالية الجودة وتفاصيل دقيقة.",
                f"عباءة راقية بتصميم مبتكر يجمع بين الأصالة والمعاصرة. مصممة بعناية من أفخم الخامات."
            ],
            'إكسسوارات': [
                f"إكسسوار أنيق يضيف لمسة مميزة لإطلالتك. مصنوع بدقة عالية من خامات فاخرة تدوم طويلاً.",
                f"إكسسوار عصري بتصميم فريد، يكمل إطلالتك بأناقة. مناسب لمختلف المناسبات والإطلالات.",
                f"قطعة إكسسوار مميزة تضفي لمسة فاخرة على مظهرك. مصممة بعناية لتتناسب مع مختلف الأزياء."
            ],
            'أحذية': [
                f"حذاء أنيق بتصميم عصري، مصنوع من أجود الخامات. يجمع بين الراحة والأناقة لإطلالة مميزة.",
                f"حذاء فاخر يمنحكِ الراحة طوال اليوم. مناسب للمناسبات المختلفة بتصميم يواكب أحدث الصيحات.",
                f"حذاء مميز بلمسات عصرية، قطعة أساسية تكمل أناقتك. مصنوع بعناية لضمان الراحة والمتانة."
            ],
            'حقائب': [
                f"حقيبة أنيقة بتصميم عصري، مصنوعة من خامات عالية الجودة. تتسع لجميع احتياجاتك اليومية.",
                f"حقيبة فاخرة بلمسات مميزة، تضيف أناقة لإطلالتك. متعددة الاستخدامات ومناسبة لجميع المناسبات.",
                f"حقيبة عصرية بتصميم فريد، مصنوعة بعناية من أفخم الخامات. تجمع بين الأناقة والعملية."
            ]
        }
        
        return random.choice(descriptions.get(category_name, ["منتج مميز بتصميم عصري وخامة فاخرة. يمنحكِ إطلالة أنيقة تناسب جميع المناسبات."]))

    @transaction.atomic
    def create_products_with_images(self, num_products=5):
        """Create products with Unsplash images for each category"""
        categories = Category.objects.all()
        colors = list(Color.objects.all())
        sizes = list(Size.objects.all())
        
        product_count = 0
        
        for category in categories:
            self.stdout.write(f"Creating products for category: {category.name}")
            
            # Keywords for Unsplash search based on category
            search_keywords = {
                'فساتين': 'dress,fashion,women',
                'بلوزات': 'blouse,top,fashion,women',
                'تنانير': 'skirt,fashion,women',
                'بناطيل': 'pants,trousers,fashion,women',
                'عبايات': 'abaya,modest,fashion,women',
                'إكسسوارات': 'accessories,jewelry,fashion,women',
                'أحذية': 'shoes,heels,fashion,women',
                'حقائب': 'handbag,purse,fashion,women'
            }
            
            query = search_keywords.get(category.name, f"{category.name},fashion")
            
            for i in range(1, num_products + 1):
                # Generate product details
                product_name = f"{category.name} {random.choice(['أنيق', 'عصري', 'فاخر', 'مميز', 'راقٍ'])} {i}"
                price = round(random.uniform(50, 500), 2)
                has_discount = random.choice([True, False])
                discount_price = round(price * random.uniform(0.5, 0.9), 2) if has_discount else None
                is_featured = random.choice([True, False])
                is_new = random.choice([True, False])
                stock = random.randint(5, 50)
                sku = f"{category.slug[:3].upper()}-{random.randint(1000, 9999)}"
                
                # Create product
                product = Product.objects.create(
                    name=product_name,
                    slug=f"{slugify(category.slug)}-{i}-{random.randint(1000, 9999)}",
                    description=self.generate_arabic_description(category.name),
                    price=price,
                    discount_price=discount_price,
                    category=category,
                    in_stock=True,
                    is_featured=is_featured,
                    is_new=is_new,
                    is_sale=has_discount,
                    sku=sku,
                    stock_quantity=stock
                )
                
                # Add random colors and sizes
                product_colors = random.sample(colors, k=min(random.randint(1, 5), len(colors)))
                product_sizes = random.sample(sizes, k=min(random.randint(1, 6), len(sizes)))
                product.colors.set(product_colors)
                product.sizes.set(product_sizes)
                
                # Create variations
                for color in product_colors:
                    for size in product_sizes:
                        ProductVariation.objects.create(
                            product=product,
                            color=color,
                            size=size,
                            stock_count=random.randint(1, 10)
                        )
                
                # Add multiple images for the product (1-4 images)
                num_images = random.randint(1, 4)
                for img_idx in range(num_images):
                    filename = f"{product.slug}-{img_idx}.jpg"
                    image_path = self.get_unsplash_image(f"{query}", 'products', filename)
                    
                    if image_path:
                        ProductImage.objects.create(
                            product=product,
                            image=image_path,
                            is_main=(img_idx == 0)  # First image is main
                        )
                
                product_count += 1
                if product_count % 10 == 0:
                    self.stdout.write(f"Created {product_count} products so far...")
        
        self.stdout.write(self.style.SUCCESS(f"Successfully created {product_count} products with images"))

    def create_trending_collections(self):
        """Create trending collections"""
        collection_data = [
            {'name': 'مجموعة الصيف', 'description': 'تشكيلة رائعة من الأزياء الصيفية المميزة بألوان زاهية وتصاميم عصرية مناسبة للشاطئ والإجازات.'},
            {'name': 'عروس متألقة', 'description': 'كل ما تحتاجينه ليوم زفافك من فساتين وإكسسوارات فاخرة لتكوني الأجمل في يومك المميز.'},
            {'name': 'أزياء رمضان', 'description': 'تشكيلة مميزة من الأزياء الرمضانية الأنيقة، تجمع بين الراحة والفخامة لمناسبات وسهرات الشهر الكريم.'},
            {'name': 'إطلالة رسمية', 'description': 'مجموعة متكاملة من الأزياء الرسمية المناسبة للعمل والمناسبات الرسمية بقصات أنيقة وخامات فاخرة.'},
        ]
        
        all_products = list(Product.objects.all())
        if not all_products:
            self.stdout.write(self.style.WARNING("No products found to add to collections"))
            return
        
        for collection_info in collection_data:
            filename = f"{slugify(collection_info['name'])}.jpg"
            image_path = self.get_unsplash_image('fashion,collection', 'collections', filename)
            
            collection = TrendingCollection.objects.create(
                name=collection_info['name'],
                slug=slugify(collection_info['name']),
                description=collection_info['description'],
                image=image_path,
                is_active=True
            )
            
            # Add random products to collection (5-12 products)
            if all_products:
                products_to_add = random.sample(all_products, min(random.randint(5, 12), len(all_products)))
                collection.products.set(products_to_add)
            
            self.stdout.write(f"Created trending collection: {collection.name}")

    def create_discounts(self):
        """Create discount campaigns"""
        discount_data = [
            {
                'name': 'خصم نهاية الموسم',
                'description': 'خصومات حصرية تصل إلى 50% على تشكيلة واسعة من الأزياء النسائية. العرض محدود لفترة محدودة!',
                'discount_percent': 50,
                'days_valid': 30
            },
            {
                'name': 'عروض العيد',
                'description': 'تخفيضات خاصة بمناسبة العيد على مجموعة مختارة من المنتجات الفاخرة لإطلالة مميزة.',
                'discount_percent': 30,
                'days_valid': 15
            },
            {
                'name': 'الجمعة البيضاء',
                'description': 'أقوى عروض السنة! خصومات هائلة على جميع المنتجات لفترة محدودة. تسوقي الآن قبل نفاد الكمية.',
                'discount_percent': 70,
                'days_valid': 7
            },
            {
                'name': 'عرض خاص للعضوات',
                'description': 'عروض حصرية لعضوات الموقع المسجلات. استمتعي بأسعار خاصة على منتجات مختارة.',
                'discount_percent': 25,
                'days_valid': 45
            }
        ]
        
        categories = list(Category.objects.all())
        products = list(Product.objects.all())
        
        for discount_info in discount_data:
            filename = f"{slugify(discount_info['name'])}.jpg"
            image_path = self.get_unsplash_image('sale,discount,fashion', 'discounts', filename)
            
            start_date = timezone.now()
            end_date = start_date + timezone.timedelta(days=discount_info['days_valid'])
            
            discount = Discount.objects.create(
                name=discount_info['name'],
                description=discount_info['description'],
                discount_percent=discount_info['discount_percent'],
                start_date=start_date,
                end_date=end_date,
                is_active=True
            )
            
            # Add random categories and products to the discount
            if categories:
                cats_to_add = random.sample(categories, min(random.randint(1, 3), len(categories)))
                discount.categories.set(cats_to_add)
            
            if products:
                prods_to_add = random.sample(products, min(random.randint(5, 15), len(products)))
                discount.products.set(prods_to_add)
            
            self.stdout.write(f"Created discount: {discount.name}") 