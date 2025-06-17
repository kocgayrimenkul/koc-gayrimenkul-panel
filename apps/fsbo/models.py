# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - FSBO (For Sale By Owner) Modülleri
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.employees.models import EmployeeProfile
from apps.customers.models import Neighborhood

class FSBO(models.Model):
    """FSBO (For Sale By Owner - Sahibinden Satılık) aramaları için model"""
    
    RESULT_CHOICES = [
        ('bekliyor', 'Bekliyor'),
        ('olumlu', 'Olumlu'),
        ('olumsuz', 'Olumsuz'),
        ('aranmadi', 'Aranmadı'),
    ]
    
    REMINDER_STATUS_CHOICES = [
        ('kapali', 'Kapalı'),
        ('acik', 'Açık'),
    ]
    
    CONTACT_TYPE_CHOICES = [
        ('bilgi_alma', 'Bilgi Alma'),
        ('daire_sunumu', 'Daire Sunumu'),
        ('sikayet', 'Şikayet'),
    ]
    
    # Temel bilgiler
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Kayıt Tarihi")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                 null=True, related_name="created_fsbos", verbose_name="Oluşturan")
    full_name = models.CharField(max_length=100, verbose_name="Adı Soyadı")
    phone = models.CharField(max_length=20, verbose_name="Telefon")
    
    # İşlem sonucu
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default='bekliyor', verbose_name="Sonuç")
    
    # Danışmana yönlendirme
    consultant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                 null=True, blank=True, related_name="assigned_fsbos", 
                                 verbose_name="Danışman")
    
    # İletişim türü
    contact_type = models.CharField(max_length=50, choices=CONTACT_TYPE_CHOICES, 
                                   default='bilgi_alma', verbose_name="İletişim Türü")
    
    # Linkler
    link1 = models.URLField(blank=True, null=True, verbose_name="Link 1")
    link2 = models.URLField(blank=True, null=True, verbose_name="Link 2")
    
    # Hatırlatıcı
    reminder_status = models.CharField(max_length=10, choices=REMINDER_STATUS_CHOICES, 
                                     default='kapali', verbose_name="Hatırlatıcı Durumu")
    reminder_date = models.DateField(null=True, blank=True, verbose_name="Hatırlatıcı Tarihi")
    reminder_time = models.TimeField(null=True, blank=True, verbose_name="Hatırlatıcı Saati")
    
    # Görüşme notları
    notes = models.TextField(blank=True, null=True, verbose_name="Görüşme Notları")
    
    def __str__(self):
        return f"{self.full_name} - {self.phone}"
    
    class Meta:
        verbose_name = "FSBO"
        verbose_name_plural = "FSBO'lar"
        ordering = ['-created_at']
        
        
class FSBOLog(models.Model):
    """FSBO işlem günlüğü"""
    fsbo = models.ForeignKey(FSBO, on_delete=models.CASCADE, related_name="logs", verbose_name="FSBO")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                           null=True, related_name="fsbo_logs", verbose_name="Kullanıcı")
    action = models.CharField(max_length=200, verbose_name="İşlem")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Zaman")
    details = models.TextField(blank=True, verbose_name="Detaylar")
    
    def __str__(self):
        return f"{self.fsbo.full_name} - {self.action} - {self.timestamp}"
    
    class Meta:
        verbose_name = "FSBO Log"
        verbose_name_plural = "FSBO Logları"
        ordering = ['-timestamp']
