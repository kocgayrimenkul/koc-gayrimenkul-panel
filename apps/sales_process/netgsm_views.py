# -*- coding: utf-8 -*-
"""
Netgsm Santral Entegrasyonu Views
Santral webhook'ları ve arama yönetimi için view'lar
"""

import json
import logging
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Sum, Max
from .models import Lead, CallLog
from .netgsm_service import NetgsmService
from .forms import LeadFilterForm

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def netgsm_webhook(request):
    """
    Netgsm webhook endpoint
    GET: Webhook doğrulama
    POST: Arama event'lerini işle
    """
    if request.method == 'GET':
        # Webhook doğrulama
        verify_token = request.GET.get('verify_token')
        challenge = request.GET.get('challenge')
        
        netgsm_service = NetgsmService()
        if verify_token == netgsm_service.webhook_secret:
            return HttpResponse(challenge)
        else:
            return HttpResponse('Unauthorized', status=401)
    
    elif request.method == 'POST':
        try:
            # Webhook signature doğrulama
            signature = request.headers.get('X-Netgsm-Signature', '')
            body = request.body.decode('utf-8')
            
            netgsm_service = NetgsmService()
            
            if not netgsm_service.verify_webhook_signature(body, signature):
                logger.warning("Invalid webhook signature")
                return JsonResponse({'error': 'Invalid signature'}, status=401)
            
            # Webhook data'sını parse et
            webhook_data = json.loads(body)
            
            # Call webhook'unu işle
            call_log = netgsm_service.process_call_webhook(webhook_data)
            
            return JsonResponse({
                'success': True,
                'call_log_id': call_log.id if call_log else None
            })
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return JsonResponse({'error': 'Processing failed'}, status=500)

@login_required
def call_logs(request):
    """
    Arama geçmişi listesi
    """
    # Filtreleme
    call_type = request.GET.get('call_type', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    phone_search = request.GET.get('phone_search', '')
    
    # Base queryset
    calls = CallLog.objects.select_related('lead').order_by('-start_time')
    
    # Filtreler
    if call_type:
        calls = calls.filter(call_type=call_type)
    
    if status:
        calls = calls.filter(status=status)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            calls = calls.filter(start_time__date__gte=date_from_obj.date())
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            calls = calls.filter(start_time__date__lte=date_to_obj.date())
        except ValueError:
            pass
    
    if phone_search:
        calls = calls.filter(
            Q(phone_number__icontains=phone_search) |
            Q(lead__customer_phone__icontains=phone_search) |
            Q(lead__customer_name__icontains=phone_search)
        )
    
    # Sayfalama
    paginator = Paginator(calls, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # İstatistikler
    stats = {
        'total_calls': calls.count(),
        'answered_calls': calls.filter(status='answered').count(),
        'missed_calls': calls.filter(status='missed').count(),
        'busy_calls': calls.filter(status='busy').count(),
        'total_duration': calls.aggregate(Sum('duration'))['duration__sum'] or 0,
        'avg_duration': calls.aggregate(Avg('duration'))['duration__avg'] or 0,
    }
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'call_type': call_type,
        'status': status,
        'date_from': date_from,
        'date_to': date_to,
        'phone_search': phone_search,
    }
    
    return render(request, 'sales_process/call_logs.html', context)

@login_required
def call_statistics(request):
    """
    Arama istatistikleri sayfası
    """
    # Tarih aralığı
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    end_date = timezone.now()
    
    # Netgsm servisinden istatistikleri al
    netgsm_service = NetgsmService()
    stats = netgsm_service.get_call_statistics(start_date, end_date)
    
    # Günlük trend verileri
    daily_stats = CallLog.objects.filter(
        start_time__range=[start_date, end_date]
    ).extra(
        select={'day': 'DATE(start_time)'}
    ).values('day').annotate(
        total_calls=Count('id'),
        answered_calls=Count('id', filter=Q(status='answered')),
        missed_calls=Count('id', filter=Q(status='missed')),
        total_duration=Sum('duration')
    ).order_by('day')
    
    # Agent performansı (eğer agent_extension bilgisi varsa)
    agent_stats = CallLog.objects.filter(
        start_time__range=[start_date, end_date],
        agent_extension__isnull=False
    ).values('agent_extension').annotate(
        total_calls=Count('id'),
        answered_calls=Count('id', filter=Q(status='answered')),
        total_duration=Sum('duration'),
        avg_duration=Avg('duration')
    ).order_by('-total_calls')
    
    # En çok aranan numaralar
    top_numbers = CallLog.objects.filter(
        start_time__range=[start_date, end_date]
    ).values('phone_number').annotate(
        call_count=Count('id'),
        last_call=Max('start_time')
    ).order_by('-call_count')[:10]
    
    context = {
        'stats': stats,
        'daily_stats': list(daily_stats),
        'agent_stats': list(agent_stats),
        'top_numbers': list(top_numbers),
        'days': days,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'sales_process/call_statistics.html', context)

@login_required
@require_http_methods(["POST"])
def make_call(request, lead_id):
    """
    Lead'e arama başlat
    """
    try:
        lead = get_object_or_404(Lead, id=lead_id)
        agent_extension = request.POST.get('agent_extension')
        
        netgsm_service = NetgsmService()
        result = netgsm_service.make_outbound_call(
            phone_number=lead.customer_phone,
            agent_extension=agent_extension
        )
        
        if result['success']:
            # Arama başlatıldı notu ekle
            from .models import LeadNote
            LeadNote.objects.create(
                lead=lead,
                note=f"Arama başlatıldı - Agent: {agent_extension or 'Belirtilmedi'}",
                note_type='call',
                created_by=request.user
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Arama başlatıldı',
                'call_id': result.get('call_id')
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Arama başlatılamadı')
            })
            
    except Exception as e:
        logger.error(f"Error making call: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Bir hata oluştu'
        })

@login_required
def call_detail(request, call_id):
    """
    Arama detayları
    """
    call_log = get_object_or_404(CallLog, id=call_id)
    
    context = {
        'call_log': call_log,
    }
    
    return render(request, 'sales_process/call_detail.html', context)

@login_required
def agent_dashboard(request):
    """
    Agent dashboard - günlük arama özeti
    """
    today = timezone.now().date()
    
    # Bugünkü aramalar
    today_calls = CallLog.objects.filter(
        start_time__date=today
    )
    
    # Agent extension'ı varsa filtrele
    agent_extension = request.GET.get('extension')
    if agent_extension:
        today_calls = today_calls.filter(agent_extension=agent_extension)
    
    # İstatistikler
    stats = {
        'total_calls': today_calls.count(),
        'incoming_calls': today_calls.filter(call_type='incoming').count(),
        'outgoing_calls': today_calls.filter(call_type='outgoing').count(),
        'answered_calls': today_calls.filter(status='answered').count(),
        'missed_calls': today_calls.filter(status='missed').count(),
        'total_duration': today_calls.aggregate(Sum('duration'))['duration__sum'] or 0,
    }
    
    # Son aramalar
    recent_calls = today_calls.select_related('lead').order_by('-start_time')[:10]
    
    # Bekleyen görevler (kaçırılmış aramalardan)
    from .models import Task
    pending_tasks = Task.objects.filter(
        task_type='call',
        status='pending',
        assigned_to=request.user
    ).select_related('lead')[:5]
    
    context = {
        'stats': stats,
        'recent_calls': recent_calls,
        'pending_tasks': pending_tasks,
        'agent_extension': agent_extension,
        'today': today,
    }
    
    return render(request, 'sales_process/agent_dashboard.html', context)

@login_required
@require_http_methods(["POST"])
def update_call_notes(request, call_id):
    """
    Arama notlarını güncelle
    """
    try:
        call_log = get_object_or_404(CallLog, id=call_id)
        notes = request.POST.get('notes', '')
        
        call_log.notes = notes
        call_log.save()
        
        # Lead'e de not ekle
        if call_log.lead and notes:
            from .models import LeadNote
            LeadNote.objects.create(
                lead=call_log.lead,
                note=f"Arama notu: {notes}",
                note_type='call',
                created_by=request.user
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Notlar güncellendi'
        })
        
    except Exception as e:
        logger.error(f"Error updating call notes: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Notlar güncellenemedi'
        })

@login_required
def export_call_logs(request):
    """
    Arama geçmişini Excel olarak dışa aktar
    """
    import openpyxl
    from django.http import HttpResponse
    from openpyxl.utils import get_column_letter
    
    # Filtreleri uygula
    calls = CallLog.objects.select_related('lead').order_by('-start_time')
    
    # Tarih filtresi
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            calls = calls.filter(start_time__date__gte=date_from_obj.date())
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            calls = calls.filter(start_time__date__lte=date_to_obj.date())
        except ValueError:
            pass
    
    # Excel dosyası oluştur
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Arama Geçmişi"
    
    # Başlıklar
    headers = [
        'Tarih/Saat', 'Telefon', 'Müşteri Adı', 'Arama Tipi', 
        'Durum', 'Süre (sn)', 'Agent', 'Notlar'
    ]
    
    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
    
    # Veriler
    for row, call in enumerate(calls[:1000], 2):  # Max 1000 kayıt
        ws.cell(row=row, column=1, value=call.start_time.strftime('%d.%m.%Y %H:%M'))
        ws.cell(row=row, column=2, value=call.phone_number)
        ws.cell(row=row, column=3, value=call.lead.customer_name if call.lead else 'Bilinmiyor')
        ws.cell(row=row, column=4, value=call.get_call_type_display())
        ws.cell(row=row, column=5, value=call.get_status_display())
        ws.cell(row=row, column=6, value=call.duration)
        ws.cell(row=row, column=7, value=call.agent_extension or '')
        ws.cell(row=row, column=8, value=call.notes or '')
    
    # Sütun genişliklerini ayarla
    for col in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col)].width = 15
    
    # Response oluştur
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="arama_gecmisi_{timezone.now().strftime("%Y%m%d")}.xlsx"'
    
    wb.save(response)
    return response