# -*- encoding: utf-8 -*-
"""
Context processors for template variables
"""
from django.conf import settings

def settings_context(request):
    """Template'lerde settings değişkenlerine erişim sağlar"""
    return {
        'settings': settings
    } 