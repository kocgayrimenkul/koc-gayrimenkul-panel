# -*- coding: utf-8 -*-
import json
import logging
import hmac
import hashlib
import requests as http_requests

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import IncomingMessage, AutoReplyTemplate

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# AI OTOMATIK YANIT
# ─────────────────────────────────────────────────────────────

def generate_ai_response(message_text: str, platform: str, sender_name: str = '') -> str:
    """OpenAI ile otomatik yanıt üret"""
    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    if not api_key:
        return _fallback_response(message_text, platform)

    system_prompt = """Sen Koç Gayrimenkul'ün sanal asistanısın.
Türkçe, samimi ve profesyonel yanıtlar ver.
Gayrimenkul satış ve kiralama konusunda yardımcı ol.
Müşteri bilgilerini almaya çalış (ad-soyad, telefon, ihtiyaç).
Kısa ve net yanıtlar ver, fazla uzatma.
Müşteriyi danışmanımızla görüştürmek için telefon numarası iste."""

    user_msg = f"Müşteri ({sender_name or 'Bilinmiyor'}) şunu yazdı: {message_text}"

    try:
        resp = http_requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={
                'model': 'gpt-4o-mini',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_msg},
                ],
                'max_tokens': 300,
                'temperature': 0.7,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        logger.error(f"OpenAI API hatası: {e}")

    return _fallback_response(message_text, platform)


def _fallback_response(message_text: str, platform: str) -> str:
    """AI yoksa kural bazlı yanıt"""
    text_lower = message_text.lower()

    # Keyword bazlı şablonlar
    template = AutoReplyTemplate.objects.filter(is_active=True).order_by('-priority').first()
    if template:
        for t in AutoReplyTemplate.objects.filter(is_active=True).order_by('-priority'):
            if not t.keyword or t.keyword.lower() in text_lower:
                return t.response

    # Varsayılan
    keywords = {
        'fiyat': 'Merhaba! Fiyat bilgisi için danışmanımız sizinle iletişime geçecektir. Telefon numaranızı paylaşabilir misiniz?',
        'satılık': 'Satılık gayrimenkullerimiz için sizi danışmanımıza yönlendiriyoruz. İletişim bilgilerinizi alabilir miyiz?',
        'kiralık': 'Kiralık seçeneklerimiz hakkında danışmanımız bilgi verecektir. Telefonunuzu paylaşır mısınız?',
    }
    for kw, resp in keywords.items():
        if kw in text_lower:
            return resp

    return ('Merhaba! Koç Gayrimenkul\'e hoş geldiniz. 🏠\n'
            'Mesajınızı aldık, en kısa sürede danışmanımız sizinle iletişime geçecektir.\n'
            'Hızlı yanıt için telefon numaranızı paylaşabilirsiniz.')


# ─────────────────────────────────────────────────────────────
# META (WhatsApp + Instagram + Facebook) WEBHOOK
# ─────────────────────────────────────────────────────────────

@csrf_exempt
def meta_webhook(request):
    """Meta Webhook — Doğrulama (GET) + Mesaj alma (POST)"""

    if request.method == 'GET':
        # Webhook doğrulama
        mode      = request.GET.get('hub.mode')
        token     = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        verify_token = getattr(settings, 'META_VERIFY_TOKEN', 'koc_gayrimenkul_verify')

        if mode == 'subscribe' and token == verify_token:
            logger.info("Meta webhook doğrulandı")
            return HttpResponse(challenge, content_type='text/plain')
        return HttpResponse('Forbidden', status=403)

    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            logger.info(f"Meta webhook payload: {json.dumps(body)[:500]}")

            object_type = body.get('object', '')

            # WhatsApp
            if object_type == 'whatsapp_business_account':
                _process_whatsapp(body)

            # Instagram
            elif object_type == 'instagram':
                _process_instagram(body)

            # Facebook Messenger
            elif object_type == 'page':
                _process_facebook(body)

            return JsonResponse({'status': 'ok'})

        except Exception as e:
            logger.error(f"Meta webhook hatası: {e}", exc_info=True)
            return JsonResponse({'status': 'error', 'error': str(e)}, status=500)

    return HttpResponse(status=405)


def _process_whatsapp(body: dict):
    for entry in body.get('entry', []):
        for change in entry.get('changes', []):
            value = change.get('value', {})
            messages = value.get('messages', [])
            contacts = {c['wa_id']: c.get('profile', {}).get('name', '') for c in value.get('contacts', [])}

            for msg in messages:
                if msg.get('type') != 'text':
                    continue
                msg_id     = msg['id']
                sender_id  = msg['from']
                sender_name = contacts.get(sender_id, '')
                text       = msg['text']['body']
                phone      = sender_id  # WA numarası telefon numarasıdır

                _save_and_reply(
                    platform='whatsapp',
                    sender_id=sender_id,
                    sender_name=sender_name,
                    sender_phone=phone,
                    message_text=text,
                    meta_message_id=msg_id,
                    raw_data=msg,
                )


def _process_instagram(body: dict):
    for entry in body.get('entry', []):
        for msg_event in entry.get('messaging', []):
            sender_id = msg_event.get('sender', {}).get('id', '')
            message   = msg_event.get('message', {})
            if not message or 'text' not in message:
                continue
            msg_id = message.get('mid', '')
            text   = message['text']

            _save_and_reply(
                platform='instagram',
                sender_id=sender_id,
                sender_name='',
                sender_phone='',
                message_text=text,
                meta_message_id=msg_id,
                raw_data=msg_event,
            )


def _process_facebook(body: dict):
    for entry in body.get('entry', []):
        for msg_event in entry.get('messaging', []):
            sender_id = msg_event.get('sender', {}).get('id', '')
            message   = msg_event.get('message', {})
            if not message or 'text' not in message:
                continue
            msg_id = message.get('mid', '')
            text   = message['text']

            _save_and_reply(
                platform='facebook',
                sender_id=sender_id,
                sender_name='',
                sender_phone='',
                message_text=text,
                meta_message_id=msg_id,
                raw_data=msg_event,
            )


def _save_and_reply(platform, sender_id, sender_name, sender_phone,
                    message_text, meta_message_id, raw_data):
    """Mesajı kaydet, müşteri eşleştir, AI yanıtı gönder"""

    # Duplicate kontrolü
    if meta_message_id and IncomingMessage.objects.filter(meta_message_id=meta_message_id).exists():
        return

    # Müşteri eşleştir (telefon ile)
    customer = None
    if sender_phone:
        from apps.customers.models import Customer
        clean = ''.join(filter(str.isdigit, sender_phone))
        customer = Customer.objects.filter(phone__endswith=clean[-10:]).first()

    # AI yanıtı üret
    ai_resp = generate_ai_response(message_text, platform, sender_name)

    msg = IncomingMessage.objects.create(
        platform=platform,
        sender_id=sender_id,
        sender_name=sender_name,
        sender_phone=sender_phone,
        message_text=message_text,
        ai_response=ai_resp,
        is_ai_replied=bool(ai_resp),
        customer=customer,
        status='replied' if ai_resp else 'new',
        meta_message_id=meta_message_id or None,
        raw_data=raw_data,
    )

    # Yanıtı platforma gönder
    if ai_resp:
        if platform == 'whatsapp':
            _send_whatsapp_reply(sender_id, ai_resp)
        elif platform in ('instagram', 'facebook'):
            _send_meta_reply(sender_id, ai_resp)

    return msg


def _send_whatsapp_reply(to: str, text: str):
    phone_number_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', '')
    access_token    = getattr(settings, 'META_ACCESS_TOKEN', '')
    if not phone_number_id or not access_token:
        return

    try:
        http_requests.post(
            f'https://graph.facebook.com/v18.0/{phone_number_id}/messages',
            headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'},
            json={
                'messaging_product': 'whatsapp',
                'to': to,
                'type': 'text',
                'text': {'body': text},
            },
            timeout=10,
        )
    except Exception as e:
        logger.error(f"WhatsApp gönderim hatası: {e}")


def _send_meta_reply(recipient_id: str, text: str):
    """Instagram / Facebook Messenger yanıtı"""
    access_token = getattr(settings, 'META_ACCESS_TOKEN', '')
    if not access_token:
        return

    try:
        http_requests.post(
            'https://graph.facebook.com/v18.0/me/messages',
            params={'access_token': access_token},
            json={'recipient': {'id': recipient_id}, 'message': {'text': text}},
            timeout=10,
        )
    except Exception as e:
        logger.error(f"Meta Messenger gönderim hatası: {e}")


# ─────────────────────────────────────────────────────────────
# WEB SİTESİ CHAT API
# ─────────────────────────────────────────────────────────────

@csrf_exempt
def website_chat(request):
    """Web sitesi chat widget'ından gelen mesajlar"""
    if request.method == 'OPTIONS':
        resp = HttpResponse()
        resp['Access-Control-Allow-Origin'] = '*'
        resp['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp

    if request.method != 'POST':
        return JsonResponse({'error': 'POST gerekli'}, status=405)

    try:
        body = json.loads(request.body)
        text       = body.get('message', '').strip()
        name       = body.get('name', '').strip()
        phone      = body.get('phone', '').strip()
        session_id = body.get('session_id', '')

        if not text:
            return JsonResponse({'error': 'Mesaj boş olamaz'}, status=400)

        # Müşteri eşleştir
        customer = None
        if phone:
            from apps.customers.models import Customer
            clean = ''.join(filter(str.isdigit, phone))
            customer = Customer.objects.filter(phone__endswith=clean[-10:]).first()

        ai_resp = generate_ai_response(text, 'website', name)

        IncomingMessage.objects.create(
            platform='website',
            sender_id=session_id or f'web_{timezone.now().timestamp()}',
            sender_name=name,
            sender_phone=phone,
            message_text=text,
            ai_response=ai_resp,
            is_ai_replied=bool(ai_resp),
            customer=customer,
            status='replied' if ai_resp else 'new',
            raw_data={'name': name, 'phone': phone, 'session_id': session_id},
        )

        resp = JsonResponse({'reply': ai_resp, 'success': True})
        resp['Access-Control-Allow-Origin'] = '*'
        return resp

    except Exception as e:
        logger.error(f"Website chat hatası: {e}")
        return JsonResponse({'error': str(e)}, status=500)


# ─────────────────────────────────────────────────────────────
# PANEL: Mesaj Listesi + Aksiyonlar
# ─────────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def message_list(request):
    """Tüm gelen mesajları listele"""
    platform = request.GET.get('platform', '')
    status   = request.GET.get('status', '')
    q        = request.GET.get('q', '')

    msgs = IncomingMessage.objects.select_related('customer', 'assigned_to').all()

    if platform:
        msgs = msgs.filter(platform=platform)
    if status:
        msgs = msgs.filter(status=status)
    if q:
        msgs = msgs.filter(message_text__icontains=q) | msgs.filter(sender_name__icontains=q) | msgs.filter(sender_phone__icontains=q)

    stats = {
        'total':     IncomingMessage.objects.count(),
        'new':       IncomingMessage.objects.filter(status='new').count(),
        'whatsapp':  IncomingMessage.objects.filter(platform='whatsapp').count(),
        'instagram': IncomingMessage.objects.filter(platform='instagram').count(),
        'facebook':  IncomingMessage.objects.filter(platform='facebook').count(),
        'website':   IncomingMessage.objects.filter(platform='website').count(),
    }

    return render(request, 'messaging/message_list.html', {
        'messages_list': msgs[:200],
        'stats': stats,
        'platform': platform,
        'status': status,
        'q': q,
    })


@login_required(login_url='/login/')
@require_POST
def convert_message_to_customer(request, msg_id):
    """Mesajı müşteriye dönüştür"""
    msg = get_object_or_404(IncomingMessage, pk=msg_id)
    from apps.customers.models import Customer
    from django.db.models import Q as DQ

    # Zaten müşteri varsa sadece bağla
    if msg.customer:
        msg.status = 'converted'
        msg.save(update_fields=['status'])
        return JsonResponse({'success': True, 'customer_id': msg.customer.id,
                             'customer_name': msg.customer.get_full_name()})

    # Yeni müşteri oluştur
    name_parts = (msg.sender_name or 'Bilinmiyor').split()
    first_name = name_parts[0] if name_parts else 'Bilinmiyor'
    last_name  = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

    customer = Customer.objects.create(
        first_name=first_name,
        last_name=last_name,
        phone=msg.sender_phone or '',
        notes=f"[{msg.get_platform_display()}] {msg.message_text[:300]}",
    )

    msg.customer = customer
    msg.status   = 'converted'
    msg.save(update_fields=['customer', 'status'])

    return JsonResponse({'success': True, 'customer_id': customer.id,
                         'customer_name': customer.get_full_name(),
                         'is_new': True})


@login_required(login_url='/login/')
@require_POST
def send_manual_reply(request, msg_id):
    """Panelden manuel yanıt gönder"""
    msg  = get_object_or_404(IncomingMessage, pk=msg_id)
    body = json.loads(request.body)
    text = body.get('text', '').strip()

    if not text:
        return JsonResponse({'error': 'Yanıt metni boş'}, status=400)

    if msg.platform == 'whatsapp':
        _send_whatsapp_reply(msg.sender_id, text)
    elif msg.platform in ('instagram', 'facebook'):
        _send_meta_reply(msg.sender_id, text)

    msg.ai_response = text
    msg.status = 'replied'
    msg.save(update_fields=['ai_response', 'status'])

    return JsonResponse({'success': True})


@csrf_exempt
def website_chat_widget(request):
    """Web sitesine eklenecek chat widget JavaScript dosyası"""
    panel_url = getattr(settings, 'PANEL_URL', 'https://panelkocgayrimenkul.com')
    js = f"""
(function() {{
  var PANEL_URL = '{panel_url}';
  var sessionId = Math.random().toString(36).substr(2, 9);

  // Widget HTML
  var style = document.createElement('style');
  style.innerHTML = `
    #koc-chat-btn {{
      position: fixed; bottom: 24px; right: 24px; z-index: 9999;
      width: 60px; height: 60px; border-radius: 50%;
      background: linear-gradient(135deg, #9d2235, #c0392b);
      color: white; border: none; cursor: pointer;
      box-shadow: 0 4px 20px rgba(157,34,53,0.4);
      font-size: 24px; display: flex; align-items: center; justify-content: center;
      transition: transform .2s;
    }}
    #koc-chat-btn:hover {{ transform: scale(1.1); }}
    #koc-chat-box {{
      position: fixed; bottom: 100px; right: 24px; z-index: 9999;
      width: 340px; background: white; border-radius: 16px;
      box-shadow: 0 8px 40px rgba(0,0,0,.15); overflow: hidden;
      display: none; flex-direction: column; font-family: sans-serif;
    }}
    #koc-chat-header {{
      background: linear-gradient(135deg, #9d2235, #c0392b);
      color: white; padding: 14px 16px; font-weight: bold; font-size: 14px;
    }}
    #koc-chat-messages {{
      height: 260px; overflow-y: auto; padding: 12px;
      display: flex; flex-direction: column; gap: 8px; background: #f8fafc;
    }}
    .koc-msg {{ max-width: 80%; padding: 8px 12px; border-radius: 12px; font-size: 13px; line-height: 1.4; }}
    .koc-msg.bot {{ background: #e2e8f0; color: #1e293b; align-self: flex-start; border-bottom-left-radius: 4px; }}
    .koc-msg.user {{ background: #9d2235; color: white; align-self: flex-end; border-bottom-right-radius: 4px; }}
    #koc-chat-form {{ display: flex; gap: 8px; padding: 10px; border-top: 1px solid #e2e8f0; background: white; }}
    #koc-chat-input {{
      flex: 1; border: 1px solid #e2e8f0; border-radius: 20px;
      padding: 8px 14px; font-size: 13px; outline: none;
    }}
    #koc-chat-send {{
      background: #9d2235; color: white; border: none; border-radius: 20px;
      padding: 8px 14px; cursor: pointer; font-size: 13px; font-weight: bold;
    }}
  `;
  document.head.appendChild(style);

  document.body.insertAdjacentHTML('beforeend', `
    <button id="koc-chat-btn" title="Bizimle sohbet edin">💬</button>
    <div id="koc-chat-box">
      <div id="koc-chat-header">🏠 Koç Gayrimenkul - Canlı Destek</div>
      <div id="koc-chat-messages">
        <div class="koc-msg bot">Merhaba! Size nasıl yardımcı olabilirim? 😊</div>
      </div>
      <div id="koc-chat-form">
        <input id="koc-chat-input" type="text" placeholder="Mesajınızı yazın...">
        <button id="koc-chat-send">Gönder</button>
      </div>
    </div>
  `);

  var btn = document.getElementById('koc-chat-btn');
  var box = document.getElementById('koc-chat-box');
  var input = document.getElementById('koc-chat-input');
  var msgs = document.getElementById('koc-chat-messages');
  var send = document.getElementById('koc-chat-send');

  btn.addEventListener('click', function() {{
    box.style.display = box.style.display === 'flex' ? 'none' : 'flex';
    if (box.style.display === 'flex') input.focus();
  }});

  function addMsg(text, cls) {{
    var div = document.createElement('div');
    div.className = 'koc-msg ' + cls;
    div.textContent = text;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
  }}

  function sendMsg() {{
    var text = input.value.trim();
    if (!text) return;
    addMsg(text, 'user');
    input.value = '';
    send.disabled = true;

    fetch(PANEL_URL + '/api/chat/website/', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{message: text, session_id: sessionId}})
    }})
    .then(function(r) {{ return r.json(); }})
    .then(function(d) {{
      addMsg(d.reply || 'Mesajınız alındı, en kısa sürede dönüş yapılacaktır.', 'bot');
    }})
    .catch(function() {{
      addMsg('Bağlantı hatası oluştu, lütfen tekrar deneyin.', 'bot');
    }})
    .finally(function() {{ send.disabled = false; }});
  }}

  send.addEventListener('click', sendMsg);
  input.addEventListener('keypress', function(e) {{ if (e.key === 'Enter') sendMsg(); }});
}})();
""".strip()
    return HttpResponse(js, content_type='application/javascript')
