# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Portföy Yönetimi Uygulaması Yapılandırması
"""

from django.apps import AppConfig


class PortfolioConfig(AppConfig):
    name = 'apps.portfolio'
    verbose_name = 'Portföy Yönetimi'
    
    def ready(self):
        import apps.portfolio.signals  # noqa 