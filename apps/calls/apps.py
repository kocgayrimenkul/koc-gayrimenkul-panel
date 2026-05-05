# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Çağrı Kayıtları Uygulama Yapılandırması
"""

from django.apps import AppConfig


class CallsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.calls'
    verbose_name = 'Çağrı Kayıtları'