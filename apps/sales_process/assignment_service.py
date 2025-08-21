# -*- coding: utf-8 -*-
"""
Sticky Assignment ve Otomatik Görev Atama Servisi
Lead'lerin personele otomatik atanması ve görev yönetimi
"""

import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()
from django.db.models import Count, Q, Avg
from .models import Lead, Task, SalesStage, LeadAssignment
from .business_rules import SalesProcessRules

logger = logging.getLogger(__name__)

class AssignmentService:
    """
    Lead atama ve görev yönetimi servisi
    """
    
    def __init__(self):
        self.business_rules = SalesProcessRules()
    
    def auto_assign_lead(self, lead):
        """
        Lead'i otomatik olarak uygun personele ata
        
        Args:
            lead: Atanacak lead objesi
            
        Returns:
            dict: Atama sonucu
        """
        try:
            # Önce sticky assignment kontrolü
            sticky_assignment = self.check_sticky_assignment(lead)
            if sticky_assignment:
                return self.assign_lead_to_user(lead, sticky_assignment['user'], 
                                               reason=sticky_assignment['reason'])
            
            # Coğrafi bölge bazlı atama
            regional_assignment = self.get_regional_assignment(lead)
            if regional_assignment:
                return self.assign_lead_to_user(lead, regional_assignment['user'],
                                               reason=regional_assignment['reason'])
            
            # İş yükü bazlı atama
            workload_assignment = self.get_workload_based_assignment(lead)
            if workload_assignment:
                return self.assign_lead_to_user(lead, workload_assignment['user'],
                                               reason=workload_assignment['reason'])
            
            # Varsayılan atama (round-robin)
            default_assignment = self.get_round_robin_assignment(lead)
            if default_assignment:
                return self.assign_lead_to_user(lead, default_assignment['user'],
                                               reason=default_assignment['reason'])
            
            return {
                'success': False,
                'error': 'Uygun personel bulunamadı'
            }
            
        except Exception as e:
            logger.error(f"Auto assignment error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_sticky_assignment(self, lead):
        """
        Sticky assignment kontrolü - önceki etkileşimlere göre atama
        
        Args:
            lead: Kontrol edilecek lead
            
        Returns:
            dict: Sticky assignment bilgisi
        """
        try:
            # Aynı telefon numarasından önceki lead'ler
            previous_leads = Lead.objects.filter(
                customer_phone=lead.customer_phone,
                assigned_staff__isnull=False
            ).exclude(id=lead.id).order_by('-created_at')
            
            if previous_leads.exists():
                last_assigned_user = previous_leads.first().assigned_staff
                
                # Personelin aktif olup olmadığını kontrol et
                if (last_assigned_user.is_active and 
                    last_assigned_user.is_staff):
                    
                    return {
                        'user': last_assigned_user,
                        'reason': f'Sticky assignment - Önceki lead: {previous_leads.first().id}'
                    }
            
            # Aynı müşteri adından önceki lead'ler
            if lead.customer_name:
                name_leads = Lead.objects.filter(
                    customer_name__iexact=lead.customer_name,
                    assigned_staff__isnull=False
                ).exclude(id=lead.id).order_by('-created_at')
                
                if name_leads.exists():
                    last_assigned_user = name_leads.first().assigned_staff
                    
                    if (last_assigned_user.is_active and 
                        last_assigned_user.is_staff):
                        
                        return {
                            'user': last_assigned_user,
                            'reason': f'Sticky assignment - Aynı isim: {lead.customer_name}'
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Sticky assignment check error: {str(e)}")
            return None
    
    def get_regional_assignment(self, lead):
        """
        Coğrafi bölge bazlı atama
        
        Args:
            lead: Atanacak lead
            
        Returns:
            dict: Bölgesel atama bilgisi
        """
        try:
            # Lead'in bölge bilgisi varsa
            if hasattr(lead, 'region') and lead.region:
                # O bölgeden sorumlu personeli bul
                regional_staff = User.objects.filter(
                    is_active=True,
                    is_staff=True
                ).first()
                
                if regional_staff:
                    return {
                        'user': regional_staff,
                        'reason': f'Bölgesel atama - Bölge: {lead.region}'
                    }
            
            # Telefon kodu bazlı bölge tespiti
            if lead.customer_phone:
                phone_prefix = lead.customer_phone[:4]  # İlk 4 hanesi
                
                # Telefon koduna göre bölge ataması yapan personeli bul
                prefix_staff = User.objects.filter(
                    is_active=True,
                    is_staff=True
                ).first()
                
                if prefix_staff:
                    return {
                        'user': prefix_staff,
                        'reason': f'Telefon kodu bazlı atama - Kod: {phone_prefix}'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Regional assignment error: {str(e)}")
            return None
    
    def get_workload_based_assignment(self, lead):
        """
        İş yükü bazlı atama - en az yüklü personele ata
        
        Args:
            lead: Atanacak lead
            
        Returns:
            dict: İş yükü bazlı atama bilgisi
        """
        try:
            # Aktif satış personelini al
            sales_staff = User.objects.filter(
                is_active=True,
                is_staff=True
            )
            
            if not sales_staff.exists():
                return None
            
            # Her personelin iş yükünü hesapla
            staff_workloads = []
            
            for staff in sales_staff:
                workload = self.business_rules.calculate_staff_workload(staff)
                staff_workloads.append({
                    'user': staff,
                    'workload': workload['total_score'],
                    'active_leads': workload['active_leads'],
                    'pending_tasks': workload['pending_tasks']
                })
            
            # En az yüklü personeli bul
            least_loaded = min(staff_workloads, key=lambda x: x['workload'])
            
            # İş yükü dengesini kontrol et
            max_workload = max(staff_workloads, key=lambda x: x['workload'])['workload']
            
            # Eğer en yüksek iş yükü ile en düşük arasında büyük fark varsa
            if max_workload - least_loaded['workload'] > 10:
                return {
                    'user': least_loaded['user'],
                    'reason': f'İş yükü dengeleme - Yük: {least_loaded["workload"]}'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Workload assignment error: {str(e)}")
            return None
    
    def get_round_robin_assignment(self, lead):
        """
        Round-robin atama - sırayla atama
        
        Args:
            lead: Atanacak lead
            
        Returns:
            dict: Round-robin atama bilgisi
        """
        try:
            # Aktif satış personelini al
            sales_staff = User.objects.filter(
                is_active=True,
                is_staff=True
            ).order_by('id')
            
            if not sales_staff.exists():
                return None
            
            # Son atanan personeli bul
            last_assignment = LeadAssignment.objects.filter(
                assignment_type='auto'
            ).order_by('-created_at').first()
            
            if last_assignment and last_assignment.assigned_to:
                # Son atanan personelden sonraki personeli bul
                try:
                    current_index = list(sales_staff).index(last_assignment.assigned_to)
                    next_index = (current_index + 1) % len(sales_staff)
                    next_user = sales_staff[next_index]
                except (ValueError, IndexError):
                    # Hata durumunda ilk personeli seç
                    next_user = sales_staff.first()
            else:
                # İlk atama
                next_user = sales_staff.first()
            
            return {
                'user': next_user,
                'reason': 'Round-robin atama'
            }
            
        except Exception as e:
            logger.error(f"Round-robin assignment error: {str(e)}")
            return None
    
    def assign_lead_to_user(self, lead, user, reason="Manuel atama"):
        """
        Lead'i belirtilen kullanıcıya ata
        
        Args:
            lead: Atanacak lead
            user: Atanacak kullanıcı
            reason: Atama sebebi
            
        Returns:
            dict: Atama sonucu
        """
        try:
            # Lead'i ata
            lead.assigned_staff = user
            lead.assignment_date = timezone.now()
            lead.save()
            
            # Atama kaydı oluştur
            LeadAssignment.objects.create(
                lead=lead,
                assigned_to=user,
                assigned_by=None,  # Otomatik atama
                assignment_type='auto',
                reason=reason
            )
            
            # İlk görevleri oluştur
            self.create_initial_tasks(lead)
            
            logger.info(f"Lead {lead.id} assigned to {user.username}: {reason}")
            
            return {
                'success': True,
                'assigned_to': user,
                'reason': reason
            }
            
        except Exception as e:
            logger.error(f"Lead assignment error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_initial_tasks(self, lead):
        """
        Lead için başlangıç görevlerini oluştur
        
        Args:
            lead: Görev oluşturulacak lead
        """
        try:
            # Mevcut stage'e göre görevler oluştur
            stage_tasks = self.business_rules.get_stage_required_tasks(lead.current_stage)
            
            for task_config in stage_tasks:
                Task.objects.create(
                    lead=lead,
                    title=task_config['title'],
                    description=task_config['description'],
                    task_type=task_config['task_type'],
                    priority=task_config['priority'],
                    assigned_to=lead.assigned_to,
                    due_date=timezone.now() + timedelta(hours=task_config['due_hours']),
                    status='pending'
                )
            
            # İlk iletişim görevi
            Task.objects.create(
                lead=lead,
                title="İlk İletişim",
                description=f"Yeni lead ile ilk iletişimi kur: {lead.customer_name}",
                task_type='call',
                priority=4,
                assigned_to=lead.assigned_to,
                due_date=timezone.now() + timedelta(hours=2),
                status='pending'
            )
            
            logger.info(f"Initial tasks created for lead {lead.id}")
            
        except Exception as e:
            logger.error(f"Initial task creation error: {str(e)}")
    
    def reassign_overdue_leads(self):
        """
        Süresi geçmiş lead'leri yeniden ata
        
        Returns:
            dict: Yeniden atama sonuçları
        """
        try:
            # 3 günden fazla işlem görmemiş lead'ler
            overdue_date = timezone.now() - timedelta(days=3)
            
            overdue_leads = Lead.objects.filter(
                assigned_to__isnull=False,
                last_activity_date__lt=overdue_date,
                current_stage__in=['new', 'contacted', 'qualified']
            )
            
            reassigned_count = 0
            
            for lead in overdue_leads:
                # Mevcut personelin iş yükünü kontrol et
                current_workload = self.business_rules.calculate_staff_workload(lead.assigned_to)
                
                # Eğer çok yüklüyse yeniden ata
                if current_workload['total_score'] > 15:
                    assignment_result = self.auto_assign_lead(lead)
                    
                    if assignment_result['success']:
                        reassigned_count += 1
                        
                        # Yeniden atama notu ekle
                        from .models import LeadNote
                        LeadNote.objects.create(
                            lead=lead,
                            note=f"Lead yeniden atandı: {assignment_result['reason']}",
                            note_type='system',
                            created_by=None
                        )
            
            return {
                'success': True,
                'reassigned_count': reassigned_count,
                'total_overdue': overdue_leads.count()
            }
            
        except Exception as e:
            logger.error(f"Overdue lead reassignment error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def balance_workload(self):
        """
        Personel iş yüklerini dengele
        
        Returns:
            dict: Dengeleme sonuçları
        """
        try:
            # Tüm aktif personelin iş yükünü hesapla
            sales_staff = User.objects.filter(
                is_active=True,
                is_staff=True
            )
            
            workloads = []
            for staff in sales_staff:
                workload = self.business_rules.calculate_staff_workload(staff)
                workloads.append({
                    'user': staff,
                    'workload': workload['total_score'],
                    'active_leads': workload['active_leads']
                })
            
            if len(workloads) < 2:
                return {'success': True, 'message': 'Yeterli personel yok'}
            
            # En yüklü ve en az yüklü personeli bul
            max_workload = max(workloads, key=lambda x: x['workload'])
            min_workload = min(workloads, key=lambda x: x['workload'])
            
            workload_diff = max_workload['workload'] - min_workload['workload']
            
            # Eğer fark 10'dan fazlaysa dengeleme yap
            if workload_diff > 10:
                # En yüklü personelden bazı lead'leri al
                leads_to_transfer = Lead.objects.filter(
                    assigned_to=max_workload['user'],
                    current_stage__in=['new', 'contacted'],
                    last_activity_date__lt=timezone.now() - timedelta(days=1)
                ).order_by('last_activity_date')[:2]
                
                transferred_count = 0
                
                for lead in leads_to_transfer:
                    assignment_result = self.assign_lead_to_user(
                        lead, 
                        min_workload['user'], 
                        reason="İş yükü dengeleme"
                    )
                    
                    if assignment_result['success']:
                        transferred_count += 1
                
                return {
                    'success': True,
                    'transferred_count': transferred_count,
                    'workload_diff': workload_diff
                }
            
            return {
                'success': True,
                'message': 'İş yükü dengeli',
                'workload_diff': workload_diff
            }
            
        except Exception as e:
            logger.error(f"Workload balancing error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_assignment_statistics(self):
        """
        Atama istatistiklerini getir
        
        Returns:
            dict: Atama istatistikleri
        """
        try:
            today = timezone.now().date()
            week_ago = today - timedelta(days=7)
            
            stats = {
                'total_assignments_today': LeadAssignment.objects.filter(
                    created_at__date=today
                ).count(),
                
                'total_assignments_week': LeadAssignment.objects.filter(
                    created_at__date__gte=week_ago
                ).count(),
                
                'auto_assignments_today': LeadAssignment.objects.filter(
                    created_at__date=today,
                    assignment_type='auto'
                ).count(),
                
                'manual_assignments_today': LeadAssignment.objects.filter(
                    created_at__date=today,
                    assignment_type='manual'
                ).count(),
                
                'sticky_assignments_today': LeadAssignment.objects.filter(
                    created_at__date=today,
                    reason__icontains='Sticky'
                ).count(),
                
                'unassigned_leads': Lead.objects.filter(
                    assigned_to__isnull=True
                ).count(),
                
                'avg_assignment_time': LeadAssignment.objects.filter(
                    created_at__date__gte=week_ago
                ).aggregate(
                    avg_time=Avg('created_at')
                )['avg_time']
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Assignment statistics error: {str(e)}")
            return {}