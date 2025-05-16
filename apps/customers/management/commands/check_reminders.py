# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Müşteri Hatırlatmaları Kontrol Komutu
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.customers.models import Customer, CustomerReminder
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Bugün için hatırlatması olan müşterileri kontrol eder ve bildirim oluşturur'
    
    def handle(self, *args, **options):
        today = timezone.now().date()
        
        # Bugün için hatırlatması olan müşterileri bul
        reminders = CustomerReminder.objects.filter(
            reminder_date=today,
            is_sent=False  # Henüz gönderilmemiş hatırlatmalar
        )
        
        if not reminders.exists():
            self.stdout.write(self.style.SUCCESS('Bugün için hatırlatma bulunmuyor.'))
            return
        
        self.stdout.write(f'Toplam {reminders.count()} hatırlatma bulundu.')
        
        for reminder in reminders:
            customer = reminder.customer
            
            # İlgili danışmana e-posta gönder
            if customer.consultant:
                consultant = customer.consultant
                # E-posta gönderme işlemi
                subject = 'Müşteri Hatırlatması'
                message = f"""
                Sayın {consultant.first_name} {consultant.last_name},
                
                {customer.full_name} isimli müşteriniz için bugün bir hatırlatma var.
                
                Müşteri Bilgileri:
                - Ad Soyad: {customer.full_name}
                - Telefon: {customer.phone}
                - Mahalle: {customer.neighborhood.name}
                
                Hatırlatma Mesajı: {reminder.message}
                
                İyi çalışmalar,
                Koç Gayrimenkul
                """
                
                try:
                    if consultant.email:
                        send_mail(
                            subject,
                            message,
                            settings.DEFAULT_FROM_EMAIL,
                            [consultant.email],
                            fail_silently=False,
                        )
                        self.stdout.write(self.style.SUCCESS(f'{consultant.email} adresine bildirim gönderildi.'))
                    else:
                        self.stdout.write(self.style.WARNING(f'{consultant.username} kullanıcısının e-posta adresi bulunamadı.'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'E-posta gönderilirken hata oluştu: {str(e)}'))
            
            # Hatırlatma gönderildi olarak işaretle
            reminder.is_sent = True
            reminder.save()
            
            self.stdout.write(self.style.SUCCESS(f'{customer.full_name} için hatırlatma işlendi.'))
            
        self.stdout.write(self.style.SUCCESS('Hatırlatma işlemleri tamamlandı.')) 