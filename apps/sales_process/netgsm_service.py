# -*- coding: utf-8 -*-
"""
Netgsm Santral Entegrasyonu
Santral webhook'ları ve API işlemleri için servis sınıfı
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .models import Lead, CallLog
from .whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)

class NetgsmService:
    """
    Netgsm santral entegrasyonu için servis sınıfı
    """
    
    def __init__(self):
        self.username = settings.NETGSM_USERNAME
        self.password = settings.NETGSM_PASSWORD
        self.api_key = settings.NETGSM_API_KEY
        self.webhook_secret = settings.NETGSM_WEBHOOK_SECRET
        self.base_url = "https://api.netgsm.com.tr"
        
    def verify_webhook_signature(self, request_data, signature):
        """
        Webhook imzasını doğrula
        """
        import hmac
        import hashlib
        
        expected_signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            request_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def process_call_webhook(self, webhook_data):
        """
        Gelen arama webhook'unu işle
        """
        try:
            call_type = webhook_data.get('call_type')  # 'incoming', 'outgoing'
            phone_number = webhook_data.get('phone_number', '').strip()
            caller_id = webhook_data.get('caller_id', '').strip()
            call_duration = webhook_data.get('duration', 0)
            call_status = webhook_data.get('status')  # 'answered', 'missed', 'busy'
            call_start_time = webhook_data.get('start_time')
            call_end_time = webhook_data.get('end_time')
            agent_extension = webhook_data.get('agent_extension')
            
            # Telefon numarasını temizle
            clean_phone = self._clean_phone_number(phone_number if call_type == 'incoming' else caller_id)
            
            # Lead'i bul
            lead = self._find_lead_by_phone(clean_phone)
            
            # Call log oluştur
            call_log = CallLog.objects.create(
                lead=lead,
                phone_number=clean_phone,
                call_type=call_type,
                duration=call_duration,
                status=call_status,
                start_time=self._parse_datetime(call_start_time),
                end_time=self._parse_datetime(call_end_time),
                agent_extension=agent_extension,
                raw_data=webhook_data
            )
            
            # Lead varsa otomatik işlemler yap
            if lead:
                self._handle_lead_call(lead, call_log)
            else:
                # Yeni lead oluştur (eğer gelen arama ise)
                if call_type == 'incoming':
                    lead = self._create_lead_from_call(clean_phone, call_log)
                    if lead:
                        call_log.lead = lead
                        call_log.save()
            
            logger.info(f"Call webhook processed: {call_type} call from {clean_phone}")
            return call_log
            
        except Exception as e:
            logger.error(f"Error processing call webhook: {str(e)}")
            raise
    
    def _clean_phone_number(self, phone):
        """
        Telefon numarasını temizle ve standart formata getir
        """
        if not phone:
            return ''
        
        # Sadece rakamları al
        clean = ''.join(filter(str.isdigit, phone))
        
        # Türkiye formatına çevir
        if clean.startswith('90'):
            clean = clean[2:]
        elif clean.startswith('0'):
            clean = clean[1:]
        
        return clean
    
    def _find_lead_by_phone(self, phone_number):
        """
        Telefon numarasına göre lead bul
        """
        if not phone_number:
            return None
            
        try:
            # Tam eşleşme ara
            return Lead.objects.filter(
                customer_phone__icontains=phone_number
            ).first()
        except Lead.DoesNotExist:
            return None
    
    def _parse_datetime(self, datetime_str):
        """
        Datetime string'ini parse et
        """
        if not datetime_str:
            return timezone.now()
        
        try:
            # Farklı formatları dene
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%SZ',
                '%d.%m.%Y %H:%M:%S'
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(datetime_str, fmt)
                    return timezone.make_aware(dt)
                except ValueError:
                    continue
            
            # Hiçbiri çalışmazsa şu anki zamanı döndür
            return timezone.now()
            
        except Exception:
            return timezone.now()
    
    def _handle_lead_call(self, lead, call_log):
        """
        Lead için arama sonrası otomatik işlemler
        """
        try:
            # Son aktivite zamanını güncelle
            lead.last_contact_date = call_log.start_time
            lead.save()
            
            # Arama durumuna göre işlemler
            if call_log.status == 'answered':
                self._handle_answered_call(lead, call_log)
            elif call_log.status == 'missed':
                self._handle_missed_call(lead, call_log)
            elif call_log.status == 'busy':
                self._handle_busy_call(lead, call_log)
                
        except Exception as e:
            logger.error(f"Error handling lead call: {str(e)}")
    
    def _handle_answered_call(self, lead, call_log):
        """
        Cevaplanmış arama işlemleri
        """
        from .models import LeadNote, Task
        
        # Not ekle
        LeadNote.objects.create(
            lead=lead,
            note=f"Arama cevaplanmış - Süre: {call_log.duration} saniye",
            note_type='call',
            created_by_id=1  # System user
        )
        
        # Eğer arama 30 saniyeden kısaysa follow-up task oluştur
        if call_log.duration < 30:
            Task.objects.create(
                lead=lead,
                title="Kısa Arama Takibi",
                description=f"Müşteri ile yapılan arama {call_log.duration} saniye sürdü. Detaylı görüşme yapılması gerekiyor.",
                task_type='call',
                priority=3,
                due_date=timezone.now() + timedelta(hours=2),
                assigned_to_id=lead.assigned_to_id or 1
            )
    
    def _handle_missed_call(self, lead, call_log):
        """
        Kaçırılmış arama işlemleri
        """
        from .models import LeadNote, Task
        
        # Not ekle
        LeadNote.objects.create(
            lead=lead,
            note="Kaçırılmış arama - Geri arama yapılması gerekiyor",
            note_type='call',
            created_by_id=1
        )
        
        # Geri arama task'ı oluştur
        Task.objects.create(
            lead=lead,
            title="Kaçırılmış Arama - Geri Arama",
            description=f"Müşteri {call_log.start_time.strftime('%d.%m.%Y %H:%M')} tarihinde aradı ancak arama cevaplanamadı.",
            task_type='call',
            priority=4,
            due_date=timezone.now() + timedelta(hours=1),
            assigned_to_id=lead.assigned_to_id or 1
        )
        
        # WhatsApp mesajı gönder (opsiyonel)
        self._send_missed_call_whatsapp(lead)
    
    def _handle_busy_call(self, lead, call_log):
        """
        Meşgul arama işlemleri
        """
        from .models import LeadNote, Task
        
        # Not ekle
        LeadNote.objects.create(
            lead=lead,
            note="Arama meşgul - Daha sonra tekrar aranacak",
            note_type='call',
            created_by_id=1
        )
        
        # 30 dakika sonra tekrar arama task'ı
        Task.objects.create(
            lead=lead,
            title="Meşgul Arama - Tekrar Ara",
            description=f"Müşteri meşguldü. Tekrar aranması gerekiyor.",
            task_type='call',
            priority=2,
            due_date=timezone.now() + timedelta(minutes=30),
            assigned_to_id=lead.assigned_to_id or 1
        )
    
    def _create_lead_from_call(self, phone_number, call_log):
        """
        Gelen aramadan yeni lead oluştur
        """
        try:
            from .models import SalesStage
            
            # İlk aşamayı bul
            first_stage = SalesStage.objects.filter(order=1).first()
            if not first_stage:
                return None
            
            # Yeni lead oluştur
            lead = Lead.objects.create(
                customer_name=f"Gelen Arama - {phone_number}",
                customer_phone=phone_number,
                source='phone_call',
                current_stage=first_stage,
                priority=3,
                notes=f"Gelen aramadan otomatik oluşturuldu - {call_log.start_time.strftime('%d.%m.%Y %H:%M')}"
            )
            
            # İlk not ekle
            from .models import LeadNote
            LeadNote.objects.create(
                lead=lead,
                note="Gelen aramadan otomatik lead oluşturuldu",
                note_type='system',
                created_by_id=1
            )
            
            logger.info(f"New lead created from incoming call: {lead.id}")
            return lead
            
        except Exception as e:
            logger.error(f"Error creating lead from call: {str(e)}")
            return None
    
    def _send_missed_call_whatsapp(self, lead):
        """
        Kaçırılmış arama için WhatsApp mesajı gönder
        """
        try:
            whatsapp_service = WhatsAppService()
            
            message = f"""Merhaba {lead.customer_name},

Az önce bizi aradınız ancak aramanızı cevaplayamadık. 
En kısa sürede size geri dönüş yapacağız.

Koç Gayrimenkul
📞 {lead.customer_phone}"""
            
            whatsapp_service.send_text_message(
                lead=lead,
                message=message
            )
            
        except Exception as e:
            logger.error(f"Error sending missed call WhatsApp: {str(e)}")
    
    def get_call_statistics(self, start_date=None, end_date=None):
        """
        Arama istatistiklerini getir
        """
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()
        
        calls = CallLog.objects.filter(
            start_time__range=[start_date, end_date]
        )
        
        stats = {
            'total_calls': calls.count(),
            'incoming_calls': calls.filter(call_type='incoming').count(),
            'outgoing_calls': calls.filter(call_type='outgoing').count(),
            'answered_calls': calls.filter(status='answered').count(),
            'missed_calls': calls.filter(status='missed').count(),
            'busy_calls': calls.filter(status='busy').count(),
            'total_duration': sum(call.duration for call in calls),
            'average_duration': calls.aggregate(
                avg_duration=models.Avg('duration')
            )['avg_duration'] or 0,
        }
        
        # Günlük dağılım
        daily_calls = calls.extra(
            select={'day': 'DATE(start_time)'}
        ).values('day').annotate(
            count=models.Count('id')
        ).order_by('day')
        
        stats['daily_breakdown'] = list(daily_calls)
        
        return stats
    
    def make_outbound_call(self, phone_number, agent_extension=None):
        """
        Dışarı arama başlat (API üzerinden)
        """
        try:
            url = f"{self.base_url}/call/make"
            
            data = {
                'username': self.username,
                'password': self.password,
                'phone_number': phone_number,
                'agent_extension': agent_extension
            }
            
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Outbound call initiated to {phone_number}")
            
            return {
                'success': True,
                'call_id': result.get('call_id'),
                'message': 'Arama başlatıldı'
            }
            
        except requests.RequestException as e:
            logger.error(f"Error making outbound call: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_agent_status(self, extension=None):
        """
        Santral agent durumunu getir
        """
        try:
            url = f"{self.base_url}/agent/status"
            
            params = {
                'username': self.username,
                'password': self.password
            }
            
            if extension:
                params['extension'] = extension
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Error getting agent status: {str(e)}")
            return None