# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Müşteriler URL Yapılandırması
"""

from django.urls import path, re_path
from . import views

urlpatterns = [
    # Müşteri listeleme ve filtreleme
    path('musteri/', views.customer_list, name='customer_list'),
    
    # Müşteri detay görünümü
    path('musteri/<int:customer_id>/', views.customer_detail, name='customer_detail'),
    
    # Müşteri oluşturma görünümü
    path('musteri/ekle/', views.customer_create, name='customer_create'),
    
    # Müşteri düzenleme görünümü
    path('musteri/duzenle/<int:customer_id>/', views.customer_edit, name='customer_edit'),
    
    # Müşteri kayıt (Santral için)
    path('musteri-kayit/', views.customer_register, name='customer_register'),
    
    # AJAX ile müşteri durumu güncelleme
    path('musteri/durum/<int:customer_id>/', views.update_meeting_status, name='update_meeting_status'),
    
    # Mahalle yönetimi
    path('mahalle/', views.neighborhood_list, name='neighborhood_list'),
    path('mahalle/ekle/', views.neighborhood_edit, name='neighborhood_add'),
    path('mahalle/duzenle/<int:neighborhood_id>/', views.neighborhood_edit, name='neighborhood_edit'),
    
    # Danışmanlar JSON
    path('api/mahalle/<int:neighborhood_id>/danismanlar/', views.consultants_by_neighborhood, name='consultants_by_neighborhood'),
]
