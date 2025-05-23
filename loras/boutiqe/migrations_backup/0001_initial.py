# Generated by Django 5.0 on 2025-05-09 13:11

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='اسم الفئة')),
                ('slug', models.SlugField(blank=True, unique=True)),
                ('image', models.ImageField(upload_to='categories/', verbose_name='صورة الفئة')),
            ],
            options={
                'verbose_name': 'فئة',
                'verbose_name_plural': 'الفئات',
            },
        ),
        migrations.CreateModel(
            name='Color',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='اسم اللون')),
                ('code', models.CharField(max_length=10, verbose_name='كود اللون')),
            ],
            options={
                'verbose_name': 'لون',
                'verbose_name_plural': 'الألوان',
            },
        ),
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='الاسم')),
                ('email', models.EmailField(max_length=254, verbose_name='البريد الإلكتروني')),
                ('phone', models.CharField(max_length=20, verbose_name='رقم الهاتف')),
                ('message', models.TextField(verbose_name='الرسالة')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإرسال')),
            ],
            options={
                'verbose_name': 'رسالة تواصل',
                'verbose_name_plural': 'رسائل التواصل',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Size',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, verbose_name='المقاس')),
            ],
            options={
                'verbose_name': 'مقاس',
                'verbose_name_plural': 'المقاسات',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='اسم المنتج')),
                ('slug', models.SlugField(blank=True, unique=True)),
                ('description', models.TextField(verbose_name='وصف المنتج')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='السعر')),
                ('discount_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='سعر الخصم')),
                ('is_featured', models.BooleanField(default=False, verbose_name='مميز')),
                ('in_stock', models.BooleanField(default=True, verbose_name='متوفر')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإضافة')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='boutiqe.category', verbose_name='الفئة')),
                ('colors', models.ManyToManyField(blank=True, to='boutiqe.color', verbose_name='الألوان المتاحة')),
                ('sizes', models.ManyToManyField(blank=True, to='boutiqe.size', verbose_name='المقاسات المتاحة')),
            ],
            options={
                'verbose_name': 'منتج',
                'verbose_name_plural': 'المنتجات',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='products/', verbose_name='صورة المنتج')),
                ('is_main', models.BooleanField(default=False, verbose_name='صورة رئيسية')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='boutiqe.product', verbose_name='المنتج')),
            ],
            options={
                'verbose_name': 'صورة المنتج',
                'verbose_name_plural': 'صور المنتجات',
            },
        ),
        migrations.CreateModel(
            name='CartItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='الكمية')),
                ('added_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإضافة')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='المستخدم')),
                ('color', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='boutiqe.color', verbose_name='اللون')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='boutiqe.product', verbose_name='المنتج')),
                ('size', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='boutiqe.size', verbose_name='المقاس')),
            ],
            options={
                'verbose_name': 'عنصر السلة',
                'verbose_name_plural': 'عناصر السلة',
            },
        ),
        migrations.CreateModel(
            name='Wishlist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('added_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإضافة')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='boutiqe.product', verbose_name='المنتج')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='المستخدم')),
            ],
            options={
                'verbose_name': 'قائمة المفضلة',
                'verbose_name_plural': 'قوائم المفضلة',
                'unique_together': {('user', 'product')},
            },
        ),
    ]
