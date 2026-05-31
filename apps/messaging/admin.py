from django.contrib import admin
from .models import IncomingMessage, AutoReplyTemplate


@admin.register(IncomingMessage)
class IncomingMessageAdmin(admin.ModelAdmin):
    list_display = ['platform', 'sender_name', 'sender_phone', 'message_text', 'status', 'is_ai_replied', 'created_at']
    list_filter  = ['platform', 'status', 'is_ai_replied']
    search_fields = ['sender_name', 'sender_phone', 'message_text']
    readonly_fields = ['created_at', 'updated_at', 'raw_data']


@admin.register(AutoReplyTemplate)
class AutoReplyTemplateAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'platform', 'response', 'priority', 'is_active']
    list_filter  = ['platform', 'is_active']
