# -*- coding: utf-8 -*-
from django.db import models
from django.conf import settings


class IncomingMessage(models.Model):
    """WhatsApp, Instagram, Facebook ve Web sitesinden gelen mesajlar"""

    PLATFORM_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('website', 'Web Sitesi'),
    ]

    STATUS_CHOICES = [
        ('new', 'Yeni'),
        ('replied', 'Yanıtlandı'),
        ('converted', 'Müşteriye Dönüştürüldü'),
        ('ignored', 'Yoksayıldı'),
    ]

    platform       = models.CharField('Platform', max_length=20, choices=PLATFORM_CHOICES)
    sender_id      = models.CharField('Gönderen ID', max_length=255)          # WhatsApp numarası, IG/FB user_id
    sender_name    = models.CharField('Gönderen Adı', max_length=255, blank=True)
    sender_phone   = models.CharField('Telefon', max_length=50, blank=True)
    message_text   = models.TextField('Mesaj')
    ai_response    = models.TextField('AI Yanıtı', blank=True)
    is_ai_replied  = models.BooleanField('AI Yanıtladı', default=False)

    customer       = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='incoming_messages',
        verbose_name='Müşteri'
    )
    assigned_to    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_messages',
        verbose_name='Atanan Personel'
    )

    status         = models.CharField('Durum', max_length=20, choices=STATUS_CHOICES, default='new')
    raw_data       = models.JSONField('Ham Veri', default=dict, blank=True)
    meta_message_id = models.CharField('Meta Mesaj ID', max_length=255, blank=True, unique=True, null=True)
    created_at     = models.DateTimeField('Alındı', auto_now_add=True)
    updated_at     = models.DateTimeField('Güncellendi', auto_now=True)

    class Meta:
        verbose_name = 'Gelen Mesaj'
        verbose_name_plural = 'Gelen Mesajlar'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_platform_display()}] {self.sender_name or self.sender_id} - {self.created_at:%d.%m.%Y %H:%M}"

    @property
    def platform_icon(self):
        icons = {
            'whatsapp': 'fab fa-whatsapp',
            'instagram': 'fab fa-instagram',
            'facebook': 'fab fa-facebook-messenger',
            'website': 'fas fa-globe',
        }
        return icons.get(self.platform, 'fas fa-comment')

    @property
    def platform_color(self):
        colors = {
            'whatsapp': '#25D366',
            'instagram': '#E1306C',
            'facebook': '#0084FF',
            'website': '#6366f1',
        }
        return colors.get(self.platform, '#64748b')


class AutoReplyTemplate(models.Model):
    """Otomatik yanıt şablonları — AI yanıtlayamazsa kullanılır"""
    platform    = models.CharField('Platform', max_length=20, choices=IncomingMessage.PLATFORM_CHOICES, blank=True)
    keyword     = models.CharField('Anahtar Kelime', max_length=100, blank=True, help_text='Boş bırakılırsa tüm mesajlara uygulanır')
    response    = models.TextField('Yanıt Metni')
    is_active   = models.BooleanField('Aktif', default=True)
    priority    = models.IntegerField('Öncelik', default=0)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Otomatik Yanıt Şablonu'
        verbose_name_plural = 'Otomatik Yanıt Şablonları'
        ordering = ['-priority']

    def __str__(self):
        return f"{self.keyword or 'Genel'} → {self.response[:50]}"
