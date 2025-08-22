# -*- encoding: utf-8 -*-
"""
WhatsApp Business Cloud API Entegrasyonu
Satış süreç yönetimi için WhatsApp mesajlaşma servisi
"""

import requests
import json
from django.conf import settings
from django.utils import timezone
from datetime import datetime
import logging

from .models import WhatsAppMessage, Lead

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    WhatsApp Business Cloud API servisi
    """
    
    def __init__(self):
        self.access_token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', '')
        self.phone_number_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', '')
        self.verify_token = getattr(settings, 'WHATSAPP_VERIFY_TOKEN', '')
        self.base_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"
        
        # Mock mode - WhatsApp entegrasyonu henüz aktif değilse mock kullan
        self.mock_mode = getattr(settings, 'WHATSAPP_MOCK_MODE', True)
        
        if not self.access_token or not self.phone_number_id:
            logger.warning("WhatsApp credentials not configured properly")
            self.mock_mode = True
    
    def send_text_message(self, to_phone, message_text, lead_id=None):
        """
        Metin mesajı gönderir
        """
        try:
            # Telefon numarasını temizle
            clean_phone = self._clean_phone_number(to_phone)
            
            # Mock mode kontrolü
            if self.mock_mode:
                return self._send_mock_message(clean_phone, message_text, 'text', lead_id)
            
            payload = {
                "messaging_product": "whatsapp",
                "to": clean_phone,
                "type": "text",
                "text": {
                    "body": message_text
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            response_data = response.json()
            
            if response.status_code == 200:
                message_id = response_data.get('messages', [{}])[0].get('id')
                
                # Veritabanına kaydet
                whatsapp_message = WhatsAppMessage.objects.create(
                    lead_id=lead_id,
                    message_id=message_id,
                    direction='outbound',
                    message_type='text',
                    content=message_text,
                    status='sent'
                )
                
                logger.info(f"WhatsApp message sent successfully to {clean_phone}")
                return {
                    'success': True,
                    'message_id': message_id,
                    'db_id': whatsapp_message.id
                }
            else:
                error_msg = response_data.get('error', {}).get('message', 'Unknown error')
                logger.error(f"WhatsApp API error: {error_msg}")
                
                # Hatalı mesajı da kaydet
                WhatsAppMessage.objects.create(
                    lead_id=lead_id,
                    message_id=f"failed_{timezone.now().timestamp()}",
                    direction='outbound',
                    message_type='text',
                    content=message_text,
                    status='failed',
                    error_message=error_msg
                )
                
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"WhatsApp request error: {str(e)}")
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"WhatsApp service error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_offer_message(self, to_phone, offer_content, lead_id=None):
        """
        Teklif mesajı gönderir - Osman'ın istediği zorunlu WhatsApp teklif gönderimi
        """
        try:
            # Telefon numarasını temizle
            clean_phone = self._clean_phone_number(to_phone)
            
            # Mock mode kontrolü
            if self.mock_mode:
                return self._send_mock_message(clean_phone, offer_content, 'offer_sent', lead_id)
            
            payload = {
                "messaging_product": "whatsapp",
                "to": clean_phone,
                "type": "text",
                "text": {
                    "body": offer_content
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            response_data = response.json()
            
            if response.status_code == 200:
                message_id = response_data.get('messages', [{}])[0].get('id')
                
                # Veritabanına offer_sent olarak kaydet
                whatsapp_message = WhatsAppMessage.objects.create(
                    lead_id=lead_id,
                    message_id=message_id,
                    direction='outbound',
                    message_type='offer_sent',  # Özel teklif mesaj tipi
                    content=offer_content,
                    status='sent'
                )
                
                logger.info(f"WhatsApp offer message sent successfully to {clean_phone}")
                return {
                    'success': True,
                    'message_id': message_id,
                    'db_id': whatsapp_message.id
                }
            else:
                error_msg = response_data.get('error', {}).get('message', 'Unknown error')
                logger.error(f"WhatsApp API error: {error_msg}")
                
                # Hatalı mesajı da kaydet
                WhatsAppMessage.objects.create(
                    lead_id=lead_id,
                    message_id=f"failed_{timezone.now().timestamp()}",
                    direction='outbound',
                    message_type='offer_sent',
                    content=offer_content,
                    status='failed',
                    error_message=error_msg
                )
                
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp offer message: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_template_message(self, to_phone, template_name, template_params=None, lead_id=None):
        """
        Template mesajı gönderir
        """
        try:
            clean_phone = self._clean_phone_number(to_phone)
            
            payload = {
                "messaging_product": "whatsapp",
                "to": clean_phone,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": "tr"
                    }
                }
            }
            
            # Template parametreleri varsa ekle
            if template_params:
                payload["template"]["components"] = [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": param} for param in template_params
                        ]
                    }
                ]
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            response_data = response.json()
            
            if response.status_code == 200:
                message_id = response_data.get('messages', [{}])[0].get('id')
                
                # Veritabanına kaydet
                whatsapp_message = WhatsAppMessage.objects.create(
                    lead_id=lead_id,
                    message_id=message_id,
                    direction='outbound',
                    message_type='template',
                    content=f"Template: {template_name}",
                    template_name=template_name,
                    status='sent'
                )
                
                logger.info(f"WhatsApp template message sent to {clean_phone}")
                return {
                    'success': True,
                    'message_id': message_id,
                    'db_id': whatsapp_message.id
                }
            else:
                error_msg = response_data.get('error', {}).get('message', 'Unknown error')
                logger.error(f"WhatsApp template error: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            logger.error(f"WhatsApp template service error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_document(self, to_phone, document_url, filename=None, caption=None, lead_id=None):
        """
        Doküman gönderir
        """
        try:
            clean_phone = self._clean_phone_number(to_phone)
            
            payload = {
                "messaging_product": "whatsapp",
                "to": clean_phone,
                "type": "document",
                "document": {
                    "link": document_url
                }
            }
            
            if filename:
                payload["document"]["filename"] = filename
            
            if caption:
                payload["document"]["caption"] = caption
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            response_data = response.json()
            
            if response.status_code == 200:
                message_id = response_data.get('messages', [{}])[0].get('id')
                
                # Veritabanına kaydet
                whatsapp_message = WhatsAppMessage.objects.create(
                    lead_id=lead_id,
                    message_id=message_id,
                    direction='outbound',
                    message_type='document',
                    content=caption or f"Document: {filename or 'file'}",
                    media_url=document_url,
                    status='sent'
                )
                
                logger.info(f"WhatsApp document sent to {clean_phone}")
                return {
                    'success': True,
                    'message_id': message_id,
                    'db_id': whatsapp_message.id
                }
            else:
                error_msg = response_data.get('error', {}).get('message', 'Unknown error')
                logger.error(f"WhatsApp document error: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            logger.error(f"WhatsApp document service error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_webhook(self, webhook_data):
        """
        Webhook verilerini işler
        """
        try:
            entry = webhook_data.get('entry', [])
            if not entry:
                return {'success': False, 'error': 'No entry data'}
            
            changes = entry[0].get('changes', [])
            if not changes:
                return {'success': False, 'error': 'No changes data'}
            
            value = changes[0].get('value', {})
            
            # Mesaj durumu güncellemeleri
            if 'statuses' in value:
                self._process_status_updates(value['statuses'])
            
            # Gelen mesajlar
            if 'messages' in value:
                self._process_incoming_messages(value['messages'])
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _process_status_updates(self, statuses):
        """
        Mesaj durumu güncellemelerini işler
        """
        for status in statuses:
            message_id = status.get('id')
            status_type = status.get('status')
            timestamp = status.get('timestamp')
            
            if message_id:
                try:
                    whatsapp_message = WhatsAppMessage.objects.get(
                        message_id=message_id
                    )
                    
                    # Durumu güncelle
                    if status_type in ['delivered', 'read', 'failed']:
                        whatsapp_message.status = status_type
                        
                        if status_type == 'delivered':
                            whatsapp_message.delivered_at = datetime.fromtimestamp(int(timestamp))
                        elif status_type == 'read':
                            whatsapp_message.read_at = datetime.fromtimestamp(int(timestamp))
                        elif status_type == 'failed':
                            whatsapp_message.error_message = status.get('errors', [{}])[0].get('title', 'Failed')
                        
                        whatsapp_message.save()
                        logger.info(f"Message {message_id} status updated to {status_type}")
                        
                except WhatsAppMessage.DoesNotExist:
                    logger.warning(f"WhatsApp message not found: {message_id}")
                except Exception as e:
                    logger.error(f"Status update error: {str(e)}")
    
    def _process_incoming_messages(self, messages):
        """
        Gelen mesajları işler
        """
        for message in messages:
            try:
                from_phone = message.get('from')
                message_id = message.get('id')
                timestamp = message.get('timestamp')
                message_type = message.get('type')
                
                # Mesaj içeriğini al
                content = ''
                if message_type == 'text':
                    content = message.get('text', {}).get('body', '')
                elif message_type == 'image':
                    content = 'Image received'
                elif message_type == 'document':
                    content = 'Document received'
                elif message_type == 'audio':
                    content = 'Audio received'
                
                # Lead'i bul
                lead = None
                try:
                    lead = Lead.objects.filter(
                        customer_phone__icontains=from_phone[-10:]  # Son 10 hanesi ile eşleştir
                    ).first()
                except:
                    pass
                
                # Gelen mesajı kaydet
                WhatsAppMessage.objects.create(
                    lead=lead,
                    message_id=message_id,
                    direction='inbound',
                    message_type=message_type,
                    content=content,
                    status='delivered'  # Gelen mesajlar delivered olarak işaretlenir
                )
                
                logger.info(f"Incoming WhatsApp message from {from_phone}: {content[:50]}")
                
                # Otomatik yanıt (isteğe bağlı)
                if lead and content.lower() in ['merhaba', 'hello', 'hi']:
                    self._send_auto_reply(from_phone, lead)
                    
            except Exception as e:
                logger.error(f"Incoming message processing error: {str(e)}")
    
    def _send_auto_reply(self, to_phone, lead):
        """
        Otomatik yanıt gönderir
        """
        try:
            auto_reply = (
                f"Merhaba {lead.customer_name}, "
                "mesajınız alındı. En kısa sürede size dönüş yapacağız. "
                "Koç Gayrimenkul"
            )
            
            self.send_text_message(to_phone, auto_reply, lead.id)
            
        except Exception as e:
            logger.error(f"Auto reply error: {str(e)}")
    
    def _send_mock_message(self, to_phone, content, message_type, lead_id=None):
        """
        Mock mode için WhatsApp mesajı simülasyonu
        """
        try:
            import uuid
            
            # Mock message ID oluştur
            mock_message_id = f"mock_{uuid.uuid4().hex[:12]}"
            
            # Veritabanına kaydet
            whatsapp_message = WhatsAppMessage.objects.create(
                lead_id=lead_id,
                message_id=mock_message_id,
                direction='outbound',
                message_type=message_type,
                content=content,
                status='sent'
            )
            
            logger.info(f"[MOCK MODE] WhatsApp message simulated to {to_phone}: {content[:50]}...")
            
            return {
                'success': True,
                'message_id': mock_message_id,
                'db_id': whatsapp_message.id,
                'mock_mode': True
            }
            
        except Exception as e:
            logger.error(f"Mock message error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'mock_mode': True
            }
    
    def _clean_phone_number(self, phone):
        """
        Telefon numarasını WhatsApp formatına çevirir
        """
        # Sadece rakamları al
        clean = ''.join(filter(str.isdigit, phone))
        
        # Türkiye için ülke kodu ekle
        if clean.startswith('0'):
            clean = '90' + clean[1:]  # 0 ile başlıyorsa 90 ile değiştir
        elif not clean.startswith('90'):
            clean = '90' + clean  # Ülke kodu yoksa ekle
        
        return clean
    
    def get_message_history(self, lead_id, limit=50):
        """
        Lead'in WhatsApp mesaj geçmişini getirir
        """
        try:
            messages = WhatsAppMessage.objects.filter(
                lead_id=lead_id
            ).order_by('-created_at')[:limit]
            
            return [
                {
                    'id': msg.id,
                    'content': msg.content,
                    'type': msg.message_type,
                    'direction': msg.direction,
                    'status': msg.status,
                    'created_at': msg.created_at.isoformat() if msg.created_at else None,
                    'delivered_at': msg.delivered_at.isoformat() if msg.delivered_at else None,
                    'read_at': msg.read_at.isoformat() if msg.read_at else None
                }
                for msg in messages
            ]
            
        except Exception as e:
            logger.error(f"Message history error: {str(e)}")
            return []


# Hazır template mesajları
class WhatsAppTemplates:
    """
    Önceden tanımlanmış WhatsApp template mesajları
    """
    
    @staticmethod
    def welcome_message(customer_name):
        return (
            f"Merhaba {customer_name}, "
            "Koç Gayrimenkul'e hoş geldiniz! "
            "Size en uygun gayrimenkul seçeneklerini sunmak için buradayız. "
            "Sorularınız için bize ulaşabilirsiniz."
        )
    
    @staticmethod
    def appointment_reminder(customer_name, appointment_date, location):
        return (
            f"Sayın {customer_name}, "
            f"{appointment_date} tarihinde {location} adresinde randevunuz bulunmaktadır. "
            "Randevunuzu onaylamak için lütfen yanıtlayın. "
            "Koç Gayrimenkul"
        )
    
    @staticmethod
    def offer_sent(customer_name):
        return (
            f"Sayın {customer_name}, "
            "talebiniz doğrultusunda hazırladığımız teklif e-posta adresinize gönderilmiştir. "
            "Teklif ile ilgili sorularınız için bize ulaşabilirsiniz. "
            "Koç Gayrimenkul"
        )
    
    @staticmethod
    def contract_ready(customer_name):
        return (
            f"Sayın {customer_name}, "
            "sözleşmeniz hazır! Sözleşme imzalama randevusu için "
            "lütfen bizimle iletişime geçin. "
            "Koç Gayrimenkul"
        )
    
    @staticmethod
    def satisfaction_survey(customer_name):
        return (
            f"Sayın {customer_name}, "
            "hizmetimizden memnuniyetinizi öğrenmek için kısa bir anket hazırladık. "
            "Görüşleriniz bizim için çok değerli. "
            "Koç Gayrimenkul"
        )


# Singleton instance
whatsapp_service = WhatsAppService()