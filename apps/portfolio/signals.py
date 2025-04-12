# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Portföy Yönetimi Sinyalleri
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import Property, PropertyImage, PropertyEnvironment

# Burada gelecekte gerekirse signal tanımları eklenebilir
# Örneğin, yeni bir portföy eklendiğinde otomatik bildirim gönderme gibi 