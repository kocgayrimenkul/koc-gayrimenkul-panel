# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Çalışan Yönetimi URL Yapılandırması
"""

from django.urls import path
from . import views

urlpatterns = [
    # Çalışan listeleme ve yönetim
    path('calisan/', views.employee_list, name='employee_list'),
    path('calisan/ekle/', views.employee_create, name='employee_create'),
    path('calisan/<int:employee_id>/', views.employee_edit, name='employee_edit'),
    
    # Şifre yönetimi
    path('calisan/<int:employee_id>/sifre-degistir/', views.reset_password, name='reset_password'),
    
    # İzin yönetimi
    path('calisan/<int:employee_id>/izinler/', views.manage_permissions, name='manage_permissions'),
    
    # Pozisyon yönetimi
    path('pozisyon/', views.position_list, name='position_list'),
    
    # Rol yönetimi
    path('rol/', views.role_list, name='role_list'),
    
    # Aktivite kayıtları
    path('aktivite/', views.activity_log, name='activity_log'),
]
