# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - FSBO URL Yapılandırması
"""

from django.urls import path
from . import views

urlpatterns = [
    # FSBO liste sayfası
    path('', views.fsbo_list, name='fsbo_list'),
    
    # FSBO yönetimi
    path('create/', views.fsbo_create, name='fsbo_create'),
    path('edit/<int:fsbo_id>/', views.fsbo_edit, name='fsbo_edit'),
    path('detail/<int:fsbo_id>/', views.fsbo_detail, name='fsbo_detail'),
    path('delete/<int:fsbo_id>/', views.fsbo_delete, name='fsbo_delete'),
    
    # AJAX işlemleri
    path('search/', views.fsbo_search, name='fsbo_search'),
    
    # Hatırlatıcılar
    path('reminders/today/', views.fsbo_reminders_today, name='fsbo_reminders_today'),
] 