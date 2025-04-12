# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Takvim/Ajanda Modülleri
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.customers.models import Customer
from apps.portfolio.models import Property

class Event(models.Model):
    """Takvim Etkinlikleri"""
    
    EVENT_TYPE_CHOICES = [
        ('meeting', 'Toplantı'),
        ('viewing', 'Gayrimenkul Gösterimi'),
        ('call', 'Telefon Görüşmesi'),
        ('reminder', 'Hatırlatıcı'),
        ('appointment', 'Randevu'),
        ('task', 'Görev'),
        ('other', 'Diğer'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Etkinlik Başlığı")
    description = models.TextField(verbose_name="Açıklama", blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, verbose_name="Etkinlik Tipi")
    start_time = models.DateTimeField(verbose_name="Başlangıç Zamanı")
    end_time = models.DateTimeField(verbose_name="Bitiş Zamanı", null=True, blank=True)
    location = models.CharField(max_length=200, verbose_name="Konum", blank=True)
    
    # İlişkili kayıtlar
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name="events", verbose_name="Müşteri")
    property = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name="events", verbose_name="Gayrimenkul")
    consultant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="events", 
                                  verbose_name="Danışman")
    
    # Durum bilgisi
    is_completed = models.BooleanField(default=False, verbose_name="Tamamlandı")
    completed_at = models.DateTimeField(verbose_name="Tamamlanma Zamanı", null=True, blank=True)
    notes = models.TextField(verbose_name="Notlar", blank=True)
    
    # Sistem bilgileri
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name="created_events", verbose_name="Oluşturan")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name="updated_events", verbose_name="Güncelleyen")
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Etkinlik"
        verbose_name_plural = "Etkinlikler"
        ordering = ['-start_time']

class TodoItem(models.Model):
    """Yapılacaklar Listesi"""
    
    PRIORITY_CHOICES = [
        ('yuksek', 'Yüksek'),
        ('orta', 'Orta'),
        ('dusuk', 'Düşük'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Başlık")
    description = models.TextField(verbose_name="Açıklama", blank=True)
    due_date = models.DateField(verbose_name="Son Tarih", null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='orta', verbose_name="Öncelik")
    is_completed = models.BooleanField(default=False, verbose_name="Tamamlandı")
    
    # İlişkiler
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="todos", verbose_name="Kullanıcı")
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name="todos", verbose_name="Müşteri")
    property = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True, 
                               related_name="todos", verbose_name="Gayrimenkul")
    
    # Sistem bilgileri
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Yapılacak"
        verbose_name_plural = "Yapılacaklar"
        ordering = ['-created_at']
