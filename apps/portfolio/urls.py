# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Portföy URL Yapılandırması
"""

from django.urls import path, re_path
from . import views
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Gayrimenkul listeleme ve filtreleme
    path('gayrimenkul/', views.property_list, name='property_list'),
    
    # Gayrimenkul detay görünümü
    path('gayrimenkul/<int:property_id>/', views.property_detail, name='property_detail'),
    
    # Gayrimenkul ekleme
    path('gayrimenkul/ekle/', views.property_create, name='property_create'),
    
    # Gayrimenkul güncelleme
    path('gayrimenkul/duzenle/<int:property_id>/', views.property_update, name='property_update'),
    
    # Gayrimenkul görsel yükleme
    path('property-image-upload/', views.property_image_upload, name='property_image_upload'),
    
    # Gayrimenkul görsel silme
    path('property-image-delete/', views.property_image_delete, name='property_image_delete'),
    
    # AJAX ile gayrimenkul alan değişiklikleri
    path('property-update-field/', views.property_update_field, name='property_update_field'),
    
    # Gayrimenkul silme
    path('gayrimenkul/sil/<int:property_id>/', views.property_delete, name='property_delete'),
    
    # API URL'leri
    path('api/properties/', views.api_properties, name='api_properties'),
    
    path('image-delete/', views.property_image_delete, name='image-delete'),
    path('image-update-main/', views.image_update_main, name='image-update-main'),
    path('image-update-order/', views.image_update_order, name='image-update-order'),
] 

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

