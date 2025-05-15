import os
import random
import requests
import io
from PIL import Image
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from django.conf import settings
from django.db import transaction
from boutiqe.models import Category, Color, Size, Product, ProductImage

class Command(BaseCommand):
    help = 'Populate database with products, categories, and images from Unsplash'

    def add_arguments(self, parser):
        parser.add_argument(
            '--products',
            type=int,
            default=5,
            help='Number of products to create per category',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database population...'))
        
        # Create media folders if they don't exist
        self.create_media_folders()
        
        # Create basic data
        self.create_colors()
        self.create_sizes()
        
        # Create categories with Unsplash images
        self.create_categories_with_images()
        
        # Create products with Unsplash images
        self.create_products_with_images(num_products=options['products'])
        
        self.stdout.write(self.style.SUCCESS('Database population completed successfully!'))
    
    def create_media_folders(self):
        """Create media folders if they don't exist"""
        media_folders = [
            os.path.join(settings.MEDIA_ROOT, 'products'),
            os.path.join(settings.MEDIA_ROOT, 'categories'),
            os.path.join(settings.MEDIA_ROOT, 'collections'),
        ]
        
        for folder in media_folders:
            if not os.path.exists(folder):
                os.makedirs(folder)
                self.stdout.write(f'Created folder: {folder}')

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

    def create_colors(self):
        """Create color options"""
        colors = [
            {'name': 'أسود', 'code': '#000000'},
            {'name': 'أبيض', 'code': '#FFFFFF'},
            {'name': 'أحمر', 'code': '#FF0000'},
            {'name': 'أزرق', 'code': '#0000FF'},
            {'name': 'أخضر', 'code': '#008000'},
            {'name': 'وردي', 'code': '#FFC0CB'},
        ]
        
        for color_data in colors:
            Color.objects.get_or_create(
                name=color_data['name'],
                defaults={'code': color_data['code']}
            )
        
        self.stdout.write(f'Created {len(colors)} colors')

    def create_sizes(self):
        """Create size options"""
        sizes = ['XS', 'S', 'M', 'L', 'XL']
        
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
            ],
            'بلوزات': [
                f"بلوزة أنيقة بقصة عصرية مريحة، مصنوعة من أجود أنواع الأقمشة. مناسبة للإطلالات اليومية والرسمية.",
                f"بلوزة بتصميم فريد وخامة ممتازة، تضيف لمسة أناقة لإطلالتك. متوفرة بألوان متعددة تناسب جميع الأذواق.",
            ],
            'تنانير': [
                f"تنورة أنيقة بقصة مميزة تناسب مختلف المناسبات. مصنوعة من أجود الخامات لراحة فائقة طوال اليوم.",
                f"تنورة عصرية بتصميم راقٍ، مناسبة للإطلالات اليومية والرسمية. تتميز بخامة عالية الجودة وألوان ثابتة.",
            ],
            'بناطيل': [
                f"بنطلون عصري بقصة مريحة، مصنوع من أفضل الخامات. يمنحكِ إطلالة أنيقة مع راحة طوال اليوم.",
                f"بنطلون أنيق يجمع بين الراحة والأناقة. مناسب للعمل والمناسبات المختلفة، سهل التنسيق مع عدة قطع.",
            ],
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
            }
            
            query = search_keywords.get(category.name, f"{category.name},fashion")
            
            for i in range(1, num_products + 1):
                # Generate product details
                product_name = f"{category.name} {random.choice(['أنيق', 'عصري', 'فاخر', 'مميز'])} {i}"
                price = round(random.uniform(50, 500), 2)
                has_discount = random.choice([True, False])
                discount_price = round(price * random.uniform(0.5, 0.9), 2) if has_discount else None
                is_featured = random.choice([True, False])
                is_new = random.choice([True, False])
                stock = random.randint(5, 50)
                sku = f"{category.slug[:3].upper()}-{random.randint(1000, 9999)}"
                
                try:
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
                    product_colors = random.sample(colors, k=min(random.randint(1, 3), len(colors)))
                    product_sizes = random.sample(sizes, k=min(random.randint(1, 3), len(sizes)))
                    product.colors.set(product_colors)
                    product.sizes.set(product_sizes)
                    
                    # Add image for the product
                    filename = f"{product.slug}.jpg"
                    image_path = self.get_unsplash_image(f"{query}", 'products', filename)
                    
                    if image_path:
                        ProductImage.objects.create(
                            product=product,
                            image=image_path,
                            is_main=True
                        )
                    
                    product_count += 1
                    if product_count % 5 == 0:
                        self.stdout.write(f"Created {product_count} products so far...")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error creating product: {e}"))
        
        self.stdout.write(self.style.SUCCESS(f"Successfully created {product_count} products with images")) 