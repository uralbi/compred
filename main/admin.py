from django.contrib import admin
from .models import Product, Brand, Promotions, Margin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.utils.safestring import mark_safe

def to_promote(self, request, queryset):
        for product in queryset:
            existing_promotion = Promotions.objects.filter(product=product).first()
            if not existing_promotion:
                Promotions.objects.create(product=product)
        self.message_user(request, f'Selected products added to promotions.')

to_promote.short_description = 'Add to Promotion'


def set_brand_lumens(modeladmin, request, queryset):
    brand_id = 2  # Replace with the ID of the brand you want to set
    brand = Brand.objects.get(id=brand_id)
    queryset.update(brand=brand)

set_brand_lumens.short_description = "Set brand for Lumens"

class ProductAdmin (admin.ModelAdmin):
    list_display = ( 'image_th', 'code', 'info',  'price', 'id',)
    list_editable = ('price',)
    actions = [set_brand_lumens, to_promote]
    search_fields = ['code']

    def image_th(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="60" height="60" />', obj.image.url)
        return "-"
    image_th.short_description = 'Image'

class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')

class PromotionAdmin(admin.ModelAdmin):
    list_display = ( 'Image', 'product', 'quantity')
    list_editable = ('quantity',)

    def Image(self, obj):
        if obj.product:
            return mark_safe(f'<img src="{obj.product.image.url}" width="50" height="50" />')
        return "No Product"

    Image.short_description = 'Image'

class MarginAdmin(admin.ModelAdmin):
    list_display = ('brand', 'margin')
    list_editable = ('margin',)

# Register your models here.
admin.site.register(Product, ProductAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(Promotions, PromotionAdmin)
admin.site.register(Margin, MarginAdmin)




