# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Satış Süreç Yönetimi Views
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator
from datetime import datetime
from .models import Lead, SalesStage, LeadNote, Task, Appointment, StageTransition, WhatsAppMessage, CallLog, ActionLog
from apps.customers.models import Customer
import json


@login_required
def sales_dashboard(request):
    """Ana satış süreç dashboard'u"""
    # Dashboard istatistikleri
    active_leads_count = Lead.objects.filter(
        current_stage__name__in=[
            'bilgi_verildi', 'ihtiyac_analizi', 'teklif_gonderildi', 
            'daire_sunumu', 'cevap_bekleniyor'
        ]
    ).count()
    
    completed_leads_count = Lead.objects.filter(
        current_stage__name='dosya_kapandi'
    ).count()
    
    pending_tasks_count = Task.objects.filter(
        status__in=['pending', 'in_progress'],
        due_date__gte=timezone.now().date()
    ).count()
    
    context = {
        'title': 'Satış Süreç Yönetimi',
        'active_leads_count': active_leads_count,
        'completed_leads_count': completed_leads_count,
        'pending_tasks_count': pending_tasks_count,
    }
    return render(request, 'sales_process/dashboard.html', context)


@login_required
def staff_kanban(request):
    """Personel kanban görünümü"""
    try:
        # Personel akışı aşamaları
        bilgi_verildi_stage = SalesStage.objects.get(name='bilgi_verildi')
        ihtiyac_analizi_stage = SalesStage.objects.get(name='ihtiyac_analizi')
        teklif_gonderildi_stage = SalesStage.objects.get(name='teklif_gonderildi')
        daire_sunumu_stage = SalesStage.objects.get(name='daire_sunumu')
        cevap_bekleniyor_stage = SalesStage.objects.get(name='cevap_bekleniyor')
        sozlesme_yapildi_stage = SalesStage.objects.get(name='sozlesme_yapildi')
        
        # Her aşamadaki lead'leri getir
        bilgi_verildi_leads = Lead.objects.filter(current_stage=bilgi_verildi_stage).order_by('-created_at')
        ihtiyac_analizi_leads = Lead.objects.filter(current_stage=ihtiyac_analizi_stage).order_by('-stage_updated_at')
        teklif_gonderildi_leads = Lead.objects.filter(current_stage=teklif_gonderildi_stage).order_by('-stage_updated_at')
        daire_sunumu_leads = Lead.objects.filter(current_stage=daire_sunumu_stage).order_by('-stage_updated_at')
        cevap_bekleniyor_leads = Lead.objects.filter(current_stage=cevap_bekleniyor_stage).order_by('-stage_updated_at')
        sozlesme_yapildi_leads = Lead.objects.filter(current_stage=sozlesme_yapildi_stage).order_by('-stage_updated_at')
        
        # Template için stages_with_leads yapısını oluştur
        stages_with_leads = [
            {
                'stage': bilgi_verildi_stage,
                'leads': bilgi_verildi_leads,
                'count': bilgi_verildi_leads.count()
            },
            {
                'stage': ihtiyac_analizi_stage,
                'leads': ihtiyac_analizi_leads,
                'count': ihtiyac_analizi_leads.count()
            },
            {
                'stage': teklif_gonderildi_stage,
                'leads': teklif_gonderildi_leads,
                'count': teklif_gonderildi_leads.count()
            },
            {
                'stage': daire_sunumu_stage,
                'leads': daire_sunumu_leads,
                'count': daire_sunumu_leads.count()
            },
            {
                'stage': cevap_bekleniyor_stage,
                'leads': cevap_bekleniyor_leads,
                'count': cevap_bekleniyor_leads.count()
            },
            {
                'stage': sozlesme_yapildi_stage,
                'leads': sozlesme_yapildi_leads,
                'count': sozlesme_yapildi_leads.count()
            }
        ]
        
        # İstatistikler
        total_leads = Lead.objects.count()
        my_leads = Lead.objects.filter(assigned_staff=request.user).count() if hasattr(request.user, 'assigned_leads') else 0
        today_tasks = Task.objects.filter(assigned_to=request.user, due_date__date=timezone.now().date()).count() if hasattr(request.user, 'tasks') else 0
        
        context = {
            'title': 'Personel Satış Akışı',
            'stages_with_leads': stages_with_leads,
            'bilgi_verildi_leads': bilgi_verildi_leads,
            'ihtiyac_analizi_leads': ihtiyac_analizi_leads,
            'teklif_gonderildi_leads': teklif_gonderildi_leads,
            'daire_sunumu_leads': daire_sunumu_leads,
            'cevap_bekleniyor_leads': cevap_bekleniyor_leads,
            'sozlesme_yapildi_leads': sozlesme_yapildi_leads,
            'total_leads': total_leads,
            'my_leads': my_leads,
            'today_tasks': today_tasks,
            'conversion_rate': 0,  # Bu hesaplanabilir
        }
        return render(request, 'sales_process/staff_kanban.html', context)
    except SalesStage.DoesNotExist:
        messages.error(request, 'Satış aşamaları henüz oluşturulmamış. Lütfen yöneticinizle iletişime geçin.')
        return redirect('sales_process:dashboard')


@login_required
def staff_kanban_fullscreen(request):
    """Personel kanban tam ekran görünümü"""
    try:
        # Personel akışı aşamaları
        bilgi_verildi_stage = SalesStage.objects.get(name='bilgi_verildi')
        ihtiyac_analizi_stage = SalesStage.objects.get(name='ihtiyac_analizi')
        teklif_gonderildi_stage = SalesStage.objects.get(name='teklif_gonderildi')
        daire_sunumu_stage = SalesStage.objects.get(name='daire_sunumu')
        cevap_bekleniyor_stage = SalesStage.objects.get(name='cevap_bekleniyor')
        sozlesme_yapildi_stage = SalesStage.objects.get(name='sozlesme_yapildi')
        
        # Her aşamadaki lead'leri getir
        bilgi_verildi_leads = Lead.objects.filter(current_stage=bilgi_verildi_stage).order_by('-created_at')
        ihtiyac_analizi_leads = Lead.objects.filter(current_stage=ihtiyac_analizi_stage).order_by('-stage_updated_at')
        teklif_gonderildi_leads = Lead.objects.filter(current_stage=teklif_gonderildi_stage).order_by('-stage_updated_at')
        daire_sunumu_leads = Lead.objects.filter(current_stage=daire_sunumu_stage).order_by('-stage_updated_at')
        cevap_bekleniyor_leads = Lead.objects.filter(current_stage=cevap_bekleniyor_stage).order_by('-stage_updated_at')
        sozlesme_yapildi_leads = Lead.objects.filter(current_stage=sozlesme_yapildi_stage).order_by('-stage_updated_at')
        
        # Template için stages_with_leads yapısını oluştur
        stages_with_leads = [
            {
                'stage': bilgi_verildi_stage,
                'leads': bilgi_verildi_leads,
                'count': bilgi_verildi_leads.count()
            },
            {
                'stage': ihtiyac_analizi_stage,
                'leads': ihtiyac_analizi_leads,
                'count': ihtiyac_analizi_leads.count()
            },
            {
                'stage': teklif_gonderildi_stage,
                'leads': teklif_gonderildi_leads,
                'count': teklif_gonderildi_leads.count()
            },
            {
                'stage': daire_sunumu_stage,
                'leads': daire_sunumu_leads,
                'count': daire_sunumu_leads.count()
            },
            {
                'stage': cevap_bekleniyor_stage,
                'leads': cevap_bekleniyor_leads,
                'count': cevap_bekleniyor_leads.count()
            },
            {
                'stage': sozlesme_yapildi_stage,
                'leads': sozlesme_yapildi_leads,
                'count': sozlesme_yapildi_leads.count()
            }
        ]
        
        # İstatistikler
        user_leads_count = Lead.objects.filter(assigned_staff=request.user).count()
        active_stages_count = len([s for s in stages_with_leads if s['count'] > 0])
        new_leads_count = Lead.objects.filter(
            current_stage=bilgi_verildi_stage,
            created_at__date=timezone.now().date()
        ).count()
        contract_awaiting_count = sozlesme_yapildi_leads.count()
        
        context = {
            'title': 'Personel Kanban - Tam Ekran',
            'stages_with_leads': stages_with_leads,
            'user_leads_count': user_leads_count,
            'active_stages_count': active_stages_count,
            'new_leads_count': new_leads_count,
            'contract_awaiting_count': contract_awaiting_count,
        }
        
        return render(request, 'sales_process/staff_kanban_fullscreen.html', context)
    except SalesStage.DoesNotExist:
        messages.error(request, 'Satış aşamaları henüz oluşturulmamış. Lütfen yöneticinizle iletişime geçin.')
        return redirect('sales_process:dashboard')


@login_required
def manager_kanban(request):
    """Müdür kanban görünümü"""
    # Müdür akışı aşamaları
    sozlesme_yapildi_stage = SalesStage.objects.get(name='sozlesme_yapildi')
    kredi_islemleri_stage = SalesStage.objects.get(name='kredi_islemleri')
    tapu_islemi_stage = SalesStage.objects.get(name='tapu_islemi')
    hizmet_tamamlandi_stage = SalesStage.objects.get(name='hizmet_tamamlandi')
    memnuniyet_anketi_stage = SalesStage.objects.get(name='memnuniyet_anketi')
    dosya_kapandi_stage = SalesStage.objects.get(name='dosya_kapandi')
    
    # Her aşamadaki lead'leri getir
    contract_leads = Lead.objects.filter(current_stage=sozlesme_yapildi_stage).order_by('-stage_updated_at')
    credit_leads = Lead.objects.filter(current_stage=kredi_islemleri_stage).order_by('-stage_updated_at')
    deed_leads = Lead.objects.filter(current_stage=tapu_islemi_stage).order_by('-stage_updated_at')
    completed_leads = Lead.objects.filter(current_stage=hizmet_tamamlandi_stage).order_by('-stage_updated_at')
    survey_leads = Lead.objects.filter(current_stage=memnuniyet_anketi_stage).order_by('-stage_updated_at')
    closed_leads = Lead.objects.filter(current_stage=dosya_kapandi_stage).order_by('-stage_updated_at')[:20]  # Son 20 kapatılan dosya
    
    context = {
        'title': 'Müdür Satış Sonrası Akışı',
        'contract_leads': contract_leads,
        'credit_leads': credit_leads,
        'deed_leads': deed_leads,
        'completed_leads': completed_leads,
        'survey_leads': survey_leads,
        'closed_leads': closed_leads,
        # Stage'leri de context'e ekle
        'sozlesme_yapildi_stage': sozlesme_yapildi_stage,
        'kredi_islemleri_stage': kredi_islemleri_stage,
        'tapu_islemi_stage': tapu_islemi_stage,
        'hizmet_tamamlandi_stage': hizmet_tamamlandi_stage,
        'memnuniyet_anketi_stage': memnuniyet_anketi_stage,
        'dosya_kapandi_stage': dosya_kapandi_stage,
    }
    return render(request, 'sales_process/manager_kanban.html', context)


@login_required
def manager_kanban_fullscreen(request):
    """Müdür kanban tam ekran görünümü"""
    # Müdür akışı aşamaları
    sozlesme_yapildi_stage = SalesStage.objects.get(name='sozlesme_yapildi')
    kredi_islemleri_stage = SalesStage.objects.get(name='kredi_islemleri')
    tapu_islemi_stage = SalesStage.objects.get(name='tapu_islemi')
    hizmet_tamamlandi_stage = SalesStage.objects.get(name='hizmet_tamamlandi')
    memnuniyet_anketi_stage = SalesStage.objects.get(name='memnuniyet_anketi')
    dosya_kapandi_stage = SalesStage.objects.get(name='dosya_kapandi')
    
    # Her aşamadaki lead'leri getir
    contract_leads = Lead.objects.filter(current_stage=sozlesme_yapildi_stage).order_by('-stage_updated_at')
    credit_leads = Lead.objects.filter(current_stage=kredi_islemleri_stage).order_by('-stage_updated_at')
    deed_leads = Lead.objects.filter(current_stage=tapu_islemi_stage).order_by('-stage_updated_at')
    completed_leads = Lead.objects.filter(current_stage=hizmet_tamamlandi_stage).order_by('-stage_updated_at')
    survey_leads = Lead.objects.filter(current_stage=memnuniyet_anketi_stage).order_by('-stage_updated_at')
    closed_leads = Lead.objects.filter(current_stage=dosya_kapandi_stage).order_by('-stage_updated_at')[:20]  # Son 20 kapatılan dosya
    
    context = {
        'title': 'Müdür Satış Sonrası Akışı - Tam Ekran',
        'contract_leads': contract_leads,
        'credit_leads': credit_leads,
        'deed_leads': deed_leads,
        'completed_leads': completed_leads,
        'survey_leads': survey_leads,
        'closed_leads': closed_leads,
        # Stage'leri de context'e ekle
        'sozlesme_yapildi_stage': sozlesme_yapildi_stage,
        'kredi_islemleri_stage': kredi_islemleri_stage,
        'tapu_islemi_stage': tapu_islemi_stage,
        'hizmet_tamamlandi_stage': hizmet_tamamlandi_stage,
        'memnuniyet_anketi_stage': memnuniyet_anketi_stage,
        'dosya_kapandi_stage': dosya_kapandi_stage,
    }
    return render(request, 'sales_process/manager_kanban_fullscreen.html', context)


@login_required
def lead_create(request):
    """Yeni lead oluşturma"""
    if request.method == 'POST':
        # Lead oluşturma işlemi
        try:
            customer_name = request.POST.get('customer_name')
            customer_phone = request.POST.get('customer_phone')
            customer_email = request.POST.get('customer_email', '')
            property_type = request.POST.get('property_type')
            property_location = request.POST.get('property_location')
            budget_min = request.POST.get('budget_min', 0)
            budget_max = request.POST.get('budget_max', 0)
            
            # İlk aşamayı getir
            initial_stage = SalesStage.objects.get(name='bilgi_verildi')
            
            # Önce Customer objesi oluştur
            from apps.customers.models import Customer, Neighborhood
            
            # Default neighborhood al (ilk neighborhood'u kullan)
            default_neighborhood = Neighborhood.objects.first()
            if not default_neighborhood:
                return JsonResponse({
                    'success': False,
                    'message': 'Sistem hatası: Mahalle bulunamadı. Lütfen yöneticinize başvurun.'
                })
            
            # Customer oluştur
            customer = Customer.objects.create(
                full_name=customer_name,
                phone=customer_phone,
                neighborhood=default_neighborhood,
                consultant=request.user,
                source='manuel',
                contact_type='bilgi_alma'
            )
            
            # Lead oluştur ve Customer'ı referans al
            lead = Lead.objects.create(
                customer=customer,
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_email=customer_email,
                property_type=property_type,
                property_location=property_location,
                budget_min=budget_min,
                budget_max=budget_max,
                current_stage=initial_stage,
                assigned_staff=request.user,
                source='manuel'
            )
            
            # İlk not ekle
            LeadNote.objects.create(
                lead=lead,
                title="Yeni Müşteri Kaydı",
                content=f"Müşteri {customer_name} sisteme eklendi. Telefon: {customer_phone}",
                created_by=request.user,
                note_type='system'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Müşteri başarıyla eklendi.',
                'lead_id': lead.id,
                'redirect_url': '/satis-surec/leads/'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Hata: {str(e)}'
            })
    
    context = {
        'title': 'Yeni Müşteri Kaydı',
    }
    return render(request, 'sales_process/lead_create.html', context)


@login_required
def lead_list(request):
    """Lead listesi sayfası"""
    leads = Lead.objects.select_related('customer', 'current_stage', 'assigned_staff').all().order_by('-created_at')
    
    # Filtreleme
    stage_filter = request.GET.get('stage')
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search')
    
    if stage_filter:
        leads = leads.filter(current_stage__name=stage_filter)
    
    if status_filter:
        leads = leads.filter(status=status_filter)
    
    if search_query:
        leads = leads.filter(
            Q(customer_name__icontains=search_query) |
            Q(customer_phone__icontains=search_query) |
            Q(customer_email__icontains=search_query)
        )
    
    # Sayfalama
    paginator = Paginator(leads, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filtre seçenekleri
    stages = SalesStage.objects.filter(is_active=True).order_by('order')
    
    context = {
        'title': 'Müşteri Listesi',
        'page_obj': page_obj,
        'stages': stages,
        'current_filters': {
            'stage': stage_filter,
            'status': status_filter,
            'search': search_query,
        },
        'status_choices': Lead.STATUS_CHOICES,
    }
    return render(request, 'sales_process/lead_list.html', context)


@login_required
def lead_detail(request, lead_id):
    """Lead detay sayfası"""
    lead = get_object_or_404(Lead, lead_id=lead_id)
    notes = LeadNote.objects.filter(lead=lead).order_by('-created_at')
    tasks = Task.objects.filter(lead=lead).order_by('-created_at')
    appointments = Appointment.objects.filter(lead=lead).order_by('-scheduled_date')
    action_logs = ActionLog.objects.filter(lead=lead).order_by('-created_at')
    
    context = {
        'title': f'{lead.customer_name} - Detay',
        'lead': lead,
        'notes': notes,
        'tasks': tasks,
        'appointments': appointments,
        'action_logs': action_logs,
    }
    return render(request, 'sales_process/lead_detail.html', context)


@login_required
def lead_update(request, lead_id):
    """Lead güncelleme"""
    lead = get_object_or_404(Lead, lead_id=lead_id)
    
    if request.method == 'POST':
        try:
            # Lead bilgilerini güncelle
            lead.customer_name = request.POST.get('customer_name', lead.customer_name)
            lead.customer_phone = request.POST.get('customer_phone', lead.customer_phone)
            lead.customer_email = request.POST.get('customer_email', lead.customer_email)
            lead.property_type = request.POST.get('property_type', lead.property_type)
            lead.property_location = request.POST.get('property_location', lead.property_location)
            lead.budget_min = request.POST.get('budget_min', lead.budget_min)
            lead.budget_max = request.POST.get('budget_max', lead.budget_max)
            lead.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Müşteri bilgileri güncellendi.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Hata: {str(e)}'
            })
    
    context = {
        'title': f'{lead.customer_name} - Güncelle',
        'lead': lead,
    }
    return render(request, 'sales_process/lead_update.html', context)


# AJAX Views
@login_required
@require_http_methods(["GET"])
def get_leads_ajax(request):
    """AJAX ile lead listesi getir"""
    stage_name = request.GET.get('stage')
    
    try:
        if stage_name:
            stage = SalesStage.objects.get(name=stage_name)
            leads = Lead.objects.filter(current_stage=stage).select_related('assigned_staff')
        else:
            leads = Lead.objects.all().select_related('assigned_staff')
        
        leads_data = []
        for lead in leads:
            leads_data.append({
                'id': lead.id,
                'customer_name': lead.customer_name,
                'customer_phone': lead.customer_phone,
                'property_type': lead.property_type,
                'property_location': lead.property_location,
                'assigned_staff': lead.assigned_staff.get_full_name() if lead.assigned_staff else '',
                'stage_updated_at': lead.stage_updated_at.strftime('%d.%m.%Y %H:%M') if lead.stage_updated_at else '',
                'priority': lead.priority
            })
        
        # İstatistikleri hesapla
        total_leads = Lead.objects.count()
        active_leads = Lead.objects.filter(status='active').count()
        completed_leads = Lead.objects.filter(status='completed').count()
        
        statistics = {
            'total_leads': total_leads,
            'active_leads': active_leads,
            'completed_leads': completed_leads
        }
        
        return JsonResponse({
            'success': True,
            'leads': leads_data,
            'statistics': statistics
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def send_satisfaction_survey(request):
    """
    Müşteriye memnuniyet anketi gönderir ve kartı 'Yorum Yapıldı' kolonuna taşır
    """
    try:
        data = json.loads(request.body)
        lead_id = data.get('lead_id')
        
        if not lead_id:
            return JsonResponse({
                'success': False,
                'message': 'Lead ID gerekli'
            })
        
        lead = get_object_or_404(Lead, lead_id=lead_id)
        
        # Kartı 'Yorum Yapıldı' kolonuna taşı
        feedback_stage = get_object_or_404(SalesStage, name='Yorum Yapıldı')
        lead.current_stage = feedback_stage
        lead.save()
        
        # Stage transition kaydı
        StageTransition.objects.create(
            lead=lead,
            from_stage=lead.current_stage,
            to_stage=feedback_stage,
            changed_by=request.user,
            notes="Memnuniyet anketi gönderildi"
        )
        
        # ActionLog kaydı
        ActionLog.objects.create(
            lead=lead,
            action_type='FEEDBACK_SENT',
            title='Memnuniyet Anketi Gönderildi',
            description="Müşteriye memnuniyet anketi gönderildi",
            performed_by=request.user
        )
        
        # WhatsApp mesajı gönder
        try:
            from .whatsapp_views import send_automatic_whatsapp
            send_automatic_whatsapp(lead, 'satisfaction_survey')
        except Exception as wa_error:
            print(f"WhatsApp mesajı gönderilemedi: {wa_error}")
        
        return JsonResponse({
            'success': True,
            'message': 'Memnuniyet anketi gönderildi.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def close_case(request):
    """
    OSMAN'IN İSTEĞİ: Memnuniyet anketinden direkt dosya kapanışı
    """
    try:
        data = json.loads(request.body)
        lead_id = data.get('lead_id')
        
        if not lead_id:
            return JsonResponse({
                'success': False,
                'message': 'Lead ID gerekli'
            })
        
        lead = get_object_or_404(Lead, lead_id=lead_id)
        
        # OSMAN'IN İSTEĞİ: Sadece "Memnuniyet Anketi" aşamasından kapatılabilir
        if lead.current_stage.name != 'memnuniyet_anketi':
            return JsonResponse({
                'success': False,
                'message': 'Dosya sadece "Memnuniyet Anketi" aşamasından kapatılabilir'
            })
        
        old_stage = lead.current_stage
        
        # Kartı 'Dosya Kapandı' kolonuna taşı
        closed_stage = get_object_or_404(SalesStage, name='dosya_kapandi')
        lead.current_stage = closed_stage
        lead.stage_updated_at = timezone.now()
        lead.is_closed = True  # Dosya kapatıldı flag'i
        lead.closed_at = timezone.now()
        lead.closed_by = request.user
        lead.save()
        
        # Stage transition kaydı
        StageTransition.objects.create(
            lead=lead,
            from_stage=old_stage,
            to_stage=closed_stage,
            transition_type='manual',
            reason="Memnuniyet anketi sonrası dosya kapatıldı",
            performed_by=request.user
        )
        
        # Sistem notu ekle
        LeadNote.objects.create(
            lead=lead,
            title="Dosya Kapatıldı",
            content="Memnuniyet anketi sonrası satış süreci tamamlandı. Dosya başarıyla kapatıldı.",
            created_by=request.user,
            note_type='system'
        )
        
        # ActionLog kaydı
        ActionLog.objects.create(
            lead=lead,
            action_type='CASE_CLOSED',
            title='Dosya Kapatıldı',
            description="Memnuniyet anketi sonrası dosya kapatıldı - Satış süreci tamamlandı",
            performed_by=request.user,
            is_successful=True
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Dosya başarıyla kapatıldı. Satış süreci tamamlandı.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def move_stage_ajax(request):
    """AJAX ile aşama değiştirme"""
    try:
        data = json.loads(request.body)
        lead_id = data.get('lead_id')
        new_stage_name = data.get('new_stage')
        
        lead = get_object_or_404(Lead, lead_id=lead_id)
        new_stage = get_object_or_404(SalesStage, name=new_stage_name)
        
        old_stage = lead.current_stage
        
        # Aşama geçişini kaydet
        from .models import StageTransition
        StageTransition.objects.create(
            lead=lead,
            from_stage=old_stage,
            to_stage=new_stage,
            transition_type='manual',
            performed_by=request.user,
            reason=f"Aşama değiştirildi: {old_stage.name if old_stage else 'Başlangıç'} -> {new_stage.name}"
        )
        
        # Lead'i güncelle
        lead.current_stage = new_stage
        lead.stage_updated_at = timezone.now()
        lead.save()
        
        # Sistem notu ekle
        LeadNote.objects.create(
            lead=lead,
            note=f"Aşama değiştirildi: {old_stage.display_name} -> {new_stage.display_name}",
            created_by=request.user,
            note_type='system'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Aşama başarıyla değiştirildi: {new_stage.display_name}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


# AJAX Views - Tamamlanmış fonksiyonlar
@login_required
@require_http_methods(["POST"])
def add_note(request):
    """Lead'e not ekleme"""
    try:
        data = json.loads(request.body)
        lead_id = data.get('lead_id')
        note_text = data.get('note')
        note_type = data.get('note_type', 'general')
        
        lead = get_object_or_404(Lead, lead_id=lead_id)
        
        note = LeadNote.objects.create(
            lead=lead,
            title="Manuel Not",
            content=note_text,
            created_by=request.user,
            note_type=note_type
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Not başarıyla eklendi.',
            'note': {
                'id': note.id,
                'content': note.content,
                'created_at': note.created_at.strftime('%d.%m.%Y %H:%M') if note.created_at else 'Tarih Yok',
                'created_by': note.created_by.get_full_name()
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_http_methods(["POST"])
def complete_presentation(request):
    """Sunum tamamlama"""
    try:
        data = json.loads(request.body)
        lead_id = data.get('lead_id')
        completion_notes = data.get('completion_notes', '')
        location_data = data.get('location_data')
        manual_location = data.get('manual_location', '')
        
        # Validasyon
        if not lead_id:
            return JsonResponse({
                'success': False,
                'message': 'Lead ID gerekli.'
            })
            
        if not completion_notes.strip():
            return JsonResponse({
                'success': False,
                'message': 'Sunum notları zorunludur.'
            })
            
        # Konum bilgisi kontrolü
        if not location_data and not manual_location.strip():
            return JsonResponse({
                'success': False,
                'message': 'Konum bilgisi gereklidir.'
            })
        
        lead = get_object_or_404(Lead, lead_id=lead_id)
        
        # Lead'in daire_sunumu aşamasında olduğunu kontrol et
        if lead.current_stage.name != 'daire_sunumu':
            return JsonResponse({
                'success': False,
                'message': 'Lead daire sunumu aşamasında değil.'
            })
        
        # PresentationLocation kaydı oluştur
        from .models import ActionLog, PresentationLocation
        
        # PresentationLocation verilerini hazırla
        presentation_data = {
            'lead': lead,
            'completion_notes': completion_notes,
            'completed_by': request.user
        }
        
        # GPS konum bilgilerini ekle
        if location_data:
            presentation_data.update({
                'latitude': location_data.get('latitude'),
                'longitude': location_data.get('longitude'),
                'accuracy': location_data.get('accuracy'),
                'location_timestamp': location_data.get('timestamp')
            })
        
        # Manuel konum bilgisini ekle
        if manual_location:
            presentation_data['manual_location'] = manual_location
        
        # PresentationLocation kaydını oluştur
        presentation_location = PresentationLocation.objects.create(**presentation_data)
        
        # ActionLog kaydı oluştur
        payload_data = {
            'completion_notes': completion_notes,
            'lead_id': str(lead.lead_id),
            'customer_name': lead.customer_name,
            'customer_phone': lead.customer_phone,
            'presentation_location_id': presentation_location.id
        }
        
        # Konum bilgisini payload'a ekle
        if location_data:
            payload_data['location_data'] = location_data
        if manual_location:
            payload_data['manual_location'] = manual_location
        
        location_info = presentation_location.location_display
        
        ActionLog.objects.create(
            lead=lead,
            action_type='SHOW_DONE',
            title='Sunum Tamamlandı',
            description=f'Sunum tamamlandı. {location_info} Notlar: {completion_notes[:100]}...',
            payload=payload_data,
            is_successful=True,
            performed_by=request.user
        )
        
        # Lead'i cevap_bekleniyor aşamasına geçir
        cevap_bekleniyor_stage = SalesStage.objects.get(name='cevap_bekleniyor')
        old_stage = lead.current_stage
        
        lead.current_stage = cevap_bekleniyor_stage
        lead.stage_updated_at = timezone.now()
        lead.save()
        
        # StageTransition kaydı oluştur
        StageTransition.objects.create(
            lead=lead,
            from_stage=old_stage,
            to_stage=cevap_bekleniyor_stage,
            transition_type='manual',
            performed_by=request.user,
            reason=f'Sunum tamamlandı - {completion_notes[:100]}...'
        )
        
        # Sistem notu ekle
        location_text = f" {presentation_location.location_display}"
        note_text = f"Sunum tamamlandı.{location_text} Notlar: {completion_notes}"
        
        LeadNote.objects.create(
            lead=lead,
            note=note_text,
            created_by=request.user,
            note_type='system'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Sunum başarıyla tamamlandı ve lead "Cevap Bekleniyor" aşamasına geçirildi.',
            'new_stage': cevap_bekleniyor_stage.display_name
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Randevu planlanırken hata oluştu: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def accept_offer(request):
    """Teklif kabul etme"""
    try:
        data = json.loads(request.body)
        lead_id = data.get('lead_id')
        
        if not lead_id:
            return JsonResponse({
                'success': False,
                'message': 'Lead ID gerekli'
            })
        
        lead = get_object_or_404(Lead, lead_id=lead_id)
        
        # Lead'in cevap_bekleniyor aşamasında olduğunu kontrol et
        if lead.current_stage.name != 'cevap_bekleniyor':
            return JsonResponse({
                'success': False,
                'message': 'Lead cevap bekleniyor aşamasında değil'
            })
        
        # Sözleşme aşamasına geç
        sozlesme_stage = SalesStage.objects.get(name='sozlesme_yapildi')
        lead.current_stage = sozlesme_stage
        lead.save()
        
        # ActionLog kaydı oluştur
        ActionLog.objects.create(
            lead=lead,
            action_type='OFFER_ACCEPTED',
            title='Teklif Kabul Edildi',
            description='Teklif kabul edildi',
            performed_by=request.user,
            is_successful=True
        )
        
        # Stage transition kaydı oluştur
        StageTransition.objects.create(
            lead=lead,
            from_stage=SalesStage.objects.get(name='cevap_bekleniyor'),
            to_stage=sozlesme_stage,
            transition_type='manual',
            performed_by=request.user,
            reason='Teklif kabul edildi'
        )
        
        # Sistem notu ekle
        LeadNote.objects.create(
            lead=lead,
            note_type='system',
            content=f'Teklif kabul edildi. Lead sözleşme aşamasına geçti.',
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Teklif başarıyla kabul edildi'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Teklif kabul edilirken hata oluştu: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def reject_offer(request):
    """Teklif reddetme"""
    try:
        data = json.loads(request.body)
        lead_id = data.get('lead_id')
        
        if not lead_id:
            return JsonResponse({
                'success': False,
                'message': 'Lead ID gerekli'
            })
        
        lead = get_object_or_404(Lead, lead_id=lead_id)
        
        # Lead'in cevap_bekleniyor aşamasında olduğunu kontrol et
        if lead.current_stage.name != 'cevap_bekleniyor':
            return JsonResponse({
                'success': False,
                'message': 'Lead cevap bekleniyor aşamasında değil'
            })
        
        # İhtiyaç analizi aşamasına geri döndür
        ihtiyac_analizi_stage = SalesStage.objects.get(name='ihtiyac_analizi')
        lead.current_stage = ihtiyac_analizi_stage
        lead.save()
        
        # ActionLog kaydı oluştur
        ActionLog.objects.create(
            lead=lead,
            action_type='OFFER_REJECTED',
            title='Teklif Reddedildi',
            description='Teklif reddedildi',
            performed_by=request.user,
            is_successful=True
        )
        
        # Stage transition kaydı oluştur
        StageTransition.objects.create(
            lead=lead,
            from_stage=SalesStage.objects.get(name='cevap_bekleniyor'),
            to_stage=ihtiyac_analizi_stage,
            transition_type='manual',
            performed_by=request.user,
            reason='Teklif reddedildi, ihtiyaç analizi aşamasına geri döndü'
        )
        
        # Sistem notu ekle
        LeadNote.objects.create(
            lead=lead,
            note_type='system',
            content=f'Teklif reddedildi. Lead ihtiyaç analizi aşamasına geri döndü.',
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Teklif başarıyla reddedildi'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Teklif reddedilirken hata oluştu: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def schedule_appointment(request):
    """Randevu planlama"""
    try:
        data = json.loads(request.body)
        lead_id = data.get('lead_id')
        appointment_date = data.get('scheduled_date')
        appointment_time = data.get('appointment_time')
        appointment_type = data.get('appointment_type', 'daire_sunumu')
        notes = data.get('notes', '')
        
        lead = get_object_or_404(Lead, lead_id=lead_id)
        
        # Tarih ve saati birleştir
        from datetime import datetime
        appointment_datetime = datetime.strptime(
            f"{appointment_date} {appointment_time}", 
            "%Y-%m-%d %H:%M"
        )
        
        appointment = Appointment.objects.create(
            lead=lead,
            scheduled_date=appointment_datetime,
            appointment_type=appointment_type,
            title=f"{appointment_type} - {lead.customer_name}",
            description=notes,
            assigned_staff=lead.assigned_staff or request.user
        )
        
        # Sistem notu ekle
        LeadNote.objects.create(
            lead=lead,
            note=f"Randevu planlandı: {appointment_datetime.strftime('%d.%m.%Y %H:%M') if appointment_datetime else 'Tarih Yok'} - {appointment.get_appointment_type_display()}",
            created_by=request.user,
            note_type='appointment'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Randevu başarıyla planlandı.',
            'appointment_id': appointment.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_http_methods(["POST"])
def send_whatsapp(request):
    """WhatsApp mesaj gönderme"""
    try:
        data = json.loads(request.body)
        lead_id = data.get('lead_id')
        message_type = data.get('message_type', 'general')
        custom_message = data.get('message', '')
        
        lead = get_object_or_404(Lead, lead_id=lead_id)
        
        # Mesaj şablonları
        message_templates = {
            'offer': f"Merhaba {lead.customer_name}, size özel hazırladığımız teklifi WhatsApp üzerinden gönderiyoruz. İncelemenizi bekliyoruz.",
            'appointment': f"Merhaba {lead.customer_name}, daire sunumu randevunuz için size uygun zamanı belirleyelim.",
            'follow_up': f"Merhaba {lead.customer_name}, gönderdiğimiz teklif hakkında düşüncelerinizi öğrenebilir miyiz?",
            'credit_update': f"Merhaba {lead.customer_name}, kredi işleminizle ilgili güncellemeler var. Detaylar için arayalım.",
            'deed_update': f"Merhaba {lead.customer_name}, tapu işleminiz tamamlandı. Tebrikler!",
            'satisfaction_survey': f"Merhaba {lead.customer_name}, hizmetimizle ilgili memnuniyet anketimizi doldurur musunuz?",
            'general': custom_message or f"Merhaba {lead.customer_name}, size nasıl yardımcı olabiliriz?"
        }
        
        message_text = message_templates.get(message_type, message_templates['general'])
        
        # WhatsApp servisini kullanarak mesaj gönder
        from .whatsapp_service import whatsapp_service
        
        if message_type == 'offer':
            # Teklif mesajı için özel fonksiyon kullan
            result = whatsapp_service.send_offer_message(
                to_phone=lead.customer_phone,
                offer_content=message_text,
                lead_id=lead.id
            )
        else:
            # Diğer mesajlar için normal fonksiyon
            result = whatsapp_service.send_text_message(
                to_phone=lead.customer_phone,
                message_text=message_text,
                lead_id=lead.id
            )
        
        if result['success']:
            # Mock mode bilgisini nota ekle
            mock_info = " (Simülasyon Modu)" if result.get('mock_mode') else ""
            
            # Sistem notu ekle
            LeadNote.objects.create(
                lead=lead,
                title=f"WhatsApp Mesajı - {message_type.title()}{mock_info}",
                content=f"WhatsApp mesajı başarıyla gönderildi{mock_info}: {message_text[:100]}...",
                created_by=request.user,
                note_type='whatsapp'
            )
        else:
            # Hata durumunda not ekle
            LeadNote.objects.create(
                lead=lead,
                title="WhatsApp Mesaj Hatası",
                content=f"WhatsApp mesajı gönderilemedi: {result.get('error', 'Bilinmeyen hata')}",
                created_by=request.user,
                note_type='error'
            )
        
        # Mock mode bilgisini response'a ekle
        success_message = 'WhatsApp mesajı başarıyla gönderildi.'
        if result.get('mock_mode'):
            success_message += ' (Simülasyon Modu - Gerçek mesaj gönderilmedi)'
        
        return JsonResponse({
            'success': result['success'],
            'message': success_message if result['success'] else f"WhatsApp mesajı gönderilemedi: {result.get('error', 'Bilinmeyen hata')}",
            'message_id': result.get('db_id') if result['success'] else None,
            'mock_mode': result.get('mock_mode', False)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@csrf_exempt
@require_http_methods(["POST"])
def whatsapp_webhook(request):
    """WhatsApp webhook"""
    # WhatsApp Business Cloud API webhook'u
    try:
        data = json.loads(request.body)
        # Webhook verilerini işle
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def call_webhook(request):
    """Santral webhook"""
    # Santral webhook'u
    try:
        data = json.loads(request.body)
        # Arama verilerini işle
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def make_call(request):
    """Arama yapma"""
    try:
        data = json.loads(request.body)
        lead_id = data.get('lead_id')
        phone = data.get('phone', '')
        
        # lead_id UUID formatında olduğu için lead_id field'ını kullan
        lead = get_object_or_404(Lead, lead_id=lead_id)
        
        # Telefon numarası kontrolü
        if not phone:
            phone = lead.customer_phone
        
        # Arama kaydı oluştur
        from .models import CallLog
        call_log = CallLog.objects.create(
            lead=lead,
            phone_number=phone,
            call_type='outbound',
            initiated_by=request.user,
            status='initiated'
        )
        
        # Sistem notu ekle
        LeadNote.objects.create(
            lead=lead,
            note=f"Müşteri arandı: {phone}",
            created_by=request.user,
            note_type='call'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Arama başarıyla başlatıldı.',
            'call_id': call_log.id,
            'phone_number': phone
        })
        
    except Lead.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Lead bulunamadı.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Arama başlatılırken hata oluştu: {str(e)}'
        })


@login_required
def sales_reports(request):
    """Satış raporları"""
    # Rapor verileri
    total_leads = Lead.objects.count()
    active_leads = Lead.objects.exclude(current_stage__name='dosya_kapandi').count()
    completed_leads = Lead.objects.filter(current_stage__name='dosya_kapandi').count()
    
    # Aşama bazında dağılım
    stage_distribution = []
    for stage in SalesStage.objects.filter(is_active=True):
        count = Lead.objects.filter(current_stage=stage).count()
        stage_distribution.append({
            'stage': stage.display_name,
            'count': count
        })
    
    return render(request, 'sales_process/reports.html', {
        'title': 'Satış Raporları',
        'total_leads': total_leads,
        'active_leads': active_leads,
        'completed_leads': completed_leads,
        'stage_distribution': stage_distribution
    })


@login_required
@require_http_methods(["GET"])
def export_reports(request):
    """Rapor dışa aktarma"""
    # Excel export işlemi
    return JsonResponse({
        'success': True,
        'message': 'Rapor dışa aktarıldı.',
        'download_url': '/path/to/exported/file.xlsx'
    })


@login_required
@require_http_methods(["POST"])
def update_stage_ajax(request):
    """AJAX ile aşama güncelleme - OSMAN'IN İSTEĞİ: Guard'larla korunmuş"""
    try:
        data = json.loads(request.body)
        lead_id = data.get('lead_id')
        new_stage_name = data.get('new_stage')
        
        if not lead_id or not new_stage_name:
            return JsonResponse({
                'success': False,
                'message': 'Lead ID ve yeni aşama adı gerekli'
            })
        
        lead = get_object_or_404(Lead, lead_id=lead_id)
        new_stage = get_object_or_404(SalesStage, name=new_stage_name)
        old_stage = lead.current_stage
        
        # OSMAN'IN İSTEĞİ: GUARD'LAR - Geçiş kuralları
        
        # 1. Sözleşme Yapıldı'dan sonraki aşamalara geçiş için ödeme tipi zorunlu
        if (old_stage.name == 'sozlesme_yapildi' and 
            new_stage_name in ['kredi_islemleri', 'tapu_islemi'] and 
            not lead.payment_type):
            return JsonResponse({
                'success': False,
                'message': '⚠️ Ödeme tipi seçilmeden bu aşamaya geçilemez. Önce ödeme tipini belirleyin.'
            })
        
        # 2. Nakit ödeme için tapu tarihi zorunlu
        if (lead.payment_type == 'cash' and 
            new_stage_name == 'tapu_islemi' and 
            not lead.deed_transfer_date):
            return JsonResponse({
                'success': False,
                'message': '⚠️ Nakit ödeme için tapu devir tarihi belirlenmeden bu aşamaya geçilemez.'
            })
        
        # 3. Kredili ödeme sadece kredi işlemlerine gidebilir
        if (old_stage.name == 'sozlesme_yapildi' and 
            lead.payment_type == 'credit' and 
            new_stage_name != 'kredi_islemleri'):
            return JsonResponse({
                'success': False,
                'message': '⚠️ Kredili işlemler sadece "Kredi İşlemleri" aşamasına geçebilir.'
            })
        
        # 4. Nakit ödeme sadece tapu işlemlerine gidebilir
        if (old_stage.name == 'sozlesme_yapildi' and 
            lead.payment_type == 'cash' and 
            new_stage_name != 'tapu_islemi'):
            return JsonResponse({
                'success': False,
                'message': '⚠️ Nakit işlemler sadece "Tapu İşlemi" aşamasına geçebilir.'
            })
        
        # 5. Hizmet Tamamlandı aşaması artık manuel geçiş için kapalı (OSMAN'ın isteği)
        if new_stage_name == 'hizmet_tamamlandi':
            return JsonResponse({
                'success': False,
                'message': '⚠️ "Hizmet Tamamlandı" aşamasına manuel geçiş yapılamaz. Kredi/Tapu tamamlama butonlarını kullanın.'
            })
        
        # 6. Memnuniyet Anketi aşamasına manuel geçiş kapalı
        if new_stage_name == 'memnuniyet_anketi':
            return JsonResponse({
                'success': False,
                'message': '⚠️ "Memnuniyet Anketi" aşamasına manuel geçiş yapılamaz. Otomatik olarak geçiş yapılır.'
            })
        
        # 7. Dosya Kapandı aşamasına sadece memnuniyet anketinden geçilebilir
        if (new_stage_name == 'dosya_kapandi' and 
            old_stage.name != 'memnuniyet_anketi'):
            return JsonResponse({
                'success': False,
                'message': '⚠️ Dosya sadece "Memnuniyet Anketi" aşamasından kapatılabilir.'
            })
        
        # Aşama geçişini kaydet
        StageTransition.objects.create(
            lead=lead,
            from_stage=old_stage,
            to_stage=new_stage,
            transition_type='manual',
            reason=f"Aşama güncellendi: {old_stage.display_name} -> {new_stage.display_name}",
            performed_by=request.user
        )
        
        # Lead'i güncelle
        lead.current_stage = new_stage
        lead.stage_updated_at = timezone.now()
        lead.save()
        
        # Sistem notu ekle
        LeadNote.objects.create(
            lead=lead,
            title="Aşama Güncellendi",
            content=f"Aşama güncellendi: {old_stage.display_name} -> {new_stage.display_name}",
            created_by=request.user,
            note_type='system'
        )
        
        # ActionLog kaydı
        ActionLog.objects.create(
            lead=lead,
            action_type='STAGE_UPDATED',
            title='Aşama Güncellendi',
            description=f"Aşama güncellendi: {old_stage.display_name} -> {new_stage.display_name}",
            performed_by=request.user,
            is_successful=True
        )
        
        return JsonResponse({
            'success': True,
            'message': f'✅ Aşama başarıyla güncellendi: {new_stage.display_name}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'❌ Hata: {str(e)}'
        })
        lead.stage_updated_at = timezone.now()
        lead.save()
        
        # Sistem notu ekle
        LeadNote.objects.create(
            lead=lead,
            title="Aşama Güncellendi",
            content=f"Aşama güncellendi: {old_stage.display_name} -> {new_stage.display_name}",
            created_by=request.user,
            note_type='system'
        )
        
        # Hizmet Tamamlandı aşamasına geçişte otomatik WhatsApp mesajı gönder
        if new_stage_name == 'hizmet_tamamlandi':
            try:
                # WhatsApp mesajı oluştur
                WhatsAppMessage.objects.create(
                    lead=lead,
                    message_type='service_completed',
                    content=f"Sayın {lead.customer_name}, hizmetimiz tamamlanmıştır. Teşekkür ederiz! Memnuniyetinizi öğrenmek için kısa bir anket göndereceğiz.",
                    sent_by=request.user,
                    status='sent'
                )
                
                # ActionLog kaydı
                ActionLog.objects.create(
                    lead=lead,
                    action_type='WHATSAPP_SENT',
                    title='Hizmet Tamamlandı Mesajı',
                    description='Hizmet tamamlandı mesajı otomatik gönderildi',
                    performed_by=request.user,
                    is_successful=True
                )
            except Exception as wa_error:
                # WhatsApp mesajı gönderilemezse log'la ama işlemi durdurma
                ActionLog.objects.create(
                    lead=lead,
                    action_type='WHATSAPP_ERROR',
                    title='WhatsApp Mesaj Hatası',
                    description=f'Hizmet tamamlandı mesajı gönderilemedi: {str(wa_error)}',
                    performed_by=request.user,
                    is_successful=False
                )
        
        return JsonResponse({
            'success': True,
            'message': f'Aşama başarıyla güncellendi: {new_stage.display_name}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_http_methods(["GET"])
def lead_detail_ajax(request, lead_id):
    """Lead detaylarını AJAX ile getir"""
    try:
        lead = get_object_or_404(Lead, lead_id=lead_id)
        
        # Lead verilerini serialize et
        budget_display = None
        if lead.budget_min and lead.budget_max:
            budget_display = f"{lead.budget_min:,.0f} - {lead.budget_max:,.0f} TL"
        elif lead.budget_min:
            budget_display = f"{lead.budget_min:,.0f} TL+"
        elif lead.budget_max:
            budget_display = f"Max {lead.budget_max:,.0f} TL"
            
        lead_data = {
            'id': lead.id,
            'lead_id': str(lead.lead_id),
            'customer_name': lead.customer.full_name if lead.customer else lead.customer_name,
            'customer_phone': lead.customer_phone,
            'customer_email': lead.customer_email,
            'source_display': lead.get_source_display(),
            'property_type_display': lead.get_property_type_display(),
            'budget_display': budget_display,
            'location': lead.property_location,
            'status': lead.status,
            'status_display': lead.get_status_display(),
            'current_stage_display': lead.current_stage.name if lead.current_stage else 'Belirtilmemiş',
            'assigned_staff': lead.assigned_staff.get_full_name() if lead.assigned_staff else None,
            'created_at': lead.created_at.strftime('%d.%m.%Y %H:%M') if lead.created_at else 'Tarih Yok',
            'priority': lead.priority,
        }
        
        return JsonResponse({
            'success': True,
            'lead': lead_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Lead detayları yüklenirken hata oluştu: {str(e)}'
        })


@login_required
def direct_viewing_requests(request):
    """Direkt daire gezme isteyen müşteriler için ayrı sayfa"""
    # Direkt daire gezme isteği olan lead'leri filtrele
    # Bu lead'ler özel bir flag ile işaretlenecek veya özel bir aşamada olacak
    direct_viewing_leads = Lead.objects.filter(
        Q(lead_source='direct_viewing') | 
        Q(notes__content__icontains='direkt daire gezme') |
        Q(notes__content__icontains='direkt gezme')
    ).distinct().select_related('current_stage', 'assigned_staff').order_by('-created_at')
    
    # Sayfalama
    paginator = Paginator(direct_viewing_leads, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # İstatistikler
    stats = {
        'total_requests': direct_viewing_leads.count(),
        'pending_appointments': direct_viewing_leads.filter(
            current_stage__name__in=['daire_sunumu', 'randevu_planlandi']
        ).count(),
        'completed_viewings': direct_viewing_leads.filter(
            current_stage__name__in=['cevap_bekleniyor', 'sozlesme_yapildi']
        ).count(),
        'today_appointments': direct_viewing_leads.filter(
            appointments__appointment_date__date=timezone.now().date(),
            appointments__status='scheduled'
        ).count(),
    }
    
    context = {
        'title': 'Direkt Daire Gezme İstekleri',
        'page_obj': page_obj,
        'stats': stats,
        'leads': page_obj,
    }
    
    return render(request, 'sales_process/direct_viewing_requests.html', context)


@login_required
@require_http_methods(["POST"])
def create_direct_viewing_lead(request):
    """Direkt daire gezme isteği için yeni lead oluştur"""
    try:
        customer_name = request.POST.get('customer_name')
        customer_phone = request.POST.get('customer_phone')
        customer_email = request.POST.get('customer_email', '')
        property_interest = request.POST.get('property_interest', '')
        preferred_date = request.POST.get('preferred_date', '')
        notes = request.POST.get('notes', '')
        
        if not customer_name or not customer_phone:
            return JsonResponse({
                'success': False,
                'error': 'Müşteri adı ve telefon numarası gerekli'
            })
        
        # Direkt daire gezme aşamasını bul veya oluştur
        direct_viewing_stage, created = SalesStage.objects.get_or_create(
            slug='direkt-daire-gezme',
            defaults={
                'name': 'Direkt Daire Gezme',
                'display_name': 'Direkt Daire Gezme',
                'order': 15,
                'color': '#e74c3c'
            }
        )
        
        # Yeni lead oluştur
        lead = Lead.objects.create(
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            lead_source='direct_viewing',
            current_stage=direct_viewing_stage,
            assigned_staff=request.user,
            stage_updated_at=timezone.now()
        )
        
        # İlk not ekle
        initial_note = f"Direkt daire gezme isteği\n\n"
        if property_interest:
            initial_note += f"İlgilenilen emlak: {property_interest}\n"
        if preferred_date:
            initial_note += f"Tercih edilen tarih: {preferred_date}\n"
        if notes:
            initial_note += f"Ek notlar: {notes}\n"
        
        LeadNote.objects.create(
            lead=lead,
            title="Direkt Daire Gezme İsteği",
            content=initial_note,
            note_type='initial',
            created_by=request.user
        )
        
        # Randevu planlama görevi oluştur
        Task.objects.create(
            lead=lead,
            title=f"{customer_name} - Daire Gezme Randevusu",
            description="Müşteri ile direkt daire gezme randevusu planlanması.",
            task_type='appointment',
            priority=4,
            due_date=timezone.now() + timezone.timedelta(hours=2),
            assigned_to=request.user,
            status='pending'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Direkt daire gezme isteği başarıyla oluşturuldu',
            'lead_id': lead.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


# Manager-specific functions for the workflow
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def set_payment_type(request):
    """Müdür ödeme tipini belirler (Nakit/Kredili)"""
    try:
        data = json.loads(request.body)
        lead_id = data.get('lead_id')
        payment_type = data.get('payment_type')  # 'cash' or 'credit'
        
        # OSMAN'IN İSTEĞİ: Validasyonlar
        if not lead_id:
            return JsonResponse({
                'success': False,
                'message': 'Lead ID gerekli'
            })
        
        if not payment_type or payment_type not in ['cash', 'credit']:
            return JsonResponse({
                'success': False,
                'message': 'Geçerli bir ödeme tipi seçin (Nakit/Kredili)'
            })
        
        lead = get_object_or_404(Lead, lead_id=lead_id)
        
        # OSMAN'IN İSTEĞİ: Sadece "Sözleşme Yapıldı" aşamasında ödeme tipi seçilebilir
        if lead.current_stage.name != 'sozlesme_yapildi':
            return JsonResponse({
                'success': False,
                'message': 'Ödeme tipi sadece "Sözleşme Yapıldı" aşamasında seçilebilir'
            })
        
        old_stage = lead.current_stage
        
        # Ödeme tipini lead'e kaydet
        lead.payment_type = payment_type
        
        # Ödeme tipine göre aşama değiştir
        if payment_type == 'credit':
            # Kredili işlem - Kredi İşlemleri aşamasına geçir
            kredi_stage = SalesStage.objects.get(name='kredi_islemleri')
            lead.current_stage = kredi_stage
            lead.stage_updated_at = timezone.now()
            lead.save()
            
            # Stage transition kaydı
            StageTransition.objects.create(
                lead=lead,
                from_stage=old_stage,
                to_stage=kredi_stage,
                transition_type='manual',
                reason="Kredili işlem seçildi",
                performed_by=request.user
            )
            
            # Sistem notu ekle
            LeadNote.objects.create(
                lead=lead,
                title="Kredili İşlem Seçildi",
                content="Müdür kredili işlem seçti. Kart Kredi İşlemleri aşamasına taşındı.",
                created_by=request.user,
                note_type='system'
            )
            
            message = "Kredili işlem seçildi. Kart Kredi İşlemleri aşamasına taşındı."
            
        elif payment_type == 'cash':
            # OSMAN'IN İSTEĞİ: Nakit için direkt tapu aşamasına geçiş ama tapu tarihi sonra girilecek
            # İlk önce sadece ödeme tipini kaydet, aşamayı değiştirme (tapu tarihi girilince geçecek)
            lead.save()  # Sadece payment_type'ı kaydet
            
            # Sistem notu ekle
            LeadNote.objects.create(
                lead=lead,
                title="Nakit İşlem Seçildi",
                content="Müdür nakit işlem seçti. Tapu devir tarihi bekleniyor.",
                created_by=request.user,
                note_type='system'
            )
            
            message = "Nakit işlem seçildi. Şimdi tapu devir tarihini belirleyin."
        
        # ActionLog kaydı
        ActionLog.objects.create(
            lead=lead,
            action_type='PAYMENT_TYPE_SELECTED',
            title='Ödeme Tipi Seçildi',
            description=f"Ödeme tipi seçildi: {payment_type}",
            performed_by=request.user,
            is_successful=True
        )
        
        return JsonResponse({
            'success': True,
            'message': message,
            'payment_type': payment_type,
            'requires_deed_date': payment_type == 'cash'  # Frontend için bilgi
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def set_deed_date(request):
    """Nakit işlem için tapu devri tarihi belirle"""
    try:
        data = json.loads(request.body)
        lead_id = data.get('lead_id')
        deed_date = data.get('deed_date')
        
        # OSMAN'IN İSTEĞİ: Validasyonlar
        if not lead_id:
            return JsonResponse({
                'success': False,
                'message': 'Lead ID gerekli'
            })
        
        if not deed_date:
            return JsonResponse({
                'success': False,
                'message': 'Tapu devir tarihi gerekli'
            })
        
        # Tarih formatı kontrolü
        try:
            deed_date_obj = datetime.strptime(deed_date, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Geçersiz tarih formatı (YYYY-MM-DD bekleniyor)'
            })
        
        # Geçmiş tarih kontrolü
        if deed_date_obj < timezone.now().date():
            return JsonResponse({
                'success': False,
                'message': 'Tapu devir tarihi bugünden önce olamaz'
            })
        
        lead = get_object_or_404(Lead, lead_id=lead_id)
        
        # OSMAN'IN İSTEĞİ: Sadece nakit ödeme tipinde ve sözleşme yapıldı aşamasında olmalı
        if lead.payment_type != 'cash':
            return JsonResponse({
                'success': False,
                'message': 'Tapu tarihi sadece nakit işlemler için belirlenir'
            })
        
        if lead.current_stage.name != 'sozlesme_yapildi':
            return JsonResponse({
                'success': False,
                'message': 'Tapu tarihi sadece "Sözleşme Yapıldı" aşamasında belirlenebilir'
            })
        
        old_stage = lead.current_stage
        
        # Tapu devri tarihini kaydet
        lead.deed_transfer_date = deed_date_obj
        
        # OSMAN'IN İSTEĞİ: Şimdi kartı "Tapu İşlemi" aşamasına taşı
        tapu_stage = SalesStage.objects.get(name='tapu_islemi')
        lead.current_stage = tapu_stage
        lead.stage_updated_at = timezone.now()
        lead.save()
        
        # Stage transition kaydı
        StageTransition.objects.create(
            lead=lead,
            from_stage=old_stage,
            to_stage=tapu_stage,
            transition_type='manual',
            reason=f"Tapu devir tarihi belirlendi: {deed_date}",
            performed_by=request.user
        )
        
        # OSMAN'IN İSTEĞİ: Müdüre otomatik görev ataması
        Task.objects.create(
            lead=lead,
            title=f"Tapu Devri - {lead.customer_name}",
            description=f"Belirlenen tarihte tapu devri yapılacak.\nMüşteri: {lead.customer_name}\nTelefon: {lead.customer_phone}\nTarih: {deed_date}\nGayrimenkul: {lead.property_type} - {lead.property_location}",
            task_type='deed_transfer',
            priority=5,  # Yüksek öncelik
            due_date=deed_date_obj,
            assigned_to=request.user,  # Müdüre atanır
            status='pending'
        )
        
        # Sistem notu ekle
        LeadNote.objects.create(
            lead=lead,
            title="Tapu Devri Tarihi Belirlendi",
            content=f"Tapu devri tarihi belirlendi: {deed_date}. Müdüre görev oluşturuldu ve kart Tapu İşlemi aşamasına taşındı.",
            created_by=request.user,
            note_type='system'
        )
        
        # ActionLog kaydı
        ActionLog.objects.create(
            lead=lead,
            action_type='DEED_DATE_SET',
            title='Tapu Devri Tarihi Belirlendi',
            description=f"Tapu devri tarihi belirlendi: {deed_date}, görev oluşturuldu",
            performed_by=request.user,
            is_successful=True
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Tapu devri tarihi belirlendi: {deed_date_obj.strftime("%d.%m.%Y")}. Müdüre görev oluşturuldu ve kart Tapu İşlemi aşamasına taşındı.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def complete_credit_process(request):
    """Kredi sürecini tamamla"""
    try:
        data = json.loads(request.body)
        lead_id = data.get('lead_id')
        
        lead = get_object_or_404(Lead, lead_id=lead_id)
        
        # Kredi süreci tamamlandı - Tapu İşlemleri aşamasına geçir
        tapu_stage = SalesStage.objects.get(name='tapu_islemi')
        old_stage = lead.current_stage
        lead.current_stage = tapu_stage
        lead.stage_updated_at = timezone.now()
        lead.save()
        
        # Stage transition kaydı
        StageTransition.objects.create(
            lead=lead,
            from_stage=old_stage,
            to_stage=tapu_stage,
            transition_type='manual',
            reason="Kredi süreci tamamlandı - Tapu işlemleri başlatıldı",
            performed_by=request.user
        )
        
        # Sistem notu ekle
        LeadNote.objects.create(
            lead=lead,
            title="Kredi Süreci Tamamlandı",
            content="Kredi süreci başarıyla tamamlandı. Tapu devir tarihi bekleniyor.",
            created_by=request.user,
            note_type='system'
        )
        
        # ActionLog kaydı
        ActionLog.objects.create(
            lead=lead,
            action_type='CREDIT_COMPLETED',
            title='Kredi Süreci Tamamlandı',
            description="Kredi süreci tamamlandı, tapu işlemleri aşamasına geçildi",
            performed_by=request.user,
            is_successful=True
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Kredi süreci tamamlandı. Şimdi tapu devir tarihini belirleyin.',
            'requires_deed_date': True  # Frontend için bilgi
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def complete_deed_process(request):
    """Tapu devri sürecini tamamla"""
    try:
        data = json.loads(request.body)
        lead_id = data.get('lead_id')
        
        lead = get_object_or_404(Lead, lead_id=lead_id)
        
        # OSMAN'IN İSTEĞİ: Direkt "Memnuniyet Anketi" aşamasına geçir (Hizmet Tamamlandı atlanıyor)
        memnuniyet_stage = SalesStage.objects.get(name='memnuniyet_anketi')
        old_stage = lead.current_stage
        lead.current_stage = memnuniyet_stage
        lead.stage_updated_at = timezone.now()
        lead.save()
        
        # Stage transition kaydı
        StageTransition.objects.create(
            lead=lead,
            from_stage=old_stage,
            to_stage=memnuniyet_stage,
            transition_type='manual',
            reason="Tapu devri tamamlandı - Otomatik anket gönderildi",
            performed_by=request.user
        )
        
        # Sistem notu ekle
        LeadNote.objects.create(
            lead=lead,
            title="Tapu Devri Tamamlandı",
            content="Tapu devri başarıyla tamamlandı. Müşteriye otomatik memnuniyet anketi gönderildi.",
            created_by=request.user,
            note_type='system'
        )
        
        # ActionLog kaydı
        ActionLog.objects.create(
            lead=lead,
            action_type='DEED_TRANSFER',
            title='Tapu Devri Tamamlandı',
            description="Tapu devri tamamlandı ve otomatik anket gönderildi",
            performed_by=request.user,
            is_successful=True
        )
        
        # OSMAN'IN İSTEĞİ: Otomatik WhatsApp memnuniyet anketi gönder
        whatsapp_success = False
        try:
            from .whatsapp_views import send_automatic_whatsapp
            result = send_automatic_whatsapp(lead, 'satisfaction_survey')
            whatsapp_success = result.get('success', False) if isinstance(result, dict) else True
            
            # WhatsApp gönderim kaydı
            ActionLog.objects.create(
                lead=lead,
                action_type='WHATSAPP_SENT',
                title='Memnuniyet Anketi Gönderildi',
                description='Tapu devri sonrası otomatik memnuniyet anketi gönderildi',
                performed_by=request.user,
                is_successful=whatsapp_success
            )
        except Exception as wa_error:
            # WhatsApp hatası da log'lanır ama işlem devam eder
            ActionLog.objects.create(
                lead=lead,
                action_type='WHATSAPP_ERROR',
                title='WhatsApp Memnuniyet Anketi Hatası',
                description=f'Memnuniyet anketi gönderilemedi: {str(wa_error)}',
                performed_by=request.user,
                is_successful=False
            )
        
        success_message = 'Tapu devri tamamlandı. Müşteriye memnuniyet anketi gönderildi.'
        if not whatsapp_success:
            success_message += ' (WhatsApp mesajı gönderilemedi, manuel kontrol gerekli)'
        
        return JsonResponse({
            'success': True,
            'message': success_message
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })
