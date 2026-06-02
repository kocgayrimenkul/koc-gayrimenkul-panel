# -*- coding: utf-8 -*-
from django.db import models
from django.conf import settings

OFİS_CHOICES = [
    ('beykent',   'Beykent'),
    ('fistiklik', 'Fıstıklık'),
]

ODEME_YONTEMI = [
    ('nakit',       'Nakit'),
    ('havale',      'Havale / EFT'),
    ('kredi_karti', 'Kredi Kartı'),
    ('cek',         'Çek'),
    ('diger',       'Diğer'),
]

GIDER_KATEGORI = [
    ('kira',        'Kira'),
    ('maas',        'Maaş / Prim'),
    ('reklam',      'Reklam / Pazarlama'),
    ('fatura',      'Fatura'),
    ('arac',        'Araç / Yakıt'),
    ('kirtasiye',   'Kırtasiye / Ofis'),
    ('vergi',       'Vergi / SGK'),
    ('diger',       'Diğer'),
]

AY_CHOICES = [(i, f'{i}. Ay') for i in range(1, 13)]


class KaporaKayit(models.Model):
    """Henüz gerçekleşmemiş kapora kayıtları"""
    ofis        = models.CharField('Ofis', max_length=20, choices=OFİS_CHOICES)
    satan       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='satan_kaporalar', verbose_name='Satan')
    yer         = models.CharField('Yer', max_length=255)
    kapora      = models.DecimalField('Kapora (TL)', max_digits=12, decimal_places=2, default=0)
    ay          = models.IntegerField('Ay', choices=AY_CHOICES)
    yil         = models.IntegerField('Yıl')
    olusturan   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='olusturulan_kaporalar', verbose_name='Kaydeden')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Kapora'
        verbose_name_plural = 'Kaporalar'
        ordering = ['-yil', '-ay', '-created_at']

    def __str__(self):
        return f"{self.get_ofis_display()} - {self.yer} - {self.kapora} TL"


class GelirKayit(models.Model):
    """Gerçekleşmiş gelir kayıtları"""
    ofis            = models.CharField('Ofis', max_length=20, choices=OFİS_CHOICES)
    bulan           = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='bulan_gelirler', verbose_name='Bulan')
    satan           = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='satan_gelirler', verbose_name='Satan')
    yer             = models.CharField('Yer', max_length=255)
    gelir           = models.DecimalField('Gelir (TL)', max_digits=12, decimal_places=2, default=0)
    kapora          = models.DecimalField('Kapora (TL)', max_digits=12, decimal_places=2, default=0)
    toplam          = models.DecimalField('Toplam (TL)', max_digits=12, decimal_places=2, default=0)
    ay              = models.IntegerField('Ay', choices=AY_CHOICES)
    yil             = models.IntegerField('Yıl')
    olusturan       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='olusturulan_gelirler', verbose_name='Kaydeden')
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Gelir'
        verbose_name_plural = 'Gelirler'
        ordering = ['-yil', '-ay', '-created_at']

    def save(self, *args, **kwargs):
        self.toplam = (self.gelir or 0) + (self.kapora or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_ofis_display()} - {self.yer} - {self.toplam} TL"


class Gider(models.Model):
    """Gider kaydı"""
    tarih           = models.DateField('Tarih')
    tutar           = models.DecimalField('Tutar (TL)', max_digits=12, decimal_places=2)
    kategori        = models.CharField('Kategori', max_length=50, choices=GIDER_KATEGORI)
    aciklama        = models.TextField('Açıklama', blank=True)
    odeme_yontemi   = models.CharField('Ödeme Yöntemi', max_length=20, choices=ODEME_YONTEMI, default='nakit')
    personel        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='giderler', verbose_name='İlgili Personel')
    belge           = models.FileField('Belge', upload_to='muhasebe/gider/', blank=True, null=True)
    olusturan       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='olusturulan_giderler', verbose_name='Kaydeden')
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Gider'
        verbose_name_plural = 'Giderler'
        ordering = ['-tarih', '-created_at']

    def __str__(self):
        return f"{self.tarih} - {self.get_kategori_display()} - {self.tutar} TL"
