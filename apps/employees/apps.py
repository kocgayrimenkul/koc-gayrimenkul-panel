# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Çalışan Yönetimi Uygulaması Yapılandırması
"""

from django.apps import AppConfig


class EmployeesConfig(AppConfig):
    name = 'apps.employees'
    verbose_name = 'Çalışan Yönetimi'
    
    def ready(self):
        import apps.employees.signals  # noqa
