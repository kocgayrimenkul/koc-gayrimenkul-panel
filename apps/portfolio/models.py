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
        ('mustakil', 'Müstakil'),
        ('dublex', 'Dublex'),
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
        ('yerden', 'Yerden Isıtma'),
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
    
    # Yeni seçenekler
    USAGE_STATUS_CHOICES = [
        ('mulk_sahibi', 'Mülk Sahibi'),
        ('kiracili', 'Kiracılı'),
        ('bos', 'Boş'),
    ]
    
    BANNER_STATUS_CHOICES = [
        ('asildi', 'Asıldı'),
        ('asilmadi', 'Asılmadı'),
    ]
    
    PHOTO_STATUS_CHOICES = [
        ('cekildi', 'Çekildi'),
        ('cektirmiyor', 'Çektirmiyor'),
        ('cekilmedi', 'Çekilmedi'),
        ('cekilmiyor', 'Çekilmiyor'),
    ]
    
    CATEGORY_CHOICES = [
        ('konut', 'Konut'),
        ('ticari', 'Ticari'),
        ('arsa', 'Arsa'),
        ('otel', 'Otel'),
        ('diger', 'Diğer'),
    ]
    
    LISTING_TYPE_CHOICES = [
        ('acil', 'Acil'),
        ('firsat', 'Fırsat'),
        ('yeni', 'Yeni'),
        ('ozel', 'Özel'),
        ('normal', 'Normal'),
    ]
    
    # Temel Bilgiler
    apartment_name = models.CharField(max_length=200, verbose_name="Daire Adı", null=True)
    description = models.TextField(verbose_name="Detay", blank=True)
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES, verbose_name="Emlak Tipi")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name="Durum")
    price = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Fiyat")
    
    # Lokasyon Bilgileri
    neighborhood = models.ForeignKey(Neighborhood, on_delete=models.CASCADE, verbose_name="Mahalle")
    address = models.TextField(verbose_name="Açık Adres", blank=True)
    map_coordinates = models.CharField(max_length=100, verbose_name="Harita Koordinatları", blank=True, null=True)
    
    # Detay Bilgiler - Daire için
    gross_area = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Brüt m²", null=True, blank=True)
    net_area = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Net m²", null=True, blank=True)
    room_count = models.CharField(max_length=20, verbose_name="Oda Sayısı", blank=True)
    floor = models.CharField(max_length=20, verbose_name="Bulunduğu Kat", blank=True)
    building_age = models.PositiveSmallIntegerField(verbose_name="Bina Yaşı", null=True, blank=True)
    heating = models.CharField(max_length=20, choices=HEATING_CHOICES, verbose_name="Isıtma", blank=True)
    has_balcony = models.BooleanField(default=False, verbose_name="Balkon")
    dues = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Aidat", null=True, blank=True)
    
    # Yeni detay bilgileri
    floor_count = models.CharField(max_length=20, verbose_name="Kat Sayısı", null=True, blank=True)
    bathroom_count = models.PositiveSmallIntegerField(verbose_name="Banyo Sayısı", null=True, blank=True)
    usage_status = models.CharField(max_length=20, choices=USAGE_STATUS_CHOICES, verbose_name="Kullanım Durumu", blank=True)
    is_furnished = models.BooleanField(default=False, verbose_name="Eşyalı")
    is_in_site = models.BooleanField(default=False, verbose_name="Site İçerisinde")
    is_exchangeable = models.BooleanField(default=False, verbose_name="Takas")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name="Kategori", blank=True) 
    listing_type = models.CharField(max_length=20, choices=LISTING_TYPE_CHOICES, verbose_name="İlan Türü", blank=True)
    
    # Diğer Bilgiler
    deed_status = models.CharField(max_length=20, choices=DEED_STATUS_CHOICES, verbose_name="Tapu Durumu", blank=True)
    is_suitable_for_credit = models.BooleanField(default=True, verbose_name="Krediye Uygunluk")
    is_bargainable = models.BooleanField(default=True, verbose_name="Pazarlık Payı")
    
    # Portföy Sahibi Bilgileri
    owner_name = models.CharField(max_length=100, verbose_name="Mal Sahibi", blank=True)
    owner_phone = models.CharField(max_length=20, verbose_name="Mal Sahibi Telefon", blank=True)
    owner_listing_number = models.CharField(max_length=50, verbose_name="Sahibinden İlan No", blank=True)
    emlakjet_listing_number = models.CharField(max_length=50, verbose_name="Emlakjet İlan No", blank=True)
    hepsiemlak_listing_number = models.CharField(max_length=50, verbose_name="Hepsiemlak İlan No", blank=True)
    website_listing_number = models.CharField(max_length=50, verbose_name="Web Sitesi İlan No", blank=True)
    branda_number = models.CharField(max_length=50, verbose_name="Branda No", blank=True)
    
    # Operasyonel Bilgiler
    key_holder = models.CharField(max_length=20, choices=KEY_HOLDER_CHOICES, verbose_name="Anahtar Kimde", blank=True)
    photo_status = models.CharField(max_length=20, choices=PHOTO_STATUS_CHOICES, verbose_name="Fotoğraf Durumu", blank=True, default='cekilmedi')
    banner_status = models.CharField(max_length=20, choices=BANNER_STATUS_CHOICES, verbose_name="Branda Durumu", blank=True)
    listing_date = models.DateField(default=timezone.now, verbose_name="İlan Tarihi")
    consultant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name="properties", verbose_name="Danışman")
    
    # Sistem Bilgileri
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    
    def __str__(self):
        return self.apartment_name if self.apartment_name else "İsimsiz Gayrimenkul"
    
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
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="images", null=True, blank=True)
    image = models.ImageField(upload_to='properties/', verbose_name="Görsel")
    title = models.CharField(max_length=100, verbose_name="Görsel Başlığı", blank=True)
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Sıralama")
    
    def __str__(self):
        return f"{self.property.apartment_name if self.property and self.property.apartment_name else 'Bağlantısız'} - {self.title or 'Görsel'}"
    
    class Meta:
        verbose_name = "Gayrimenkul Görseli"
        verbose_name_plural = "Gayrimenkul Görselleri"
        ordering = ['order']
