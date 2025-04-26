# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Müşteri Yönetimi Admin Yapılandırması
"""

from django.contrib import admin
from .models import Customer, Neighborhood

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'neighborhood', 'meeting_status', 'response_date', 'created_at', 'consultant')
    list_filter = ('meeting_status', 'neighborhood', 'consultant', 'response_date')
    search_fields = ('full_name', 'phone', 'apartment', 'notes')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('full_name', 'phone', 'neighborhood', 'apartment', 'consultant')
        }),
        ('Görüşme Bilgileri', {
            'fields': ('meeting_status', 'meeting_result', 'response_date')
        }),
        ('Ek Bilgiler', {
            'fields': ('notes',)
        }),
    )

@admin.register(Neighborhood)
class NeighborhoodAdmin(admin.ModelAdmin):
    list_display = ('name', 'district', 'consultant')
    list_filter = ('consultant',)
    search_fields = ('name', 'district') 