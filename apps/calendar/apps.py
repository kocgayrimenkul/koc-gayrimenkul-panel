# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Takvim/Ajanda Uygulaması Yapılandırması
"""

from django.apps import AppConfig


class CalendarConfig(AppConfig):
    name = 'apps.calendar'
    verbose_name = 'Takvim ve Ajanda'
    
    def ready(self):
        import apps.calendar.signals  # noqa 