# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Müşteri Yönetimi Uygulaması Yapılandırması
"""

from django.apps import AppConfig


class CustomersConfig(AppConfig):
    name = 'apps.customers'
    verbose_name = 'Müşteri Yönetimi'
    
    def ready(self):
        import apps.customers.signals  # noqa 