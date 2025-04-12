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
    list_display = ('employee', 'can_manage_employees', 'can_view_reports')
    list_filter = ('can_manage_employees', 'can_view_reports')
    search_fields = ('employee__user__username', 'employee__user__first_name', 'employee__user__last_name')

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'action', 'details')
    date_hierarchy = 'timestamp'
    readonly_fields = ('user', 'action', 'timestamp', 'details')
