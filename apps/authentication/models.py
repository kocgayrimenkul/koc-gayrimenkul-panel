# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Kimlik Doğrulama Modelleri
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    """
    Özelleştirilmiş kullanıcı modeli
    """
    email = models.EmailField(_('e-posta adresi'), unique=True)
    phone_number = models.CharField(
        _('telefon numarası'), 
        max_length=20, 
        blank=True, 
        null=True,
        help_text='Cep telefonu numarası (örn: 05321112233)'
    )
    position = models.CharField(_('pozisyon'), max_length=100, blank=True, null=True)
    department = models.CharField(_('departman'), max_length=100, blank=True, null=True)
    profile_photo = models.ImageField(
        _('profil fotoğrafı'), 
        upload_to='profile_photos/', 
        blank=True, 
        null=True
    )
    last_login_ip = models.GenericIPAddressField(_('son giriş IP'), blank=True, null=True)
    is_active = models.BooleanField(_('aktif'), default=True)
    
    class Meta:
        verbose_name = _('kullanıcı')
        verbose_name_plural = _('kullanıcılar')
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    def get_role_display(self):
        """Kullanıcının rolünü döndür"""
        roles = self.groups.all()
        if roles.exists():
            return ", ".join([role.name for role in roles])
        return _("Rol atanmamış")
    
    def has_role(self, role_name):
        """Kullanıcının belirtilen role sahip olup olmadığını kontrol et"""
        return self.groups.filter(name=role_name).exists()
        
    def add_role(self, role_name):
        """Kullanıcıya rol ekle"""
        role, created = Group.objects.get_or_create(name=role_name)
        self.groups.add(role)
        
    def remove_role(self, role_name):
        """Kullanıcıdan rol kaldır"""
        try:
            role = Group.objects.get(name=role_name)
            self.groups.remove(role)
        except Group.DoesNotExist:
            pass


class UserRole(models.Model):
    """Rol tanımları (Group modeli üzerine ekstra alan eklemek için)"""
    group = models.OneToOneField(
        Group, 
        on_delete=models.CASCADE, 
        related_name='role_info'
    )
    description = models.TextField(
        blank=True, 
        null=True, 
        verbose_name=_('Açıklama')
    )
    is_default = models.BooleanField(
        default=False, 
        verbose_name=_('Varsayılan Rol')
    )
    priority = models.IntegerField(
        default=0, 
        verbose_name=_('Öncelik (Yüksek değer daha önemli)')
    )
    
    class Meta:
        verbose_name = _('Kullanıcı Rolü')
        verbose_name_plural = _('Kullanıcı Rolleri')
        ordering = ['-priority']
    
    def __str__(self):
        return self.group.name