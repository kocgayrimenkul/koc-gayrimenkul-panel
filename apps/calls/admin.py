# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Calls Admin
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import CallLog


@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'direction', 'caller', 'called', 'customer_link', 'duration_formatted', 'status', 'recording_link')
    list_filter = ('direction', 'status', 'start_time')
    search_fields = ('caller', 'called', 'customer__full_name', 'call_id')
    readonly_fields = ('recording_link', 'created_at', 'duration_formatted')
    date_hierarchy = 'start_time'
    
    fieldsets = (
        ('Çağrı Bilgileri', {
            'fields': ('call_id', 'direction', 'status')
        }),
        ('Telefon Numaraları', {
            'fields': ('caller', 'called', 'extension')
        }),
        ('Zaman Bilgileri', {
            'fields': ('start_time', 'end_time', 'duration', 'duration_formatted')
        }),
        ('İlişkiler', {
            'fields': ('customer', 'user')
        }),
        ('Kayıt', {
            'fields': ('recording_url', 'recording_link')
        }),
        ('Meta', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def customer_link(self, obj):
        """Müşteri linkini göster"""
        if obj.customer:
            return format_html(
                '<a href="/admin/customers/customer/{}/change/">{}</a>',
                obj.customer.id,
                obj.customer.full_name or obj.customer.phone
            )
        return "-"
    customer_link.short_description = "Müşteri"

    def recording_link(self, obj):
        """Kayıt dinleme linki"""
        if obj.recording_url:
            return format_html(
                '<audio controls><source src="{}" type="audio/wav">Tarayıcınız ses oynatmayı desteklemiyor.</audio>',
                obj.recording_url
            )
        return "-"
    recording_link.short_description = "Kayıt Dinle"