# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Kariyer Modülleri
"""

from django.db import models
from django.utils import timezone
import os


def cv_upload_path(instance, filename):
    """CV dosyası için upload path"""
    return f'careers/cv/{instance.created_at.year}/{instance.created_at.month}/{filename}'


class JobApplication(models.Model):
    """İş Başvurusu Modeli"""
    
    EXPERIENCE_CHOICES = [
        ('0-1', '0-1 Yıl'),
        ('1-3', '1-3 Yıl'),
        ('3-5', '3-5 Yıl'),
        ('5-10', '5-10 Yıl'),
        ('10+', '10+ Yıl'),
    ]
    
    POSITION_CHOICES = [
        ('emlak_danisman', 'Emlak Danışmanı'),
        ('satis_temsilci', 'Satış Temsilcisi'),
        ('ofis_eleman', 'Ofis Elemanı'),
        ('muhasebe', 'Muhasebe Elemanı'),
        ('pazarlama', 'Pazarlama Uzmanı'),
        ('insan_kaynaklari', 'İnsan Kaynakları'),
        ('teknik_destek', 'Teknik Destek'),
        ('diger', 'Diğer'),
    ]
    
    STATUS_CHOICES = [
        ('yeni', 'Yeni Başvuru'),
        ('inceleniyor', 'İnceleniyor'),
        ('mulakat', 'Mülakat Aşaması'),
        ('onaylandi', 'Onaylandı'),
        ('reddedildi', 'Reddedildi'),
    ]
    
    # Kişisel Bilgiler
    first_name = models.CharField(max_length=50, verbose_name="Ad")
    last_name = models.CharField(max_length=50, verbose_name="Soyad")
    email = models.EmailField(verbose_name="E-posta")
    phone = models.CharField(max_length=20, verbose_name="Telefon")
    
    # Başvuru Bilgileri
    position = models.CharField(max_length=30, choices=POSITION_CHOICES, verbose_name="Başvurulan Pozisyon")
    experience = models.CharField(max_length=10, choices=EXPERIENCE_CHOICES, verbose_name="Deneyim Süresi")
    cover_letter = models.TextField(verbose_name="Ön Yazı/Açıklama")
    
    # CV Dosyası
    cv_file = models.FileField(
        upload_to=cv_upload_path, 
        verbose_name="CV Dosyası",
        help_text="PDF, DOC, DOCX formatında olmalıdır"
    )
    
    # Sistem Bilgileri
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='yeni', verbose_name="Durum")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Başvuru Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncelleme Tarihi")
    notes = models.TextField(blank=True, verbose_name="Notlar", help_text="İK değerlendirme notları")
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.get_position_display()}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def cv_filename(self):
        if self.cv_file:
            return os.path.basename(self.cv_file.name)
        return None
    
    class Meta:
        verbose_name = "İş Başvurusu"
        verbose_name_plural = "İş Başvuruları"
        ordering = ['-created_at']


class JobPosting(models.Model):
    """İş İlanları Modeli"""
    
    DEPARTMENT_CHOICES = [
        ('satis', 'Satış'),
        ('pazarlama', 'Pazarlama'),
        ('insan_kaynaklari', 'İnsan Kaynakları'),
        ('muhasebe', 'Muhasebe'),
        ('teknik', 'Teknik'),
        ('yonetim', 'Yönetim'),
    ]
    
    EMPLOYMENT_TYPE_CHOICES = [
        ('tam_zamanli', 'Tam Zamanlı'),
        ('yari_zamanli', 'Yarı Zamanlı'),
        ('staj', 'Staj'),
        ('freelance', 'Freelance'),
    ]
    
    # İlan Bilgileri
    title = models.CharField(max_length=100, verbose_name="İş İlanı Başlığı")
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, verbose_name="Departman")
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, verbose_name="Çalışma Şekli")
    location = models.CharField(max_length=100, verbose_name="Lokasyon", default="İstanbul")
    
    # İlan İçeriği
    description = models.TextField(verbose_name="İş Tanımı")
    requirements = models.TextField(verbose_name="Aranan Özellikler")
    qualifications = models.TextField(verbose_name="Nitelikler", blank=True)
    benefits = models.TextField(verbose_name="Sağladığımız Imkanlar", blank=True)
    
    # Diğer Bilgiler
    salary_range = models.CharField(max_length=50, verbose_name="Maaş Aralığı", blank=True)
    experience_required = models.CharField(max_length=20, verbose_name="Gereken Deneyim", blank=True)
    
    # Sistem Bilgileri
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncelleme Tarihi")
    deadline = models.DateField(null=True, blank=True, verbose_name="Son Başvuru Tarihi")
    
    def __str__(self):
        return self.title
    
    @property
    def is_deadline_passed(self):
        if self.deadline:
            return timezone.now().date() > self.deadline
        return False
    
    class Meta:
        verbose_name = "İş İlanı"
        verbose_name_plural = "İş İlanları"
        ordering = ['-created_at']
