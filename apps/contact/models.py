# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - İletişim Modülleri
"""

from django.db import models
from django.utils import timezone


class ContactMessage(models.Model):
    """İletişim Mesaj Modeli"""
    
    PROPERTY_CHOICES = [
        ('satilik', 'Satılık'),
        ('kiralik', 'Kiralık'),
        ('proje', 'Proje'),
        ('diger', 'Diğer'),
    ]
    
    STATUS_CHOICES = [
        ('yeni', 'Yeni'),
        ('okundu', 'Okundu'),
        ('tamamlandi', 'Tamamlandı'),
    ]
    
    # Temel bilgiler
    name = models.CharField(max_length=100, verbose_name="Ad Soyad")
    email = models.EmailField(verbose_name="E-posta")
    phone = models.CharField(max_length=20, verbose_name="Telefon", blank=True)
    property_type = models.CharField(
        max_length=20, 
        choices=PROPERTY_CHOICES, 
        verbose_name="Gayrimenkul Tercihi",
        blank=True
    )
    message = models.TextField(verbose_name="Mesaj")
    
    # Sistem bilgileri
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='yeni', 
        verbose_name="Durum"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Tarih")
    
    def __str__(self):
        return f"{self.name} - {self.get_property_type_display() or 'Genel'}"
    
    @property
    def is_new(self):
        return self.status == 'yeni'
    
    class Meta:
        verbose_name = "İletişim Mesajı"
        verbose_name_plural = "İletişim Mesajları"
        ordering = ['-created_at']
