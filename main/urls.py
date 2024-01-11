from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('clear-session/', clear_session, name='clear_session'),
    path('update-quantity', update_quantity, name='update_quantity'),
    path('delete-product', delete_product, name='delete_product'),
    path('add-to-cart/', add_to_cart, name='add-to-cart'),
    path('download-excel/', download_excel, name='download_excel'),
    ]


