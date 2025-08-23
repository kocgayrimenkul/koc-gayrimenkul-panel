# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Satış Süreç Yönetimi Modülleri
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import RegexValidator
from apps.customers.models import Customer, Neighborhood
from apps.portfolio.models import Property
import uuid


class SalesStage(models.Model):
    """Satış süreç aşamaları"""
    
    STAGE_TYPE_CHOICES = [
        ('staff', 'Personel Akışı'),
        ('manager', 'Müdür Akışı'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Aşama Adı")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Slug")
    stage_type = models.CharField(max_length=20, choices=STAGE_TYPE_CHOICES, verbose_name="Akış Tipi")
    order = models.PositiveIntegerField(verbose_name="Sıra", default=0)
    description = models.TextField(blank=True, verbose_name="Açıklama")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    
    # Otomatik geçiş kuralları
    auto_transition_enabled = models.BooleanField(default=False, verbose_name="Otomatik Geçiş")
    auto_transition_condition = models.CharField(max_length=200, blank=True, verbose_name="Geçiş Koşulu")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def display_name(self):
        """Aşama adını daha okunabilir formatta döndürür"""
        stage_names = {
            'bilgi_verildi': 'Bilgi Verildi',
            'ihtiyac_analizi': 'İhtiyaç Analizi',
            'teklif_gonderildi': 'Teklif Gönderildi',
            'daire_sunumu': 'Daire Sunumu',
            'cevap_bekleniyor': 'Cevap Bekleniyor',
            'sozlesme_yapildi': 'Sözleşme Yapıldı',
            'kredi_islemleri': 'Kredi İşlemleri',
            'tapu_islemi': 'Tapu İşlemi',
            'hizmet_tamamlandi': 'Hizmet Tamamlandı',
            'memnuniyet_anketi': 'Memnuniyet Anketi',
            'dosya_kapandi': 'Dosya Kapandı'
        }
        return stage_names.get(self.name, self.name.replace('_', ' ').title())
    
    def __str__(self):
        return f"{self.get_stage_type_display()} - {self.display_name}"
    
    class Meta:
        verbose_name = "Satış Aşaması"
        verbose_name_plural = "Satış Aşamaları"
        ordering = ['stage_type', 'order']


class Lead(models.Model):
    """Satış potansiyeli (müşteri lead'i)"""
    
    STATUS_CHOICES = [
        ('active', 'Aktif'),
        ('completed', 'Tamamlandı'),
        ('cancelled', 'İptal'),
        ('lost', 'Kaybedildi'),
    ]
    
    PAYMENT_TYPE_CHOICES = [
        ('cash', 'Nakit'),
        ('credit', 'Kredili'),
    ]
    
    SOURCE_CHOICES = [
        ('branda', 'Branda'),
        ('sahibinden', 'Sahibinden'),
        ('referans', 'Referans'),
        ('emlakjet', 'Emlakjet'),
        ('hepsi_emlak', 'Hepsi Emlak'),
        ('sosyal_medya', 'Sosyal Medya'),
        ('netgsm_call', 'Santral Çağrısı'),
        ('whatsapp', 'WhatsApp'),
        ('diger', 'Diğer'),
    ]
    
    PROPERTY_TYPE_CHOICES = [
        ('apartment', 'Daire'),
        ('villa', 'Villa'),
        ('office', 'Ofis'),
        ('shop', 'Dükkan'),
        ('land', 'Arsa'),
        ('other', 'Diğer'),
    ]
    
    # Temel bilgiler
    lead_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Lead ID")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="leads", verbose_name="Müşteri")
    assigned_staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="assigned_leads", verbose_name="Atanan Personel")
    current_stage = models.ForeignKey(SalesStage, on_delete=models.PROTECT, verbose_name="Mevcut Aşama")
    
    # Müşteri bilgileri
    customer_name = models.CharField(max_length=100, verbose_name="Müşteri Adı")
    customer_phone = models.CharField(max_length=20, verbose_name="Telefon", 
                                    validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$')])
    customer_email = models.EmailField(blank=True, verbose_name="E-posta")
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, verbose_name="Kaynak")
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES, blank=True, verbose_name="Gayrimenkul Tipi")
    property_location = models.CharField(max_length=200, blank=True, verbose_name="Gayrimenkul Lokasyonu")
    
    # İlgilenilen gayrimenkul
    interested_property = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name="interested_leads", verbose_name="İlgilenilen Gayrimenkul")
    neighborhood = models.ForeignKey(Neighborhood, on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name="İlgilenilen Mahalle")
    budget_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Min Bütçe")
    budget_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Max Bütçe")
    
    # Süreç bilgileri
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Durum")
    stage_updated_at = models.DateTimeField(null=True, blank=True, verbose_name="Aşama Güncelleme Tarihi")
    priority = models.PositiveIntegerField(default=3, verbose_name="Öncelik (1-5)")
    
    # Sözleşme bilgileri (müdür akışı için)
    contract_signed = models.BooleanField(default=False, verbose_name="Sözleşme İmzalandı")
    contract_date = models.DateTimeField(null=True, blank=True, verbose_name="Sözleşme Tarihi")
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, blank=True, verbose_name="Ödeme Tipi")
    contract_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Sözleşme Tutarı")
    
    # Tapu işlemleri
    deed_transfer_date = models.DateField(null=True, blank=True, verbose_name="Tapu Devir Tarihi")
    deed_completed = models.BooleanField(default=False, verbose_name="Tapu Devri Tamamlandı")
    
    # Memnuniyet anketi
    satisfaction_survey_sent = models.BooleanField(default=False, verbose_name="Memnuniyet Anketi Gönderildi")
    satisfaction_score = models.PositiveIntegerField(null=True, blank=True, verbose_name="Memnuniyet Puanı (1-5)")
    satisfaction_feedback = models.TextField(blank=True, verbose_name="Memnuniyet Geri Bildirimi")
    
    # Sticky assignment için
    original_staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="original_leads", verbose_name="İlk Atanan Personel")
    
    # Zaman damgaları
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    last_contact_date = models.DateTimeField(null=True, blank=True, verbose_name="Son İletişim Tarihi")
    next_follow_up_date = models.DateTimeField(null=True, blank=True, verbose_name="Sonraki Takip Tarihi")
    
    def save(self, *args, **kwargs):
        # İlk kayıtta original_staff'ı set et
        if not self.pk and self.assigned_staff and not self.original_staff:
            self.original_staff = self.assigned_staff
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.customer_name} - {self.current_stage.name}"
    
    class Meta:
        verbose_name = "Satış Potansiyeli"
        verbose_name_plural = "Satış Potansiyelleri"
        ordering = ['-created_at']


class LeadNote(models.Model):
    """Lead ile ilgili notlar ve iletişim kayıtları"""
    
    NOTE_TYPE_CHOICES = [
        ('call', 'Telefon Görüşmesi'),
        ('whatsapp', 'WhatsApp Mesajı'),
        ('meeting', 'Yüz Yüze Görüşme'),
        ('email', 'E-posta'),
        ('system', 'Sistem Notu'),
        ('reminder', 'Hatırlatma'),
        ('error', 'Hata'),
    ]
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="notes", verbose_name="Lead")
    note_type = models.CharField(max_length=20, choices=NOTE_TYPE_CHOICES, verbose_name="Not Tipi")
    title = models.CharField(max_length=200, verbose_name="Başlık")
    content = models.TextField(verbose_name="İçerik")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Oluşturan")
    is_important = models.BooleanField(default=False, verbose_name="Önemli")
    
    # İletişim detayları
    contact_duration = models.PositiveIntegerField(null=True, blank=True, verbose_name="Görüşme Süresi (saniye)")
    contact_successful = models.BooleanField(null=True, blank=True, verbose_name="İletişim Başarılı")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    
    def __str__(self):
        return f"{self.lead.customer_name} - {self.title}"
    
    class Meta:
        verbose_name = "Lead Notu"
        verbose_name_plural = "Lead Notları"
        ordering = ['-created_at']


class StageTransition(models.Model):
    """Aşama geçiş kayıtları"""
    
    TRANSITION_TYPE_CHOICES = [
        ('manual', 'Manuel'),
        ('automatic', 'Otomatik'),
        ('webhook', 'Webhook'),
        ('system', 'Sistem'),
    ]
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="stage_transitions", verbose_name="Lead")
    from_stage = models.ForeignKey(SalesStage, on_delete=models.PROTECT, related_name="transitions_from", 
                                 null=True, blank=True, verbose_name="Önceki Aşama")
    to_stage = models.ForeignKey(SalesStage, on_delete=models.PROTECT, related_name="transitions_to", 
                               verbose_name="Sonraki Aşama")
    transition_type = models.CharField(max_length=20, choices=TRANSITION_TYPE_CHOICES, verbose_name="Geçiş Tipi")
    reason = models.TextField(blank=True, verbose_name="Geçiş Nedeni")
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name="Gerçekleştiren")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Geçiş Tarihi")
    
    def __str__(self):
        from_stage_name = self.from_stage.name if self.from_stage else "Başlangıç"
        return f"{self.lead.customer_name}: {from_stage_name} → {self.to_stage.name}"
    
    class Meta:
        verbose_name = "Aşama Geçişi"
        verbose_name_plural = "Aşama Geçişleri"
        ordering = ['-created_at']


class Task(models.Model):
    """Otomatik görevler ve hatırlatmalar"""
    
    TASK_TYPE_CHOICES = [
        ('call', 'Arama Yapma'),
        ('whatsapp', 'WhatsApp Gönderme'),
        ('email', 'E-posta Gönderme'),
        ('meeting', 'Randevu Ayarlama'),
        ('follow_up', 'Takip'),
        ('deed_transfer', 'Tapu Devri'),
        ('survey', 'Anket Gönderme'),
        ('reminder', 'Hatırlatma'),
    ]
    
    PRIORITY_CHOICES = [
        (1, 'Çok Düşük'),
        (2, 'Düşük'),
        (3, 'Normal'),
        (4, 'Yüksek'),
        (5, 'Çok Yüksek'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Bekliyor'),
        ('in_progress', 'Devam Ediyor'),
        ('completed', 'Tamamlandı'),
        ('cancelled', 'İptal'),
        ('overdue', 'Gecikmiş'),
    ]
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="tasks", verbose_name="Lead")
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, verbose_name="Görev Tipi")
    title = models.CharField(max_length=200, verbose_name="Görev Başlığı")
    description = models.TextField(blank=True, verbose_name="Açıklama")
    
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                                  related_name="assigned_tasks", verbose_name="Atanan Kişi")
    priority = models.PositiveIntegerField(choices=PRIORITY_CHOICES, default=3, verbose_name="Öncelik")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Durum")
    
    # Zaman bilgileri
    due_date = models.DateTimeField(verbose_name="Bitiş Tarihi")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Tamamlanma Tarihi")
    
    # Otomatik görev bilgileri
    is_automatic = models.BooleanField(default=False, verbose_name="Otomatik Görev")
    auto_complete_condition = models.CharField(max_length=200, blank=True, verbose_name="Otomatik Tamamlama Koşulu")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    
    def __str__(self):
        return f"{self.lead.customer_name} - {self.title}"
    
    class Meta:
        verbose_name = "Görev"
        verbose_name_plural = "Görevler"
        ordering = ['due_date', '-priority']


class Appointment(models.Model):
    """Randevu yönetimi"""
    
    APPOINTMENT_TYPE_CHOICES = [
        ('property_viewing', 'Daire Gezisi'),
        ('meeting', 'Görüşme'),
        ('contract_signing', 'Sözleşme İmzalama'),
        ('deed_transfer', 'Tapu Devri'),
        ('other', 'Diğer'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Planlandı'),
        ('confirmed', 'Onaylandı'),
        ('completed', 'Tamamlandı'),
        ('cancelled', 'İptal'),
        ('no_show', 'Gelmedi'),
        ('rescheduled', 'Ertelendi'),
    ]
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="appointments", verbose_name="Lead")
    appointment_type = models.CharField(max_length=30, choices=APPOINTMENT_TYPE_CHOICES, verbose_name="Randevu Tipi")
    title = models.CharField(max_length=200, verbose_name="Randevu Başlığı")
    description = models.TextField(blank=True, verbose_name="Açıklama")
    
    # Zaman ve yer
    scheduled_date = models.DateTimeField(verbose_name="Randevu Tarihi")
    duration_minutes = models.PositiveIntegerField(default=60, verbose_name="Süre (dakika)")
    location = models.CharField(max_length=300, blank=True, verbose_name="Konum")
    
    # Katılımcılar
    assigned_staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                     related_name="staff_appointments", verbose_name="Sorumlu Personel")
    customer_confirmed = models.BooleanField(default=False, verbose_name="Müşteri Onayı")
    
    # Durum
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name="Durum")
    result_notes = models.TextField(blank=True, verbose_name="Sonuç Notları")
    
    # İlgili gayrimenkul (daire gezisi için)
    property = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="appointments", verbose_name="Gayrimenkul")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    
    def __str__(self):
        date_str = self.scheduled_date.strftime('%d.%m.%Y %H:%M') if self.scheduled_date else 'Tarih Yok'
        return f"{self.lead.customer_name} - {self.title} ({date_str})"
    
    class Meta:
        verbose_name = "Randevu"
        verbose_name_plural = "Randevular"
        ordering = ['scheduled_date']


class WhatsAppMessage(models.Model):
    """WhatsApp mesaj kayıtları"""
    
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Metin'),
        ('image', 'Resim'),
        ('document', 'Belge'),
        ('template', 'Şablon'),
        ('interactive', 'Etkileşimli'),
        ('offer_sent', 'Teklif Gönderildi'),
    ]
    
    DIRECTION_CHOICES = [
        ('outbound', 'Giden'),
        ('inbound', 'Gelen'),
    ]
    
    STATUS_CHOICES = [
        ('sent', 'Gönderildi'),
        ('delivered', 'Teslim Edildi'),
        ('read', 'Okundu'),
        ('failed', 'Başarısız'),
    ]
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="whatsapp_messages", verbose_name="Lead")
    message_id = models.CharField(max_length=100, unique=True, verbose_name="Mesaj ID")
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, verbose_name="Yön")
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, verbose_name="Mesaj Tipi")
    
    # Mesaj içeriği
    content = models.TextField(verbose_name="İçerik")
    media_url = models.URLField(blank=True, verbose_name="Medya URL")
    
    # Durum bilgileri
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent', verbose_name="Durum")
    error_message = models.TextField(blank=True, verbose_name="Hata Mesajı")
    
    # Şablon bilgileri (template mesajlar için)
    template_name = models.CharField(max_length=100, blank=True, verbose_name="Şablon Adı")
    template_language = models.CharField(max_length=10, default='tr', verbose_name="Şablon Dili")
    
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                              verbose_name="Gönderen")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Gönderim Tarihi")
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name="Teslim Tarihi")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Okunma Tarihi")
    
    def __str__(self):
        date_str = self.created_at.strftime('%d.%m.%Y %H:%M') if self.created_at else 'Tarih Yok'
        return f"{self.lead.customer_name} - {self.get_direction_display()} ({date_str})"
    
    class Meta:
        verbose_name = "WhatsApp Mesajı"
        verbose_name_plural = "WhatsApp Mesajları"
        ordering = ['-created_at']


class CallLog(models.Model):
    """Santral çağrı kayıtları"""
    
    CALL_TYPE_CHOICES = [
        ('inbound', 'Gelen'),
        ('outbound', 'Giden'),
        ('missed', 'Cevapsız'),
    ]
    
    STATUS_CHOICES = [
        ('answered', 'Cevaplanmış'),
        ('missed', 'Cevapsız'),
        ('busy', 'Meşgul'),
        ('failed', 'Başarısız'),
        ('no_answer', 'Cevap Yok'),
    ]
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="call_logs", verbose_name="Lead")
    call_id = models.CharField(max_length=100, unique=True, verbose_name="Çağrı ID")
    call_type = models.CharField(max_length=10, choices=CALL_TYPE_CHOICES, verbose_name="Çağrı Tipi")
    
    # Çağrı bilgileri
    caller_number = models.CharField(max_length=20, verbose_name="Arayan Numara")
    called_number = models.CharField(max_length=20, verbose_name="Aranan Numara")
    
    # Personel bilgisi
    handled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="handled_calls", verbose_name="Görüşen Personel")
    
    # Çağrı detayları
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name="Durum")
    duration_seconds = models.PositiveIntegerField(default=0, verbose_name="Süre (saniye)")
    
    # Kayıt bilgileri
    recording_url = models.URLField(blank=True, verbose_name="Kayıt URL")
    recording_available = models.BooleanField(default=False, verbose_name="Kayıt Mevcut")
    
    # Zaman bilgileri
    started_at = models.DateTimeField(verbose_name="Başlangıç Tarihi")
    ended_at = models.DateTimeField(null=True, blank=True, verbose_name="Bitiş Tarihi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Kayıt Tarihi")
    
    # Notlar
    notes = models.TextField(blank=True, verbose_name="Notlar")
    
    def __str__(self):
        date_str = self.started_at.strftime('%d.%m.%Y %H:%M') if self.started_at else 'Tarih Yok'
        return f"{self.lead.customer_name} - {self.get_call_type_display()} ({date_str})"
    
    @property
    def duration_formatted(self):
        """Süreyi dakika:saniye formatında döndür"""
        minutes = self.duration_seconds // 60
        seconds = self.duration_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    class Meta:
        verbose_name = "Çağrı Kaydı"
        verbose_name_plural = "Çağrı Kayıtları"
        ordering = ['-started_at']


class LeadAssignment(models.Model):
    """Lead atama geçmişi ve sticky assignment takibi"""
    
    ASSIGNMENT_TYPE_CHOICES = [
        ('auto', 'Otomatik'),
        ('manual', 'Manuel'),
        ('sticky', 'Sticky Assignment'),
        ('geographic', 'Coğrafi'),
        ('workload', 'İş Yükü'),
        ('round_robin', 'Sıralı'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Aktif'),
        ('reassigned', 'Yeniden Atandı'),
        ('completed', 'Tamamlandı'),
        ('cancelled', 'İptal'),
    ]
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="assignments", verbose_name="Lead")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                                  related_name="lead_assignments", verbose_name="Atanan Kişi")
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name="made_assignments", verbose_name="Atayan Kişi")
    
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPE_CHOICES, verbose_name="Atama Tipi")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Durum")
    
    # Sticky assignment için
    is_sticky = models.BooleanField(default=False, verbose_name="Sticky Assignment")
    sticky_reason = models.CharField(max_length=200, blank=True, verbose_name="Sticky Nedeni")
    
    # Atama nedeni ve notları
    assignment_reason = models.TextField(blank=True, verbose_name="Atama Nedeni")
    notes = models.TextField(blank=True, verbose_name="Notlar")
    
    # Zaman bilgileri
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name="Atama Tarihi")
    reassigned_at = models.DateTimeField(null=True, blank=True, verbose_name="Yeniden Atama Tarihi")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Tamamlanma Tarihi")
    
    # İstatistik bilgileri
    workload_score = models.FloatField(null=True, blank=True, verbose_name="İş Yükü Skoru")
    geographic_match = models.BooleanField(default=False, verbose_name="Coğrafi Eşleşme")
    
    def __str__(self):
        return f"{self.lead.customer_name} -> {self.assigned_to.get_full_name()}"
    
    class Meta:
        verbose_name = "Lead Ataması"
        verbose_name_plural = "Lead Atamaları"
        ordering = ['-assigned_at']
        indexes = [
            models.Index(fields=['lead', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['is_sticky']),
        ]


class ActionLog(models.Model):
    """Satış süreç aksiyonları için log sistemi"""
    
    ACTION_TYPE_CHOICES = [
        ('CALL_OK', 'Arama Başarılı'),
        ('CALL_FAIL', 'Arama Başarısız'),
        ('OFFER_SENT', 'Teklif Gönderildi'),
        ('OFFER_ACCEPTED', 'Teklif Kabul Edildi'),
        ('OFFER_REJECTED', 'Teklif Reddedildi'),
        ('APPT_SET', 'Randevu Ayarlandı'),
        ('SHOW_DONE', 'Sunum Tamamlandı'),
        ('CONTRACT_CREATED', 'Sözleşme Oluşturuldu'),
        ('CONTRACT_SIGNED', 'Sözleşme İmzalandı'),
        ('PAYMENT_RECEIVED', 'Ödeme Alındı'),
        ('DEED_TRANSFER', 'Tapu Devri'),
        ('SURVEY_SENT', 'Anket Gönderildi'),
        ('STAGE_CHANGED', 'Aşama Değişti'),
        ('NOTE_ADDED', 'Not Eklendi'),
        ('TASK_CREATED', 'Görev Oluşturuldu'),
        ('TASK_COMPLETED', 'Görev Tamamlandı'),
        ('WHATSAPP_SENT', 'WhatsApp Gönderildi'),
        ('EMAIL_SENT', 'E-posta Gönderildi'),
        ('DOCUMENT_UPLOADED', 'Belge Yüklendi'),
        ('PROPERTY_SHOWN', 'Gayrimenkul Gösterildi'),
        ('FOLLOW_UP', 'Takip Yapıldı'),
        ('LEAD_CREATED', 'Lead Oluşturuldu'),
        ('LEAD_ASSIGNED', 'Lead Atandı'),
        ('CUSTOMER_RESPONSE', 'Müşteri Yanıtı'),
        ('SYSTEM_ACTION', 'Sistem Aksiyonu'),
    ]
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="action_logs", verbose_name="Lead")
    action_type = models.CharField(max_length=20, choices=ACTION_TYPE_CHOICES, verbose_name="Aksiyon Tipi")
    title = models.CharField(max_length=200, verbose_name="Başlık")
    description = models.TextField(blank=True, verbose_name="Açıklama")
    payload = models.JSONField(blank=True, default=dict, verbose_name="Ek Veriler")
    is_successful = models.BooleanField(default=True, verbose_name="Başarılı")
    error_message = models.TextField(blank=True, verbose_name="Hata Mesajı")
    
    # İlişkiler
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name="Gerçekleştiren")
    related_appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name="action_logs", verbose_name="İlgili Randevu")
    related_task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="action_logs", verbose_name="İlgili Görev")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Aksiyon Tarihi")
    
    def __str__(self):
        return f"{self.lead.customer_name} - {self.get_action_type_display()}: {self.title}"
    
    class Meta:
        verbose_name = "Aksiyon Logu"
        verbose_name_plural = "Aksiyon Logları"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['lead', 'action_type']),
            models.Index(fields=['performed_by', 'created_at']),
            models.Index(fields=['is_successful']),
        ]
