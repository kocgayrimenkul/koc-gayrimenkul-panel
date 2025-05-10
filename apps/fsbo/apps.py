# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - FSBO Uygulama Yapılandırması
"""

from django.apps import AppConfig


class FsboConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.fsbo'
    verbose_name = 'FSBO Yönetimi'
    
    def ready(self):
        import apps.fsbo.signals  # Sinyalleri yükle
