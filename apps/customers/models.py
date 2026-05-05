# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Müşteriler Modülleri
(Genişletilmiş sürüm - CRM Müşteri Detay sayfası için)
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class Neighborhood(models.Model):
    """Mahalle bilgisi ve bağlı danışman"""
    name = models.CharField(max_length=100, verbose_name="Mahalle Adı", unique=True)
    consultant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="neighborhoods",
        verbose_name="Bağlı Danışman",
    )
    district = models.CharField(max_length=100, verbose_name="İlçe", blank=True)

    def __str__(self):
        if self.district:
            return f"{self.name} ({self.district})"
        return self.name

    class Meta:
        verbose_name = "Mahalle"
        verbose_name_plural = "Mahalleler"
        ordering = ['name']


class Customer(models.Model):
    """Müşteri kayıt bilgileri (genişletilmiş)"""

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
        ('hepsi_emlak', 'Hepsi Emlak'),
        ('sosyal_medya', 'Sosyal Medya'),
        ('diger', 'Diğer'),
    ]

    CONTACT_TYPE_CHOICES = [
        ('bilgi_alma', 'Bilgi Alma'),
        ('daire_sunumu', 'Daire Sunumu'),
        ('sikayet', 'Şikayet'),
    ]

    # YENİ EKLENEN CHOICES
    CUSTOMER_TYPE_CHOICES = [
        ('bireysel', 'Bireysel Müşteri'),
        ('kurumsal', 'Kurumsal Müşteri'),
    ]

    STATUS_CHOICES = [
        ('potansiyel', 'Potansiyel'),
        ('aktif', 'Aktif'),
        ('pasif', 'Pasif'),
        ('kapandi', 'Kapandı'),
    ]

    GENDER_CHOICES = [
        ('erkek', 'Erkek'),
        ('kadin', 'Kadın'),
        ('belirtilmemis', 'Belirtilmemiş'),
    ]

    # Temel bilgiler
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Kayıt Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")

    # full_name artık opsiyonel - 'Bilinmeyen Müşteri' senaryosu için
    full_name = models.CharField(
        max_length=100,
        verbose_name="Adı Soyadı",
        blank=True,
        default='',
        help_text="Boş bırakılırsa 'Bilinmeyen Müşteri' olarak gösterilir",
    )

    # Telefon - unique ile aynı numara tekrarını önle
    phone = models.CharField(
        max_length=20,
        verbose_name="Telefon",
        unique=True,
        error_messages={'unique': 'Bu telefon numarası ile kayıtlı bir müşteri zaten mevcut.'},
    )

    # YENİ EKLENEN ALANLAR
    email = models.EmailField(
        verbose_name="E-posta",
        blank=True, null=True,
    )
    customer_type = models.CharField(
        max_length=20,
        choices=CUSTOMER_TYPE_CHOICES,
        default='bireysel',
        verbose_name="Müşteri Tipi",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='potansiyel',
        verbose_name="Müşteri Durumu",
    )
    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        default='belirtilmemis',
        verbose_name="Cinsiyet",
    )
    address = models.TextField(
        verbose_name="Açık Adres",
        blank=True, null=True,
    )
    city = models.CharField(
        max_length=50,
        verbose_name="İl",
        blank=True, null=True,
    )
    district = models.CharField(
        max_length=50,
        verbose_name="İlçe",
        blank=True, null=True,
    )

    # İletişim izinleri
    email_permission = models.BooleanField(default=True, verbose_name="E-posta İzni")
    sms_permission = models.BooleanField(default=True, verbose_name="SMS İzni")
    whatsapp_permission = models.BooleanField(default=True, verbose_name="WhatsApp İzni")

    # İlişkiler (mevcut)
    neighborhood = models.ForeignKey(
        Neighborhood,
        on_delete=models.CASCADE,
        verbose_name="Mahalle",
        null=True, blank=True,  # Bilinmeyen müşteri için opsiyonel yaptık
    )
    consultant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="customers",
        verbose_name="Danışman",
    )
    real_estate = models.ForeignKey(
        'portfolio.Property',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="customers",
        verbose_name="İlgilendiği Gayrimenkul",
    )

    # Müşteri kaynağı & iletişim türü
    source = models.CharField(
        max_length=50,
        choices=SOURCE_CHOICES,
        blank=True, null=True,
        verbose_name="Müşteri Kaynağı",
    )
    contact_type = models.CharField(
        max_length=50,
        choices=CONTACT_TYPE_CHOICES,
        default='bilgi_alma',
        verbose_name="İletişim Türü",
    )

    # Görüşme bilgileri
    meeting_result = models.TextField(verbose_name="Görüşme Sonucu", blank=True)
    meeting_status = models.CharField(
        max_length=20,
        choices=MEETING_STATUS_CHOICES,
        default='bekliyor',
        verbose_name="Görüşme Durumu",
    )

    # Tarihler
    response_date = models.DateField(
        verbose_name="Geri Dönüş Tarihi",
        null=True, blank=True,
    )
    reminder_date = models.DateField(
        verbose_name="Hatırlatma Tarihi",
        null=True, blank=True,
    )

    # Notlar (basit not - eski alan, korundu)
    notes = models.TextField(verbose_name="Notlar", blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.pk and not self.consultant_id and self.neighborhood_id:
            try:
                if self.neighborhood.consultant:
                    self.consultant = self.neighborhood.consultant
            except Exception:
                pass
        super().save(*args, **kwargs)

    @property
    def display_name(self):
        """Template'de kullanılacak - boşsa 'Bilinmeyen Müşteri' gösterir"""
        return self.full_name.strip() if self.full_name and self.full_name.strip() else "Bilinmeyen Müşteri"

    @property
    def display_address(self):
        """İl / İlçe birleşik gösterim"""
        parts = [p for p in [self.city, self.district] if p]
        if parts:
            return " / ".join(parts)
        if self.neighborhood:
            return str(self.neighborhood)
        return "- / -"

    @property
    def is_reminder_due(self):
        if self.reminder_date:
            return self.reminder_date <= timezone.now().date()
        return False

    @property
    def meeting_status_badge(self):
        badge_map = {
            'bekliyor': 'warning',
            'olumlu': 'success',
            'olumsuz': 'danger',
        }
        return badge_map.get(self.meeting_status, 'secondary')

    @property
    def status_color(self):
        """Template'deki renk koduna uygun"""
        colors = {
            'potansiyel': 'orange',
            'aktif': 'emerald',
            'pasif': 'gray',
            'kapandi': 'red',
        }
        return colors.get(self.status, 'gray')

    def __str__(self):
        return f"{self.display_name} ({self.phone})"

    class Meta:
        verbose_name = "Müşteri"
        verbose_name_plural = "Müşteriler"
        ordering = ['-created_at']


class CustomerReminder(models.Model):
    """Müşteri hatırlatma bildirimleri (mevcut)"""
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="reminders",
        verbose_name="Müşteri",
    )
    reminder_date = models.DateField(verbose_name="Hatırlatma Tarihi")
    message = models.TextField(verbose_name="Hatırlatma Mesajı")
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False, verbose_name="Okundu mu?")
    is_sent = models.BooleanField(default=False, verbose_name="Gönderildi mi?")

    @property
    def is_overdue(self):
        return not self.is_sent and self.reminder_date < timezone.now().date()

    def __str__(self):
        return f"{self.customer.full_name} - {self.reminder_date}"

    class Meta:
        verbose_name = "Müşteri Hatırlatma"
        verbose_name_plural = "Müşteri Hatırlatmaları"
        ordering = ['-reminder_date']


# ============================================================
# YENİ MODELLER - CRM Detay Sayfası için
# ============================================================

class CustomerFinancialInfo(models.Model):
    """Müşteri finansal bilgileri"""
    customer = models.OneToOneField(
        Customer,
        on_delete=models.CASCADE,
        related_name="financial_info",
        verbose_name="Müşteri",
    )
    monthly_income = models.DecimalField(
        max_digits=14, decimal_places=2,
        null=True, blank=True,
        verbose_name="Aylık Gelir",
    )
    credit_score = models.IntegerField(
        null=True, blank=True,
        verbose_name="Kredi Notu",
    )
    budget_min = models.DecimalField(
        max_digits=14, decimal_places=2,
        null=True, blank=True,
        verbose_name="Minimum Bütçe",
    )
    budget_max = models.DecimalField(
        max_digits=14, decimal_places=2,
        null=True, blank=True,
        verbose_name="Maksimum Bütçe",
    )
    notes = models.TextField(blank=True, verbose_name="Finansal Notlar")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Finansal Bilgi - {self.customer.display_name}"

    class Meta:
        verbose_name = "Müşteri Finansal Bilgi"
        verbose_name_plural = "Müşteri Finansal Bilgileri"


class CustomerNote(models.Model):
    """Müşteri notları ve CRM yorumları"""

    PRIORITY_CHOICES = [
        ('dusuk', 'Düşük'),
        ('normal', 'Normal'),
        ('yuksek', 'Yüksek'),
        ('acil', 'Acil'),
    ]

    TYPE_CHOICES = [
        ('not', 'Not'),
        ('yorum', 'CRM Yorumu'),
        ('hatirlatici', 'Hatırlatıcı'),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="customer_notes",
        verbose_name="Müşteri",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Oluşturan",
    )
    content = models.TextField(verbose_name="İçerik")
    note_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='not',
        verbose_name="Tür",
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='normal',
        verbose_name="Öncelik",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.display_name} - {self.get_note_type_display()}"

    class Meta:
        verbose_name = "Müşteri Notu"
        verbose_name_plural = "Müşteri Notları"
        ordering = ['-created_at']


class CustomerTask(models.Model):
    """Müşteri görevleri"""

    PRIORITY_CHOICES = [
        ('dusuk', 'Düşük'),
        ('normal', 'Normal'),
        ('yuksek', 'Yüksek'),
        ('acil', 'Acil'),
    ]

    STATUS_CHOICES = [
        ('acik', 'Açık'),
        ('devam_ediyor', 'Devam Ediyor'),
        ('tamamlandi', 'Tamamlandı'),
        ('iptal', 'İptal'),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name="Müşteri",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="assigned_customer_tasks",
        verbose_name="Atanan Kişi",
    )
    title = models.CharField(max_length=200, verbose_name="Görev Başlığı")
    description = models.TextField(blank=True, verbose_name="Açıklama")
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default='normal',
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='acik',
    )
    due_date = models.DateTimeField(null=True, blank=True, verbose_name="Son Tarih")
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_completed(self):
        return self.status == 'tamamlandi'

    def __str__(self):
        return f"{self.customer.display_name} - {self.title}"

    class Meta:
        verbose_name = "Müşteri Görevi"
        verbose_name_plural = "Müşteri Görevleri"
        ordering = ['-created_at']


class CustomerWorkflow(models.Model):
    """Müşteriye özel iş akışı kartları"""

    PRIORITY_CHOICES = [
        ('dusuk', 'Düşük'),
        ('normal', 'Normal'),
        ('yuksek', 'Yüksek'),
        ('acil', 'Acil'),
    ]

    STATUS_CHOICES = [
        ('aktif', 'Aktif'),
        ('tamamlandi', 'Tamamlandı'),
        ('gecikmis', 'Gecikmiş'),
        ('arsivlendi', 'Arşivlendi'),
        ('iptal', 'İptal'),
    ]

    WORKFLOW_TYPE_CHOICES = [
        ('satis', 'Satış Süreci'),
        ('kiralama', 'Kiralama Süreci'),
        ('takip', 'Takip Süreci'),
        ('gorusme', 'Görüşme Süreci'),
        ('diger', 'Diğer'),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="workflows",
        verbose_name="Müşteri",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_workflows",
        verbose_name="Oluşturan",
    )
    title = models.CharField(max_length=200, verbose_name="Başlık")
    description = models.TextField(blank=True, verbose_name="Açıklama")
    workflow_type = models.CharField(
        max_length=20, choices=WORKFLOW_TYPE_CHOICES, default='diger',
        verbose_name="İş Akışı Türü",
    )
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default='normal',
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='aktif',
    )
    related_property = models.ForeignKey(
        'portfolio.Property',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="workflows",
        verbose_name="İlgili Portföy",
    )
    due_date = models.DateField(null=True, blank=True, verbose_name="Bitiş Tarihi")
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.customer.display_name} - {self.title}"

    class Meta:
        verbose_name = "Müşteri İş Akışı"
        verbose_name_plural = "Müşteri İş Akışları"
        ordering = ['-created_at']


class CustomerOffer(models.Model):
    """Müşteriye gönderilen portföy teklifleri"""

    STATUS_CHOICES = [
        ('bekliyor', 'Bekliyor'),
        ('kabul', 'Kabul Edildi'),
        ('red', 'Reddedildi'),
        ('suresi_doldu', 'Süresi Doldu'),
    ]

    CURRENCY_CHOICES = [
        ('TRY', 'TRY - Türk Lirası'),
        ('USD', 'USD - Amerikan Doları'),
        ('EUR', 'EUR - Euro'),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="offers",
        verbose_name="Müşteri",
    )
    related_property = models.ForeignKey(
        'portfolio.Property',
        on_delete=models.CASCADE,
        related_name="offers",
        verbose_name="Portföy",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_offers",
        verbose_name="Oluşturan Danışman",
    )
    title = models.CharField(max_length=250, verbose_name="Teklif Başlığı", blank=True)
    offer_price = models.DecimalField(
        max_digits=14, decimal_places=2,
        verbose_name="Teklif Fiyatı",
    )
    currency = models.CharField(
        max_length=3, choices=CURRENCY_CHOICES, default='TRY',
        verbose_name="Para Birimi",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='bekliyor',
    )
    notes = models.TextField(blank=True, verbose_name="Notlar / Açıklama")
    matterport_url = models.URLField(
        blank=True, null=True,
        verbose_name="Matterport 3D Sanal Tur",
    )
    view_count = models.PositiveIntegerField(default=0, verbose_name="Görüntülenme")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="Son Geçerlilik")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def status_color(self):
        colors = {
            'bekliyor': 'yellow',
            'kabul': 'emerald',
            'red': 'red',
            'suresi_doldu': 'gray',
        }
        return colors.get(self.status, 'gray')

    def __str__(self):
        return f"{self.customer.display_name} - {self.title or str(self.property)}"

    class Meta:
        verbose_name = "Müşteri Teklifi"
        verbose_name_plural = "Müşteri Teklifleri"
        ordering = ['-created_at']


class CustomerDemand(models.Model):
    """Müşteri emlak talepleri"""

    STATUS_CHOICES = [
        ('aktif', 'Aktif'),
        ('pasif', 'Pasif'),
        ('tamamlandi', 'Tamamlandı'),
        ('iptal', 'İptal'),
    ]

    PROPERTY_TYPE_CHOICES = [
        ('daire', 'Daire'),
        ('mustakil', 'Müstakil'),
        ('dublex', 'Dublex'),
        ('arsa', 'Arsa'),
        ('isyeri', 'İşyeri'),
    ]

    TRANSACTION_TYPE_CHOICES = [
        ('satilik', 'Satılık'),
        ('kiralik', 'Kiralık'),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="demands",
        verbose_name="Müşteri",
    )
    property_type = models.CharField(
        max_length=20, choices=PROPERTY_TYPE_CHOICES,
        verbose_name="Emlak Tipi",
    )
    transaction_type = models.CharField(
        max_length=20, choices=TRANSACTION_TYPE_CHOICES,
        verbose_name="İşlem Tipi",
    )
    min_price = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
        verbose_name="Min Fiyat",
    )
    max_price = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
        verbose_name="Max Fiyat",
    )
    min_area = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name="Min m²",
    )
    max_area = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name="Max m²",
    )
    room_count = models.CharField(max_length=20, blank=True, verbose_name="Oda Sayısı")
    preferred_locations = models.TextField(
        blank=True, verbose_name="Tercih Edilen Bölgeler",
    )
    notes = models.TextField(blank=True, verbose_name="Notlar")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='aktif',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.customer.display_name} - {self.get_property_type_display()} {self.get_transaction_type_display()}"

    class Meta:
        verbose_name = "Müşteri Talebi"
        verbose_name_plural = "Müşteri Talepleri"
        ordering = ['-created_at']


class CustomerSmsLog(models.Model):
    """Müşteriye gönderilen SMS kayıtları"""

    STATUS_CHOICES = [
        ('gonderildi', 'İletildi'),
        ('basarisiz', 'Başarısız'),
        ('beklemede', 'Beklemede'),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="sms_logs",
        verbose_name="Müşteri",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Gönderen",
    )
    phone = models.CharField(max_length=20, verbose_name="Telefon")
    message = models.TextField(verbose_name="Mesaj")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='beklemede',
    )
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SMS -> {self.customer.display_name}"

    class Meta:
        verbose_name = "Müşteri SMS"
        verbose_name_plural = "Müşteri SMS Kayıtları"
        ordering = ['-sent_at']


class CustomerWhatsappLog(models.Model):
    """Müşteriye gönderilen WhatsApp mesaj kayıtları"""

    STATUS_CHOICES = [
        ('gonderildi', 'İletildi'),
        ('basarisiz', 'Başarısız'),
        ('beklemede', 'Beklemede'),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="whatsapp_logs",
        verbose_name="Müşteri",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Gönderen",
    )
    phone = models.CharField(max_length=20, verbose_name="Telefon")
    message = models.TextField(verbose_name="Mesaj")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='beklemede',
    )
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"WhatsApp -> {self.customer.display_name}"

    class Meta:
        verbose_name = "Müşteri WhatsApp"
        verbose_name_plural = "Müşteri WhatsApp Kayıtları"
        ordering = ['-sent_at']


class CustomerActivity(models.Model):
    """Müşteri aktivite/timeline kayıtları"""

    ACTIVITY_TYPE_CHOICES = [
        ('cagri_gelen', 'Gelen Arama'),
        ('cagri_giden', 'Giden Arama'),
        ('sms_gonderildi', 'SMS Gönderildi'),
        ('whatsapp_gonderildi', 'WhatsApp Gönderildi'),
        ('teklif_olusturuldu', 'Teklif Oluşturuldu'),
        ('surec_baslatildi', 'Süreç Başlatıldı'),
        ('not_eklendi', 'Not Eklendi'),
        ('gorev_olusturuldu', 'Görev Oluşturuldu'),
        ('gorev_tamamlandi', 'Görev Tamamlandı'),
        ('talep_olusturuldu', 'Talep Oluşturuldu'),
        ('musteri_guncellendi', 'Müşteri Güncellendi'),
        ('diger', 'Diğer'),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="activities",
        verbose_name="Müşteri",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Kullanıcı",
    )
    activity_type = models.CharField(
        max_length=30, choices=ACTIVITY_TYPE_CHOICES,
        verbose_name="Aktivite Türü",
    )
    source_label = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Kaynak Etiketi",
        help_text="Örn: 'Sanal Santral', 'Manuel', 'Sistem'",
    )
    description = models.CharField(max_length=500, verbose_name="Açıklama")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.display_name} - {self.get_activity_type_display()}"

    class Meta:
        verbose_name = "Müşteri Aktivitesi"
        verbose_name_plural = "Müşteri Aktiviteleri"
        ordering = ['-created_at']
