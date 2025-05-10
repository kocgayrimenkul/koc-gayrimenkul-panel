# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - FSBO Sinyalleri
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import FSBO, FSBOLog
from django.utils import timezone

@receiver(post_save, sender=FSBO)
def log_fsbo_save(sender, instance, created, **kwargs):
    """FSBO kaydı oluşturulduğunda/güncellendiğinde log oluştur"""
    # Log oluşturmayı views.py içinde manuel olarak yapıyoruz
    # Bu sadece emniyet amaçlı, sistem dışı değişiklikleri loglamak için
    pass

@receiver(post_delete, sender=FSBO)
def log_fsbo_delete(sender, instance, **kwargs):
    """FSBO kaydı silindiğinde log oluştur"""
    # Bu sinyal, model silinirken tetiklenir
    # instance silinen kayıt, ancak bu noktada veritabanında artık yok
    try:
        # Log oluşturmak için ayrı bir tablo kullanıyoruz, bu sayede
        # ana kayıt silinse bile log kalıyor
        FSBOLog.objects.create(
            fsbo=None,  # Artık kayıt olmadığı için None
            action="Kayıt silindi",
            details=f"ID: {instance.id}, İsim: {instance.full_name}, Telefon: {instance.phone}"
        )
    except Exception:
        # Log oluşturma hatası işlemi engellememeli
        pass 