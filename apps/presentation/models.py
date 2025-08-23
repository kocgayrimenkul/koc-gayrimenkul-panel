# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Daire Sunumu Modülleri
"""

from django.db import models
from django.conf import settings
from apps.portfolio.models import Property
from apps.customers.models import Neighborhood

class Presentation(models.Model):
    """Daire sunumu bilgileri"""
    
    STATUS_CHOICES = [
        ('bekliyor', 'Bekliyor'),
        ('tamamlandi', 'Tamamlandı'),
        ('iptal', 'İptal'),
    ]
    
    SOURCE_CHOICES = [
        ('branda', 'Branda'),
        ('sahibinden', 'Sahibinden'),
        ('referans', 'Referans'),
        ('emlakjet', 'Emlakjet'),
        ('sosyal_medya', 'Sosyal Medya'),
        ('diger', 'Diğer'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Sunum Başlığı")
    property = models.ForeignKey(Property, on_delete=models.CASCADE, verbose_name="Daire", related_name="presentations")
    presenter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Sunan Kişi", related_name="presentations")
    presentation_date = models.DateTimeField(verbose_name="Sunum Tarihi")
    customer_name = models.CharField(max_length=100, verbose_name="Müşteri Adı")
    customer_phone = models.CharField(max_length=20, verbose_name="Müşteri Telefonu")
    
    # Yeni eklenen alanlar
    customer_source = models.CharField(max_length=50, choices=SOURCE_CHOICES, blank=True, null=True, verbose_name="Müşteri Kaynağı")
    neighborhood = models.ForeignKey(Neighborhood, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Mahalle")
    
    # Gezdirilen diğer daireler
    other_property1 = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True, 
                                      related_name="shown_in_presentation1", verbose_name="Diğer Gezdirilen Daire 1")
    other_property2 = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True, 
                                      related_name="shown_in_presentation2", verbose_name="Diğer Gezdirilen Daire 2")
    other_property3 = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True, 
                                      related_name="shown_in_presentation3", verbose_name="Diğer Gezdirilen Daire 3")
    
    # Her daire için ayrı not alanları
    property_notes1 = models.TextField(verbose_name="Daire 1 Notları", blank=True, null=True)
    property_notes2 = models.TextField(verbose_name="Daire 2 Notları", blank=True, null=True)
    property_notes3 = models.TextField(verbose_name="Daire 3 Notları", blank=True, null=True)
    
    notes = models.TextField(verbose_name="Notlar", blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='bekliyor', verbose_name="Durum")
    
    # Sunum tamamlama bilgileri
    is_completed = models.BooleanField(default=False, verbose_name="Sunum Tamamlandı")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Tamamlanma Tarihi")
    completion_notes = models.TextField(blank=True, null=True, verbose_name="Tamamlama Notları")
    shown_properties = models.JSONField(default=list, blank=True, verbose_name="Gösterilen Daireler")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    
    def save(self, *args, **kwargs):
        # Eğer mahalle seçildiyse ve kullanıcı atanmamışsa, mahalledeki danışmanı ata
        if self.neighborhood and self.neighborhood.consultant and not self.presenter_id:
            self.presenter = self.neighborhood.consultant
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} - {self.property.title}"
    
    class Meta:
        verbose_name = "Daire Sunumu"
        verbose_name_plural = "Daire Sunumları"
        ordering = ['-presentation_date']
        
class PresentationFeedback(models.Model):
    """Daire sunumu geri bildirimleri"""
    
    RATING_CHOICES = [
        (1, '1 - Çok Kötü'),
        (2, '2 - Kötü'),
        (3, '3 - Ortalama'),
        (4, '4 - İyi'),
        (5, '5 - Çok İyi'),
    ]
    
    presentation = models.ForeignKey(Presentation, on_delete=models.CASCADE, related_name="feedbacks", verbose_name="Sunum")
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, verbose_name="Değerlendirme")
    comments = models.TextField(verbose_name="Yorumlar", blank=True, null=True)
    feedback_date = models.DateTimeField(auto_now_add=True, verbose_name="Değerlendirme Tarihi")
    
    def __str__(self):
        return f"{self.presentation.title} - {self.rating}/5"
    
    class Meta:
        verbose_name = "Sunum Geri Bildirimi"
        verbose_name_plural = "Sunum Geri Bildirimleri"
        ordering = ['-feedback_date']
