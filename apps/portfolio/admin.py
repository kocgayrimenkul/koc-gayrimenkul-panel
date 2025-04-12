# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Portföy Yönetimi Admin Yapılandırması
"""

from django.contrib import admin
from .models import Property, PropertyEnvironment, PropertyImage

class PropertyEnvironmentInline(admin.TabularInline):
    model = PropertyEnvironment
    extra = 1

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'property_type', 'status', 'price', 'neighborhood', 'is_active', 'listing_date', 'consultant')
    list_filter = ('property_type', 'status', 'neighborhood', 'is_active', 'consultant')
    search_fields = ('title', 'description', 'address', 'owner_name')
    date_hierarchy = 'listing_date'
    inlines = [PropertyEnvironmentInline, PropertyImageInline]

@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'title', 'order')
    list_filter = ('property',)
    search_fields = ('property__title', 'title') 