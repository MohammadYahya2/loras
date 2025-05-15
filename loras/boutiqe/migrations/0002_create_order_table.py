from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('boutiqe', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="SELECT 1 FROM sqlite_master WHERE type='table' AND name='boutiqe_order';",
            reverse_sql=None,
            state_operations=[
                migrations.CreateModel(
                    name='Order',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('order_id', models.CharField(max_length=50, unique=True, verbose_name='رقم الطلب')),
                        ('status', models.CharField(choices=[('pending', 'بانتظار الدفع'), ('processing', 'قيد التحضير'), ('shipped', 'تم الشحن'), ('delivered', 'تم التوصيل'), ('cancelled', 'ملغي')], default='pending', max_length=20, verbose_name='حالة الطلب')),
                        ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الطلب')),
                        ('paid_at', models.DateTimeField(blank=True, null=True, verbose_name='تاريخ الدفع')),
                        ('email', models.EmailField(blank=True, max_length=254, null=True, verbose_name='البريد الإلكتروني')),
                        ('shipping_address', models.TextField(blank=True, null=True, verbose_name='عنوان الشحن')),
                        ('phone_number', models.CharField(blank=True, max_length=20, null=True, verbose_name='رقم الهاتف')),
                        ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='orders', to=settings.AUTH_USER_MODEL, verbose_name='المستخدم')),
                    ],
                    options={
                        'verbose_name': 'طلب',
                        'verbose_name_plural': 'الطلبات',
                        'ordering': ['-created_at'],
                    },
                ),
                migrations.CreateModel(
                    name='OrderItem',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('quantity', models.PositiveIntegerField(default=1, verbose_name='الكمية')),
                        ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='boutiqe.order', verbose_name='الطلب')),
                        ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='boutiqe.product', verbose_name='المنتج')),
                    ],
                    options={
                        'verbose_name': 'عنصر الطلب',
                        'verbose_name_plural': 'عناصر الطلب',
                    },
                ),
            ]
        ),
    ] 