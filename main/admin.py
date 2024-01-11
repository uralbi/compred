from django.contrib import admin
from .models import Product, Brand
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html


def set_brand_lumens(modeladmin, request, queryset):
    brand_id = 2  # Replace with the ID of the brand you want to set
    brand = Brand.objects.get(id=brand_id)
    queryset.update(brand=brand)

set_brand_lumens.short_description = "Set brand for Lumens"

class ProductAdmin (admin.ModelAdmin):
    list_display = ( 'image_th', 'code', 'info',  'price', 'id',)
    list_editable = ('price',)
    actions = [set_brand_lumens]
    search_fields = ['code']

    def image_th(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="60" height="60" />', obj.image.url)
        return "-"
    image_th.short_description = 'Image'

class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')

# Register your models here.
admin.site.register(Product, ProductAdmin)
admin.site.register(Brand, BrandAdmin)





