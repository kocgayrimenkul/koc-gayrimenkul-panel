# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Daire Sunumu Admin
"""

from django.contrib import admin
from .models import Presentation, PresentationFeedback

class PresentationFeedbackInline(admin.TabularInline):
    model = PresentationFeedback
    extra = 0

@admin.register(Presentation)
class PresentationAdmin(admin.ModelAdmin):
    list_display = ('title', 'property', 'presenter', 'presentation_date', 'customer_name', 'status')
    list_filter = ('status', 'presentation_date', 'property__property_type')
    search_fields = ('title', 'customer_name', 'customer_phone', 'notes')
    date_hierarchy = 'presentation_date'
    inlines = [PresentationFeedbackInline]

@admin.register(PresentationFeedback)
class PresentationFeedbackAdmin(admin.ModelAdmin):
    list_display = ('presentation', 'rating', 'feedback_date')
    list_filter = ('rating', 'feedback_date')
    search_fields = ('comments',)
