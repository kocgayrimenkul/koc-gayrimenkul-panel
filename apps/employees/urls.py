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
    path('calisan/<int:employee_id>/sil/', views.employee_delete, name='employee_delete'),
    path('calisan/<int:employee_id>/durum-degistir/', views.employee_status_toggle, name='employee_status_toggle'),
    
    # Şifre yönetimi
    path('calisan/<int:employee_id>/sifre-degistir/', views.reset_password, name='reset_password'),
    
    # İzin yönetimi
    path('calisan/<int:employee_id>/izinler/', views.manage_permissions, name='manage_permissions'),
    path('calisan/<int:employee_id>/izinler-sifirla/', views.employee_permissions_reset, name='employee_permissions_reset'),
    path('calisan/<int:employee_id>/yetkileri-kaldir/', views.revoke_all_permissions, name='revoke_all_permissions'),
    
    # Toplu işlemler
    path('calisan/toplu-islemler/', views.bulk_employee_actions, name='bulk_employee_actions'),
    
    # Pozisyon yönetimi
    path('pozisyon/', views.position_list, name='position_list'),
    
    # Rol yönetimi
    path('rol/', views.role_list, name='role_list'),
    
    # Aktivite kayıtları
    path('aktivite/', views.activity_log, name='activity_log'),
    
    # Extension Management API Endpoints
    path('api/extensions/', views.employee_extensions_api, name='employee_extensions_api'),
    path('api/extensions/available/', views.available_extensions_api, name='available_extensions_api'),
    path('api/extensions/<int:employee_id>/assign/', views.assign_extension_api, name='assign_extension_api'),
    path('api/extensions/<int:employee_id>/remove/', views.remove_extension_api, name='remove_extension_api'),
]
