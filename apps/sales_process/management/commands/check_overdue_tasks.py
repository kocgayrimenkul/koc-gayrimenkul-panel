# -*- encoding: utf-8 -*-
"""
Geciken Görevleri Kontrol Eden Management Command
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.sales_process.models import Task, LeadNote
from apps.sales_process.signals import check_overdue_tasks


class Command(BaseCommand):
    help = 'Geciken görevleri kontrol eder ve bildirim gönderir'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=0,
            help='Kaç gün öncesinden itibaren geciken görevleri kontrol et (varsayılan: bugün)'
        )
        
        parser.add_argument(
            '--notify-only',
            action='store_true',
            help='Sadece bildirim gönder, görev durumunu değiştirme'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        notify_only = options['notify_only']
        
        # Geciken görevleri bul
        cutoff_date = timezone.now() - timedelta(days=days)
        
        overdue_tasks = Task.objects.filter(
            due_date__lt=cutoff_date,
            status__in=['pending', 'in_progress']
        ).select_related('lead', 'assigned_to')
        
        if not overdue_tasks.exists():
            self.stdout.write(
                self.style.SUCCESS('Geciken görev bulunamadı.')
            )
            return
        
        self.stdout.write(
            self.style.WARNING(f'{overdue_tasks.count()} geciken görev bulundu.')
        )
        
        processed_count = 0
        
        for task in overdue_tasks:
            try:
                # Gecikme süresini hesapla
                overdue_duration = timezone.now() - task.due_date
                overdue_days = overdue_duration.days
                overdue_hours = overdue_duration.seconds // 3600
                
                # Bildirim notu oluştur
                note_text = (
                    f"GECİKEN GÖREV: {task.title}\n"
                    f"Bitiş tarihi: {task.due_date.strftime('%d.%m.%Y %H:%M')}\n"
                    f"Gecikme süresi: {overdue_days} gün, {overdue_hours} saat"
                )
                
                # Mevcut gecikme notu var mı kontrol et
                existing_note = LeadNote.objects.filter(
                    lead=task.lead,
                    note__icontains=f"GECİKEN GÖREV: {task.title}",
                    created_at__date=timezone.now().date()
                ).exists()
                
                if not existing_note:
                    LeadNote.objects.create(
                        lead=task.lead,
                        note=note_text,
                        created_by=task.assigned_to,
                        note_type='warning'
                    )
                
                # Görev durumunu güncelle (eğer sadece bildirim modu değilse)
                if not notify_only and task.status != 'overdue':
                    task.status = 'overdue'
                    task.save(update_fields=['status'])
                
                processed_count += 1
                
                self.stdout.write(
                    f"✓ {task.lead.customer_name} - {task.title} (Gecikme: {overdue_days}g {overdue_hours}s)"
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Hata - {task.title}: {str(e)}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n{processed_count} geciken görev işlendi.'
            )
        )
        
        # Özet bilgi
        if processed_count > 0:
            self.stdout.write('\n--- ÖZET ---')
            
            # Personel bazında geciken görev sayıları
            from django.db.models import Count
            
            staff_overdue = Task.objects.filter(
                due_date__lt=cutoff_date,
                status='overdue'
            ).values(
                'assigned_to__first_name',
                'assigned_to__last_name'
            ).annotate(
                overdue_count=Count('id')
            ).order_by('-overdue_count')
            
            for staff in staff_overdue:
                name = f"{staff['assigned_to__first_name']} {staff['assigned_to__last_name']}"
                count = staff['overdue_count']
                self.stdout.write(f"  {name}: {count} geciken görev")