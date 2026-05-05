from django.db import models
from apps.portfolio.models import Property


class SahibindenSettings(models.Model):
    """Sahibinden API ayarları (tek kayıt)"""
    api_token = models.CharField(max_length=500, blank=True, verbose_name="API Token")
    office_id = models.CharField(max_length=100, blank=True, verbose_name="Ofis ID")
    feed_url_override = models.URLField(blank=True, verbose_name="XML Feed URL (otomatik üretilir)")
    auto_sync_enabled = models.BooleanField(default=False, verbose_name="Otomatik Senkronizasyon")
    last_import_at = models.DateTimeField(null=True, blank=True, verbose_name="Son İçe Aktarma")
    last_export_at = models.DateTimeField(null=True, blank=True, verbose_name="Son Dışa Aktarma")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sahibinden Ayarları"
        verbose_name_plural = "Sahibinden Ayarları"

    def __str__(self):
        return "Sahibinden API Ayarları"

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class SahibindenSyncLog(models.Model):
    """Her ilanın Sahibinden senkronizasyon durumu"""

    STATUS_CHOICES = [
        ('pending', 'Bekliyor'),
        ('synced', 'Senkronize'),
        ('error', 'Hata'),
        ('deleted', 'Silindi'),
    ]

    DIRECTION_CHOICES = [
        ('export', 'Panel → Sahibinden'),
        ('import', 'Sahibinden → Panel'),
    ]

    property = models.OneToOneField(
        Property,
        on_delete=models.CASCADE,
        related_name='sahibinden_sync',
        verbose_name="Gayrimenkul"
    )
    sahibinden_listing_id = models.CharField(max_length=100, blank=True, verbose_name="Sahibinden İlan No")
    sahibinden_url = models.URLField(max_length=500, blank=True, verbose_name="Sahibinden URL")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Durum")
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, default='export', verbose_name="Yön")
    last_synced_at = models.DateTimeField(null=True, blank=True, verbose_name="Son Senkronizasyon")
    error_message = models.TextField(blank=True, verbose_name="Hata Mesajı")
    sync_count = models.PositiveIntegerField(default=0, verbose_name="Senkronizasyon Sayısı")
    include_in_feed = models.BooleanField(default=True, verbose_name="XML Feed'e Dahil Et")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sahibinden Senkronizasyon"
        verbose_name_plural = "Sahibinden Senkronizasyonları"
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.property} — {self.get_status_display()}"
