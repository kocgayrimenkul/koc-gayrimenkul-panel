# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Çalışan Yönetimi Modülleri
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import Group

class Position(models.Model):
    """Pozisyon bilgileri"""
    name = models.CharField(max_length=100, verbose_name="Pozisyon Adı")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Pozisyon"
        verbose_name_plural = "Pozisyonlar"
        ordering = ['name']

class EmployeeProfile(models.Model):
    """Çalışan profil bilgileri - Kullanıcı modelini genişletir"""
    ROLE_CHOICES = [
        ('admin', 'Yönetici'),
        ('manager', 'Müdür'),
        ('consultant', 'Danışman'),
        ('secretary', 'Santral/Sekreter'),
        ('employee', 'Çalışan'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                               related_name='employee_profile', verbose_name="Kullanıcı")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefon")
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name="employees", verbose_name="Pozisyon")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee', verbose_name="Rol")
    is_active = models.BooleanField(default=True, verbose_name="Aktif mi?")
    
    def save(self, *args, **kwargs):
        # Rol değiştiğinde otomatik olarak uygun grup ataması yap
        creating = not self.pk  # Yeni oluşturuluyor mu kontrol et
        
        super().save(*args, **kwargs)
        
        if creating or self._role_changed():
            self._update_user_groups()
    
    def _role_changed(self):
        """Rol değişti mi kontrol et"""
        if not self.pk:
            return False
        
        old_instance = EmployeeProfile.objects.get(pk=self.pk)
        return old_instance.role != self.role
    
    def _update_user_groups(self):
        """Kullanıcı gruplarını role göre güncelle"""
        # Kullanıcıyı tüm gruplardan çıkar
        self.user.groups.clear()
        
        # Role uygun grubu ekle
        group_name = dict(self.ROLE_CHOICES).get(self.role)
        if group_name:
            group, created = Group.objects.get_or_create(name=group_name)
            self.user.groups.add(group)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"
    
    class Meta:
        verbose_name = "Çalışan Profili"
        verbose_name_plural = "Çalışan Profilleri"
        ordering = ['-is_active', 'user__last_name', 'user__first_name']

class Permission(models.Model):
    """Özel izin ayarları"""
    employee = models.OneToOneField(EmployeeProfile, on_delete=models.CASCADE, 
                                  related_name='custom_permissions', verbose_name="Çalışan")
    # Müşteri yönetimi izinleri
    can_view_customers = models.BooleanField(default=True, verbose_name="Müşteri Görüntüleme")
    can_add_customers = models.BooleanField(default=False, verbose_name="Müşteri Ekleme")
    can_edit_customers = models.BooleanField(default=False, verbose_name="Müşteri Düzenleme")
    can_delete_customers = models.BooleanField(default=False, verbose_name="Müşteri Silme")
    
    # Gayrimenkul yönetimi izinleri
    can_view_properties = models.BooleanField(default=True, verbose_name="Gayrimenkul Görüntüleme")
    can_add_properties = models.BooleanField(default=False, verbose_name="Gayrimenkul Ekleme")
    can_edit_properties = models.BooleanField(default=False, verbose_name="Gayrimenkul Düzenleme")
    
    # Takvim ve etkinlik izinleri
    can_view_calendar = models.BooleanField(default=True, verbose_name="Takvim Görüntüleme")
    can_create_events = models.BooleanField(default=True, verbose_name="Etkinlik Oluşturma")
    can_edit_events = models.BooleanField(default=False, verbose_name="Etkinlik Düzenleme")
    
    # Sistem yönetimi izinleri
    can_view_reports = models.BooleanField(default=False, verbose_name="Raporları Görüntüleme")
    can_manage_employees = models.BooleanField(default=False, verbose_name="Çalışan Yönetimi")
    can_manage_settings = models.BooleanField(default=False, verbose_name="Sistem Ayarları")
    
    def __str__(self):
        return f"{self.employee.user.get_full_name()} İzinleri"
    
    class Meta:
        verbose_name = "Özel İzin"
        verbose_name_plural = "Özel İzinler"

class ActivityLog(models.Model):
    """Çalışan aktivite kaydı"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                           related_name='activity_logs', verbose_name="Kullanıcı")
    action = models.CharField(max_length=200, verbose_name="Eylem")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Zaman")
    details = models.TextField(blank=True, verbose_name="Detaylar")
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.action} - {self.timestamp}"
    
    class Meta:
        verbose_name = "Aktivite Kaydı"
        verbose_name_plural = "Aktivite Kayıtları"
        ordering = ['-timestamp']
