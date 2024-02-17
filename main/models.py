from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from PIL import Image
from pathlib import Path
from io import BytesIO
from django.core.files import File


def image_process(image):
    width, height = 600, 600
    img = Image.open(image)
    ch_width, ch_height = img.size
    if ch_width <= 600 or ch_height <= 600:
        return
    if img.width > width or img.height > height:
        output_size = (width, height)
        img.thumbnail(output_size)
        img_filename = Path(image.file.name).stem  # file name without the extension
        cur_w, cur_h = img.size
        img_ratio = round(cur_w / cur_h, 2)
        if img_ratio < 0.8: # Vertical cropping
            cr_size = (cur_h - cur_w) / 2.2
            top = cr_size
            bottom = cur_h - cr_size
            img = img.crop((0, top, cur_w, bottom))
        elif img_ratio > 1.6: # Horizontal cropping
            cr_size = (cur_w - cur_h) / 2.7
            left = cr_size
            right = cur_w - cr_size
            img = img.crop((left, 0, right, cur_h))

        buffer = BytesIO()
        img.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)  # Move to the beginning of the BytesIO buffer before saving
        new_img_filename = f"{img_filename}.png"
        image.save(new_img_filename, File(buffer), save=False)


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
