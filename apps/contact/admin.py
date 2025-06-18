# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - İletişim Admin
"""

from django.contrib import admin
from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'property_type', 'status', 'created_at']
    list_filter = ['status', 'property_type', 'created_at']
    search_fields = ['name', 'email', 'message']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Kişi Bilgileri', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Mesaj Bilgileri', {
            'fields': ('property_type', 'message')
        }),
        ('Durum', {
            'fields': ('status', 'created_at')
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        return True
    
    def has_add_permission(self, request):
        return False  # Mesajlar sadece frontend'den gelir
