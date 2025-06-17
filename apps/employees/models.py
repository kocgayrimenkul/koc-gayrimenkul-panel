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
    """Çalışan özel izin ayarları - Modül bazlı"""
    employee = models.OneToOneField(EmployeeProfile, on_delete=models.CASCADE, 
                                  related_name='custom_permissions', verbose_name="Çalışan")
    
    # Müşteri Yönetimi İzinleri
    can_view_customers = models.BooleanField(default=True, verbose_name="Müşteri Görüntüleme")
    can_add_customers = models.BooleanField(default=False, verbose_name="Müşteri Ekleme")
    can_edit_customers = models.BooleanField(default=False, verbose_name="Müşteri Düzenleme")
    can_delete_customers = models.BooleanField(default=False, verbose_name="Müşteri Silme")
    
    # Gayrimenkul Portföy İzinleri
    can_view_portfolio = models.BooleanField(default=True, verbose_name="Portföy Görüntüleme")
    can_add_portfolio = models.BooleanField(default=False, verbose_name="Portföy Ekleme")
    can_edit_portfolio = models.BooleanField(default=False, verbose_name="Portföy Düzenleme")
    can_delete_portfolio = models.BooleanField(default=False, verbose_name="Portföy Silme")
    
    # Takvim ve Etkinlik İzinleri
    can_view_calendar = models.BooleanField(default=True, verbose_name="Takvim Görüntüleme")
    can_add_calendar = models.BooleanField(default=False, verbose_name="Takvim Etkinlik Ekleme")
    can_edit_calendar = models.BooleanField(default=False, verbose_name="Takvim Etkinlik Düzenleme")
    can_delete_calendar = models.BooleanField(default=False, verbose_name="Takvim Etkinlik Silme")
    
    # FSBO (Satış İlanları) İzinleri
    can_view_fsbo = models.BooleanField(default=True, verbose_name="FSBO Görüntüleme")
    can_add_fsbo = models.BooleanField(default=False, verbose_name="FSBO Ekleme")
    can_edit_fsbo = models.BooleanField(default=False, verbose_name="FSBO Düzenleme")
    can_delete_fsbo = models.BooleanField(default=False, verbose_name="FSBO Silme")
    
    # Prezentasyon İzinleri
    can_view_presentation = models.BooleanField(default=True, verbose_name="Prezentasyon Görüntüleme")
    can_add_presentation = models.BooleanField(default=False, verbose_name="Prezentasyon Ekleme")
    can_edit_presentation = models.BooleanField(default=False, verbose_name="Prezentasyon Düzenleme")
    can_delete_presentation = models.BooleanField(default=False, verbose_name="Prezentasyon Silme")
    
    # Kariyer İzinleri
    can_view_careers = models.BooleanField(default=True, verbose_name="Kariyer Başvuru Görüntüleme")
    can_add_careers = models.BooleanField(default=False, verbose_name="Kariyer İlanı Ekleme")
    can_edit_careers = models.BooleanField(default=False, verbose_name="Kariyer İlanı Düzenleme")
    can_delete_careers = models.BooleanField(default=False, verbose_name="Kariyer İlanı Silme")
    
    # Çalışan Yönetimi İzinleri
    can_view_employees = models.BooleanField(default=False, verbose_name="Çalışan Görüntüleme")
    can_add_employees = models.BooleanField(default=False, verbose_name="Çalışan Ekleme")
    can_edit_employees = models.BooleanField(default=False, verbose_name="Çalışan Düzenleme")
    can_delete_employees = models.BooleanField(default=False, verbose_name="Çalışan Silme")
    
    # Raporlama ve Sistem İzinleri
    can_view_reports = models.BooleanField(default=False, verbose_name="Rapor Görüntüleme")
    can_manage_settings = models.BooleanField(default=False, verbose_name="Sistem Ayarları")
    can_access_api = models.BooleanField(default=False, verbose_name="API Erişimi")
    
    def __str__(self):
        return f"{self.employee.user.get_full_name()} İzinleri"
    
    @property
    def permissions_summary(self):
        """İzin özetini döndür"""
        permissions = []
        
        # Müşteri izinleri
        customer_perms = []
        if self.can_view_customers: customer_perms.append("Görüntüleme")
        if self.can_add_customers: customer_perms.append("Ekleme")
        if self.can_edit_customers: customer_perms.append("Düzenleme")
        if self.can_delete_customers: customer_perms.append("Silme")
        if customer_perms: permissions.append(f"Müşteri: {', '.join(customer_perms)}")
        
        # Portföy izinleri
        portfolio_perms = []
        if self.can_view_portfolio: portfolio_perms.append("Görüntüleme")
        if self.can_add_portfolio: portfolio_perms.append("Ekleme")
        if self.can_edit_portfolio: portfolio_perms.append("Düzenleme")
        if self.can_delete_portfolio: portfolio_perms.append("Silme")
        if portfolio_perms: permissions.append(f"Portföy: {', '.join(portfolio_perms)}")
        
        # Takvim izinleri
        calendar_perms = []
        if self.can_view_calendar: calendar_perms.append("Görüntüleme")
        if self.can_add_calendar: calendar_perms.append("Ekleme")
        if self.can_edit_calendar: calendar_perms.append("Düzenleme")
        if self.can_delete_calendar: calendar_perms.append("Silme")
        if calendar_perms: permissions.append(f"Takvim: {', '.join(calendar_perms)}")
        
        return "; ".join(permissions) if permissions else "İzin yok"
    
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
