# Generated by Django 4.2 on 2024-01-23 18:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_remove_promotions_code_remove_promotions_image_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='promotions',
            name='product',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='main.product', verbose_name='Пром-товар'),
        ),
    ]
