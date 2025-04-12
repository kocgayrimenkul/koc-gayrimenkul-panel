# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Takvim/Ajanda Sinyalleri
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import Event, TodoItem

# Burada gelecekte gerekirse signal tanımları eklenebilir
# Örneğin, bir etkinlik oluşturulduğunda bildirim gönderme gibi

# @receiver(post_save, sender=Event)
# def event_created_handler(sender, instance, created, **kwargs):
#     if created:
#         # Yeni etkinlik oluşturulduğunda yapılacak işler
#         pass 