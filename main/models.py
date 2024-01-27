from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Product(models.Model):
    image = models.ImageField(upload_to='lumens/', verbose_name='Фото')
    code = models.CharField(max_length=100, verbose_name='Артикул')
    info = models.TextField(verbose_name='Описание')
    price = models.IntegerField()
    brand = models.ForeignKey('Brand', on_delete=models.PROTECT, null=True, blank=True,  verbose_name='Бренд')

    def __str__(self):
        return self.code


class Brand(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self) -> str:
        return self.name


class Promotions(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, verbose_name="Пром-товар", null=True, blank=True)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f'{self.product}'


class Margin(models.Model):
    brand = models.ForeignKey('Brand', on_delete=models.PROTECT, verbose_name='Бренд')
    margin = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(99)]
    )

    def __str__(self):
        return f"{self.brand} - {self.margin}%"
