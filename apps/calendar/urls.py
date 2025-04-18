# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Takvim/Ajanda URL Yapılandırması
"""

from django.urls import path
from . import views

urlpatterns = [
    # Takvim ana görünümü
    path('ajanda/', views.calendar_view, name='calendar'),
    
    # Etkinlik işlemleri
    path('ajanda/etkinlikler/', views.event_list, name='event_list'),
    path('ajanda/etkinlik/ekle/', views.event_create, name='event_create'),
    path('ajanda/etkinlik/ekle-form/', views.event_create_form, name='event_create_form'),
    path('ajanda/etkinlik/<int:event_id>/', views.event_detail, name='event_detail'),
    path('ajanda/etkinlik/duzenle/<int:event_id>/', views.event_update, name='event_update'),
    path('ajanda/etkinlik/sil/<int:event_id>/', views.event_delete, name='event_delete'),
    path('ajanda/etkinlik/tamamla/<int:event_id>/', views.event_complete, name='event_complete'),
    path('ajanda/etkinlik/yeniden-ac/<int:event_id>/', views.event_reopen, name='event_reopen'),
    
    # Yapılacaklar işlemleri
    path('ajanda/yapilacak/ekle/', views.todo_create, name='todo_create'),
    path('ajanda/yapilacak/duzenle/<int:todo_id>/', views.todo_update, name='todo_update'),
    path('ajanda/yapilacak/sil/<int:todo_id>/', views.todo_delete, name='todo_delete'),
    path('ajanda/yapilacak/durum/<int:todo_id>/', views.toggle_todo_status, name='toggle_todo_status'),
]
