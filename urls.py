# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Ana URL Yapılandırması
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import json
from datetime import datetime


# NetGSM Click-to-Call Fonksiyonu
@csrf_exempt
def click_to_call(request, phone):
    """NetGSM Çağrı Bağlama - Giriş yapan personelin numarasını kullanır"""
    
    # Giriş kontrolü
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Giriş yapmanız gerekiyor'}, status=401)
    
    # Personelin telefon numarasını al
    personel_phone = request.user.phone_number
    
    if not personel_phone:
        return JsonResponse({
            'error': 'Telefon numaranız kayıtlı değil.',
            'help': 'Lütfen yöneticinizle iletişime geçin ve profilinize telefon numarası ekletin.'
        }, status=400)
    
    # NetGSM bilgileri
    username = "8508850860"
    password = settings.NETGSM_PASSWORD.strip()
    
    # Numaraları temizle ve formatla
    personel_phone = ''.join(filter(str.isdigit, personel_phone))
    if not personel_phone.startswith('0'):
        personel_phone = '0' + personel_phone
    
    customer_phone = ''.join(filter(str.isdigit, phone))
    if not customer_phone.startswith('0'):
        customer_phone = '0' + customer_phone
    
    # API parametreleri
    params = {
        'username': username,
        'password': password,
        'caller': personel_phone,      # Personelin numarası
        'called': customer_phone,      # Müşteri numarası
        'ring_timeout': '20',
        'crm_id': f'crm_{request.user.id}_{int(datetime.now().timestamp())}',
        'wait_response': '1',
        'originate_order': 'if',       # Önce personel aranır
        'trunk': username,
    }
    
    url = f'https://crmsntrl.netgsm.com.tr/{username}/linkup'
    
    print(f"📞 {request.user.get_full_name()} ({personel_phone}) → Müşteri ({customer_phone})")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"📡 Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'Success':
                # Çağrı kaydı oluştur
                try:
                    from calls.models import CallLog
                    from apps.customers.models import Customer
                    from django.utils import timezone as tz
                    
                    # Müşteriyi bul
                    customer = Customer.objects.filter(phone=customer_phone).first()
                    
                    # CallLog oluştur
                    CallLog.objects.create(
                        call_id=data.get('unique_id', params['crm_id']),
                        customer=customer,
                        user=request.user,
                        direction='outbound',
                        caller=personel_phone,
                        called=customer_phone,
                        start_time=tz.now(),
                        status='ringing',
                    )
                    print(f"✅ Çağrı kaydı oluşturuldu")
                except Exception as e:
                    print(f"⚠️ Çağrı kaydı oluşturulamadı: {e}")
                
                return JsonResponse({
                    'success': True,
                    'message': f'✅ Çağrı başlatıldı! {personel_phone} numaranız çalacak...',
                    'unique_id': data.get('unique_id'),
                    'caller': personel_phone,
                    'called': customer_phone
                })
            else:
                return JsonResponse({
                    'error': data.get('message', 'Çağrı başlatılamadı')
                }, status=400)
        else:
            return JsonResponse({'error': response.text}, status=400)
    except Exception as e:
        print(f"❌ Hata: {e}")
        return JsonResponse({'error': str(e)}, status=500)


# NetGSM Webhook Fonksiyonu
@csrf_exempt
def netgsm_webhook(request):
    """NetGSM Webhook - Çağrı kayıtlarını otomatik kaydeder"""
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Sadece POST metodu destekleniyor'}, status=405)
    
    try:
        # Import'ları fonksiyon içinde yap
        from apps.calls.models import CallLog
        from apps.customers.models import Customer
        from django.utils import timezone as tz
        
        # JSON parse
        data = json.loads(request.body.decode('utf-8'))
        
        print(f"📥 Webhook alındı: {data}")
        
        # Webhook verilerini çek
        unique_id = data.get('unique_id', '')
        pbx_num = data.get('pbx_num', '')
        internal_num = data.get('internal_num', '')
        customer_num = data.get('customer_num', '')
        incoming_number = data.get('incoming_number', '')
        scenario = data.get('scenario', '')
        talktime = data.get('talktime', '0')
        timestamp = data.get('timestamp', '')
        
        if not unique_id:
            return JsonResponse({'error': 'unique_id eksik'}, status=400)
        
        # Yönü belirle
        if 'Inbound' in scenario or 'incoming' in scenario.lower():
            direction = 'inbound'
            caller = customer_num or incoming_number
            called = pbx_num
        elif 'Outbound' in scenario or 'outgoing' in scenario.lower():
            direction = 'outbound'
            caller = pbx_num
            called = customer_num
        else:
            direction = 'internal'
            caller = internal_num
            called = customer_num or pbx_num
        
        # Timestamp'i datetime'a çevir
        if timestamp:
            try:
                start_time = tz.make_aware(datetime.fromtimestamp(int(timestamp) / 1000))
            except:
                start_time = tz.now()
        else:
            start_time = tz.now()
        
        # Süre
        try:
            duration = int(talktime) if talktime else 0
        except:
            duration = 0
        
        # Müşteri eşleştir
        phone = caller if direction == 'inbound' else called
        if phone and phone.startswith('0'):
            phone = '+90' + phone[1:]
        
        customer = None
        if phone:
            customer = Customer.objects.filter(phone=phone).first()
        
        # Durum
        if 'Hangup' in scenario:
            status = 'completed' if duration > 0 else 'missed'
        elif 'Answer' in scenario:
            status = 'answered'
        else:
            status = 'ringing'
        
        # Veritabanına kaydet
        obj, created = CallLog.objects.update_or_create(
            call_id=unique_id,
            defaults={
                'customer': customer,
                'direction': direction,
                'caller': caller,
                'called': called,
                'extension': internal_num,
                'start_time': start_time,
                'duration': duration,
                'status': status,
            }
        )
        
        action = "Yeni kayıt" if created else "Güncellendi"
        print(f"✅ {action}: {unique_id} | {scenario} | {caller} → {called}")
        
        return JsonResponse({'status': 'success', 'action': action})
        
    except Exception as e:
        print(f"❌ Webhook hatası: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


# URL Patterns
urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # NetGSM API
    path('api/calls/click/<str:phone>/', click_to_call, name='click_to_call'),
    path('api/calls/webhook/', netgsm_webhook, name='netgsm_webhook'),
    
    # REST API'ler
    path('api/', include('apps.api.urls')),
    path('api/careers/', include('apps.careers.urls')),
    path('api/contact/', include(('apps.contact.urls', 'contact'), namespace='contact-api')),
    
    # Uygulama URL'leri
    path("", include("apps.authentication.urls")),
    path("", include("apps.customers.urls")),
    path("", include("apps.portfolio.urls")),
    path("", include("apps.employees.urls")),
    path("", include("apps.presentation.urls")),
    path("fsbo/", include("apps.fsbo.urls")),
    path("", include("apps.calendar.urls")),
    path("", include("apps.home.urls")),
    path("genel-bakis/", include("apps.home.urls")),
    path("contact/", include(('apps.contact.urls', 'contact'), namespace='contact-views')),
    path("careers/", include(('apps.careers.urls', 'careers'), namespace='careers-views')),
    path("team/", include(('apps.team.urls', 'team'), namespace='team')),
    path("satis-surec/", include(('apps.sales_process.urls', 'sales_process'), namespace='sales_process')),
    path("", include("apps.calls.urls")),
]

# Media dosyalarını development'ta servis et
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)