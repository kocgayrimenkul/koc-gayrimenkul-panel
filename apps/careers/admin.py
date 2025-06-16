# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Kariyer Admin
"""

from django.contrib import admin
from .models import JobApplication, JobPosting


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


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ['title', 'department', 'employment_type', 'location', 'is_active', 'deadline', 'created_at']
    list_filter = ['department', 'employment_type', 'is_active', 'created_at']
    search_fields = ['title', 'description', 'requirements']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('İlan Bilgileri', {
            'fields': ['title', 'department', 'employment_type', 'location']
        }),
        ('İlan İçeriği', {
            'fields': ['description', 'requirements', 'qualifications', 'benefits']
        }),
        ('Diğer Bilgiler', {
            'fields': ['salary_range', 'experience_required', 'deadline']
        }),
        ('Sistem Bilgileri', {
            'fields': ['is_active', 'created_at', 'updated_at']
        }),
    ]
