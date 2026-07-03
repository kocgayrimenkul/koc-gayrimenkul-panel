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
    recording_url = models.TextField('Kayıt', blank=True, null=True, default='')
    notes = models.TextField('Notlar', blank=True, null=True)
    is_returned = models.BooleanField('Geri Donus Yapildi', default=False)
    returned_at = models.DateTimeField('Geri Donus Zamani', null=True, blank=True)
    returned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='returned_calls',
        verbose_name='Geri Donus Yapan'
    )
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
    
    @staticmethod
    def normalize_phone(raw: str) -> str:
        """Ham telefon numarasını 05xxxxxxxxx formatına çevir."""
        clean = ''.join(filter(str.isdigit, raw or ''))
        if clean.startswith('90') and len(clean) >= 11:
            clean = '0' + clean[2:]
        elif not clean.startswith('0') and clean:
            clean = '0' + clean
        return clean

    def save(self, *args, **kwargs):
        """Kaydederken müşteriyi, personeli eşleştir; geri dönüş mantığını çalıştır."""

        # Müşteriyi bul
        if not self.customer:
            from apps.customers.models import Customer
            raw = self.caller if self.direction == 'inbound' else self.called
            phone = self.normalize_phone(raw)
            if phone:
                self.customer = Customer.objects.filter(phone=phone).first()

        # Personeli bul
        if not self.user:
            from apps.authentication.models import CustomUser
            raw = self.caller if self.direction == 'outbound' else self.called
            phone = self.normalize_phone(raw)
            if phone:
                self.user = CustomUser.objects.filter(phone_number=phone).first()

        super().save(*args, **kwargs)

        # ── Geri dönüş otomasyonu ──────────────────────────────────────────
        # update_fields ile çağrılmışsa bu blok atlanır (sonsuz döngü engeli)
        if kwargs.get('update_fields'):
            return

        from django.utils import timezone as tz
        cutoff = tz.now() - timezone.timedelta(days=7)
        MISSED = ('missed', 'busy', 'failed')

        if self.direction == 'outbound':
            # Personel bir numara aradı → o numaradan gelen cevapsız çağrıları kapat
            target = self.normalize_phone(self.called)
            if target:
                unresolved = CallLog.objects.filter(
                    direction='inbound',
                    status__in=MISSED,
                    is_returned=False,
                    start_time__gte=cutoff,
                    caller__icontains=target[-9:],   # son 9 haneden eşle
                )
                unresolved.update(
                    is_returned=True,
                    returned_at=self.start_time,
                    returned_by=self.user,
                )

        elif self.direction == 'inbound' and self.status == 'answered':
            # Müşteri geri aradı ve cevaplandı → kendi numarasındaki cevapsızları kapat
            target = self.normalize_phone(self.caller)
            if target:
                unresolved = CallLog.objects.filter(
                    direction='inbound',
                    status__in=MISSED,
                    is_returned=False,
                    start_time__gte=cutoff,
                    caller__icontains=target[-9:],
                ).exclude(pk=self.pk)
                unresolved.update(
                    is_returned=True,
                    returned_at=self.start_time,
                    returned_by=self.user,
                )