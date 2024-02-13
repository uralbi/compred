from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import DictionaryEntry


class DictionaryAdmin(admin.ModelAdmin):
    list_display = ('kyrgyz_word', 'russian_translation', 'part_of_speech', 'updated_at')
    search_fields = ['kyrgyz_word', 'russian_translation']

admin.site.register(DictionaryEntry, DictionaryAdmin)
