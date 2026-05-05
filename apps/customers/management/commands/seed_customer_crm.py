# -*- encoding: utf-8 -*-
"""
Örnek müşteri verisi oluşturma komutu (DÜZELTİLMİŞ).
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.customers.models import (
    Customer, Neighborhood,
    CustomerFinancialInfo, CustomerNote, CustomerTask,
    CustomerWorkflow, CustomerOffer, CustomerDemand,
    CustomerSmsLog, CustomerWhatsappLog, CustomerActivity,
)
from apps.portfolio.models import Property

User = get_user_model()


class Command(BaseCommand):
    help = 'CRM müşteri detay sayfası için örnek veri oluşturur'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🌱 CRM seed data oluşturuluyor..."))

        consultant = User.objects.filter(username__iexact='osman').first() \
                     or User.objects.filter(is_staff=True).first() \
                     or User.objects.first()

        if not consultant:
            self.stdout.write(self.style.ERROR("❌ Sistemde kullanıcı yok."))
            return

        self.stdout.write(f"✓ Danışman: {consultant.username}")

        neighborhood, _ = Neighborhood.objects.get_or_create(
            name="Şehitkamil Merkez",
            defaults={'district': 'Şehitkamil'},
        )
        self.stdout.write(f"✓ Mahalle: {neighborhood}")

        property_obj = Property.objects.filter(is_active=True).first()
        if not property_obj:
            self.stdout.write(self.style.ERROR("❌ Hiç aktif portföy bulunamadı."))
            return
        self.stdout.write(f"✓ Mevcut portföy kullanıldı: {property_obj}")

        customer_unknown, created = Customer.objects.update_or_create(
            phone='05073945262',
            defaults={
                'full_name': '',
                'neighborhood': neighborhood,
                'consultant': consultant,
                'customer_type': 'bireysel',
                'status': 'potansiyel',
                'source': 'referans',
                'email_permission': True,
                'sms_permission': True,
                'whatsapp_permission': True,
            },
        )
        self.stdout.write(self.style.SUCCESS(
            f"{'✓ Oluşturuldu' if created else '↻ Güncellendi'}: {customer_unknown}"
        ))

        customer_full, created = Customer.objects.update_or_create(
            phone='05321234567',
            defaults={
                'full_name': 'Ahmet Yılmaz',
                'email': 'ahmet.yilmaz@example.com',
                'neighborhood': neighborhood,
                'consultant': consultant,
                'customer_type': 'bireysel',
                'status': 'aktif',
                'gender': 'erkek',
                'city': 'Gaziantep',
                'district': 'Şehitkamil',
                'address': 'Mücahitler Mah. 42123 Sok. No:5',
                'source': 'sahibinden',
                'email_permission': True,
                'sms_permission': True,
                'whatsapp_permission': False,
                'meeting_status': 'olumlu',
            },
        )
        self.stdout.write(self.style.SUCCESS(
            f"{'✓ Oluşturuldu' if created else '↻ Güncellendi'}: {customer_full}"
        ))

        CustomerFinancialInfo.objects.update_or_create(
            customer=customer_full,
            defaults={
                'monthly_income': Decimal('45000.00'),
                'credit_score': 1750,
                'budget_min': Decimal('2500000.00'),
                'budget_max': Decimal('3500000.00'),
                'notes': "Peşinat %30, kalan kredi.",
            },
        )

        CustomerNote.objects.get_or_create(
            customer=customer_unknown,
            content="İlk görüşmede 2+1 daire aradığını belirtti. Bütçesi 3.5M civarı.",
            defaults={'user': consultant, 'note_type': 'not', 'priority': 'normal'},
        )
        CustomerNote.objects.get_or_create(
            customer=customer_full,
            content="Müşteri fiyat konusunda pazarlık yapmak istiyor. Takasa açık.",
            defaults={'user': consultant, 'note_type': 'yorum', 'priority': 'yuksek'},
        )

        CustomerTask.objects.get_or_create(
            customer=customer_unknown,
            title="Müşteriyi geri ara",
            defaults={
                'assigned_to': consultant,
                'description': 'Pazar günü müsaitliğini sor.',
                'priority': 'yuksek',
                'status': 'acik',
                'due_date': timezone.now() + timedelta(days=2),
            },
        )
        CustomerTask.objects.get_or_create(
            customer=customer_full,
            title="Daire gösterimi ayarla",
            defaults={
                'assigned_to': consultant,
                'priority': 'normal',
                'status': 'tamamlandi',
                'completed_at': timezone.now() - timedelta(days=1),
            },
        )

        CustomerWorkflow.objects.get_or_create(
            customer=customer_full,
            title="Satış süreci - Merkez 2+1",
            defaults={
                'created_by': consultant,
                'workflow_type': 'satis',
                'priority': 'yuksek',
                'status': 'aktif',
                'description': 'Müşteri ile satış görüşmeleri başladı.',
                'related_property': property_obj,
                'due_date': (timezone.now() + timedelta(days=30)).date(),
            },
        )

        CustomerOffer.objects.get_or_create(
            customer=customer_unknown,
            related_property=property_obj,
            defaults={
                'created_by': consultant,
                'title': "1.ETAPTA PAZAR YERİ YANINDA ARA KAT YERDEN ISITM...",
                'offer_price': Decimal('3300000.00'),
                'currency': 'TRY',
                'status': 'bekliyor',
            },
        )

        CustomerDemand.objects.get_or_create(
            customer=customer_full,
            property_type='daire',
            transaction_type='satilik',
            defaults={
                'min_price': Decimal('2500000'),
                'max_price': Decimal('3500000'),
                'min_area': Decimal('100'),
                'max_area': Decimal('140'),
                'room_count': '2+1',
                'preferred_locations': 'Şehitkamil, Şahinbey merkez semtleri',
                'status': 'aktif',
            },
        )

        CustomerSmsLog.objects.create(
            customer=customer_full,
            user=consultant,
            phone=customer_full.phone,
            message="Sayın Ahmet Bey, randevunuz yarın 14:00'de.",
            status='gonderildi',
        )

        CustomerActivity.objects.create(
            customer=customer_unknown,
            user=consultant,
            activity_type='cagri_gelen',
            source_label='Sanal Santral',
            description='Gelen Arama: 05073945262',
        )
        CustomerActivity.objects.create(
            customer=customer_unknown,
            user=consultant,
            activity_type='teklif_olusturuldu',
            source_label='Manuel',
            description='Yeni teklif oluşturuldu: 3.300.000 TRY',
        )

        self.stdout.write(self.style.SUCCESS("\n🎉 Seed data başarıyla oluşturuldu!"))
        self.stdout.write(f"\n📋 Detay sayfalarına gitmek için:")
        self.stdout.write(f"   http://localhost:8000/musteriler/{customer_unknown.pk}/")
        self.stdout.write(f"   http://localhost:8000/musteriler/{customer_full.pk}/")
