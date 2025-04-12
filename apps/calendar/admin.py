# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Takvim/Ajanda Admin Yapılandırması
"""

from django.contrib import admin
from .models import Event, TodoItem

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'start_time', 'end_time', 'is_completed', 'consultant')
    list_filter = ('event_type', 'is_completed', 'consultant')
    search_fields = ('title', 'description', 'location')
    date_hierarchy = 'start_time'

@admin.register(TodoItem)
class TodoItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'due_date', 'is_completed', 'user')
    list_filter = ('priority', 'is_completed', 'user')
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at' 