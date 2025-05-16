# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Müşteri Yönetimi Sinyalleri
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import Customer, Neighborhood, CustomerReminder
from django.utils import timezone

# Burada gelecekte gerekirse signal tanımları eklenebilir
# Örneğin, bir müşteri kaydedildiğinde otomatik bildirim gönderme gibi 

@receiver(post_save, sender=Customer)
def create_reminder_for_customer(sender, instance, created, **kwargs):
    """Müşteri kaydedildiğinde veya güncellendiğinde hatırlatma tarihi kontrol edilir"""
    if instance.reminder_date:
        # Hatırlatma tarihi değiştiyse veya yeni eklendiyse
        existing_reminder = CustomerReminder.objects.filter(
            customer=instance,
            is_sent=False  # Henüz gönderilmemiş hatırlatma
        ).first()
        
        if existing_reminder:
            # Eğer tarih değiştiyse, mevcut hatırlatmayı güncelle
            if existing_reminder.reminder_date != instance.reminder_date:
                existing_reminder.reminder_date = instance.reminder_date
                existing_reminder.message = f"{instance.full_name} ile ilgili hatırlatma. Not: {instance.notes}"
                existing_reminder.is_read = False  # Tarih değiştiğinde okundu bilgisini sıfırla
                existing_reminder.save()
        else:
            # Yeni bir hatırlatma oluştur
            CustomerReminder.objects.create(
                customer=instance,
                reminder_date=instance.reminder_date,
                message=f"{instance.full_name} ile ilgili hatırlatma. Not: {instance.notes}"
            ) 