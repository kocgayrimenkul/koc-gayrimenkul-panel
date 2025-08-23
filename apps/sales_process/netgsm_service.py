# -*- coding: utf-8 -*-
"""
Netgsm Santral Entegrasyonu
Santral webhook'ları ve API işlemleri için servis sınıfı
Postman Collection'a göre tamamen yeniden yazılmıştır.
"""

import requests
import json
import logging
import uuid
from datetime import datetime, timedelta
from urllib.parse import quote_plus
from django.conf import settings
from django.utils import timezone
from .models import Lead, CallLog
from .whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)

class NetgsmService:
    """
    Netgsm santral entegrasyonu için servis sınıfı
    Postman Collection'daki endpoint'leri kullanır
    """
    
    def __init__(self):
        self.username = settings.NETGSM_USERNAME
        self.password = settings.NETGSM_PASSWORD
        self.api_key = settings.NETGSM_API_KEY
        self.webhook_secret = settings.NETGSM_WEBHOOK_SECRET
        self.pbx_number = settings.NETGSM_PBX_NUMBER or settings.NETGSM_USERNAME  # Santral numarası
        self.crm_base_url = settings.NETGSM_CRM_BASE_URL  # CRM API Base URL
        self.api_base_url = settings.NETGSM_API_BASE_URL  # Main API Base URL
        
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
        from .models import LeadNote, Task, SalesStage, StageTransition
        
        # Not ekle
        LeadNote.objects.create(
            lead=lead,
            title="Arama Cevaplanmış",
            content=f"Arama cevaplanmış - Süre: {call_log.duration} saniye",
            note_type='call',
            created_by_id=1  # System user
        )
        
        # CALL_OK durumunda otomatik aşama geçişi
        # Eğer lead 'bilgi_verildi' aşamasındaysa ve arama başarılıysa 'ihtiyac_analizi'ne geç
        if (lead.current_stage and 
            lead.current_stage.slug == 'bilgi_verildi' and 
            call_log.duration >= 30):  # En az 30 saniye konuşulmuşsa başarılı sayılır
            
            try:
                ihtiyac_analizi_stage = SalesStage.objects.get(slug='ihtiyac_analizi')
                old_stage = lead.current_stage
                
                # Aşama geçişini kaydet
                StageTransition.objects.create(
                    lead=lead,
                    from_stage=old_stage,
                    to_stage=ihtiyac_analizi_stage,
                    transition_type='automatic',
                    reason=f'Başarılı arama sonrası otomatik geçiş (Süre: {call_log.duration}s)',
                    performed_by_id=1  # System user
                )
                
                # Lead'i güncelle
                lead.current_stage = ihtiyac_analizi_stage
                lead.stage_updated_at = timezone.now()
                lead.save()
                
                # Sistem notu ekle
                LeadNote.objects.create(
                    lead=lead,
                    title="Otomatik Aşama Geçişi",
                    content=f"Otomatik aşama geçişi: {old_stage.name} → {ihtiyac_analizi_stage.name} (Başarılı arama)",
                    note_type='system',
                    created_by_id=1
                )
                
                logger.info(f"Lead {lead.lead_id} otomatik olarak {ihtiyac_analizi_stage.name} aşamasına geçirildi")
                
            except SalesStage.DoesNotExist:
                logger.error("İhtiyaç Analizi aşaması bulunamadı")
        
        # Eğer arama 30 saniyeden kısaysa follow-up task oluştur
        elif call_log.duration < 30:
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
            title="Kaçırılmış Arama",
            content="Kaçırılmış arama - Geri arama yapılması gerekiyor",
            note_type='call',
            created_by_id=1
        )
        
        # Geri arama task'ı oluştur
        Task.objects.create(
            lead=lead,
            title="Kaçırılmış Arama - Geri Arama",
            description=f"Müşteri {call_log.start_time.strftime('%d.%m.%Y %H:%M') if call_log.start_time else 'Bilinmeyen tarih'} tarihinde aradı ancak arama cevaplanamadı.",
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
            title="Arama Meşgul",
            content="Arama meşgul - Daha sonra tekrar aranacak",
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
                notes=f"Gelen aramadan otomatik oluşturuldu - {call_log.start_time.strftime('%d.%m.%Y %H:%M') if call_log.start_time else 'Bilinmeyen tarih'}"
            )
            
            # İlk not ekle
            from .models import LeadNote
            LeadNote.objects.create(
                lead=lead,
                title="Otomatik Lead Oluşturuldu",
                content="Gelen aramadan otomatik lead oluşturuldu",
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
    
    def make_outbound_call(self, phone_number, agent_extension=None, ring_timeout=20):
        """
        Dışarı arama başlat (Postman Collection - HTTP GET Çağrı Başlatma)
        URL: http://crmsntrl.netgsm.com.tr:9111/{pbx_number}/originate
        """
        
        print(f"[DEBUG] make_outbound_call called with phone: {phone_number}, extension: {agent_extension}")
        
        try:
            # Telefon numarasını temizle
            clean_phone = self._clean_phone_number(phone_number)
            print(f"[DEBUG] Cleaned phone number: {clean_phone}")
            
            # CRM ID oluştur
            crm_id = str(uuid.uuid4())[:8]
            print(f"[DEBUG] Generated CRM ID: {crm_id}")
            
            # Postman collection'daki endpoint
            url = f"{self.crm_base_url}/{self.pbx_number}/originate"
            print(f"[DEBUG] Full URL: `{url}`")
            
            # Postman collection'a göre doğru parametreler
            # username parametresi santral numarası değil, kullanıcı adı olmalı
            params = {
                'username': self.pbx_number,  # Postman'de username = santral numarası
                'password': self.password,    # Şifre (URL encode edilmemeli)
                'customer_num': clean_phone,  # Arama yapılacak dış numara
                'pbxnum': self.pbx_number,    # Santral numarası
                'internal_num': str(agent_extension or '100'),  # İç dahili numarası
                'ring_timeout': str(ring_timeout),  # Çaldırma süresi
                'crm_id': crm_id,             # CRM ID
                'wait_response': '1',         # Response bekle
                'originate_order': 'of',      # Önce dış numara çalsın
                'trunk': self.pbx_number      # Aramada görünecek numara
            }
            
            # Şifreyi gizleyerek parametreleri yazdır
            params_for_log = params.copy()
            params_for_log['password'] = '***HIDDEN***'
            
            print(f"[DEBUG] Request parameters: {params_for_log}")
            logger.info(f"Making outbound call to {clean_phone} with params: {params_for_log}")
            
            # Manuel URL oluştur - şifrenin URL encode edilmemesi için
            query_parts = []
            for key, value in params.items():
                if key == 'password':
                    # Şifreyi URL encode etme
                    query_parts.append(f"{key}={value}")
                else:
                    # Diğer parametreleri normal encode et
                    query_parts.append(f"{key}={quote_plus(str(value))}")
            
            query_string = '&'.join(query_parts)
            final_url = f"{url}?{query_string}"
            print(f"[DEBUG] Final manual URL: {final_url}")
            
            print(f"[DEBUG] Sending GET request with timeout: 30")
            response = requests.get(final_url, timeout=30)
            response.raise_for_status()
            
            print(f"[DEBUG] Response status code: {response.status_code}")
            print(f"[DEBUG] Response headers: {dict(response.headers)}")
            print(f"[DEBUG] Response URL: {response.url}")
            print(f"[DEBUG] Raw response text: '{response.text}'")
            print(f"[DEBUG] Response text length: {len(response.text)}")
            
            # Response'u kontrol et
            response_text = response.text.strip()
            
            logger.info(f"NetGSM Response: {response_text}")
            
            # NetGSM genelde basit text response döner
            if 'OK' in response_text or 'SUCCESS' in response_text.upper():
                result = {
                    'success': True,
                    'call_id': crm_id,
                    'message': 'Arama başlatıldı',
                    'response': response_text
                }
                print(f"[DEBUG] Success result: {result}")
                return result
            else:
                result = {
                    'success': False,
                    'error': f'NetGSM Error: {response_text}',
                    'response': response_text
                }
                print(f"[DEBUG] Error result: {result}")
                return result
            
        except requests.RequestException as e:
            logger.error(f"Error making outbound call: {str(e)}")
            result = {
                'success': False,
                'error': str(e)
            }
            print(f"[DEBUG] Request exception result: {result}")
            return result
        except Exception as e:
            logger.error(f"General error making outbound call: {str(e)}")
            result = {
                'success': False,
                'error': str(e)
            }
            print(f"[DEBUG] General exception result: {result}")
            return result
    
    def hangup_call(self, unique_id, crm_id=None):
        """
        Çağrı sonlandırma (Postman Collection - HTTP GET Çağrı Sonlandırma)
        URL: http://crmsntrl.netgsm.com.tr:9111/{pbx_number}/hangup
        """
        try:
            if not crm_id:
                crm_id = str(uuid.uuid4())[:8]
            
            url = f"{self.crm_base_url}/{self.pbx_number}/hangup"
            
            params = {
                'username': self.username,
                'password': quote_plus(self.password),
                'unique_id': unique_id,  # Sonlandırmak istenilen çağrıya ait ID
                'crm_id': crm_id         # CRM ID
            }
            
            logger.info(f"Hanging up call {unique_id} with params: {params}")
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            response_text = response.text.strip()
            logger.info(f"NetGSM Hangup Response: {response_text}")
            
            if 'OK' in response_text or 'SUCCESS' in response_text.upper():
                return {
                    'success': True,
                    'message': 'Çağrı sonlandırıldı',
                    'response': response_text
                }
            else:
                return {
                    'success': False,
                    'error': f'NetGSM Error: {response_text}',
                    'response': response_text
                }
            
        except requests.RequestException as e:
            logger.error(f"Error hanging up call: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def mute_call(self, unique_id, direction='all', state='mute', crm_id=None):
        """
        Çağrıyı sessize alma (Postman Collection - HTTP GET Çağrıyı Sessize Alma)
        URL: http://crmsntrl.netgsm.com.tr:9111/{pbx_number}/muteaudio
        """
        try:
            if not crm_id:
                crm_id = str(uuid.uuid4())[:8]
            
            url = f"{self.crm_base_url}/{self.pbx_number}/muteaudio"
            
            params = {
                'username': self.username,
                'password': quote_plus(self.password),
                'unique_id': unique_id,   # Sessize alınmak istenilen çağrıya ait ID
                'crm_id': crm_id,         # CRM ID
                'direction': direction,   # all/in/out
                'state': state           # mute/unmute
            }
            
            logger.info(f"Muting call {unique_id} with params: {params}")
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            response_text = response.text.strip()
            logger.info(f"NetGSM Mute Response: {response_text}")
            
            if 'OK' in response_text or 'SUCCESS' in response_text.upper():
                return {
                    'success': True,
                    'message': f'Çağrı {state} yapıldı',
                    'response': response_text
                }
            else:
                return {
                    'success': False,
                    'error': f'NetGSM Error: {response_text}',
                    'response': response_text
                }
            
        except requests.RequestException as e:
            logger.error(f"Error muting call: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def link_calls(self, caller_number, called_number, ring_timeout=20, originate_order='if', crm_id=None):
        """
        Çağrı bağlama (Postman Collection - HTTP GET Çağrı Bağlama)
        URL: http://crmsntrl.netgsm.com.tr:9111/{pbx_number}/linkup
        """
        try:
            if not crm_id:
                crm_id = str(uuid.uuid4())[:8]
            
            url = f"{self.crm_base_url}/{self.pbx_number}/linkup"
            
            params = {
                'username': self.username,
                'password': quote_plus(self.password),
                'caller': self._clean_phone_number(caller_number),    # Arama yapılacak dış numara
                'called': self._clean_phone_number(called_number),    # Çağrının bağlanacağı diğer dış numara
                'ring_timeout': ring_timeout,     # Çaldırma süresi
                'crm_id': crm_id,                # CRM ID
                'wait_response': '1',            # Response bekle
                'originate_order': originate_order,  # of/if
                'trunk': self.pbx_number         # Santral numarası
            }
            
            logger.info(f"Linking calls {caller_number} -> {called_number} with params: {params}")
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            response_text = response.text.strip()
            logger.info(f"NetGSM Link Response: {response_text}")
            
            if 'OK' in response_text or 'SUCCESS' in response_text.upper():
                return {
                    'success': True,
                    'call_id': crm_id,
                    'message': 'Çağrılar bağlandı',
                    'response': response_text
                }
            else:
                return {
                    'success': False,
                    'error': f'NetGSM Error: {response_text}',
                    'response': response_text
                }
            
        except requests.RequestException as e:
            logger.error(f"Error linking calls: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_queue_stats(self, queue_name, crm_id=None):
        """
        Kuyruk durum sorgulama (Postman Collection - HTTP GET Çağrı Kuyruğu)
        URL: http://crmsntrl.netgsm.com.tr:9111/{pbx_number}/queuestats
        """
        try:
            if not crm_id:
                crm_id = str(uuid.uuid4())[:8]
            
            url = f"{self.crm_base_url}/{self.pbx_number}/queuestats"
            
            params = {
                'username': self.username,
                'password': quote_plus(self.password),
                'queue': queue_name,  # Sorgulanmak istenen kuyruğun adı
                'crm_id': crm_id      # CRM ID
            }
            
            logger.info(f"Getting queue stats for {queue_name} with params: {params}")
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            response_text = response.text.strip()
            logger.info(f"NetGSM Queue Stats Response: {response_text}")
            
            return {
                'success': True,
                'data': response_text,
                'response': response_text
            }
            
        except requests.RequestException as e:
            logger.error(f"Error getting queue stats: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def agent_login(self, queue_name, extension, paused=1, penalty=1, crm_id=None):
        """
        Kuyruğa dahili ekleme (Postman Collection - HTTP GET Dahili Ekleme)
        URL: http://crmsntrl.netgsm.com.tr:9111/{pbx_number}/agentlogin
        """
        try:
            if not crm_id:
                crm_id = str(uuid.uuid4())[:8]
            
            url = f"{self.crm_base_url}/{self.pbx_number}/agentlogin"
            
            params = {
                'username': self.username,
                'password': quote_plus(self.password),
                'crm_id': crm_id,
                'queue': queue_name,      # Ekleme yapılmak istenen kuyruğun adı
                'paused': str(paused),    # Molada başlangıç için 1, açık başlamak için 0
                'penalty': str(penalty),  # Kuyruktaki dahililerinizin hangisine fazla çağrı verileceği
                'exten': str(extension)   # Eklenmek istenen dahili numarası
            }
            
            logger.info(f"Agent login {extension} to queue {queue_name} with params: {params}")
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            response_text = response.text.strip()
            logger.info(f"NetGSM Agent Login Response: {response_text}")
            
            if 'OK' in response_text or 'SUCCESS' in response_text.upper():
                return {
                    'success': True,
                    'message': f'Dahili {extension} kuyruğa eklendi',
                    'response': response_text
                }
            else:
                return {
                    'success': False,
                    'error': f'NetGSM Error: {response_text}',
                    'response': response_text
                }
            
        except requests.RequestException as e:
            logger.error(f"Error agent login: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def agent_logout(self, queue_name, extension, crm_id=None):
        """
        Kuyruktaki dahili çıkarma (Postman Collection - HTTP GET Dahili Çıkarma)
        URL: http://crmsntrl.netgsm.com.tr:9111/{pbx_number}/agentlogoff
        """
        try:
            if not crm_id:
                crm_id = str(uuid.uuid4())[:8]
            
            url = f"{self.crm_base_url}/{self.pbx_number}/agentlogoff"
            
            params = {
                'username': self.username,
                'password': quote_plus(self.password),
                'crm_id': crm_id,
                'exten': str(extension),  # Çıkarılmak istenen dahili numarası
                'queue': queue_name       # Dahili çıkarılmak istenen kuyruğun adı
            }
            
            logger.info(f"Agent logout {extension} from queue {queue_name} with params: {params}")
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            response_text = response.text.strip()
            logger.info(f"NetGSM Agent Logout Response: {response_text}")
            
            if 'OK' in response_text or 'SUCCESS' in response_text.upper():
                return {
                    'success': True,
                    'message': f'Dahili {extension} kuyruktan çıkarıldı',
                    'response': response_text
                }
            else:
                return {
                    'success': False,
                    'error': f'NetGSM Error: {response_text}',
                    'response': response_text
                }
            
        except requests.RequestException as e:
            logger.error(f"Error agent logout: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def agent_pause(self, queue_name, extension, paused=1, reason='CRM', crm_id=None):
        """
        Kuyruktaki dahiliyi molaya alma/çıkarma (Postman Collection - HTTP GET Dahili Mola)
        URL: http://crmsntrl.netgsm.com.tr:9111/{pbx_number}/agentpause
        """
        try:
            if not crm_id:
                crm_id = str(uuid.uuid4())[:8]
            
            url = f"{self.crm_base_url}/{self.pbx_number}/agentpause"
            
            params = {
                'username': self.username,
                'password': quote_plus(self.password),
                'crm_id': crm_id,
                'exten': str(extension),  # Dahili numarası
                'queue': queue_name,      # Dahilinin bulunduğu kuyruğun adı
                'paused': str(paused),    # Molaya almak için 1, moladan çıkmak için 0
                'reason': reason          # Molaya alma sebebi
            }
            
            logger.info(f"Agent pause {extension} in queue {queue_name} with params: {params}")
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            response_text = response.text.strip()
            logger.info(f"NetGSM Agent Pause Response: {response_text}")
            
            action = 'molaya alındı' if paused == 1 else 'moladan çıkarıldı'
            
            if 'OK' in response_text or 'SUCCESS' in response_text.upper():
                return {
                    'success': True,
                    'message': f'Dahili {extension} {action}',
                    'response': response_text
                }
            else:
                return {
                    'success': False,
                    'error': f'NetGSM Error: {response_text}',
                    'response': response_text
                }
            
        except requests.RequestException as e:
            logger.error(f"Error agent pause: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def add_external_number_to_queue(self, queue_name, phone_number, penalty=1):
        """
        Kuyruğa dış numara ekleme (Postman Collection - JSON POST)
        URL: https://api.netgsm.com.tr/netsantral/queue
        """
        try:
            url = f"{self.api_base_url}/netsantral/queue"
            
            data = {
                'username': self.username,
                'password': self.password,  # POST body'de encode etmeye gerek yok
                'command': 'queueaddnumber',
                'tenant': self.pbx_number,
                'queue': queue_name,
                'no': self._clean_phone_number(phone_number),
                'penalty': str(penalty)
            }
            
            logger.info(f"Adding external number {phone_number} to queue {queue_name} with data: {data}")
            
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            
            response_text = response.text.strip()
            logger.info(f"NetGSM Add External Number Response: {response_text}")
            
            if 'OK' in response_text or 'SUCCESS' in response_text.upper():
                return {
                    'success': True,
                    'message': f'Dış numara {phone_number} kuyruğa eklendi',
                    'response': response_text
                }
            else:
                return {
                    'success': False,
                    'error': f'NetGSM Error: {response_text}',
                    'response': response_text
                }
            
        except requests.RequestException as e:
            logger.error(f"Error adding external number to queue: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def dynamic_redirect(self, called_number, redirect_menu, redirect_type='ivr', ring_timeout=20, crm_id=None):
        """
        Dinamik yönlendirme (Postman Collection - HTTP GET Yönlendirme)
        URL: http://crmsntrl.netgsm.com.tr:9111/{pbx_number}/dynamic_redirect
        """
        try:
            if not crm_id:
                crm_id = str(uuid.uuid4())[:8]
            
            url = f"{self.crm_base_url}/{self.pbx_number}/dynamic_redirect"
            
            params = {
                'username': self.username,
                'password': quote_plus(self.password),
                'called': self._clean_phone_number(called_number),  # Arama yapılacak numara
                'redirect_menu': redirect_menu,     # Aktarılacak menü ismi
                'redirect_type': redirect_type,     # queue, announcement, ivr
                'ring_timeout': ring_timeout,       # Çaldırma süresi
                'crm_id': crm_id,                  # CRM ID
                'wait_response': '1',              # Response bekle
                'trunk': self.pbx_number           # Santral numarası
            }
            
            logger.info(f"Dynamic redirect {called_number} to {redirect_menu} with params: {params}")
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            response_text = response.text.strip()
            logger.info(f"NetGSM Dynamic Redirect Response: {response_text}")
            
            if 'OK' in response_text or 'SUCCESS' in response_text.upper():
                return {
                    'success': True,
                    'message': f'Çağrı {redirect_menu} menüsüne yönlendirildi',
                    'response': response_text
                }
            else:
                return {
                    'success': False,
                    'error': f'NetGSM Error: {response_text}',
                    'response': response_text
                }
            
        except requests.RequestException as e:
            logger.error(f"Error dynamic redirect: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }