# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Kariyer Admin
"""

from django.contrib import admin
from .models import JobApplication


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone', 'position', 'experience', 'status', 'created_at']
    list_filter = ['position', 'experience', 'status', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at', 'cv_filename']
    
    fieldsets = [
        ('Kişisel Bilgiler', {
            'fields': ['first_name', 'last_name', 'email', 'phone']
        }),
        ('Başvuru Bilgileri', {
            'fields': ['position', 'experience', 'cover_letter']
        }),
        ('CV Dosyası', {
            'fields': ['cv_file', 'cv_filename']
        }),
        ('Değerlendirme', {
            'fields': ['status', 'notes']
        }),
        ('Sistem Bilgileri', {
            'fields': ['created_at', 'updated_at']
        }),
    ]
    
    def has_delete_permission(self, request, obj=None):
        # Sadece superuser silebilir
        return request.user.is_superuser
