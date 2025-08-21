# -*- encoding: utf-8 -*-
"""
Otomatik Lead Takip Management Command
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

from apps.sales_process.models import Lead, Task, LeadNote, SalesStage
from apps.sales_process.signals import auto_follow_up_leads


class Command(BaseCommand):
    help = 'Hareketsiz lead\'leri otomatik takip eder ve görevler oluşturur'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=3,
            help='Kaç günden fazla hareketsiz lead\'leri takip et (varsayılan: 3)'
        )
        
        parser.add_argument(
            '--stages',
            nargs='+',
            default=['bilgi_verildi', 'ihtiyac_analizi', 'teklif_gonderildi', 'cevap_bekleniyor'],
            help='Hangi aşamalardaki lead\'leri kontrol et'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Sadece rapor göster, görev oluşturma'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        stages = options['stages']
        dry_run = options['dry_run']
        
        # Hareketsiz lead'leri bul
        cutoff_date = timezone.now() - timedelta(days=days)
        
        inactive_leads = Lead.objects.filter(
            stage_updated_at__lt=cutoff_date,
            current_stage__name__in=stages
        ).select_related('current_stage', 'assigned_staff')
        
        if not inactive_leads.exists():
            self.stdout.write(
                self.style.SUCCESS(f'{days} günden fazla hareketsiz lead bulunamadı.')
            )
            return
        
        self.stdout.write(
            self.style.WARNING(
                f'{inactive_leads.count()} adet {days} günden fazla hareketsiz lead bulundu.'
            )
        )
        
        if dry_run:
            self.stdout.write(
                self.style.NOTICE('DRY RUN modu - Görev oluşturulmayacak, sadece rapor gösteriliyor.')
            )
        
        processed_count = 0
        created_tasks = 0
        
        for lead in inactive_leads:
            try:
                # Hareketsizlik süresini hesapla
                inactive_duration = timezone.now() - lead.stage_updated_at
                inactive_days = inactive_duration.days
                
                # Mevcut takip görevi var mı kontrol et
                existing_follow_up = Task.objects.filter(
                    lead=lead,
                    task_type='follow_up',
                    status__in=['pending', 'in_progress']
                ).exists()
                
                status_msg = f"{lead.customer_name} - {lead.current_stage.name} ({inactive_days} gün hareketsiz)"
                
                if existing_follow_up:
                    self.stdout.write(
                        f"⚠ {status_msg} - Zaten takip görevi mevcut"
                    )
                else:
                    if not dry_run:
                        # Takip görevi oluştur
                        task = Task.objects.create(
                            lead=lead,
                            title=f"{lead.customer_name} - Takip Gerekli",
                            description=(
                                f"{inactive_days} günden fazla hareketsiz müşteri. "
                                f"Son aşama: {lead.current_stage.name}\n"
                                f"Son güncelleme: {lead.stage_updated_at.strftime('%d.%m.%Y %H:%M')}"
                            ),
                            task_type='follow_up',
                            priority=3,
                            due_date=timezone.now() + timedelta(hours=4),
                            assigned_to=lead.assigned_staff,
                            status='pending'
                        )
                        
                        # Bilgi notu ekle
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
                        
                    self.stdout.write(
                        f"✓ {status_msg} - {'Görev oluşturulacak' if dry_run else 'Takip görevi oluşturuldu'}"
                    )
                
                processed_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Hata - {lead.customer_name}: {str(e)}")
                )
        
        # Özet rapor
        self.stdout.write('\n--- ÖZET RAPOR ---')
        self.stdout.write(f"Kontrol edilen lead sayısı: {processed_count}")
        
        if not dry_run:
            self.stdout.write(f"Oluşturulan takip görevi: {created_tasks}")
        else:
            potential_tasks = processed_count - Task.objects.filter(
                lead__in=inactive_leads,
                task_type='follow_up',
                status__in=['pending', 'in_progress']
            ).count()
            self.stdout.write(f"Oluşturulacak takip görevi: {potential_tasks}")
        
        # Aşama bazında dağılım
        self.stdout.write('\nAşama bazında dağılım:')
        from django.db.models import Count
        
        stage_distribution = inactive_leads.values(
            'current_stage__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        for stage in stage_distribution:
            stage_name = stage['current_stage__name']
            count = stage['count']
            self.stdout.write(f"  {stage_name}: {count} lead")
        
        # Personel bazında dağılım
        self.stdout.write('\nPersonel bazında dağılım:')
        
        staff_distribution = inactive_leads.values(
            'assigned_staff__first_name',
            'assigned_staff__last_name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        for staff in staff_distribution:
            if staff['assigned_staff__first_name']:
                name = f"{staff['assigned_staff__first_name']} {staff['assigned_staff__last_name']}"
            else:
                name = "Atanmamış"
            count = staff['count']
            self.stdout.write(f"  {name}: {count} lead")
        
        if not dry_run and created_tasks > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n{created_tasks} takip görevi başarıyla oluşturuldu.'
                )
            )
        elif dry_run:
            self.stdout.write(
                self.style.NOTICE(
                    '\nGerçek çalıştırma için --dry-run parametresini kaldırın.'
                )
            )