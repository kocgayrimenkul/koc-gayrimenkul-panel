# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Müşteri Yönetimi Sinyalleri
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import Customer, Neighborhood

# Burada gelecekte gerekirse signal tanımları eklenebilir
# Örneğin, bir müşteri kaydedildiğinde otomatik bildirim gönderme gibi 