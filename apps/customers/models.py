# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Müşteriler Modülleri
"""

from django.db import models
from django.conf import settings
from django.utils import timezone

class Neighborhood(models.Model):
    """Mahalle bilgisi ve bağlı danışman"""
    name = models.CharField(max_length=100, verbose_name="Mahalle Adı")
    consultant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name="neighborhoods", verbose_name="Bağlı Danışman")
    district = models.CharField(max_length=100, verbose_name="İlçe", blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Mahalle"
        verbose_name_plural = "Mahalleler"
        ordering = ['name']

class Customer(models.Model):
    """Müşteri kayıt bilgileri"""
    MEETING_STATUS_CHOICES = [
        ('bekliyor', 'Bekliyor'),
        ('olumlu', 'Olumlu'),
        ('olumsuz', 'Olumsuz'),
    ]
    
    SOURCE_CHOICES = [
        ('branda', 'Branda'),
        ('sahibinden', 'Sahibinden'),
        ('referans', 'Referans'),
        ('emlakjet', 'Emlakjet'),
        ('sosyal_medya', 'Sosyal Medya'),
        ('diger', 'Diğer'),
    ]
    
    CONTACT_TYPE_CHOICES = [
        ('bilgi_alma', 'Bilgi Alma'),
        ('daire_sunumu', 'Daire Sunumu'),
        ('sikayet', 'Şikayet'),
    ]
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Kayıt Tarihi")
    full_name = models.CharField(max_length=100, verbose_name="Adı Soyadı")
    phone = models.CharField(max_length=20, verbose_name="Telefon")
    neighborhood = models.ForeignKey(Neighborhood, on_delete=models.CASCADE, verbose_name="Mahalle")
    consultant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name="customers", verbose_name="Danışman")
    
    # Eklenen yeni alanlar
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, blank=True, null=True, verbose_name="Müşteri Kaynağı")
    contact_type = models.CharField(max_length=50, choices=CONTACT_TYPE_CHOICES, default='bilgi_alma', verbose_name="İletişim Türü")
    
    meeting_result = models.TextField(verbose_name="Görüşme Sonucu", blank=True)
    meeting_status = models.CharField(max_length=20, choices=MEETING_STATUS_CHOICES, 
                                     default='bekliyor', verbose_name="Görüşme Durumu")
    response_date = models.DateField(verbose_name="Geri Dönüş Tarihi", null=True, blank=True, 
                                    help_text="Danışmanın müşteriye geri dönüş yaptığı tarih")
    reminder_date = models.DateField(verbose_name="Hatırlatma Tarihi", null=True, blank=True, 
                                    help_text="Bu tarihte sistem otomatik olarak hatırlatma bildirecek")
    notes = models.TextField(verbose_name="Notlar", blank=True, null=True)
    
    def save(self, *args, **kwargs):
        # Eğer yeni bir kayıtsa ve danışman atanmamışsa, mahalledeki danışmanı ata
        if not self.pk and not self.consultant and self.neighborhood and self.neighborhood.consultant:
            self.consultant = self.neighborhood.consultant
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.full_name
    
    class Meta:
        verbose_name = "Müşteri"
        verbose_name_plural = "Müşteriler"
        ordering = ['-created_at']

# Bildirim modeli ekleyelim
class CustomerReminder(models.Model):
    """Müşteri hatırlatma bildirimleri"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="reminders", 
                                verbose_name="Müşteri")
    reminder_date = models.DateField(verbose_name="Hatırlatma Tarihi")
    message = models.TextField(verbose_name="Hatırlatma Mesajı")
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False, verbose_name="Okundu mu?")
    is_sent = models.BooleanField(default=False, verbose_name="Gönderildi mi?")
    
    def __str__(self):
        return f"{self.customer.full_name} - {self.reminder_date}"
    
    class Meta:
        verbose_name = "Müşteri Hatırlatma"
        verbose_name_plural = "Müşteri Hatırlatmaları"
        ordering = ['-reminder_date']
