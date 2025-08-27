# -*- encoding: utf-8 -*-
"""
Satış Süreç Yönetimi - İş Kuralları
Otomatik süreç yönetimi ve iş mantığı kuralları
"""

from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()
from django.db.models import Q, Count

from .models import Lead, SalesStage, Task, LeadNote, Appointment, StageTransition


class SalesProcessRules:
    """
    Satış süreç kuralları ve otomatik işlemler
    """
    
    @staticmethod
    def can_move_to_stage(lead, target_stage):
        """
        Lead'in belirtilen aşamaya geçip geçemeyeceğini kontrol eder
        """
        current_stage = lead.current_stage
        
        # Aşama geçiş kuralları - Osman'ın istediği satış süreci akışı
        stage_flow = {
            'bilgi_verildi': ['ihtiyac_analizi'],
            'ihtiyac_analizi': ['teklif_gonderildi'],  # İhtiyaç analizinden teklif gönderilir
            'teklif_gonderildi': ['daire_sunumu'],  # Teklif sonrası daire sunumu
            'daire_sunumu': ['cevap_bekleniyor'],  # Daire sunumu sonrası cevap beklenir
            'cevap_bekleniyor': ['sozlesme_yapildi', 'ihtiyac_analizi'],  # Kabul edilirse sözleşme, reddedilirse tekrar ihtiyaç analizi
            'sozlesme_yapildi': ['kredi_islemleri', 'tapu_islemi'],  # Kredili veya nakit işlem
            'kredi_islemleri': ['tapu_islemi'],
            'tapu_islemi': ['hizmet_tamamlandi'],
            'hizmet_tamamlandi': ['memnuniyet_anketi'],
            'memnuniyet_anketi': ['dosya_kapandi'],
            'dosya_kapandi': []  # Son aşama
        }
        
        if not current_stage:
            return target_stage.name == 'bilgi_verildi'
        
        allowed_stages = stage_flow.get(current_stage.name, [])
        return target_stage.name in allowed_stages
    
    @staticmethod
    def get_required_tasks_for_stage(stage_name):
        """
        Belirtilen aşama için gerekli görevleri döndürür
        """
        required_tasks = {
            'bilgi_verildi': [
                {'type': 'call', 'title': 'İlk İletişim', 'priority': 'high', 'due_hours': 24}
            ],
            'ihtiyac_analizi': [
                {'type': 'meeting', 'title': 'İhtiyaç Analizi Görüşmesi', 'priority': 'high', 'due_hours': 48}
            ],
            'teklif_gonderildi': [
                {'type': 'follow_up', 'title': 'Teklif Takibi', 'priority': 'medium', 'due_hours': 72}
            ],
            'daire_sunumu': [
                {'type': 'appointment', 'title': 'Daire Sunumu Randevusu', 'priority': 'high', 'due_hours': 24}
            ],
            'cevap_bekleniyor': [
                {'type': 'follow_up', 'title': 'Müşteri Cevap Takibi', 'priority': 'medium', 'due_hours': 48},
                {'type': 'whatsapp', 'title': 'WhatsApp Takip Mesajı', 'priority': 'low', 'due_hours': 72}
            ],
            'sozlesme_yapildi': [
                {'type': 'document', 'title': 'Kredi Evrakları Toplama', 'priority': 'high', 'due_hours': 24}
            ],
            'kredi_islemleri': [
                {'type': 'follow_up', 'title': 'Kredi Onay Takibi', 'priority': 'medium', 'due_days': 7}
            ],
            'tapu_islemi': [
                {'type': 'legal', 'title': 'Tapu Devir İşlemleri', 'priority': 'high', 'due_days': 5}
            ],
            'hizmet_tamamlandi': [
                {'type': 'survey', 'title': 'Memnuniyet Anketi', 'priority': 'low', 'due_hours': 24}
            ]
        }
        
        return required_tasks.get(stage_name, [])
    
    @staticmethod
    def validate_stage_transition(lead, from_stage, to_stage, user):
        """
        Aşama geçişini doğrular ve gerekli kontrolleri yapar
        """
        errors = []
        warnings = []
        
        # Temel geçiş kontrolü
        if not SalesProcessRules.can_move_to_stage(lead, to_stage):
            errors.append(f"Bu aşamadan ({from_stage.name}) {to_stage.name} aşamasına geçiş yapılamaz.")
        
        # Gerekli görevler tamamlandı mı?
        if from_stage:
            pending_tasks = Task.objects.filter(
                lead=lead,
                status__in=['pending', 'in_progress'],
                task_type__in=['call', 'meeting', 'appointment']  # Kritik görevler
            )
            
            if pending_tasks.exists():
                warnings.append(
                    f"{pending_tasks.count()} kritik görev henüz tamamlanmadı. "
                    "Aşama geçişi yapılabilir ancak görevlerin tamamlanması önerilir."
                )
        
        # Minimum süre kontrolü (bazı aşamalar için)
        minimum_durations = {
            'ihtiyac_analizi': timedelta(hours=4),
            'teklif_gonderildi': timedelta(days=1),
            'cevap_bekleniyor': timedelta(hours=12)
        }
        
        if from_stage and from_stage.name in minimum_durations:
            time_in_stage = timezone.now() - lead.stage_updated_at
            min_duration = minimum_durations[from_stage.name]
            
            if time_in_stage < min_duration:
                warnings.append(
                    f"Bu aşamada minimum {min_duration} kalması önerilir. "
                    f"Şu anki süre: {time_in_stage}"
                )
        
        # Özel aşama kontrolleri
        if to_stage.name == 'teklif_gonderildi':
            # Teklif gönderildi aşaması için WhatsApp mesajı zorunlu
            from .models import WhatsAppMessage
            whatsapp_messages = WhatsAppMessage.objects.filter(
                lead=lead,
                message_type='offer_sent',
                status='sent'
            )
            if not whatsapp_messages.exists():
                errors.append("Teklif gönderildi aşamasına geçmek için WhatsApp üzerinden teklif gönderilmesi zorunludur.")
        
        elif to_stage.name == 'sozlesme_yapildi':
            # Sözleşme için gerekli bilgiler var mı?
            if not lead.phone or not lead.email:
                errors.append("Sözleşme aşaması için telefon ve e-posta bilgileri gereklidir.")
        
        elif to_stage.name == 'kredi_islemleri':
            # Kredi işlemleri için sözleşme gerekli
            if not from_stage or from_stage.name != 'sozlesme_yapildi':
                errors.append("Kredi işlemleri için önce sözleşme yapılması gereklidir.")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @staticmethod
    def auto_create_tasks_for_stage(lead, stage):
        """
        Aşama için otomatik görevler oluşturur
        """
        required_tasks = SalesProcessRules.get_required_tasks_for_stage(stage.name)
        created_tasks = []
        
        for task_config in required_tasks:
            # Aynı tipte görev zaten var mı kontrol et
            existing_task = Task.objects.filter(
                lead=lead,
                task_type=task_config['type'],
                status__in=['pending', 'in_progress']
            ).exists()
            
            if not existing_task:
                # Due date hesapla
                if 'due_hours' in task_config:
                    due_date = timezone.now() + timedelta(hours=task_config['due_hours'])
                elif 'due_days' in task_config:
                    due_date = timezone.now() + timedelta(days=task_config['due_days'])
                else:
                    due_date = timezone.now() + timedelta(days=1)
                
                task = Task.objects.create(
                    lead=lead,
                    title=f"{lead.customer_name} - {task_config['title']}",
                    description=f"Otomatik oluşturulan görev: {task_config['title']}",
                    task_type=task_config['type'],
                    priority=task_config['priority'],
                    due_date=due_date,
                    assigned_to=lead.assigned_staff,
                    status='pending'
                )
                
                created_tasks.append(task)
        
        return created_tasks
    
    @staticmethod
    def calculate_lead_priority(lead):
        """
        Lead'in öncelik seviyesini hesaplar
        """
        priority_score = 0
        
        # Aşama bazında puan
        stage_scores = {
            'bilgi_verildi': 1,
            'ihtiyac_analizi': 2,
            'teklif_gonderildi': 3,
            'daire_sunumu': 4,
            'cevap_bekleniyor': 5,
            'sozlesme_yapildi': 3,  # Sözleşme sonrası öncelik azalır
            'kredi_islemleri': 2,
            'tapu_islemi': 4,  # Tapu işlemi kritik
            'hizmet_tamamlandi': 1
        }
        
        if lead.current_stage:
            priority_score += stage_scores.get(lead.current_stage.name, 1)
        
        # Son aktivite zamanı
        days_since_update = (timezone.now() - lead.stage_updated_at).days
        if days_since_update > 7:
            priority_score += 2  # Eski lead'ler daha öncelikli
        elif days_since_update > 3:
            priority_score += 1
        
        # Geciken görev sayısı
        overdue_tasks = Task.objects.filter(
            lead=lead,
            due_date__lt=timezone.now(),
            status__in=['pending', 'in_progress']
        ).count()
        priority_score += overdue_tasks
        
        # Öncelik seviyesi belirleme
        if priority_score >= 7:
            return 'high'
        elif priority_score >= 4:
            return 'medium'
        else:
            return 'low'
    
    @staticmethod
    def get_next_recommended_actions(lead):
        """
        Lead için önerilen sonraki aksiyonları döndürür
        """
        actions = []
        
        if not lead.current_stage:
            actions.append({
                'type': 'stage_transition',
                'title': 'İlk aşamaya geç',
                'description': 'Lead\'i "Bilgi Verildi" aşamasına geçirin',
                'priority': 'high'
            })
            return actions
        
        # Geciken görevler
        overdue_tasks = Task.objects.filter(
            lead=lead,
            due_date__lt=timezone.now(),
            status__in=['pending', 'in_progress']
        )
        
        for task in overdue_tasks:
            actions.append({
                'type': 'complete_task',
                'title': f'Geciken görevi tamamla: {task.title}',
                'description': f'Bitiş tarihi: {task.due_date.strftime("%d.%m.%Y %H:%M")}',
                'priority': 'high',
                'task_id': task.id
            })
        
        # Bekleyen görevler
        pending_tasks = Task.objects.filter(
            lead=lead,
            status='pending',
            due_date__gte=timezone.now()
        ).order_by('due_date')[:3]
        
        for task in pending_tasks:
            actions.append({
                'type': 'complete_task',
                'title': f'Görevi tamamla: {task.title}',
                'description': f'Bitiş tarihi: {task.due_date.strftime("%d.%m.%Y %H:%M")}',
                'priority': 'medium',
                'task_id': task.id
            })
        
        # Sonraki aşama önerisi
        current_stage = lead.current_stage.name
        next_stages = {
            'bilgi_verildi': 'ihtiyac_analizi',
            'ihtiyac_analizi': 'teklif_gonderildi',
            'teklif_gonderildi': 'daire_sunumu',
            'daire_sunumu': 'cevap_bekleniyor',
            'cevap_bekleniyor': 'sozlesme_yapildi',
            'sozlesme_yapildi': 'kredi_islemleri',
            'kredi_islemleri': 'tapu_islemi',
            'tapu_islemi': 'hizmet_tamamlandi',
            'hizmet_tamamlandi': 'memnuniyet_anketi',
            'memnuniyet_anketi': 'dosya_kapandi'
        }
        
        if current_stage in next_stages:
            next_stage = next_stages[current_stage]
            actions.append({
                'type': 'stage_transition',
                'title': f'Sonraki aşamaya geç: {next_stage}',
                'description': f'Lead\'i {next_stage} aşamasına geçirin',
                'priority': 'low'
            })
        
        # Son aktivite kontrolü
        days_since_update = (timezone.now() - lead.stage_updated_at).days
        if days_since_update > 3:
            actions.append({
                'type': 'follow_up',
                'title': 'Müşteri ile iletişim kur',
                'description': f'{days_since_update} gündür güncelleme yapılmamış',
                'priority': 'medium'
            })
        
        return actions
    
    @staticmethod
    def validate_lead_data(lead_data):
        """
        Lead verilerini doğrular
        """
        errors = []
        warnings = []
        
        # Zorunlu alanlar
        required_fields = ['customer_name', 'phone']
        for field in required_fields:
            if not lead_data.get(field):
                errors.append(f'{field} alanı zorunludur.')
        
        # Telefon formatı kontrolü
        phone = lead_data.get('phone', '')
        if phone and not phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').isdigit():
            warnings.append('Telefon numarası formatı geçersiz olabilir.')
        

        
        # Mükerrer kontrol
        if phone:
            existing_lead = Lead.objects.filter(
                phone=phone
            ).exclude(
                id=lead_data.get('id')
            ).first()
            
            if existing_lead:
                warnings.append(
                    f'Bu telefon numarasıyla kayıtlı başka bir müşteri var: {existing_lead.customer_name}'
                )
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @staticmethod
    def get_workload_balance():
        """
        Personel iş yükü dengesini hesaplar
        """
        # User already imported above
        
        staff_workload = User.objects.filter(
            is_active=True,
            is_staff=True
        ).annotate(
            active_leads=Count(
                'assigned_leads',
                filter=Q(
                    assigned_leads__current_stage__name__in=[
                        'bilgi_verildi', 'ihtiyac_analizi', 'teklif_gonderildi',
                        'daire_sunumu', 'cevap_bekleniyor'
                    ]
                )
            ),
            pending_tasks=Count(
                'assigned_tasks',
                filter=Q(assigned_tasks__status='pending')
            ),
            overdue_tasks=Count(
                'assigned_tasks',
                filter=Q(
                    assigned_tasks__status='overdue',
                    assigned_tasks__due_date__lt=timezone.now()
                )
            )
        )
        
        balance_data = []
        
        for staff in staff_workload:
            workload_score = (
                staff.active_leads * 2 +
                staff.pending_tasks * 1 +
                staff.overdue_tasks * 3
            )
            
            balance_data.append({
                'staff': staff,
                'active_leads': staff.active_leads,
                'pending_tasks': staff.pending_tasks,
                'overdue_tasks': staff.overdue_tasks,
                'workload_score': workload_score
            })
        
        # Workload score'a göre sırala
        balance_data.sort(key=lambda x: x['workload_score'])
        
        return balance_data