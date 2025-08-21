# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Satış Süreç Yönetimi Admin
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    SalesStage, Lead, LeadNote, StageTransition, Task, 
    Appointment, WhatsAppMessage, CallLog
)


@admin.register(SalesStage)
class SalesStageAdmin(admin.ModelAdmin):
    list_display = ['name', 'stage_type', 'order', 'is_active', 'auto_transition_enabled']
    list_filter = ['stage_type', 'is_active', 'auto_transition_enabled']
    search_fields = ['name', 'description']
    ordering = ['stage_type', 'order']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('name', 'slug', 'stage_type', 'order', 'description', 'is_active')
        }),
        ('Otomatik Geçiş Ayarları', {
            'fields': ('auto_transition_enabled', 'auto_transition_condition'),
            'classes': ('collapse',)
        })
    )


class LeadNoteInline(admin.TabularInline):
    model = LeadNote
    extra = 0
    readonly_fields = ['created_at']
    fields = ['note_type', 'title', 'content', 'is_important', 'created_by', 'created_at']


class StageTransitionInline(admin.TabularInline):
    model = StageTransition
    extra = 0
    readonly_fields = ['created_at']
    fields = ['from_stage', 'to_stage', 'transition_type', 'reason', 'performed_by', 'created_at']


class TaskInline(admin.TabularInline):
    model = Task
    extra = 0
    readonly_fields = ['created_at']
    fields = ['task_type', 'title', 'assigned_to', 'priority', 'status', 'due_date', 'created_at']


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = [
        'customer_name', 'customer_phone', 'current_stage', 'assigned_staff', 
        'status', 'priority', 'source', 'contract_signed', 'created_at'
    ]
    list_filter = [
        'current_stage', 'status', 'priority', 'source', 'contract_signed', 
        'payment_type', 'deed_completed', 'satisfaction_survey_sent'
    ]
    search_fields = ['customer_name', 'customer_phone', 'customer_email']
    ordering = ['-created_at']
    readonly_fields = ['lead_id', 'created_at', 'updated_at']
    
    inlines = [LeadNoteInline, StageTransitionInline, TaskInline]
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('lead_id', 'customer', 'assigned_staff', 'current_stage', 'status', 'priority')
        }),
        ('Müşteri Bilgileri', {
            'fields': ('customer_name', 'customer_phone', 'customer_email', 'source')
        }),
        ('Gayrimenkul İlgisi', {
            'fields': ('interested_property', 'neighborhood', 'budget_min', 'budget_max'),
            'classes': ('collapse',)
        }),
        ('Sözleşme Bilgileri', {
            'fields': (
                'contract_signed', 'contract_date', 'payment_type', 'contract_amount',
                'deed_transfer_date', 'deed_completed'
            ),
            'classes': ('collapse',)
        }),
        ('Memnuniyet Anketi', {
            'fields': ('satisfaction_survey_sent', 'satisfaction_score', 'satisfaction_feedback'),
            'classes': ('collapse',)
        }),
        ('Sticky Assignment', {
            'fields': ('original_staff',),
            'classes': ('collapse',)
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'updated_at', 'last_contact_date', 'next_follow_up_date'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'customer', 'assigned_staff', 'current_stage', 'interested_property'
        )


@admin.register(LeadNote)
class LeadNoteAdmin(admin.ModelAdmin):
    list_display = ['lead', 'note_type', 'title', 'created_by', 'is_important', 'created_at']
    list_filter = ['note_type', 'is_important', 'created_at']
    search_fields = ['lead__customer_name', 'title', 'content']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('lead', 'created_by')


@admin.register(StageTransition)
class StageTransitionAdmin(admin.ModelAdmin):
    list_display = ['lead', 'from_stage', 'to_stage', 'transition_type', 'performed_by', 'created_at']
    list_filter = ['transition_type', 'from_stage', 'to_stage', 'created_at']
    search_fields = ['lead__customer_name', 'reason']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'lead', 'from_stage', 'to_stage', 'performed_by'
        )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        'lead', 'task_type', 'title', 'assigned_to', 'priority', 
        'status', 'due_date', 'is_automatic'
    ]
    list_filter = ['task_type', 'priority', 'status', 'is_automatic', 'due_date']
    search_fields = ['lead__customer_name', 'title', 'description']
    ordering = ['due_date', '-priority']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('lead', 'task_type', 'title', 'description', 'assigned_to')
        }),
        ('Durum ve Öncelik', {
            'fields': ('priority', 'status', 'due_date', 'completed_at')
        }),
        ('Otomatik Görev', {
            'fields': ('is_automatic', 'auto_complete_condition'),
            'classes': ('collapse',)
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('lead', 'assigned_to')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'lead', 'appointment_type', 'title', 'scheduled_date', 
        'assigned_staff', 'status', 'customer_confirmed'
    ]
    list_filter = ['appointment_type', 'status', 'customer_confirmed', 'scheduled_date']
    search_fields = ['lead__customer_name', 'title', 'location']
    ordering = ['scheduled_date']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('lead', 'appointment_type', 'title', 'description')
        }),
        ('Zaman ve Yer', {
            'fields': ('scheduled_date', 'duration_minutes', 'location')
        }),
        ('Katılımcılar', {
            'fields': ('assigned_staff', 'customer_confirmed')
        }),
        ('Durum ve Sonuç', {
            'fields': ('status', 'result_notes')
        }),
        ('İlgili Gayrimenkul', {
            'fields': ('property',),
            'classes': ('collapse',)
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'lead', 'assigned_staff', 'property'
        )


@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = [
        'lead', 'direction', 'message_type', 'status', 
        'template_name', 'sent_by', 'created_at'
    ]
    list_filter = ['direction', 'message_type', 'status', 'template_language', 'created_at']
    search_fields = ['lead__customer_name', 'content', 'template_name']
    ordering = ['-created_at']
    readonly_fields = ['message_id', 'created_at', 'delivered_at', 'read_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('lead', 'message_id', 'direction', 'message_type', 'sent_by')
        }),
        ('Mesaj İçeriği', {
            'fields': ('content', 'media_url')
        }),
        ('Durum', {
            'fields': ('status', 'error_message')
        }),
        ('Şablon Bilgileri', {
            'fields': ('template_name', 'template_language'),
            'classes': ('collapse',)
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'delivered_at', 'read_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('lead', 'sent_by')


@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    list_display = [
        'lead', 'call_type', 'caller_number', 'called_number', 
        'handled_by', 'status', 'duration_formatted', 'recording_available', 'started_at'
    ]
    list_filter = ['call_type', 'status', 'recording_available', 'started_at']
    search_fields = ['lead__customer_name', 'caller_number', 'called_number', 'notes']
    ordering = ['-started_at']
    readonly_fields = ['call_id', 'duration_formatted', 'created_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('lead', 'call_id', 'call_type', 'handled_by')
        }),
        ('Çağrı Bilgileri', {
            'fields': ('caller_number', 'called_number', 'status', 'duration_seconds')
        }),
        ('Kayıt', {
            'fields': ('recording_url', 'recording_available')
        }),
        ('Zaman Bilgileri', {
            'fields': ('started_at', 'ended_at', 'created_at')
        }),
        ('Notlar', {
            'fields': ('notes',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('lead', 'handled_calls')
    
    def duration_formatted(self, obj):
        return obj.duration_formatted
    duration_formatted.short_description = 'Süre'
