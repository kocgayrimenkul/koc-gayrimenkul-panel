from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.calls.models import CallLog
from apps.customers.models import Customer
import random
import uuid
from datetime import timedelta


class Command(BaseCommand):
    help = 'Test amaçlı sahte çağrı kayıtları oluşturur'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=15, help='Oluşturulacak çağrı sayısı (default: 15)')
        parser.add_argument('--clear', action='store_true', help='Önce mevcut tüm fake kayıtları sil')

    def handle(self, *args, **options):
        if options['clear']:
            deleted, _ = CallLog.objects.filter(call_id__startswith='FAKE-').delete()
            self.stdout.write(self.style.WARNING(f'{deleted} fake kayıt silindi.'))

        count = options['count']
        customers = list(Customer.objects.all()[:10])

        fake_phones = [
            '05321234567', '05334445566', '05441112233',
            '05559998877', '05067776655', '05124433221',
            '05381122334', '05469988776', '05512233445',
            '05623344556', '05734455667', '05845566778',
        ]

        statuses = [
            ('missed', 0),
            ('missed', 0),
            ('completed', 45),
            ('completed', 120),
            ('completed', 300),
            ('completed', 75),
            ('answered', 15),
        ]

        created = 0
        now = timezone.now()

        for i in range(count):
            call_id = f'FAKE-{uuid.uuid4().hex[:12].upper()}'
            direction = random.choice(['inbound', 'inbound', 'inbound', 'outbound'])
            status_tuple = random.choice(statuses)
            status, duration = status_tuple

            # Son 7 gün içinde rastgele bir zaman
            minutes_ago = random.randint(5, 60 * 24 * 7)
            start_time = now - timedelta(minutes=minutes_ago)

            phone = random.choice(fake_phones)
            customer = random.choice(customers) if customers and random.random() > 0.4 else None

            if direction == 'inbound':
                caller = phone
                called = '08508850860'
            else:
                caller = '08508850860'
                called = phone

            # Eğer müşteri varsa telefonu kullan
            if customer:
                if direction == 'inbound':
                    caller = customer.phone or phone
                else:
                    called = customer.phone or phone

            recording_url = ''
            if status == 'completed' and duration > 60 and random.random() > 0.5:
                recording_url = f'https://ses.netgsm.com.tr/recordings/{call_id}.mp3'

            CallLog.objects.create(
                call_id=call_id,
                customer=customer,
                direction=direction,
                caller=caller,
                called=called,
                extension=str(random.randint(100, 199)) if direction == 'inbound' else '',
                start_time=start_time,
                duration=duration,
                status=status,
                recording_url=recording_url,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f'✓ {created} adet fake çağrı kaydı oluşturuldu. '
            f'Silmek için: python manage.py create_fake_calls --clear'
        ))
