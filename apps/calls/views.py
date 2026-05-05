from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
import json
import datetime
import tempfile
import os
import threading
import requests as http_requests


def _auto_summarize_in_background(call_id):
    """Çağrı bittikten sonra webhook'tan tetiklenen otomatik AI özetleme (arka plan thread'i)."""
    try:
        from .models import CallLog
        from apps.customers.models import CustomerNote
        from django.conf import settings

        call = CallLog.objects.select_related('customer').get(pk=call_id)
        if not call.recording_url or not call.customer:
            return

        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if not api_key or api_key == 'buraya_openai_api_keyinizi_yazin':
            return

        # Ses dosyasını indir
        audio_response = http_requests.get(call.recording_url, timeout=60)
        audio_response.raise_for_status()

        ext = '.mp3'
        url_lower = call.recording_url.lower()
        if '.wav' in url_lower:
            ext = '.wav'
        elif '.ogg' in url_lower:
            ext = '.ogg'
        elif '.m4a' in url_lower:
            ext = '.m4a'

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(audio_response.content)
            tmp_path = tmp.name

        # Whisper ile metne çevir
        with open(tmp_path, 'rb') as audio_file:
            whisper_response = http_requests.post(
                'https://api.openai.com/v1/audio/transcriptions',
                headers={'Authorization': f'Bearer {api_key}'},
                files={'file': (os.path.basename(tmp_path), audio_file, 'audio/mpeg')},
                data={'model': 'whisper-1', 'language': 'tr'},
                timeout=120,
            )
        os.unlink(tmp_path)

        if whisper_response.status_code != 200:
            return

        transcript = whisper_response.json().get('text', '').strip()
        if not transcript:
            return

        # GPT-4o-mini ile özetle
        call_date = call.start_time.strftime('%d.%m.%Y %H:%M') if call.start_time else '—'
        direction = call.get_direction_display()
        duration = call.duration_formatted() if callable(call.duration_formatted) else call.duration_formatted

        gpt_prompt = f"""Aşağıda bir emlak danışmanlığı şirketine ait telefon görüşmesinin transkripti var.
Çağrı bilgileri: {direction} çağrı, tarih: {call_date}, süre: {duration}

Transkript:
{transcript}

Lütfen bu görüşmeyi CRM notuna uygun şekilde Türkçe özetle:
- Müşteri ne hakkında aradı?
- Hangi mülk/daire ile ilgilendi?
- Müşterinin talep veya şikayeti neydi?
- Sonraki adım ne olmalı?
Kısa ve net yaz, 4-6 cümle yeterli."""

        gpt_response = http_requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'gpt-4o-mini',
                'messages': [{'role': 'user', 'content': gpt_prompt}],
                'max_tokens': 300,
                'temperature': 0.4,
            },
            timeout=60,
        )

        if gpt_response.status_code != 200:
            return

        summary = gpt_response.json()['choices'][0]['message']['content'].strip()
        note_content = f"📞 AI Çağrı Özeti (Otomatik) — {call_date}\n\n{summary}"

        CustomerNote.objects.create(
            customer=call.customer,
            user=None,
            content=note_content,
            note_type='yorum',
            priority='normal',
        )
    except Exception:
        pass  # Arka plan hatalarını sessizce geç


def ai_summarize_call(request, call_id):
    """Çağrı kaydını Whisper ile metne çevir, GPT ile özetle, müşteri notuna kaydet."""
    from .models import CallLog
    from apps.customers.models import CustomerNote
    from django.conf import settings

    call = get_object_or_404(CallLog, pk=call_id)

    if not call.recording_url:
        return JsonResponse({'success': False, 'error': 'Bu çağrıya ait ses kaydı yok.'}, status=400)

    if not call.customer:
        return JsonResponse({'success': False, 'error': 'Çağrı bir müşteriyle eşleşmemiş.'}, status=400)

    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    if not api_key or api_key == 'buraya_openai_api_keyinizi_yazin':
        return JsonResponse({'success': False, 'error': 'OpenAI API anahtarı ayarlanmamış. .env dosyasına OPENAI_API_KEY ekleyin.'}, status=500)

    try:
        # 1. Ses dosyasını indir
        audio_response = http_requests.get(call.recording_url, timeout=60)
        audio_response.raise_for_status()

        # Uzantıyı URL'den tahmin et
        ext = '.mp3'
        url_lower = call.recording_url.lower()
        if '.wav' in url_lower:
            ext = '.wav'
        elif '.ogg' in url_lower:
            ext = '.ogg'
        elif '.m4a' in url_lower:
            ext = '.m4a'

        # Geçici dosyaya yaz
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(audio_response.content)
            tmp_path = tmp.name

        # 2. Whisper ile metne çevir
        with open(tmp_path, 'rb') as audio_file:
            whisper_response = http_requests.post(
                'https://api.openai.com/v1/audio/transcriptions',
                headers={'Authorization': f'Bearer {api_key}'},
                files={'file': (os.path.basename(tmp_path), audio_file, 'audio/mpeg')},
                data={'model': 'whisper-1', 'language': 'tr'},
                timeout=120,
            )
        os.unlink(tmp_path)  # Geçici dosyayı sil

        if whisper_response.status_code != 200:
            return JsonResponse({'success': False, 'error': f'Whisper hatası: {whisper_response.text}'}, status=500)

        transcript = whisper_response.json().get('text', '').strip()
        if not transcript:
            return JsonResponse({'success': False, 'error': 'Ses dosyasından metin çıkarılamadı.'}, status=400)

        # 3. GPT-4o-mini ile özetle
        call_date = call.start_time.strftime('%d.%m.%Y %H:%M') if call.start_time else '—'
        direction = call.get_direction_display()
        duration = call.duration_formatted() if callable(call.duration_formatted) else call.duration_formatted

        gpt_prompt = f"""Aşağıda bir emlak danışmanlığı şirketine ait telefon görüşmesinin transkripti var.
Çağrı bilgileri: {direction} çağrı, tarih: {call_date}, süre: {duration}

Transkript:
{transcript}

Lütfen bu görüşmeyi CRM notuna uygun şekilde Türkçe özetle:
- Müşteri ne hakkında aradı?
- Hangi mülk/daire ile ilgilendi?
- Müşterinin talep veya şikayeti neydi?
- Sonraki adım ne olmalı?
Kısa ve net yaz, 4-6 cümle yeterli."""

        gpt_response = http_requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'gpt-4o-mini',
                'messages': [{'role': 'user', 'content': gpt_prompt}],
                'max_tokens': 300,
                'temperature': 0.4,
            },
            timeout=60,
        )

        if gpt_response.status_code != 200:
            return JsonResponse({'success': False, 'error': f'GPT hatası: {gpt_response.text}'}, status=500)

        summary = gpt_response.json()['choices'][0]['message']['content'].strip()

        # 4. Müşteri notuna kaydet
        note_content = f"📞 AI Çağrı Özeti — {call_date}\n\n{summary}"
        note = CustomerNote.objects.create(
            customer=call.customer,
            user=request.user if request.user.is_authenticated else None,
            content=note_content,
            note_type='yorum',
            priority='normal',
        )

        return JsonResponse({
            'success': True,
            'summary': summary,
            'note_id': note.id,
            'customer_name': call.customer.display_name,
        })

    except http_requests.exceptions.Timeout:
        return JsonResponse({'success': False, 'error': 'İstek zaman aşımına uğradı. Ses dosyası çok büyük olabilir.'}, status=500)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def netgsm_webhook(request):
    """NetGSM santral webhook endpoint'i"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Sadece POST'}, status=405)

    try:
        raw_body = request.body.decode('utf-8', errors='replace')
        try:
            with open('/tmp/webhook_raw.log', 'a') as f:
                f.write(f"\n=== {datetime.datetime.now()} ===\n{raw_body[:500]}\n")
        except:
            pass

        from .models import CallLog
        from apps.customers.models import Customer

        data = json.loads(raw_body)
        scenario = data.get('scenario', '')

        # CDR - ses kaydı URL'si
        if scenario == 'cdr':
            asterisk_id = data.get('asteriskId', '')
            ses_kaydi = data.get('seskaydi', '')
            arayan = data.get('arayan', '')
            aranan = data.get('aranan', '')
            sure = data.get('sure', 0)
            bas = data.get('bas', '')

            try:
                sure = int(sure)
            except:
                sure = 0

            customer = None
            if arayan:
                clean = ''.join(filter(str.isdigit, str(arayan)))[-10:]
                if len(clean) >= 10:
                    customer = Customer.objects.filter(phone__endswith=clean).first()

            try:
                start_time = timezone.make_aware(
                    datetime.datetime.strptime(bas, '%Y-%m-%d %H:%M:%S')
                )
            except:
                start_time = timezone.now()

            if asterisk_id:
                call_obj, _ = CallLog.objects.update_or_create(
                    call_id=asterisk_id,
                    defaults={
                        'direction': 'inbound',
                        'caller': arayan or '',
                        'called': aranan or '',
                        'status': 'completed' if sure > 0 else 'missed',
                        'duration': sure,
                        'recording_url': ses_kaydi if ses_kaydi else None,
                        'customer': customer,
                        'start_time': start_time,
                    }
                )
                # Çağrı tamamlandıysa ve ses kaydı varsa otomatik AI özeti başlat
                if ses_kaydi and sure > 0 and customer:
                    t = threading.Thread(
                        target=_auto_summarize_in_background,
                        args=(call_obj.id,),
                        daemon=True,
                    )
                    t.start()
            return JsonResponse({'status': 'success', 'action': 'cdr'})

        # Anlık çağrı olayları
        unique_id = data.get('unique_id', '')
        if not unique_id:
            return JsonResponse({'error': 'unique_id eksik'}, status=400)

        scenario_lower = scenario.lower()
        customer_num = data.get('customer_num', '')
        pbx_num = data.get('pbx_num', '')
        internal_num = data.get('internal_num', '')
        incoming_num = data.get('incoming_number', '')
        talktime = data.get('talktime', '0')
        timestamp = data.get('timestamp', '')

        if any(x in scenario_lower for x in ['inbound', 'incoming', 'queue', 'answer', 'hangup', 'context']):
            direction = 'inbound'
            caller = customer_num or incoming_num
            called = pbx_num
        elif any(x in scenario_lower for x in ['outbound', 'outgoing']):
            direction = 'outbound'
            caller = pbx_num
            called = customer_num
        else:
            direction = 'inbound'
            caller = customer_num or incoming_num
            called = pbx_num

        try:
            start_time = timezone.make_aware(
                datetime.datetime.fromtimestamp(int(timestamp) / 1000)
            ) if timestamp else timezone.now()
        except:
            start_time = timezone.now()

        try:
            duration = int(talktime) if talktime else 0
        except:
            duration = 0

        customer = None
        if caller:
            clean = ''.join(filter(str.isdigit, str(caller)))[-10:]
            if len(clean) >= 10:
                customer = Customer.objects.filter(phone__endswith=clean).first()

        if 'hangup' in scenario_lower:
            status = 'completed' if duration > 0 else 'missed'
        elif 'answer' in scenario_lower:
            status = 'answered'
        else:
            status = 'ringing'

        CallLog.objects.update_or_create(
            call_id=unique_id,
            defaults={
                'customer': customer,
                'direction': direction,
                'caller': caller or '',
                'called': called or '',
                'extension': internal_num or '',
                'start_time': start_time,
                'duration': duration,
                'status': status,
            }
        )

        return JsonResponse({'status': 'success'})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


def _kullanici_cagri_gorebilir(user):
    """Yönetici, Santral veya Santral/Sekreter rolündeki kullanıcılar çağrıları görebilir."""
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=['Yönetici', 'Santral', 'Santral/Sekreter']).exists()


@login_required
def call_list(request):
    """Tüm çağrıları listele"""
    if not _kullanici_cagri_gorebilir(request.user):
        messages.warning(request, 'Bu sayfaya erişim yetkiniz bulunmuyor.')
        return redirect('customer_list')

    from .models import CallLog

    query = request.GET.get('q', '').strip()
    direction = request.GET.get('direction', '')
    status = request.GET.get('status', '')
    match = request.GET.get('match', '')

    calls = CallLog.objects.select_related('customer', 'customer__neighborhood').order_by('-start_time')

    if query:
        calls = calls.filter(Q(caller__icontains=query) | Q(called__icontains=query))
    if direction:
        calls = calls.filter(direction=direction)
    if status:
        calls = calls.filter(status=status)
    if match == 'matched':
        calls = calls.filter(customer__isnull=False)
    elif match == 'unmatched':
        calls = calls.filter(customer__isnull=True)

    all_calls = CallLog.objects.all()
    stats = {
        'total': all_calls.count(),
        'completed': all_calls.filter(status='completed').count(),
        'missed': all_calls.filter(status='missed').count(),
        'unmatched': all_calls.filter(customer__isnull=True, direction='inbound').count(),
        'with_recording': all_calls.exclude(recording_url__isnull=True).exclude(recording_url='').count(),
    }

    paginator = Paginator(calls, 50)
    page_num = request.GET.get('page', 1)
    calls_page = paginator.get_page(page_num)

    # Müşteriye dönüştür modalı için: mahalleler ve gayrimenkuller
    from apps.customers.models import Customer, Neighborhood
    from apps.portfolio.models import Property

    neighborhoods = Neighborhood.objects.select_related('consultant').order_by('name')
    properties = Property.objects.filter(is_active=True).select_related('neighborhood').order_by('-created_at')[:300]

    context = {
        'segment': 'cagrilar',
        'calls': calls_page,
        'total_count': paginator.count,
        'stats': stats,
        'query': query,
        'direction': direction,
        'status': status,
        'match': match,
        'neighborhoods': neighborhoods,
        'properties': properties,
        'source_choices': Customer.SOURCE_CHOICES,
        'customer_type_choices': Customer.CUSTOMER_TYPE_CHOICES,
    }
    return render(request, 'calls/call_list.html', context)


@login_required
@require_POST
def convert_call_to_customer(request, call_id):
    """
    Çağrıyı müşteriye dönüştürür:
    - Telefon ve tarih çağrıdan otomatik alınır
    - Mahalle seçilince bağlı danışman otomatik atanır
    - İlgilenilen daire CustomerDemand olarak kaydedilir
    - Kayıt sonrası müşteri detay sayfasına yönlendirilir
    """
    from .models import CallLog
    from apps.customers.models import Customer, Neighborhood, CustomerDemand
    from apps.portfolio.models import Property

    call = get_object_or_404(CallLog, pk=call_id)

    # Çağrıdan telefon numarasını temizle
    raw_phone = call.caller if call.direction == 'inbound' else call.called
    clean_phone = ''.join(filter(str.isdigit, raw_phone or ''))
    if clean_phone.startswith('90') and len(clean_phone) > 10:
        clean_phone = '0' + clean_phone[2:]
    elif not clean_phone.startswith('0') and len(clean_phone) >= 10:
        clean_phone = '0' + clean_phone[-10:]

    # Zaten eşleşmiş mi kontrol et
    if call.customer_id:
        messages.warning(request, 'Bu çağrı zaten bir müşteriye bağlı.')
        return redirect('customer_detail', pk=call.customer_id)

    # Aynı telefon zaten müşteride var mı?
    existing = Customer.objects.filter(phone=clean_phone).first()
    if existing:
        call.customer = existing
        call.save(update_fields=['customer'])
        messages.info(request, f"'{existing.full_name}' adlı mevcut müşteriye bağlandı.")
        return redirect('customer_detail', pk=existing.pk)

    # --- Form verilerini al ---
    full_name     = (request.POST.get('full_name') or '').strip()
    neighborhood_id = request.POST.get('neighborhood_id') or None
    property_id   = request.POST.get('property_id') or None
    reason        = (request.POST.get('reason') or '').strip()
    customer_type = request.POST.get('customer_type', 'bireysel')
    source        = request.POST.get('source') or None

    # Mahalle → danışman otomatik atama
    neighborhood = None
    consultant   = None
    if neighborhood_id:
        neighborhood = Neighborhood.objects.select_related('consultant').filter(pk=neighborhood_id).first()
        if neighborhood:
            consultant = neighborhood.consultant

    # Notlar
    note_lines = [f"Santral çağrısından oluşturuldu ({call.start_time.strftime('%d.%m.%Y %H:%M')})."]
    if reason:
        note_lines.append(f"Arama nedeni: {reason}")

    # Müşteriyi oluştur
    customer = Customer.objects.create(
        full_name=full_name or f"Bilinmiyor - {clean_phone}",
        phone=clean_phone,
        customer_type=customer_type,
        status='potansiyel',
        source=source,
        neighborhood=neighborhood,
        consultant=consultant,
        notes='\n'.join(note_lines),
    )

    # Çağrıyı yeni müşteriye bağla
    call.customer = customer
    call.save(update_fields=['customer'])

    # Seçilen daire varsa CustomerDemand oluştur
    prop = None
    if property_id:
        prop = Property.objects.filter(pk=property_id).first()
        if prop:
            CustomerDemand.objects.create(
                customer=customer,
                property_type=prop.property_type if hasattr(prop, 'property_type') else 'daire',
                transaction_type='satilik',
                preferred_locations=str(prop.neighborhood) if prop.neighborhood else '',
                notes=f"İlgilenilen daire: {prop.apartment_name}" + (f"\nArama nedeni: {reason}" if reason else ''),
                status='aktif',
            )

    # ── Satış Süreci Kanban: "Bilgi Verildi" aşamasına otomatik ekle ──
    kanban_eklendi = False
    try:
        from apps.sales_process.models import SalesStage, Lead as SalesLead

        # staff_kanban'daki gibi sadece name ile sorgula (stage_type filtresi sorun çıkarıyordu)
        bilgi_verildi_stage = SalesStage.objects.filter(
            name='bilgi_verildi'
        ).first()

        if not bilgi_verildi_stage:
            # Fallback: isim içinde 'bilgi' geçen ilk staff aşaması
            bilgi_verildi_stage = SalesStage.objects.filter(
                name__icontains='bilgi'
            ).first()

        if bilgi_verildi_stage:
            lead_source = source or 'netgsm_call'
            # Telefon numarasını normalize et (başında 0 ile 10+1 = 11 hane)
            lead_phone = clean_phone
            if not lead_phone:
                lead_phone = customer.phone or '05000000000'

            # Aynı müşteri için zaten aktif lead var mı kontrol et
            existing_lead = SalesLead.objects.filter(
                customer=customer,
                status='active'
            ).first()

            if not existing_lead:
                SalesLead.objects.create(
                    customer=customer,
                    assigned_staff=consultant,
                    current_stage=bilgi_verildi_stage,
                    customer_name=customer.full_name,
                    customer_phone=lead_phone,
                    source=lead_source,
                    contact_type='bilgi_alma',
                    neighborhood=neighborhood,
                    interested_property=prop,
                    lead_notes='\n'.join(note_lines),
                    status='active',
                )
                kanban_eklendi = True
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Kanban lead oluşturma hatası: {e}")

    # Başarı mesajı
    kanban_mesaj = " Personel kanbanına 'Bilgi Verildi' sütununa eklendi." if kanban_eklendi else ""
    if consultant:
        messages.success(
            request,
            f"Müşteri oluşturuldu ve '{neighborhood.name}' mahallesinin danışmanı "
            f"{consultant.get_full_name() or consultant.username}'a otomatik atandı.{kanban_mesaj}"
        )
    else:
        messages.success(request, f'Müşteri başarıyla oluşturuldu.{kanban_mesaj}')

    return redirect('customer_detail', pk=customer.pk)


@login_required
def properties_by_neighborhood_api(request):
    """Mahalle seçince daireleri filtreleyen AJAX endpoint'i"""
    from apps.portfolio.models import Property
    neighborhood_id = request.GET.get('neighborhood_id')
    qs = Property.objects.filter(is_active=True).select_related('neighborhood')
    if neighborhood_id:
        qs = qs.filter(neighborhood_id=neighborhood_id)
    qs = qs.order_by('apartment_name')[:200]
    data = [
        {
            'id': p.id,
            'name': p.apartment_name or str(p),
            'neighborhood': str(p.neighborhood) if p.neighborhood else '',
            'room_count': p.room_count or '',
            'floor': p.floor or '',
        }
        for p in qs
    ]
    return JsonResponse({'properties': data})


@login_required
def recent_calls_api(request):
    from .models import CallLog
    since = timezone.now() - datetime.timedelta(seconds=60)
    recent = CallLog.objects.filter(
        direction='inbound',
        start_time__gte=since,
        customer__isnull=True,
    ).order_by('-start_time')[:5]

    calls = []
    for c in recent:
        clean_phone = ''.join(filter(str.isdigit, c.caller or ''))
        calls.append({
            'id': c.id,
            'call_id': c.call_id,
            'caller': c.caller,
            'caller_clean': clean_phone,
            'status': c.status,
            'start_time': c.start_time.strftime('%H:%M:%S'),
            'customer_exists': False,
            'convert_url': f"/cagrilar/{c.id}/musteriye-donustur/",
        })
    return JsonResponse({'calls': calls})


@login_required
def unmatched_calls_api(request):
    from .models import CallLog
    unmatched = CallLog.objects.filter(
        customer__isnull=True, direction='inbound'
    ).order_by('-start_time')[:20]
    calls = []
    for c in unmatched:
        clean_phone = ''.join(filter(str.isdigit, c.caller or ''))
        calls.append({
            'id': c.id,
            'call_id': c.call_id,
            'caller': c.caller,
            'caller_clean': clean_phone,
            'status': c.status,
            'start_time': c.start_time.strftime('%d.%m.%Y %H:%M'),
            'duration': c.duration,
            'convert_url': f"/cagrilar/{c.id}/musteriye-donustur/",
        })
    return JsonResponse({'calls': calls})
