# Generated by Django 5.0 on 2025-05-13 17:45

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boutiqe', '0004_contactinfo_remove_cart_unique_user_session_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderitem',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='تاريخ الإضافة'),
        ),
    ]
