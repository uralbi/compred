from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

app_name = 'ads'

router = DefaultRouter()
router.register(r'entries', DictionaryEntryViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('search-kg/', search_by_kyrgyz_word, name='search_by_kyrgyz_word'),
    path('search-ru/', search_by_russian_word, name='search_by_russian_word'),
]