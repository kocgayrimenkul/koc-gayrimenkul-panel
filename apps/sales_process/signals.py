# -*- encoding: utf-8 -*-
"""
Satış Süreç Yönetimi - Django Signals
Otomatik süreç yönetimi ve iş kuralları
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()

from .models import Lead, SalesStage, StageTransition, Task, LeadNote, Appointment


@receiver(post_save, sender=Lead)
def lead_created_handler(sender, instance, created, **kwargs):
    """Yeni lead oluşturulduğunda otomatik işlemler"""
    if created:
        # İlk aşamaya otomatik geçiş
        initial_stage = SalesStage.objects.filter(name='bilgi_verildi').first()
        if initial_stage and not instance.current_stage:
            instance.current_stage = initial_stage
            instance.stage_updated_at = timezone.now()
            instance.save(update_fields=['current_stage', 'stage_updated_at'])
        
        # İlk görev oluştur - 24 saat içinde arama yapılması (sadece assigned_staff varsa)
        if instance.assigned_staff:
            Task.objects.create(
                lead=instance,
                title=f"{instance.customer_name} - İlk Arama",
                description=f"Müşteri {instance.customer_name} ile ilk iletişim kurulması gerekiyor.",
                task_type='call',
                priority=4,
                due_date=timezone.now() + timedelta(hours=24),
                assigned_to=instance.assigned_staff,
                status='pending'
            )
        
        # Sistem notu ekle
        LeadNote.objects.create(
            lead=instance,
            title="Yeni Lead Oluşturuldu",
            content=f"Yeni müşteri sisteme eklendi. İlk arama görevi oluşturuldu.",
            created_by=instance.assigned_staff or User.objects.filter(is_staff=True).first(),
            note_type='system'
        )


@receiver(pre_save, sender=Lead)
def lead_stage_change_handler(sender, instance, **kwargs):
    """Lead aşama değişikliği öncesi kontroller"""
    if instance.pk:  # Mevcut kayıt güncelleniyor
        try:
            old_instance = Lead.objects.get(pk=instance.pk)
            
            # Aşama değişti mi?
            if old_instance.current_stage != instance.current_stage:
                instance.stage_updated_at = timezone.now()
                
                # Sticky assignment - aşama değişse bile atanan personel değişmez
                if old_instance.assigned_staff and not instance.assigned_staff:
                    instance.assigned_staff = old_instance.assigned_staff
                    
        except Lead.DoesNotExist:
            pass


@receiver(post_save, sender=StageTransition)
def stage_transition_handler(sender, instance, created, **kwargs):
    """Aşama geçişi sonrası otomatik işlemler"""
    if created:
        lead = instance.lead
        new_stage = instance.to_stage
        
        # Aşamaya göre otomatik görevler oluştur
        if new_stage.name == 'ihtiyac_analizi':
            # İhtiyaç analizi aşamasında detaylı görüşme görevi
            Task.objects.create(
                lead=lead,
                title=f"{lead.customer_name} - İhtiyaç Analizi",
                description="Müşterinin detaylı ihtiyaçlarını belirlemek için görüşme yapılması.",
                task_type='meeting',
                priority=4,
                due_date=timezone.now() + timedelta(days=2),
                assigned_to=lead.assigned_staff,
                status='pending'
            )
            
        elif new_stage.name == 'teklif_gonderildi':
            # Teklif gönderildikten sonra takip görevi
            Task.objects.create(
                lead=lead,
                title=f"{lead.customer_name} - Teklif Takibi",
                description="Gönderilen teklifin değerlendirilmesi için müşteri ile iletişim kurulması.",
                task_type='call',
                priority=3,
                due_date=timezone.now() + timedelta(days=3),
                assigned_to=lead.assigned_staff,
                status='pending'
            )
            
        elif new_stage.name == 'daire_sunumu':
            # Daire sunumu için randevu planlama
            Task.objects.create(
                lead=lead,
                title=f"{lead.customer_name} - Daire Sunumu Randevusu",
                description="Müşteri ile daire sunumu randevusu planlanması.",
                task_type='appointment',
                priority=4,
                due_date=timezone.now() + timedelta(days=1),
                assigned_to=lead.assigned_staff,
                status='pending'
            )
            
        elif new_stage.name == 'sozlesme_yapildi':
            # Sözleşme sonrası kredi işlemleri başlatma
            Task.objects.create(
                lead=lead,
                title=f"{lead.customer_name} - Kredi İşlemleri Başlatma",
                description="Müşterinin kredi işlemlerinin başlatılması için gerekli evrakların toplanması.",
                task_type='document',
                priority=4,
                due_date=timezone.now() + timedelta(days=1),
                assigned_to=lead.assigned_staff,
                status='pending'
            )
            
        elif new_stage.name == 'kredi_islemleri':
            # Kredi onayı takibi
            Task.objects.create(
                lead=lead,
                title=f"{lead.customer_name} - Kredi Onay Takibi",
                description="Banka kredi onay sürecinin takip edilmesi.",
                task_type='follow_up',
                priority=3,
                due_date=timezone.now() + timedelta(days=7),
                assigned_to=lead.assigned_staff,
                status='pending'
            )
            
        elif new_stage.name == 'tapu_islemi':
            # Tapu işlemleri
            Task.objects.create(
                lead=lead,
                title=f"{lead.customer_name} - Tapu İşlemleri",
                description="Tapu devir işlemlerinin tamamlanması.",
                task_type='legal',
                priority=4,
                due_date=timezone.now() + timedelta(days=5),
                assigned_to=lead.assigned_staff,
                status='pending'
            )
            
        elif new_stage.name == 'hizmet_tamamlandi':
            # Memnuniyet anketi gönderme
            Task.objects.create(
                lead=lead,
                title=f"{lead.customer_name} - Memnuniyet Anketi",
                description="Müşteri memnuniyet anketinin gönderilmesi.",
                task_type='survey',
                priority=1,
                due_date=timezone.now() + timedelta(days=1),
                assigned_to=lead.assigned_staff,
                status='pending'
            )


@receiver(post_save, sender=Task)
def task_created_handler(sender, instance, created, **kwargs):
    """Görev oluşturulduğunda bildirim sistemi"""
    if created:
        # Sistem notu ekle
        LeadNote.objects.create(
            lead=instance.lead,
            title="Görev Oluşturuldu",
            content=f"Yeni görev oluşturuldu: {instance.title} (Bitiş: {instance.due_date.strftime('%d.%m.%Y %H:%M')})",
            created_by=instance.assigned_to,
            note_type='task'
        )


@receiver(post_save, sender=Appointment)
def appointment_created_handler(sender, instance, created, **kwargs):
    """Randevu oluşturulduğunda otomatik işlemler"""
    if created:
        # Randevu öncesi hatırlatma görevi oluştur
        reminder_time = instance.appointment_date - timedelta(hours=2)
        
        if reminder_time > timezone.now():
            Task.objects.create(
                lead=instance.lead,
                title=f"{instance.lead.customer_name} - Randevu Hatırlatması",
                description=f"2 saat sonra randevu var: {instance.get_appointment_type_display()}",
                task_type='reminder',
                priority=3,
                due_date=reminder_time,
                assigned_to=instance.assigned_staff,
                status='pending'
            )


def auto_assign_lead_to_staff(lead):
    """Lead'i otomatik olarak uygun personele atar (Sticky Assignment)"""
    if lead.assigned_staff:
        return lead.assigned_staff
    
    # En az lead'e sahip aktif personeli bul
    from django.db.models import Count
    
    available_staff = User.objects.filter(
        is_active=True,
        is_staff=True,
        groups__name='Sales Staff'  # Satış personeli grubu
    ).annotate(
        lead_count=Count('assigned_leads')
    ).order_by('lead_count')
    
    if available_staff.exists():
        selected_staff = available_staff.first()
        lead.assigned_staff = selected_staff
        lead.save(update_fields=['assigned_staff'])
        
        # Atama notu ekle
        LeadNote.objects.create(
            lead=lead,
            title="Otomatik Atama",
            content=f"Otomatik atama: {selected_staff.get_full_name()}",
            created_by=selected_staff,
            note_type='system'
        )
        
        return selected_staff
    
    return None


def check_overdue_tasks():
    """Geciken görevleri kontrol et ve bildirim gönder"""
    from django.utils import timezone
    
    overdue_tasks = Task.objects.filter(
        due_date__lt=timezone.now(),
        status__in=['pending', 'in_progress']
    )
    
    for task in overdue_tasks:
        # Gecikme bildirimi
        LeadNote.objects.create(
            lead=task.lead,
            title="Geciken Görev",
            content=f"GECİKEN GÖREV: {task.title} - Bitiş tarihi: {task.due_date.strftime('%d.%m.%Y %H:%M')}",
            created_by=task.assigned_to,
            note_type='warning'
        )
        
        # Görev durumunu gecikmiş olarak işaretle
        task.status = 'overdue'
        task.save(update_fields=['status'])


def auto_follow_up_leads():
    """Belirli süre boyunca hareketsiz kalan lead'ler için otomatik takip"""
    from django.utils import timezone
    from datetime import timedelta
    
    # 3 günden fazla hareketsiz lead'ler
    inactive_leads = Lead.objects.filter(
        stage_updated_at__lt=timezone.now() - timedelta(days=3),
        current_stage__name__in=['bilgi_verildi', 'ihtiyac_analizi', 'teklif_gonderildi', 'cevap_bekleniyor']
    )
    
    for lead in inactive_leads:
        # Takip görevi oluştur
        existing_follow_up = Task.objects.filter(
            lead=lead,
            task_type='follow_up',
            status__in=['pending', 'in_progress']
        ).exists()
        
        if not existing_follow_up:
            Task.objects.create(
                lead=lead,
                title=f"{lead.customer_name} - Takip Gerekli",
                description=f"3 günden fazla hareketsiz müşteri. Son aşama: {lead.current_stage.name}",
                task_type='follow_up',
                priority=3,
                due_date=timezone.now() + timedelta(hours=4),
                assigned_to=lead.assigned_staff,
                status='pending'
            )