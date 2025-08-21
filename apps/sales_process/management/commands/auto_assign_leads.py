# -*- encoding: utf-8 -*-
"""
Otomatik Lead Atama Management Command
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()
from django.db.models import Count, Q
from django.utils import timezone

from apps.sales_process.models import Lead, LeadNote
from apps.sales_process.signals import auto_assign_lead_to_staff


class Command(BaseCommand):
    help = 'Atanmamış lead\'leri otomatik olarak personele atar (Sticky Assignment)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--group',
            type=str,
            default='Sales Staff',
            help='Hangi grubun personeline atama yapılacak (varsayılan: Sales Staff)'
        )
        
        parser.add_argument(
            '--max-leads',
            type=int,
            default=50,
            help='Bir personelin maksimum lead sayısı (varsayılan: 50)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Sadece rapor göster, atama yapma'
        )
        
        parser.add_argument(
            '--rebalance',
            action='store_true',
            help='Mevcut atamaları yeniden dengele'
        )
    
    def handle(self, *args, **options):
        group_name = options['group']
        max_leads = options['max_leads']
        dry_run = options['dry_run']
        rebalance = options['rebalance']
        
        if dry_run:
            self.stdout.write(
                self.style.NOTICE('DRY RUN modu - Atama yapılmayacak, sadece rapor gösteriliyor.')
            )
        
        # Satış personeli grubunu bul
        try:
            sales_group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Grup bulunamadı: {group_name}')
            )
            return
        
        # Aktif satış personelini bul
        available_staff = User.objects.filter(
            is_active=True,
            is_staff=True,
            groups=sales_group
        ).annotate(
            active_lead_count=Count(
                'assigned_leads',
                filter=Q(assigned_leads__current_stage__name__in=[
                    'bilgi_verildi', 'ihtiyac_analizi', 'teklif_gonderildi',
                    'daire_sunumu', 'cevap_bekleniyor', 'sozlesme_yapildi'
                ])
            )
        ).order_by('active_lead_count')
        
        if not available_staff.exists():
            self.stdout.write(
                self.style.ERROR(f'{group_name} grubunda aktif personel bulunamadı.')
            )
            return
        
        self.stdout.write(f'Aktif personel sayısı: {available_staff.count()}')
        
        # Mevcut durum raporu
        self.stdout.write('\n--- MEVCUT DURUM ---')
        for staff in available_staff:
            self.stdout.write(
                f"{staff.get_full_name()}: {staff.active_lead_count} aktif lead"
            )
        
        # Atanmamış lead'leri bul
        unassigned_leads = Lead.objects.filter(
            assigned_staff__isnull=True,
            current_stage__name__in=[
                'bilgi_verildi', 'ihtiyac_analizi', 'teklif_gonderildi',
                'daire_sunumu', 'cevap_bekleniyor'
            ]
        ).order_by('created_at')
        
        self.stdout.write(f'\nAtanmamış lead sayısı: {unassigned_leads.count()}')
        
        if rebalance:
            # Yeniden dengeleme modu
            self.stdout.write('\n--- YENİDEN DENGELEME MODU ---')
            
            # Tüm aktif lead'leri al
            all_active_leads = Lead.objects.filter(
                current_stage__name__in=[
                    'bilgi_verildi', 'ihtiyac_analizi', 'teklif_gonderildi',
                    'daire_sunumu', 'cevap_bekleniyor'
                ]
            ).order_by('created_at')
            
            total_leads = all_active_leads.count()
            staff_count = available_staff.count()
            
            if staff_count == 0:
                self.stdout.write(
                    self.style.ERROR('Yeniden dengeleme için personel bulunamadı.')
                )
                return
            
            leads_per_staff = total_leads // staff_count
            extra_leads = total_leads % staff_count
            
            self.stdout.write(
                f'Toplam aktif lead: {total_leads}'
            )
            self.stdout.write(
                f'Personel başına ortalama: {leads_per_staff} lead'
            )
            self.stdout.write(
                f'Ekstra lead: {extra_leads}'
            )
            
            if not dry_run:
                # Yeniden atama yap
                lead_index = 0
                for i, staff in enumerate(available_staff):
                    # Bu personele atanacak lead sayısı
                    target_count = leads_per_staff + (1 if i < extra_leads else 0)
                    
                    # Bu personele atanacak lead'leri al
                    leads_to_assign = all_active_leads[lead_index:lead_index + target_count]
                    
                    for lead in leads_to_assign:
                        if lead.assigned_staff != staff:
                            old_staff = lead.assigned_staff
                            lead.assigned_staff = staff
                            lead.save(update_fields=['assigned_staff'])
                            
                            # Atama notu ekle
                            LeadNote.objects.create(
                                lead=lead,
                                note=(
                                    f"Yeniden atama: {old_staff.get_full_name() if old_staff else 'Atanmamış'} "
                                    f"→ {staff.get_full_name()}"
                                ),
                                created_by=staff,
                                note_type='system'
                            )
                    
                    lead_index += target_count
                    
                    self.stdout.write(
                        f"✓ {staff.get_full_name()}: {target_count} lead atandı"
                    )
        
        else:
            # Normal atama modu
            if unassigned_leads.exists():
                self.stdout.write('\n--- ATAMA İŞLEMİ ---')
                
                assigned_count = 0
                
                for lead in unassigned_leads:
                    # En az lead'e sahip personeli bul
                    target_staff = available_staff.filter(
                        active_lead_count__lt=max_leads
                    ).first()
                    
                    if not target_staff:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Tüm personel maksimum lead sayısına ({max_leads}) ulaştı. '
                                f'Kalan {unassigned_leads.count() - assigned_count} lead atanamadı.'
                            )
                        )
                        break
                    
                    if not dry_run:
                        lead.assigned_staff = target_staff
                        lead.save(update_fields=['assigned_staff'])
                        
                        # Atama notu ekle
                        LeadNote.objects.create(
                            lead=lead,
                            note=f"Otomatik atama: {target_staff.get_full_name()}",
                            created_by=target_staff,
                            note_type='system'
                        )
                        
                        # Personelin lead sayısını güncelle (cache için)
                        target_staff.active_lead_count += 1
                    
                    assigned_count += 1
                    
                    self.stdout.write(
                        f"✓ {lead.customer_name} → {target_staff.get_full_name()} "
                        f"({'Atanacak' if dry_run else 'Atandı'})"
                    )
                
                if not dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'\n{assigned_count} lead başarıyla atandı.'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.NOTICE(
                            f'\n{assigned_count} lead atanacak. '
                            'Gerçek çalıştırma için --dry-run parametresini kaldırın.'
                        )
                    )
            
            else:
                self.stdout.write(
                    self.style.SUCCESS('Atanmamış lead bulunamadı.')
                )
        
        # Son durum raporu
        self.stdout.write('\n--- SON DURUM ---')
        
        # Güncellenmiş personel istatistikleri
        updated_staff = User.objects.filter(
            is_active=True,
            is_staff=True,
            groups=sales_group
        ).annotate(
            active_lead_count=Count(
                'assigned_leads',
                filter=Q(assigned_leads__current_stage__name__in=[
                    'bilgi_verildi', 'ihtiyac_analizi', 'teklif_gonderildi',
                    'daire_sunumu', 'cevap_bekleniyor', 'sozlesme_yapildi'
                ])
            )
        ).order_by('-active_lead_count')
        
        for staff in updated_staff:
            self.stdout.write(
                f"{staff.get_full_name()}: {staff.active_lead_count} aktif lead"
            )
        
        # Hala atanmamış lead sayısı
        remaining_unassigned = Lead.objects.filter(
            assigned_staff__isnull=True,
            current_stage__name__in=[
                'bilgi_verildi', 'ihtiyac_analizi', 'teklif_gonderildi',
                'daire_sunumu', 'cevap_bekleniyor'
            ]
        ).count()
        
        if remaining_unassigned > 0:
            self.stdout.write(
                self.style.WARNING(f'\nHala atanmamış lead: {remaining_unassigned}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\nTüm lead\'ler atandı.')
            )