# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Çağrı Kayıtları Modelleri
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class CallLog(models.Model):
    """NetGSM Çağrı Kayıtları"""
    
    DIRECTION_CHOICES = [
        ('inbound', 'Gelen'),
        ('outbound', 'Giden'),
        ('internal', 'İç Arama'),
    ]
    
    STATUS_CHOICES = [
        ('ringing', 'Çalıyor'),
        ('answered', 'Cevaplandı'),
        ('completed', 'Tamamlandı'),
        ('missed', 'Cevapsız'),
        ('busy', 'Meşgul'),
        ('failed', 'Başarısız'),
    ]
    
    call_id = models.CharField('Çağrı ID', max_length=255, unique=True)
    customer = models.ForeignKey(
        'customers.Customer', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='call_logs',
        verbose_name='Müşteri'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='call_logs',
        verbose_name='Personel'
    )
    direction = models.CharField('Yön', max_length=20, choices=DIRECTION_CHOICES)
    caller = models.CharField('Arayan', max_length=50)
    called = models.CharField('Aranan', max_length=50)
    extension = models.CharField('Dahili', max_length=20, blank=True, null=True, default='')
    start_time = models.DateTimeField('Başlangıç')
    end_time = models.DateTimeField('Bitiş', null=True, blank=True)
    duration = models.IntegerField('Süre (saniye)', default=0)
    status = models.CharField('Durum', max_length=20, choices=STATUS_CHOICES)
    recording_url = models.URLField('Kayıt', blank=True, null=True)
    notes = models.TextField('Notlar', blank=True, null=True)
    created_at = models.DateTimeField('Oluşturma', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Çağrı Kaydı'
        verbose_name_plural = 'Çağrı Kayıtları'
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.get_direction_display()} - {self.caller} → {self.called}"
    
    def duration_formatted(self):
        """Süreyi HH:MM:SS formatında döndür"""
        if self.duration:
            hours = self.duration // 3600
            minutes = (self.duration % 3600) // 60
            seconds = self.duration % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return "00:00:00"
    
    def save(self, *args, **kwargs):
        """Kaydederken müşteriyi ve personeli otomatik eşleştir"""
        
        # Müşteriyi bul
        if not self.customer:
            from apps.customers.models import Customer
            phone = self.caller if self.direction == 'inbound' else self.called
            if phone:
                # Telefonu temizle
                clean_phone = ''.join(filter(str.isdigit, phone))
                if clean_phone.startswith('90'):
                    clean_phone = '0' + clean_phone[2:]
                elif not clean_phone.startswith('0'):
                    clean_phone = '0' + clean_phone
                
                self.customer = Customer.objects.filter(phone=clean_phone).first()
        
        # Personeli bul
        if not self.user:
            from apps.authentication.models import CustomUser
            phone = self.caller if self.direction == 'outbound' else self.called
            if phone:
                clean_phone = ''.join(filter(str.isdigit, phone))
                if clean_phone.startswith('90'):
                    clean_phone = '0' + clean_phone[2:]
                elif not clean_phone.startswith('0'):
                    clean_phone = '0' + clean_phone
                
                self.user = CustomUser.objects.filter(phone_number=clean_phone).first()
        
        super().save(*args, **kwargs)