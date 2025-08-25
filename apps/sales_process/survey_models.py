# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Anket Sistemi Modülleri
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
import uuid
import secrets


class Survey(models.Model):
    """
    Müşteri memnuniyet anketi modeli
    """
    
    STATUS_CHOICES = [
        ('created', 'Oluşturuldu'),
        ('sent', 'Gönderildi'),
        ('completed', 'Tamamlandı'),
        ('expired', 'Süresi Doldu'),
    ]
    
    SURVEY_TYPE_CHOICES = [
        ('satisfaction', 'Memnuniyet Anketi'),
        ('feedback', 'Geri Bildirim'),
        ('service_quality', 'Hizmet Kalitesi'),
    ]
    
    # Temel bilgiler
    survey_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Anket ID")
    lead = models.ForeignKey('Lead', on_delete=models.CASCADE, related_name="surveys", verbose_name="Lead")
    survey_type = models.CharField(max_length=20, choices=SURVEY_TYPE_CHOICES, default='satisfaction', verbose_name="Anket Tipi")
    
    # Anket linki için güvenli token
    access_token = models.CharField(max_length=64, unique=True, verbose_name="Erişim Token")
    
    # Durum bilgileri
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created', verbose_name="Durum")
    
    # Tarih bilgileri
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Gönderilme Tarihi")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Tamamlanma Tarihi")
    expires_at = models.DateTimeField(verbose_name="Son Geçerlilik Tarihi")
    
    # WhatsApp mesaj bilgileri
    whatsapp_message_id = models.CharField(max_length=100, blank=True, verbose_name="WhatsApp Mesaj ID")
    whatsapp_sent = models.BooleanField(default=False, verbose_name="WhatsApp Gönderildi")
    
    # Anket sonuçları
    overall_satisfaction = models.PositiveIntegerField(null=True, blank=True, verbose_name="Genel Memnuniyet (1-5)")
    service_quality_rating = models.PositiveIntegerField(null=True, blank=True, verbose_name="Hizmet Kalitesi (1-5)")
    staff_performance_rating = models.PositiveIntegerField(null=True, blank=True, verbose_name="Personel Performansı (1-5)")
    communication_rating = models.PositiveIntegerField(null=True, blank=True, verbose_name="İletişim (1-5)")
    process_speed_rating = models.PositiveIntegerField(null=True, blank=True, verbose_name="İşlem Hızı (1-5)")
    
    # Açık uçlu sorular
    positive_feedback = models.TextField(blank=True, verbose_name="Olumlu Geri Bildirim")
    improvement_suggestions = models.TextField(blank=True, verbose_name="İyileştirme Önerileri")
    additional_comments = models.TextField(blank=True, verbose_name="Ek Yorumlar")
    
    # Referans sorusu
    would_recommend = models.BooleanField(null=True, blank=True, verbose_name="Tavsiye Eder misiniz?")
    referral_likelihood = models.PositiveIntegerField(null=True, blank=True, verbose_name="Tavsiye Etme Olasılığı (1-10)")
    
    # İstatistik bilgileri
    view_count = models.PositiveIntegerField(default=0, verbose_name="Görüntülenme Sayısı")
    last_viewed_at = models.DateTimeField(null=True, blank=True, verbose_name="Son Görüntülenme")
    completion_time_seconds = models.PositiveIntegerField(null=True, blank=True, verbose_name="Tamamlanma Süresi (saniye)")
    
    def save(self, *args, **kwargs):
        if not self.access_token:
            self.access_token = secrets.token_urlsafe(32)
        
        # Varsayılan olarak 30 gün geçerlilik süresi
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=30)
            
        super().save(*args, **kwargs)
    
    @property
    def survey_url(self):
        """Anket URL'ini döndürür"""
        return f"/survey/{self.access_token}/"
    
    @property
    def full_survey_url(self):
        """Tam anket URL'ini döndürür (domain ile birlikte)"""
        from django.contrib.sites.models import Site
        current_site = Site.objects.get_current()
        return f"https://{current_site.domain}{self.survey_url}"
    
    @property
    def is_expired(self):
        """Anketin süresi dolmuş mu?"""
        return timezone.now() > self.expires_at
    
    @property
    def is_completed(self):
        """Anket tamamlanmış mı?"""
        return self.status == 'completed'
    
    @property
    def average_rating(self):
        """Ortalama puanı hesaplar"""
        ratings = [
            self.overall_satisfaction,
            self.service_quality_rating,
            self.staff_performance_rating,
            self.communication_rating,
            self.process_speed_rating
        ]
        valid_ratings = [r for r in ratings if r is not None]
        if valid_ratings:
            return sum(valid_ratings) / len(valid_ratings)
        return None
    
    def mark_as_sent(self, whatsapp_message_id=None):
        """Anketi gönderildi olarak işaretler"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.whatsapp_sent = True
        if whatsapp_message_id:
            self.whatsapp_message_id = whatsapp_message_id
        self.save()
    
    def mark_as_completed(self):
        """Anketi tamamlandı olarak işaretler"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        
        # Lead modelindeki satisfaction_score'u güncelle
        if self.overall_satisfaction:
            self.lead.satisfaction_score = self.overall_satisfaction
            self.lead.satisfaction_feedback = self.additional_comments or self.positive_feedback
            self.lead.save()
    
    def increment_view_count(self):
        """Görüntülenme sayısını artırır"""
        self.view_count += 1
        self.last_viewed_at = timezone.now()
        self.save(update_fields=['view_count', 'last_viewed_at'])
    
    def __str__(self):
        return f"{self.lead.customer_name} - {self.get_survey_type_display()} ({self.get_status_display()})"
    
    class Meta:
        verbose_name = "Anket"
        verbose_name_plural = "Anketler"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['access_token']),
            models.Index(fields=['lead', 'status']),
            models.Index(fields=['status', 'expires_at']),
        ]


class SurveyResponse(models.Model):
    """
    Anket yanıtları için detaylı log modeli
    """
    
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="responses", verbose_name="Anket")
    question_key = models.CharField(max_length=100, verbose_name="Soru Anahtarı")
    question_text = models.TextField(verbose_name="Soru Metni")
    answer_value = models.TextField(verbose_name="Yanıt Değeri")
    answer_type = models.CharField(max_length=20, verbose_name="Yanıt Tipi")  # rating, text, boolean
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yanıtlanma Tarihi")
    
    def __str__(self):
        return f"{self.survey} - {self.question_key}: {self.answer_value}"
    
    class Meta:
        verbose_name = "Anket Yanıtı"
        verbose_name_plural = "Anket Yanıtları"
        ordering = ['-created_at']
        unique_together = ['survey', 'question_key']