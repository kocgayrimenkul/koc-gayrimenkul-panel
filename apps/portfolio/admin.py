# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Portföy Yönetimi Admin Yapılandırması
"""

from django.contrib import admin
from .models import Property, PropertyImage, PropertyEnvironment, VideoJob

# Inline modeller
class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 0
    fields = ['image', 'title', 'order']

class PropertyEnvironmentInline(admin.TabularInline):
    model = PropertyEnvironment
    extra = 0
    fields = ['place_name', 'distance']

# Ana modeller
@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['apartment_name', 'web_title', 'property_type', 'status', 'price', 'neighborhood', 'created_at', 'is_active']
    list_filter = ['status', 'property_type', 'is_active', 'neighborhood', 'consultant']
    search_fields = ['apartment_name', 'web_title', 'address', 'owner_name', 'owner_phone']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PropertyImageInline, PropertyEnvironmentInline]
    fieldsets = [
        ('Temel Bilgiler', {
            'fields': [
                'apartment_name', 'web_title', 'description', 'property_type', 'status', 'price', 'category', 'listing_type',
                'is_active'
            ]
        }),
        ('Lokasyon', {
            'fields': [
                'neighborhood', 'address', 'map_coordinates'
            ]
        }),
        ('Detay Bilgiler', {
            'fields': [
                'gross_area', 'net_area', 'room_count', 'floor', 'building_age', 
                'heating', 'has_balcony', 'dues', 'floor_count', 'bathroom_count',
                'usage_status', 'is_furnished', 'is_in_site', 'is_exchangeable'
            ]
        }),
        ('Diğer Bilgiler', {
            'fields': [
                'deed_status', 'is_suitable_for_credit', 'is_bargainable'
            ]
        }),
        ('Portföy Sahibi Bilgileri', {
            'fields': [
                'owner_name', 'owner_phone', 'owner_listing_number', 'emlakjet_listing_number',
                'hepsiemlak_listing_number', 'website_listing_number', 'branda_number'
            ]
        }),
        ('Operasyonel Bilgiler', {
            'fields': [
                'key_holder', 'photo_status', 'banner_status', 'listing_date', 'consultant'
            ]
        }),
        ('Sistem Bilgileri', {
            'fields': [
                'created_at', 'updated_at'
            ]
        }),
    ]

@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'property', 'title', 'order']
    list_filter = ['property']
    search_fields = ['property__apartment_name', 'title']


@admin.register(VideoJob)
class VideoJobAdmin(admin.ModelAdmin):
    list_display  = ['id', 'property', 'created_by', 'status', 'resolution', 'aspect_ratio', 'created_at']
    list_filter   = ['status', 'resolution', 'aspect_ratio']
    search_fields = ['property__apartment_name', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at']