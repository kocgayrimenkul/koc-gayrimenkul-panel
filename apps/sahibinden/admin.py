from django.contrib import admin
from .models import SahibindenSettings, SahibindenSyncLog

@admin.register(SahibindenSettings)
class SahibindenSettingsAdmin(admin.ModelAdmin):
    list_display = ['api_token', 'auto_sync_enabled', 'last_import_at', 'last_export_at']

@admin.register(SahibindenSyncLog)
class SahibindenSyncLogAdmin(admin.ModelAdmin):
    list_display = ['property', 'sahibinden_listing_id', 'status', 'last_synced_at']
    list_filter = ['status', 'direction']
