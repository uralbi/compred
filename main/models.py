from django.db import models

class Product(models.Model):
    image = models.ImageField(upload_to='lumens/', verbose_name='Фото')  # Assuming media is set up for image uploads
    code = models.CharField(max_length=100, verbose_name='Артикул')       # Unique article number or identifier
    info = models.TextField(verbose_name='Описание')                        # Detailed information about the product
    price = models.IntegerField()  # Price with two decimal places for cents
    brand = models.ForeignKey('Brand', on_delete=models.PROTECT, null=True, blank=True,  verbose_name='Бренд')

    def __str__(self):
        return self.code


class Brand(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self) -> str:
        return self.name