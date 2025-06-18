# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - İletişim URL Konfigürasyonu
"""

from django.urls import path
from .views import (
    # API Views
    ContactMessageCreateView,
    ContactMessageListView,
    ContactMessageDetailView,
    # Template Views (sadece listeleme ve detay)
    contact_list,
    contact_detail,
)

app_name = 'contact'

urlpatterns = [
    # API URL'leri (korundu)
    path('api/messages/', ContactMessageCreateView.as_view(), name='api-message-create'),
    path('api/messages/list/', ContactMessageListView.as_view(), name='api-message-list'),
    path('api/messages/<int:pk>/', ContactMessageDetailView.as_view(), name='api-message-detail'),
    
    # Template-based URL'ler (sadece listeleme ve detay)
    path('', contact_list, name='contact_list'),
    path('<int:pk>/', contact_detail, name='contact_detail'),
] 