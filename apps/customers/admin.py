# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Müşteri Yönetimi Admin Yapılandırması
"""

from django.contrib import admin
from .models import Customer, Neighborhood, CustomerReminder

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'neighborhood', 'consultant', 'created_at', 'meeting_status', 'response_date', 'reminder_date')
    list_filter = ('meeting_status', 'neighborhood', 'consultant', 'source')
    search_fields = ('full_name', 'phone', 'notes')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('full_name', 'phone', 'neighborhood', 'consultant')
        }),
        ('Görüşme Bilgileri', {
            'fields': ('meeting_status', 'meeting_result', 'response_date', 'reminder_date', 'source', 'notes')
        }),
        ('Sistem Bilgileri', {
            'fields': ('created_at',)
        }),
    )

@admin.register(Neighborhood)
class NeighborhoodAdmin(admin.ModelAdmin):
    list_display = ('name', 'district', 'consultant')
    list_filter = ('district', 'consultant')
    search_fields = ('name', 'district')

@admin.register(CustomerReminder)
class CustomerReminderAdmin(admin.ModelAdmin):
    list_display = ('customer', 'reminder_date', 'is_sent', 'is_read', 'created_at')
    list_filter = ('reminder_date', 'is_sent', 'is_read')
    search_fields = ('customer__full_name', 'message')
    date_hierarchy = 'reminder_date'
    readonly_fields = ('created_at',) 