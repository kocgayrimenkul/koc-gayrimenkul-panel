# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Kimlik Doğrulama Admin Yapılandırması
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, UserRole
from django.contrib.auth.models import Group

# Admin panelinden orijinal Group'u kaldır
admin.site.unregister(Group)

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Kişisel Bilgiler'), {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'position', 'profile_photo', 'department')}),
        (_('İzinler'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Önemli Tarihler'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role_display', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'position')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions',)

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('group', 'description', 'is_default', 'priority')
    list_filter = ('is_default',)
    search_fields = ('group__name', 'description')
    ordering = ('-priority',)

# Group modelini görsel olarak UserRole üzerinden yönetmek için
admin.site.register(Group)
