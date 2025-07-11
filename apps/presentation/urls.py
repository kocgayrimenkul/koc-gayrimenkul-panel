# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Daire Sunumu URL Yapılandırması
"""

from django.urls import path
from . import views

urlpatterns = [
    # Daire sunumu sayfaları
    path('daire-sunumu/', views.presentation_list, name='presentation_list'),
    path('daire-sunumu/ekle/', views.presentation_create, name='presentation_create'),
    path('daire-sunumu/<int:presentation_id>/', views.presentation_detail, name='presentation_detail'),
    path('daire-sunumu/<int:presentation_id>/duzenle/', views.presentation_edit, name='presentation_edit'),
    path('daire-sunumu/<int:presentation_id>/sil/', views.presentation_delete, name='presentation_delete'),
    
    # AJAX işlemleri
    path('daire-sunumu/<int:presentation_id>/durum-guncelle/', views.update_presentation_status, name='update_presentation_status'),
    path('daire-sunumu/mahalle-danismani/', views.get_neighborhood_consultant, name='get_neighborhood_consultant'),
    path('daire-sunumu/daire-ara/', views.property_search_ajax, name='property_search_ajax'),
] 