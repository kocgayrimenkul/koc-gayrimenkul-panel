# -*- encoding: utf-8 -*-
"""
Satış Süreç Yönetimi - Celery Tasks
Otomatik süreç yönetimi için asenkron görevler
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()
from django.db.models import Count, Q

from .models import Lead, Task, LeadNote, SalesStage, StageTransition
from .signals import check_overdue_tasks, auto_follow_up_leads, auto_assign_lead_to_staff


@shared_task
def check_overdue_tasks_periodic():
    """
    Geciken görevleri periyodik olarak kontrol eder
    Crontab: Her 2 saatte bir çalışır
    """
    try:
        overdue_tasks = Task.objects.filter(
            due_date__lt=timezone.now(),
            status__in=['pending', 'in_progress']
        )
        
        processed_count = 0
        
        for task in overdue_tasks:
            # Gecikme bildirimi
            overdue_duration = timezone.now() - task.due_date
            overdue_days = overdue_duration.days
            overdue_hours = overdue_duration.seconds // 3600
            
            # Bugün için gecikme notu var mı kontrol et
            existing_note = LeadNote.objects.filter(
                lead=task.lead,
                note__icontains=f"GECİKEN GÖREV: {task.title}",
                created_at__date=timezone.now().date()
            ).exists()
            
            if not existing_note:
                LeadNote.objects.create(
                    lead=task.lead,
                    title="Geciken Görev Uyarısı",
                    content=(
                        f"GECİKEN GÖREV: {task.title}\n"
                        f"Bitiş tarihi: {task.due_date.strftime('%d.%m.%Y %H:%M')}\n"
                        f"Gecikme süresi: {overdue_days} gün, {overdue_hours} saat"
                    ),
                    created_by=task.assigned_to,
                    note_type='warning'
                )
            
            # Görev durumunu güncelle
            if task.status != 'overdue':
                task.status = 'overdue'
                task.save(update_fields=['status'])
            
            processed_count += 1
        
        return f"Processed {processed_count} overdue tasks"
        
    except Exception as e:
        return f"Error checking overdue tasks: {str(e)}"


@shared_task
def auto_follow_up_inactive_leads():
    """
    Hareketsiz lead'leri otomatik takip eder
    Crontab: Günde 2 kez çalışır (09:00, 15:00)
    """
    try:
        # 3 günden fazla hareketsiz lead'ler
        cutoff_date = timezone.now() - timedelta(days=3)
        
        inactive_leads = Lead.objects.filter(
            stage_updated_at__lt=cutoff_date,
            current_stage__name__in=[
                'bilgi_verildi', 'ihtiyac_analizi', 'teklif_gonderildi', 'cevap_bekleniyor'
            ]
        )
        
        created_tasks = 0
        
        for lead in inactive_leads:
            # Mevcut takip görevi var mı kontrol et
            existing_follow_up = Task.objects.filter(
                lead=lead,
                task_type='follow_up',
                status__in=['pending', 'in_progress']
            ).exists()
            
            if not existing_follow_up:
                inactive_days = (timezone.now() - lead.stage_updated_at).days
                
                Task.objects.create(
                    lead=lead,
                    title=f"{lead.customer_name} - Takip Gerekli",
                    description=(
                        f"{inactive_days} günden fazla hareketsiz müşteri. "
                        f"Son aşama: {lead.current_stage.name}"
                    ),
                    task_type='follow_up',
                    priority=3,
                    due_date=timezone.now() + timedelta(hours=4),
                    assigned_to=lead.assigned_staff,
                    status='pending'
                )
                
                LeadNote.objects.create(
                    lead=lead,
                    title="Otomatik Takip Görevi",
                    content=(
                        f"Otomatik takip görevi oluşturuldu. "
                        f"Müşteri {inactive_days} gündür hareketsiz."
                    ),
                    created_by=lead.assigned_staff,
                    note_type='system'
                )
                
                created_tasks += 1
        
        return f"Created {created_tasks} follow-up tasks for inactive leads"
        
    except Exception as e:
        return f"Error in auto follow-up: {str(e)}"


@shared_task
def auto_assign_unassigned_leads():
    """
    Atanmamış lead'leri otomatik olarak personele atar
    Crontab: Her 30 dakikada bir çalışır
    """
    try:
        # Atanmamış lead'leri bul
        unassigned_leads = Lead.objects.filter(
            assigned_staff__isnull=True,
            current_stage__name__in=[
                'bilgi_verildi', 'ihtiyac_analizi', 'teklif_gonderildi',
                'daire_sunumu', 'cevap_bekleniyor'
            ]
        )
        
        assigned_count = 0
        
        for lead in unassigned_leads:
            assigned_staff = auto_assign_lead_to_staff(lead)
            if assigned_staff:
                assigned_count += 1
        
        return f"Auto-assigned {assigned_count} leads"
        
    except Exception as e:
        return f"Error in auto assignment: {str(e)}"


@shared_task
def send_daily_summary_report():
    """
    Günlük özet raporu gönderir
    Crontab: Her gün 18:00'da çalışır
    """
    try:
        today = timezone.now().date()
        
        # Bugünkü istatistikler
        new_leads_today = Lead.objects.filter(created_at__date=today).count()
        completed_tasks_today = Task.objects.filter(
            completed_at__date=today,
            status='completed'
        ).count()
        
        overdue_tasks = Task.objects.filter(
            due_date__lt=timezone.now(),
            status='overdue'
        ).count()
        
        # Aşama geçişleri
        stage_transitions_today = StageTransition.objects.filter(
            created_at__date=today
        ).count()
        
        # Personel performansı
        staff_performance = User.objects.filter(
            is_active=True,
            is_staff=True
        ).annotate(
            completed_tasks_today=Count(
                'assigned_tasks',
                filter=Q(
                    assigned_tasks__completed_at__date=today,
                    assigned_tasks__status='completed'
                )
            ),
            active_leads=Count(
                'assigned_leads',
                filter=Q(
                    assigned_leads__current_stage__name__in=[
                        'bilgi_verildi', 'ihtiyac_analizi', 'teklif_gonderildi',
                        'daire_sunumu', 'cevap_bekleniyor'
                    ]
                )
            )
        ).order_by('-completed_tasks_today')
        
        # Rapor oluştur
        report = {
            'date': today.strftime('%d.%m.%Y'),
            'new_leads': new_leads_today,
            'completed_tasks': completed_tasks_today,
            'overdue_tasks': overdue_tasks,
            'stage_transitions': stage_transitions_today,
            'staff_performance': [
                {
                    'name': staff.get_full_name(),
                    'completed_tasks': staff.completed_tasks_today,
                    'active_leads': staff.active_leads
                }
                for staff in staff_performance[:10]  # Top 10
            ]
        }
        
        # TODO: E-posta gönderimi veya dashboard'a kaydetme
        # Bu kısım e-posta sistemi kurulduktan sonra implement edilecek
        
        return f"Daily report generated for {today}"
        
    except Exception as e:
        return f"Error generating daily report: {str(e)}"


@shared_task
def cleanup_old_notifications():
    """
    Eski bildirimleri temizler
    Crontab: Her gece 02:00'da çalışır
    """
    try:
        # 30 günden eski sistem notlarını sil
        cutoff_date = timezone.now() - timedelta(days=30)
        
        deleted_count = LeadNote.objects.filter(
            created_at__lt=cutoff_date,
            note_type__in=['system', 'warning']
        ).delete()[0]
        
        return f"Cleaned up {deleted_count} old notifications"
        
    except Exception as e:
        return f"Error cleaning up notifications: {str(e)}"


@shared_task
def update_lead_scores():
    """
    Lead skorlarını günceller (gelecekte ML modeli için)
    Crontab: Her gün 06:00'da çalışır
    """
    try:
        # Şu an için basit bir skorlama sistemi
        leads = Lead.objects.filter(
            current_stage__name__in=[
                'bilgi_verildi', 'ihtiyac_analizi', 'teklif_gonderildi',
                'daire_sunumu', 'cevap_bekleniyor'
            ]
        )
        
        updated_count = 0
        
        for lead in leads:
            # Basit skorlama faktörleri
            score = 50  # Base score
            
            # Aşama bazında puan
            stage_scores = {
                'bilgi_verildi': 10,
                'ihtiyac_analizi': 25,
                'teklif_gonderildi': 40,
                'daire_sunumu': 60,
                'cevap_bekleniyor': 75
            }
            score += stage_scores.get(lead.current_stage.name, 0)
            
            # Aktivite bazında puan
            recent_activities = LeadNote.objects.filter(
                lead=lead,
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count()
            score += min(recent_activities * 5, 25)
            
            # Görev tamamlama oranı
            total_tasks = Task.objects.filter(lead=lead).count()
            completed_tasks = Task.objects.filter(lead=lead, status='completed').count()
            
            if total_tasks > 0:
                completion_rate = completed_tasks / total_tasks
                score += int(completion_rate * 20)
            
            # Yaş faktörü (eski lead'ler daha düşük puan)
            days_old = (timezone.now().date() - lead.created_at.date()).days
            if days_old > 30:
                score -= min((days_old - 30) // 7, 20)
            
            # Skoru güncelle (eğer lead modelinde score field'ı varsa)
            # lead.score = max(0, min(100, score))
            # lead.save(update_fields=['score'])
            
            updated_count += 1
        
        return f"Updated scores for {updated_count} leads"
        
    except Exception as e:
        return f"Error updating lead scores: {str(e)}"


@shared_task
def send_appointment_reminders():
    """
    Randevu hatırlatmaları gönderir
    Crontab: Her 15 dakikada bir çalışır
    """
    try:
        # 2 saat sonraki randevuları bul
        reminder_time = timezone.now() + timedelta(hours=2)
        
        from .models import Appointment
        
        upcoming_appointments = Appointment.objects.filter(
            appointment_date__lte=reminder_time,
            appointment_date__gt=timezone.now(),
            status='scheduled'
        )
        
        reminded_count = 0
        
        for appointment in upcoming_appointments:
            # Hatırlatma notu oluştur
            LeadNote.objects.create(
                lead=appointment.lead,
                title="Randevu Hatırlatması",
                content=(
                    f"RANDEVU HATIRLATMASI: {appointment.get_appointment_type_display()}\n"
                    f"Tarih: {appointment.appointment_date.strftime('%d.%m.%Y %H:%M')}\n"
                    f"Lokasyon: {appointment.location or 'Belirtilmemiş'}"
                ),
                created_by=appointment.assigned_staff,
                note_type='reminder'
            )
            
            # TODO: SMS/WhatsApp hatırlatması gönder
            
            reminded_count += 1
        
        return f"Sent {reminded_count} appointment reminders"
        
    except Exception as e:
        return f"Error sending appointment reminders: {str(e)}"