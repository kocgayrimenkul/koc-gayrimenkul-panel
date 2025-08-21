# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Satış Süreç Yönetimi App Konfigürasyonu
"""

from django.apps import AppConfig


class SalesProcessConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.sales_process'
    verbose_name = 'Satış Süreç Yönetimi'
    
    def ready(self):
        import apps.sales_process.signals
