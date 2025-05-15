from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('boutiqe', '0003_product_is_new_product_is_sale_product_sku_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='discount',
            name='slug',
            field=models.SlugField(blank=True, null=True, unique=True),
        ),
    ] 