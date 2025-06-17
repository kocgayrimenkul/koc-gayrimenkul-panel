# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Çalışan Yönetimi Admin Yapılandırması
"""

from django.contrib import admin
from .models import Position, EmployeeProfile, Permission, ActivityLog

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'position', 'phone', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email', 'phone')

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('employee', 'can_view_customers', 'can_view_portfolio', 'can_view_calendar', 'can_view_reports')
    list_filter = ('can_view_customers', 'can_view_portfolio', 'can_view_calendar', 'can_view_reports')
    search_fields = ('employee__user__username', 'employee__user__first_name', 'employee__user__last_name')
    
    fieldsets = (
        ('Müşteri Yönetimi', {
            'fields': ('can_view_customers', 'can_add_customers', 'can_edit_customers', 'can_delete_customers'),
            'classes': ('collapse',)
        }),
        ('Portföy Yönetimi', {
            'fields': ('can_view_portfolio', 'can_add_portfolio', 'can_edit_portfolio', 'can_delete_portfolio'),
            'classes': ('collapse',)
        }),
        ('Takvim Yönetimi', {
            'fields': ('can_view_calendar', 'can_add_calendar', 'can_edit_calendar', 'can_delete_calendar'),
            'classes': ('collapse',)
        }),
        ('FSBO Yönetimi', {
            'fields': ('can_view_fsbo', 'can_add_fsbo', 'can_edit_fsbo', 'can_delete_fsbo'),
            'classes': ('collapse',)
        }),
        ('Prezentasyon Yönetimi', {
            'fields': ('can_view_presentation', 'can_add_presentation', 'can_edit_presentation', 'can_delete_presentation'),
            'classes': ('collapse',)
        }),
        ('Kariyer Yönetimi', {
            'fields': ('can_view_careers', 'can_add_careers', 'can_edit_careers', 'can_delete_careers'),
            'classes': ('collapse',)
        }),
        ('Çalışan Yönetimi', {
            'fields': ('can_view_employees', 'can_add_employees', 'can_edit_employees', 'can_delete_employees'),
            'classes': ('collapse',)
        }),
        ('Sistem İzinleri', {
            'fields': ('can_view_reports', 'can_manage_settings', 'can_access_api'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'action', 'details')
    date_hierarchy = 'timestamp'
    readonly_fields = ('user', 'action', 'timestamp', 'details')
