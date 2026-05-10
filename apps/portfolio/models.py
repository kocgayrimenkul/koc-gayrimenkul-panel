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
    web_title = models.CharField(max_length=250, verbose_name="Web Sitesi İlan Başlığı", blank=True, 
                                help_text="Web sitesinde görünecek ilan başlığı (boş bırakılırsa daire adı kullanılır)")
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
    owner_listing_number = models.CharField(max_length=500, verbose_name="Sahibinden İlan No", blank=True)
    owner_listing_updated_at = models.DateTimeField(null=True, blank=True, verbose_name="Sahibinden Güncelleme Tarihi")
    sahibinden_url = models.URLField(max_length=500, verbose_name="Sahibinden İlan Linki", blank=True)
    sahibinden_active = models.BooleanField(default=False, verbose_name="Sahibinden'de Yayında")
    emlakjet_listing_number = models.CharField(max_length=500, verbose_name="Emlakjet İlan No", blank=True)
    emlakjet_listing_updated_at = models.DateTimeField(null=True, blank=True, verbose_name="Emlakjet Güncelleme Tarihi")
    emlakjet_url = models.URLField(max_length=500, verbose_name="Emlakjet İlan Linki", blank=True)
    emlakjet_active = models.BooleanField(default=False, verbose_name="Emlakjet'te Yayında")
    hepsiemlak_listing_number = models.CharField(max_length=500, verbose_name="Hepsiemlak İlan No", blank=True)
    hepsiemlak_listing_updated_at = models.DateTimeField(null=True, blank=True, verbose_name="Hepsiemlak Güncelleme Tarihi")
    hepsiemlak_url = models.URLField(max_length=500, verbose_name="Hepsiemlak İlan Linki", blank=True)
    hepsiemlak_active = models.BooleanField(default=False, verbose_name="Hepsiemlak'ta Yayında")
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
    is_featured = models.BooleanField(default=False, verbose_name="Öne Çıkan")
    is_archived = models.BooleanField(default=False, verbose_name="Arşivlendi")
    archived_at = models.DateTimeField(null=True, blank=True, verbose_name="Arşiv Tarihi")
    archived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='archived_properties',
        verbose_name="Arşivleyen",
    )
    
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
    thumbnail = models.ImageField(upload_to='properties/thumbnails/', verbose_name="Küçük Görsel", blank=True, null=True)
    title = models.CharField(max_length=100, verbose_name="Görsel Başlığı", blank=True)
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Sıralama")
    is_main_photo = models.BooleanField(default=False, verbose_name="Ana Fotoğraf")
    
    def save(self, *args, **kwargs):
        """Kayıt sırasında thumbnail oluştur"""
        
        # Eğer bu fotoğraf ana fotoğraf olarak işaretleniyorsa, diğer ana fotoğrafları kaldır
        if self.is_main_photo and self.property:
            PropertyImage.objects.filter(property=self.property, is_main_photo=True).update(is_main_photo=False)
        
        # Eğer hiç ana fotoğraf yoksa ve bu ilk fotoğrafsa, bunu ana fotoğraf yap
        if self.property and not PropertyImage.objects.filter(property=self.property, is_main_photo=True).exists():
            self.is_main_photo = True
        
        super().save(*args, **kwargs)
        
        # Eğer thumbnail yoksa ve orijinal görsel varsa thumbnail oluştur
        if self.image and not self.thumbnail:
            from apps.api.utils import create_thumbnail
            try:
                thumbnail_url = create_thumbnail(self.image.name)
                if thumbnail_url:
                    # Thumbnail path'ini thumbnail field'a kaydet
                    thumbnail_path = thumbnail_url.split('/media/')[-1] if '/media/' in thumbnail_url else thumbnail_url
                    self.thumbnail = thumbnail_path
                    # Recursive save'i önlemek için update kullan
                    PropertyImage.objects.filter(id=self.id).update(thumbnail=thumbnail_path)
            except Exception as e:
                print(f"Thumbnail oluşturma hatası: {e}")
    
    def __str__(self):
        return f"{self.property.apartment_name if self.property and self.property.apartment_name else 'Bağlantısız'} - {self.title or 'Görsel'}"
    
    class Meta:
        verbose_name = "Gayrimenkul Görseli"
        verbose_name_plural = "Gayrimenkul Görselleri"
        ordering = ['order']

class PropertyNote(models.Model):
    """Gayrimenkul Notları"""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='notes', verbose_name="Gayrimenkul")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Kullanıcı")
    note = models.TextField(verbose_name="Not")

    PRIORITY_CHOICES = [
        ('normal', 'Normal'),
        ('onemli', 'Onemli'),
        ('acil', 'Acil'),
    ]
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal',
        verbose_name="Oncelik"
    )
    is_reminder = models.BooleanField(default=False, verbose_name="Hatirlatma mi?")
    reminder_date = models.DateTimeField(null=True, blank=True, verbose_name="Hatirlatma Tarihi")
    is_completed = models.BooleanField(default=False, verbose_name="Tamamlandi mi?")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Tarih")

    def __str__(self):
        return f"{self.property} - {self.user} - {self.created_at:%d.%m.%Y %H:%M}"

    class Meta:
        verbose_name = "Gayrimenkul Notu"
        verbose_name_plural = "Gayrimenkul Notları"
        ordering = ['-created_at']

class PortalNotification(models.Model):
    """Portal ilan süresi dolunca danışmana bildirim"""
    PORTAL_CHOICES = [
        ('sahibinden', 'Sahibinden'),
        ('emlakjet', 'Emlakjet'),
        ('hepsiemlak', 'Hepsiemlak'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='portal_notifications',
        verbose_name="Danışman"
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='portal_notifications',
        verbose_name="Gayrimenkul"
    )
    portal = models.CharField(max_length=20, choices=PORTAL_CHOICES, verbose_name="Portal")
    is_read = models.BooleanField(default=False, verbose_name="Okundu")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Tarih")

    def __str__(self):
        return f"{self.user} - {self.property} - {self.portal}"

    class Meta:
        verbose_name = "Portal Bildirimi"
        verbose_name_plural = "Portal Bildirimleri"
        ordering = ['-created_at']

