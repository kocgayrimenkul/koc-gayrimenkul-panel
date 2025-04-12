# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Çalışan Yönetimi Sinyalleri
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models import EmployeeProfile, ActivityLog

@receiver(post_save, sender=EmployeeProfile)
def update_user_groups(sender, instance, created, **kwargs):
    """
    Kullanıcı hesabı oluşturulduğunda veya rol değiştiğinde,
    uygun yetki gruplarına otomatik atama yapar.
    """
    # Kullanıcı gruplarını temizle
    instance.user.groups.clear()
    
    # Role uygun grubu belirle
    role_groups = {
        'admin': 'Yönetici',
        'manager': 'Müdür',
        'consultant': 'Danışman',
        'secretary': 'Santral',
        'employee': 'Çalışan'
    }
    
    # Grup varsa ekle, yoksa oluştur ve ekle
    group_name = role_groups.get(instance.role)
    if group_name:
        group, created = Group.objects.get_or_create(name=group_name)
        instance.user.groups.add(group)
