"""
Fake çağrı eklemek için script.
Kullanım: python add_fake_call.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

import uuid
from django.utils import timezone
from datetime import timedelta
from apps.calls.models import CallLog
from apps.customers.models import Customer

# Kayıtlı bir müşteriyi bul (varsa eşleştir)
musteri = Customer.objects.first()

cagri = CallLog.objects.create(
    call_id=str(uuid.uuid4()),
    direction='inbound',
    caller=musteri.phone if musteri else '05441112233',
    called='08508850860',
    start_time=timezone.now() - timedelta(hours=1),
    end_time=timezone.now() - timedelta(hours=1) + timedelta(seconds=125),
    duration=125,
    status='completed',
    recording_url='https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
    customer=musteri,
)

print(f"✅ Fake çağrı eklendi!")
print(f"   ID     : {cagri.call_id}")
print(f"   Arayan : {cagri.caller}")
print(f"   Müşteri: {musteri.display_name if musteri else '(eşleşmedi)'}")
print(f"   Kayıt  : {cagri.recording_url}")
