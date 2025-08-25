# -*- encoding: utf-8 -*-
"""
WhatsApp API Test Komutu
Kullanım: python manage.py test_whatsapp +905070775025 "Test mesajı"
"""

from django.core.management.base import BaseCommand, CommandError
from apps.sales_process.whatsapp_service import whatsapp_service
import sys


class Command(BaseCommand):
    help = 'WhatsApp API ile test mesajı gönderir'
    
    def add_arguments(self, parser):
        parser.add_argument('phone', type=str, help='Telefon numarası (+905070775025 formatında)')
        parser.add_argument('message', type=str, nargs='?', default='Test mesajı - Koç Gayrimenkul Panel', help='Gönderilecek mesaj')
        parser.add_argument(
            '--mock',
            action='store_true',
            help='Mock mode kullan (gerçek API çağrısı yapmaz)',
        )
    
    def handle(self, *args, **options):
        phone = options['phone']
        message = options['message']
        use_mock = options['mock']
        
        # Telefon numarası formatını kontrol et
        if not phone.startswith('+'):
            raise CommandError('Telefon numarası + ile başlamalıdır (örn: +905070775025)')
        
        self.stdout.write(f'WhatsApp mesajı gönderiliyor...')
        self.stdout.write(f'Telefon: {phone}')
        self.stdout.write(f'Mesaj: {message}')
        
        if use_mock:
            self.stdout.write(self.style.WARNING('Mock mode aktif - gerçek mesaj gönderilmeyecek'))
            # Mock mode'u zorla aktif et
            original_mock = whatsapp_service.mock_mode
            whatsapp_service.mock_mode = True
        
        try:
            # WhatsApp mesajı gönder
            result = whatsapp_service.send_text_message(
                to_phone=phone,
                message_text=message
            )
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Mesaj başarıyla gönderildi!\n'
                        f'Message ID: {result.get("message_id", "N/A")}\n'
                        f'DB ID: {result.get("db_id", "N/A")}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ Mesaj gönderilemedi!\n'
                        f'Hata: {result.get("error", "Bilinmeyen hata")}'
                    )
                )
                sys.exit(1)
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Beklenmeyen hata: {str(e)}')
            )
            sys.exit(1)
        
        finally:
            if use_mock:
                # Mock mode'u eski haline getir
                whatsapp_service.mock_mode = original_mock
        
        # WhatsApp ayarlarını göster
        self.stdout.write('\n' + '='*50)
        self.stdout.write('WhatsApp API Ayarları:')
        self.stdout.write(f'Mock Mode: {whatsapp_service.mock_mode}')
        self.stdout.write(f'Access Token: {"✅ Var" if whatsapp_service.access_token else "❌ Yok"}')
        self.stdout.write(f'Phone Number ID: {"✅ Var" if whatsapp_service.phone_number_id else "❌ Yok"}')
        self.stdout.write(f'Base URL: {whatsapp_service.base_url}')
        self.stdout.write('='*50)