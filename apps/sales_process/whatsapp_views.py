# -*- encoding: utf-8 -*-
"""
WhatsApp Business Cloud API Webhook Views
Satış süreç yönetimi için WhatsApp webhook işlemleri
"""

import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string

from .whatsapp_service import whatsapp_service
from .models import Lead, WhatsAppMessage, SalesStage, StageTransition, ActionLog
from .forms import WhatsAppMessageForm
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import uuid

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def whatsapp_webhook(request):
    """
    WhatsApp Business Cloud API Webhook endpoint
    """
    if request.method == "GET":
        # Webhook verification
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        verify_token = getattr(settings, 'WHATSAPP_VERIFY_TOKEN', '')
        
        if mode == 'subscribe' and token == verify_token:
            logger.info("WhatsApp webhook verified successfully")
            return HttpResponse(challenge)
        else:
            logger.warning(f"WhatsApp webhook verification failed. Mode: {mode}, Token: {token}")
            return HttpResponse("Verification failed", status=403)
    
    elif request.method == "POST":
        try:
            # Webhook data processing
            webhook_data = json.loads(request.body)
            logger.info(f"WhatsApp webhook received: {webhook_data}")
            
            result = whatsapp_service.process_webhook(webhook_data)
            
            if result['success']:
                return JsonResponse({'status': 'success'})
            else:
                logger.error(f"Webhook processing failed: {result['error']}")
                return JsonResponse({'status': 'error', 'message': result['error']}, status=400)
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook request")
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def send_whatsapp_message(request, lead_id):
    """
    Lead'e WhatsApp mesajı gönderme
    """
    lead = get_object_or_404(Lead, lead_id=lead_id)
    
    if request.method == 'POST':
        form = WhatsAppMessageForm(request.POST)
        if form.is_valid():
            message_text = form.cleaned_data['message']
            message_type = form.cleaned_data.get('message_type', 'text')
            
            try:
                if message_type == 'text':
                    result = whatsapp_service.send_text_message(
                        to_phone=lead.customer_phone,
                        message_text=message_text,
                        lead_id=lead.id
                    )
                elif message_type == 'template':
                    template_name = form.cleaned_data.get('template_name')
                    template_params = form.cleaned_data.get('template_params', [])
                    
                    # Eğer 'offer_sent' şablonu seçildiyse, özel offer mesajı gönder
                    if template_name == 'offer_sent':
                        result = whatsapp_service.send_offer_message(
                            to_phone=lead.customer_phone,
                            offer_content=f"Merhaba {lead.customer_name}, size özel hazırladığımız teklifi WhatsApp üzerinden gönderiyoruz. İncelemenizi bekliyoruz.",
                            lead_id=lead.id
                        )
                    else:
                        result = whatsapp_service.send_template_message(
                            to_phone=lead.customer_phone,
                            template_name=template_name,
                            template_params=template_params,
                            lead_id=lead.id
                        )
                
                if result['success']:
                    messages.success(request, 'WhatsApp mesajı başarıyla gönderildi!')
                    
                    # AJAX response
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'message': 'Mesaj gönderildi',
                            'message_id': result.get('message_id')
                        })
                    
                    # Normal form submission - redirect to staff kanban
                    from django.shortcuts import redirect
                    return redirect('sales_process:staff_kanban')
                else:
                    messages.error(request, f'Mesaj gönderilemedi: {result["error"]}')
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': result['error']
                        })
                        
            except Exception as e:
                logger.error(f"WhatsApp message send error: {str(e)}")
                messages.error(request, f'Bir hata oluştu: {str(e)}')
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
                
                # Normal form submission - redirect back to form
                from django.shortcuts import redirect
                return redirect('sales_process:send_whatsapp_message', lead_id=lead.lead_id)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Form geçersiz',
                    'form_errors': form.errors
                })
            
            # Normal form submission - form errors will be displayed on the same page
            # No redirect needed here, just continue to render the form with errors
    else:
        form = WhatsAppMessageForm()
    
    context = {
        'form': form,
        'lead': lead,
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('sales_process/whatsapp_message_form.html', context, request)
        return JsonResponse({'html': html})
    
    return render(request, 'sales_process/send_whatsapp_message.html', context)


@login_required
def whatsapp_message_history(request, lead_id):
    """
    Lead'in WhatsApp mesaj geçmişini gösterir
    """
    lead = get_object_or_404(Lead, lead_id=lead_id)
    
    # Mesaj geçmişini al
    messages_data = whatsapp_service.get_message_history(lead_id, limit=100)
    
    context = {
        'lead': lead,
        'messages': messages_data,
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('sales_process/whatsapp_message_history.html', context, request)
        return JsonResponse({'html': html})
    
    return render(request, 'sales_process/whatsapp_message_history.html', context)


@login_required
def send_template_message(request, lead_id):
    """
    Template mesajı gönderme
    """
    lead = get_object_or_404(Lead, lead_id=lead_id)
    
    if request.method == 'POST':
        template_name = request.POST.get('template_name')
        
        try:
            # Önceden tanımlanmış template'leri kullan
            from .whatsapp_service import WhatsAppTemplates
            
            if template_name == 'welcome':
                message_text = WhatsAppTemplates.welcome_message(lead.customer_name)
            elif template_name == 'appointment_reminder':
                # Son randevuyu al
                last_appointment = lead.appointments.filter(
                    status__in=['scheduled', 'confirmed']
                ).order_by('scheduled_date').first()
                
                if last_appointment:
                    message_text = WhatsAppTemplates.appointment_reminder(
                        lead.customer_name,
                        last_appointment.scheduled_date.strftime('%d.%m.%Y %H:%M'),
                        last_appointment.location or 'Ofisimiz'
                    )
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Randevu bulunamadı'
                    })
            elif template_name == 'offer_sent':
                message_text = WhatsAppTemplates.offer_sent(lead.customer_name)
            elif template_name == 'contract_ready':
                message_text = WhatsAppTemplates.contract_ready(lead.customer_name)
            elif template_name == 'satisfaction_survey':
                message_text = WhatsAppTemplates.satisfaction_survey(lead.customer_name)
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Geçersiz template'
                })
            
            # Mesajı gönder
            result = whatsapp_service.send_text_message(
                to_phone=lead.customer_phone,
                message_text=message_text,
                lead_id=lead.id
            )
            
            if result['success']:
                return JsonResponse({
                    'success': True,
                    'message': 'Template mesajı gönderildi',
                    'message_id': result.get('message_id')
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result['error']
                })
                
        except Exception as e:
            logger.error(f"Template message send error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    # Template seçeneklerini göster
    templates = [
        {'name': 'welcome', 'title': 'Hoş Geldin Mesajı'},
        {'name': 'appointment_reminder', 'title': 'Randevu Hatırlatması'},
        {'name': 'offer_sent', 'title': 'Teklif Gönderildi'},
        {'name': 'contract_ready', 'title': 'Sözleşme Hazır'},
        {'name': 'satisfaction_survey', 'title': 'Memnuniyet Anketi'},
    ]
    
    context = {
        'lead': lead,
        'templates': templates,
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('sales_process/whatsapp_template_selection.html', context, request)
        return JsonResponse({'html': html})
    
    return render(request, 'sales_process/whatsapp_template_selection.html', context)


@login_required
def whatsapp_statistics(request):
    """
    WhatsApp mesajlaşma istatistikleri
    """
    from django.db.models import Count, Q
    from datetime import datetime, timedelta
    
    # Son 30 günün istatistikleri
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    stats = {
        'total_messages': WhatsAppMessage.objects.count(),
        'sent_messages': WhatsAppMessage.objects.filter(direction='outbound').count(),
        'received_messages': WhatsAppMessage.objects.filter(direction='inbound').count(),
        'delivered_messages': WhatsAppMessage.objects.filter(status='delivered').count(),
        'read_messages': WhatsAppMessage.objects.filter(status='read').count(),
        'failed_messages': WhatsAppMessage.objects.filter(status='failed').count(),
        
        # Son 30 gün
        'monthly_sent': WhatsAppMessage.objects.filter(
            direction='outbound',
            created_at__gte=thirty_days_ago
        ).count(),
        'monthly_received': WhatsAppMessage.objects.filter(
            direction='inbound',
            created_at__gte=thirty_days_ago
        ).count(),
        
        # Mesaj tiplerinin dağılımı
        'message_types': WhatsAppMessage.objects.values('message_type').annotate(
            count=Count('id')
        ).order_by('-count'),
        
        # En aktif lead'ler
        'active_leads': WhatsAppMessage.objects.filter(
            lead__isnull=False
        ).values(
            'lead__customer_name',
            'lead__id'
        ).annotate(
            message_count=Count('id')
        ).order_by('-message_count')[:10]
    }
    
    context = {
        'stats': stats,
    }
    
    return render(request, 'sales_process/whatsapp_statistics.html', context)


@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppWebhookView(View):
    """
    Class-based WhatsApp webhook view
    """
    
    def get(self, request):
        """Webhook verification"""
        return whatsapp_webhook(request)
    
    def post(self, request):
        """Webhook data processing"""
        return whatsapp_webhook(request)


@login_required
def bulk_whatsapp_send(request):
    """
    Toplu WhatsApp mesajı gönderme
    """
    if request.method == 'POST':
        lead_ids = request.POST.getlist('lead_ids')
        message_text = request.POST.get('message_text')
        template_name = request.POST.get('template_name')
        
        if not lead_ids:
            return JsonResponse({
                'success': False,
                'error': 'Lead seçilmedi'
            })
        
        if not message_text and not template_name:
            return JsonResponse({
                'success': False,
                'error': 'Mesaj metni veya template seçilmedi'
            })
        
        leads = Lead.objects.filter(id__in=lead_ids)
        success_count = 0
        error_count = 0
        errors = []
        
        for lead in leads:
            try:
                if template_name:
                    # Template mesajı gönder
                    from .whatsapp_service import WhatsAppTemplates
                    
                    if template_name == 'welcome':
                        text = WhatsAppTemplates.welcome_message(lead.customer_name)
                    elif template_name == 'offer_sent':
                        text = WhatsAppTemplates.offer_sent(lead.customer_name)
                    else:
                        text = message_text
                else:
                    text = message_text
                
                result = whatsapp_service.send_text_message(
                    to_phone=lead.customer_phone,
                    message_text=text,
                    lead_id=lead.id
                )
                
                if result['success']:
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(f"{lead.customer_name}: {result['error']}")
                    
            except Exception as e:
                error_count += 1
                errors.append(f"{lead.customer_name}: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors[:10]  # İlk 10 hatayı göster
        })
    
    # GET request - form göster
    leads = Lead.objects.filter(status='active').select_related('current_stage')
    
    context = {
        'leads': leads,
    }
    
    return render(request, 'sales_process/bulk_whatsapp_send.html', context)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def send_offer(request, lead_id):
    """
    Kapsamlı teklif gönderme API endpoint'i
    POST /actions/offer_sent
    
    Payload: {
        'text': 'Mesaj metni (opsiyonel)',
        'images': [MultipartFile objects],
        'links': ['link1', 'link2'],
        'price': 'Fiyat bilgisi (opsiyonel)'
    }
    """
    try:
        lead = get_object_or_404(Lead, lead_id=lead_id)
        
        # Form verilerini al
        offer_text = request.POST.get('text', '').strip()
        offer_price = request.POST.get('price', '').strip()
        
        # Linkleri al (birden fazla link olabilir)
        links = []
        link_count = 1
        while f'link_{link_count}' in request.POST:
            link = request.POST.get(f'link_{link_count}', '').strip()
            if link:
                links.append(link)
            link_count += 1
        
        # Tek link alanı da kontrol et (geriye uyumluluk)
        single_link = request.POST.get('links', '').strip()
        if single_link:
            links.append(single_link)
        
        # Resimleri işle
        images = []
        uploaded_files = request.FILES.getlist('images')
        
        for uploaded_file in uploaded_files:
            try:
                # Dosya adını güvenli hale getir
                file_extension = os.path.splitext(uploaded_file.name)[1]
                safe_filename = f"offer_{uuid.uuid4().hex}{file_extension}"
                
                # Dosyayı kaydet
                file_path = f"whatsapp_offers/{safe_filename}"
                saved_path = default_storage.save(file_path, ContentFile(uploaded_file.read()))
                
                # URL oluştur
                file_url = request.build_absolute_uri(default_storage.url(saved_path))
                
                images.append({
                    'url': file_url,
                    'caption': f"Teklif - {lead.customer_name}"
                })
                
            except Exception as e:
                logger.error(f"Image upload error: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'error': f'Resim yükleme hatası: {str(e)}'
                })
        
        # Offer data hazırla
        offer_data = {}
        if offer_text:
            offer_data['text'] = offer_text
        if offer_price:
            offer_data['price'] = offer_price
        if links:
            offer_data['links'] = links
        if images:
            offer_data['images'] = images
        
        # En az bir içerik olmalı
        if not any([offer_text, offer_price, links, images]):
            return JsonResponse({
                'success': False,
                'error': 'En az bir teklif içeriği (metin, fiyat, link veya resim) gereklidir.'
            })
        
        # WhatsApp mesajını gönder
        result = whatsapp_service.send_comprehensive_offer(
            to_phone=lead.customer_phone,
            offer_data=offer_data,
            lead_id=lead.lead_id,
            sent_by=request.user
        )
        
        if result.get('success'):
            # ActionLog kaydı oluştur - Başarılı
            ActionLog.objects.create(
                lead=lead,
                action_type='OFFER_SENT',
                title='WhatsApp Teklifi Gönderildi',
                description=f'Müşteriye kapsamlı teklif gönderildi. İçerik: {offer_data.get("text", "Resim/Link içeriği")[:100]}...' if len(str(offer_data.get("text", ""))) > 100 else f'Müşteriye kapsamlı teklif gönderildi. İçerik: {offer_data.get("text", "Resim/Link içeriği")}',
                payload={
                    'offer_data': offer_data,
                    'message_id': result.get('message_id')
                },
                is_successful=True,
                performed_by=request.user
            )
            
            # Başarılı gönderim - otomatik stage geçişi
            try:
                # "Teklif Gönderildi" stage'ini bul
                teklif_stage = SalesStage.objects.filter(
                    slug='teklif_gonderildi',
                    is_active=True
                ).first()
                
                if teklif_stage and lead.current_stage != teklif_stage:
                    # Stage geçişi kaydet
                    StageTransition.objects.create(
                        lead=lead,
                        from_stage=lead.current_stage,
                        to_stage=teklif_stage,
                        transition_type='automatic',
                        reason='WhatsApp teklif gönderimi başarılı',
                        performed_by=request.user
                    )
                    
                    # Lead'in stage'ini güncelle
                    lead.current_stage = teklif_stage
                    lead.stage_updated_at = timezone.now()
                    lead.last_contact_date = timezone.now()
                    lead.save()
                    
                    logger.info(f"Lead {lead.lead_id} automatically moved to 'Teklif Gönderildi' stage")
                
            except Exception as e:
                logger.error(f"Stage transition error: {str(e)}")
                # Stage geçişi başarısız olsa da mesaj gönderimi başarılı
            
            return JsonResponse({
                'success': True,
                'message': 'Teklif başarıyla gönderildi!',
                'message_id': result.get('message_id'),
                'stage_changed': teklif_stage is not None,
                'new_stage': teklif_stage.display_name if teklif_stage else None
            })
        else:
            # ActionLog kaydı oluştur - Başarısız
            ActionLog.objects.create(
                lead=lead,
                action_type='OFFER_SENT',
                title='WhatsApp Teklifi Gönderilemedi',
                description=f'Teklif gönderimi başarısız oldu: {result.get("error", "Bilinmeyen hata")}',
                payload={
                    'offer_data': offer_data,
                    'error': result.get('error')
                },
                is_successful=False,
                error_message=result.get('error', 'Bilinmeyen hata'),
                performed_by=request.user
            )
            
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Bilinmeyen hata'),
                'partial_success': result.get('partial_success', False)
            })
            
    except Lead.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Lead bulunamadı'
        })
    except Exception as e:
        logger.error(f"Offer sending error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Sistem hatası: {str(e)}'
        })


@login_required
def get_offer_history(request, lead_id):
    """
    Lead'in teklif geçmişini getir
    """
    try:
        lead = get_object_or_404(Lead, lead_id=lead_id)
        
        # Teklif mesajlarını getir
        offer_messages = WhatsAppMessage.objects.filter(
            lead=lead,
            message_type='offer_sent',
            direction='outbound'
        ).order_by('-created_at')
        
        offers_data = []
        for msg in offer_messages:
            try:
                # JSON içeriği parse et
                if msg.content.startswith('{'):
                    content_data = json.loads(msg.content)
                else:
                    content_data = {'text': msg.content}
            except:
                content_data = {'text': msg.content}
            
            # Format the offer data for frontend
            offer_item = {
                'id': msg.id,
                'message_id': msg.message_id,
                'text': content_data.get('text', ''),
                'price': content_data.get('price'),
                'images': [],
                'links': content_data.get('links', []),
                'status': msg.status,
                'sent_by': msg.sent_by.get_full_name() if msg.sent_by else 'Sistem',
                'created_at': msg.created_at.strftime('%d.%m.%Y %H:%M'),
                'error_message': msg.error_message
            }
            
            # Process images if they exist
            if 'images' in content_data and content_data['images']:
                for img_data in content_data['images']:
                    if isinstance(img_data, dict) and 'url' in img_data:
                        offer_item['images'].append(img_data['url'])
                    elif isinstance(img_data, str):
                        offer_item['images'].append(img_data)
            
            # Ensure links is always a list
            if not isinstance(offer_item['links'], list):
                offer_item['links'] = [offer_item['links']] if offer_item['links'] else []
            
            offers_data.append(offer_item)
        
        return JsonResponse({
            'success': True,
            'offers': offers_data
        })
        
    except Exception as e:
        logger.error(f"Offer history error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })