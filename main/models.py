from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from PIL import Image
from pathlib import Path
from io import BytesIO
from django.core.files import File


def image_process(image):
    width, height = 600, 600
    img = Image.open(image)
    print('original image :', img.size)
    if img.width > width or img.height > height:
        output_size = (width, height)
        img.thumbnail(output_size)
        img_filename = Path(image.file.name).name
        idx = img_filename.find('.')
        img_format = img_filename[idx + 1:]
        cur_w, cur_h = img.size
        img_ratio = round(cur_w/cur_h, 2)
        if img_ratio < 0.8:
            cr_size = (cur_h - cur_w) / 2.2
            img = img.crop((0, cr_size, cur_w , cur_h - cr_size))
        elif img_ratio > 1.6:
            cr_size = (cur_w - cur_h) / 2.7
            img = img.crop((0 + cr_size, 0, cur_w - cr_size, cur_h))
        buffer = BytesIO()
        img.save(buffer, format='png')
        file_object = File(buffer)
        image.save(img_filename, file_object)
    print('after image image :', img.size)


class Product(models.Model):
    image = models.ImageField(upload_to='lumens/', verbose_name='Фото')
    code = models.CharField(max_length=100, verbose_name='Артикул')
    info = models.TextField(verbose_name='Описание')
    price = models.IntegerField()
    brand = models.ForeignKey('Brand', on_delete=models.PROTECT, null=True, blank=True,  verbose_name='Бренд')

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        if self.image:
            image_process(self.image)
        super().save(*args, **kwargs)

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
