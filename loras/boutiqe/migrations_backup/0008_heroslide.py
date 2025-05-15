from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('boutiqe', '0007_merge_20250510_1932'),
    ]

    operations = [
        migrations.CreateModel(
            name='HeroSlide',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='العنوان')),
                ('subtitle', models.CharField(max_length=200, verbose_name='العنوان الفرعي')),
                ('description', models.TextField(verbose_name='الوصف')),
                ('badge_text', models.CharField(help_text='النص الذي يظهر في الشارة العلوية', max_length=50, verbose_name='نص الشارة')),
                ('badge_color', models.CharField(default='primary', help_text='لون الشارة بتنسيق HEX أو اسم اللون', max_length=20, verbose_name='لون الشارة')),
                ('background_image', models.ImageField(upload_to='hero_slides/', verbose_name='صورة الخلفية')),
                ('primary_button_text', models.CharField(max_length=50, verbose_name='نص الزر الرئيسي')),
                ('primary_button_url', models.CharField(default='/products/', max_length=200, verbose_name='رابط الزر الرئيسي')),
                ('secondary_button_text', models.CharField(max_length=50, verbose_name='نص الزر الثانوي')),
                ('secondary_button_url', models.CharField(default='/products/', max_length=200, verbose_name='رابط الزر الثانوي')),
                ('features', models.JSONField(blank=True, help_text='ميزات لعرضها في هذه الشريحة (JSON)', null=True, verbose_name='المميزات')),
                ('is_active', models.BooleanField(default=True, verbose_name='نشط')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='الترتيب')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')),
            ],
            options={
                'verbose_name': 'شريحة العرض الرئيسية',
                'verbose_name_plural': 'شرائح العرض الرئيسية',
                'ordering': ['order', 'created_at'],
            },
        ),
    ] 