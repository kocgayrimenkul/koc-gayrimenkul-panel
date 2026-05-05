# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Portföy Yönetimi Sinyalleri
"""

from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from .models import Property, PropertyImage, PropertyEnvironment


@receiver(pre_save, sender=Property)
def track_price_change(sender, instance, **kwargs):
    """Fiyat değiştiğinde otomatik olarak PropertyPriceHistory kaydı oluştur"""
    if not instance.pk:
        return  # Yeni kayıt, geçmiş yok

    try:
        old = Property.objects.get(pk=instance.pk)
        if old.price != instance.price:
            from .models import PropertyPriceHistory
            PropertyPriceHistory.objects.create(
                property=instance,
                old_price=old.price,
                new_price=instance.price,
            )
    except Property.DoesNotExist:
        pass
