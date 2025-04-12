# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Portföy Modülleri
"""

from django.db import models
from django.conf import settings
from apps.customers.models import Neighborhood
from django.utils import timezone

class Property(models.Model):
    """Portföy / Emlak İlan Modeli"""
    
    # Kategori Seçenekleri
    PROPERTY_TYPE_CHOICES = [
        ('daire', 'Daire'),
        ('arsa', 'Arsa'),
        ('isyeri', 'İşyeri'),
    ]
    
    STATUS_CHOICES = [
        ('satilik', 'Satılık'),
        ('kiralik', 'Kiralık'),
    ]
    
    HEATING_CHOICES = [
        ('dogalgaz', 'Doğalgaz'),
        ('merkezi', 'Merkezi Sistem'),
        ('klima', 'Klima'),
        ('soba', 'Soba'),
        ('yok', 'Isıtma Yok'),
    ]
    
    DEED_STATUS_CHOICES = [
        ('kat_mulkiyetli', 'Kat Mülkiyetli'),
        ('kat_irtifakli', 'Kat İrtifaklı'),
        ('arsa', 'Arsa'),
        ('diger', 'Diğer'),
    ]
    
    KEY_HOLDER_CHOICES = [
        ('sahibi', 'Ev Sahibi'),
        ('danisman', 'Emlak Danışmanı'),
        ('kiracı', 'Kiracı'),
        ('diger', 'Diğer'),
    ]
    
    # Temel Bilgiler
    title = models.CharField(max_length=200, verbose_name="İlan Başlığı")
    description = models.TextField(verbose_name="Açıklama")
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES, verbose_name="Emlak Tipi")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name="Durum")
    price = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Fiyat")
    
    # Lokasyon Bilgileri
    neighborhood = models.ForeignKey(Neighborhood, on_delete=models.CASCADE, verbose_name="Mahalle")
    address = models.TextField(verbose_name="Açık Adres", blank=True)
    
    # Detay Bilgiler - Daire için
    gross_area = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Brüt m²", null=True, blank=True)
    net_area = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Net m²", null=True, blank=True)
    room_count = models.CharField(max_length=20, verbose_name="Oda Sayısı", blank=True)
    floor = models.CharField(max_length=20, verbose_name="Bulunduğu Kat", blank=True)
    building_age = models.PositiveSmallIntegerField(verbose_name="Bina Yaşı", null=True, blank=True)
    heating = models.CharField(max_length=20, choices=HEATING_CHOICES, verbose_name="Isıtma", blank=True)
    has_balcony = models.BooleanField(default=False, verbose_name="Balkon")
    dues = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Aidat", null=True, blank=True)
    
    # Diğer Bilgiler
    deed_status = models.CharField(max_length=20, choices=DEED_STATUS_CHOICES, verbose_name="Tapu Durumu", blank=True)
    is_suitable_for_credit = models.BooleanField(default=True, verbose_name="Krediye Uygunluk")
    is_bargainable = models.BooleanField(default=True, verbose_name="Pazarlık Payı")
    
    # Portföy Sahibi Bilgileri
    owner_name = models.CharField(max_length=100, verbose_name="Mal Sahibi", blank=True)
    owner_phone = models.CharField(max_length=20, verbose_name="Mal Sahibi Telefon", blank=True)
    owner_listing_number = models.CharField(max_length=50, verbose_name="Sahibinden İlan No", blank=True)
    branda_number = models.CharField(max_length=50, verbose_name="Branda No", blank=True)
    
    # Operasyonel Bilgiler
    key_holder = models.CharField(max_length=20, choices=KEY_HOLDER_CHOICES, verbose_name="Anahtar Kimde", blank=True)
    photo_status = models.BooleanField(default=False, verbose_name="Fotoğraf Çekildi")
    listing_date = models.DateField(default=timezone.now, verbose_name="İlan Tarihi")
    consultant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name="properties", verbose_name="Danışman")
    
    # Analiz Bilgileri
    swot_analysis = models.TextField(verbose_name="SWOT Analizi", blank=True)
    target_audience = models.CharField(max_length=100, verbose_name="Hedef Kitle", blank=True)
    
    # Sistem Bilgileri
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Portföy"
        verbose_name_plural = "Portföyler"
        ordering = ['-created_at']

class PropertyEnvironment(models.Model):
    """Gayrimenkul çevresi (yakın yerler)"""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="environments")
    place_name = models.CharField(max_length=100, verbose_name="Yer Adı")
    distance = models.CharField(max_length=20, verbose_name="Uzaklık")
    
    def __str__(self):
        return f"{self.place_name} - {self.distance}"
    
    class Meta:
        verbose_name = "Çevre Bilgisi"
        verbose_name_plural = "Çevre Bilgileri"

class PropertyImage(models.Model):
    """Gayrimenkul görselleri"""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to='properties/', verbose_name="Görsel")
    title = models.CharField(max_length=100, verbose_name="Görsel Başlığı", blank=True)
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Sıralama")
    
    def __str__(self):
        return f"{self.property.title} - {self.title or 'Görsel'}"
    
    class Meta:
        verbose_name = "Gayrimenkul Görseli"
        verbose_name_plural = "Gayrimenkul Görselleri"
        ordering = ['order']
