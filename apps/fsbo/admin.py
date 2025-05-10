# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - FSBO Admin Panel Yapılandırması
"""

from django.contrib import admin
from .models import FSBO, FSBOLog

@admin.register(FSBO)
class FSBOAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'result', 'consultant', 'created_at')
    list_filter = ('result', 'reminder_status', 'created_at')
    search_fields = ('full_name', 'phone', 'notes')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('full_name', 'phone', 'created_by', 'created_at')
        }),
        ('Sonuç', {
            'fields': ('result', 'consultant')
        }),
        ('Linkler', {
            'fields': ('link1', 'link2')
        }),
        ('Hatırlatıcı', {
            'fields': ('reminder_status', 'reminder_date', 'reminder_time')
        }),
        ('Notlar', {
            'fields': ('notes',)
        }),
    )

@admin.register(FSBOLog)
class FSBOLogAdmin(admin.ModelAdmin):
    list_display = ('fsbo', 'user', 'action', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('fsbo__full_name', 'user__username', 'action', 'details')
    date_hierarchy = 'timestamp'
    readonly_fields = ('fsbo', 'user', 'action', 'timestamp', 'details')
