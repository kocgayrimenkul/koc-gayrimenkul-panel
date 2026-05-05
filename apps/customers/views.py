# -*- encoding: utf-8 -*-
"""Musteri Detay View"""
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import (
    Customer,
    Neighborhood, CustomerNote, CustomerTask, CustomerWorkflow,
    CustomerOffer, CustomerDemand, CustomerSmsLog, CustomerWhatsappLog,
    CustomerActivity, CustomerReminder,
)
from apps.portfolio.models import Property


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(
        Customer.objects.select_related('consultant', 'neighborhood', 'real_estate', 'financial_info'),
        pk=pk,
    )

    notes_qs = customer.customer_notes.select_related('user').all()
    tasks_qs = customer.tasks.select_related('assigned_to').all()
    notes_stats = {
        'total': notes_qs.count() + tasks_qs.count(),
        'reminders': notes_qs.filter(note_type='hatirlatici').count(),
        'completed': tasks_qs.filter(status='tamamlandi').count(),
        'crm_comments': notes_qs.filter(note_type='yorum').count(),
        'tasks': tasks_qs.count(),
    }
    notes = list(notes_qs[:50])
    tasks = list(tasks_qs[:50])

    workflows_qs = customer.workflows.select_related('created_by', 'related_property').all()
    workflow_stats = {
        'total': workflows_qs.count(),
        'active': workflows_qs.filter(status='aktif').count(),
        'completed': workflows_qs.filter(status='tamamlandi').count(),
        'overdue': workflows_qs.filter(status='gecikmis').count(),
        'archived': workflows_qs.filter(status='arsivlendi').count(),
    }
    workflows = list(workflows_qs[:50])

    offers_qs = customer.offers.select_related('related_property', 'related_property__neighborhood', 'created_by').all()
    offer_stats = {
        'total': offers_qs.count(),
        'pending': offers_qs.filter(status='bekliyor').count(),
        'accepted': offers_qs.filter(status='kabul').count(),
        'rejected': offers_qs.filter(status='red').count(),
        'expired': offers_qs.filter(status='suresi_doldu').count(),
    }
    offers = list(offers_qs[:50])

    demands_qs = customer.demands.all()
    demand_stats = {
        'total': demands_qs.count(),
        'active': demands_qs.filter(status='aktif').count(),
        'passive': demands_qs.filter(status='pasif').count(),
        'completed': demands_qs.filter(status='tamamlandi').count(),
        'cancelled': demands_qs.filter(status='iptal').count(),
    }
    demands = list(demands_qs)

    call_logs_qs = customer.call_logs.select_related('user').all()
    sms_logs_qs = customer.sms_logs.select_related('user').all()
    whatsapp_logs_qs = customer.whatsapp_logs.select_related('user').all()

    call_stats = {
        'total': call_logs_qs.count(),
        'answered': call_logs_qs.filter(status__in=['answered', 'completed']).count(),
        'missed': call_logs_qs.filter(status='missed').count(),
    }
    sms_stats = {
        'total': sms_logs_qs.count(),
        'sent': sms_logs_qs.filter(status='gonderildi').count(),
        'failed': sms_logs_qs.filter(status='basarisiz').count(),
    }
    wa_stats = {
        'total': whatsapp_logs_qs.count(),
        'sent': whatsapp_logs_qs.filter(status='gonderildi').count(),
        'failed': whatsapp_logs_qs.filter(status='basarisiz').count(),
    }
    action_stats = {
        'total': tasks_qs.count(),
        'open': tasks_qs.filter(status='acik').count(),
        'completed': tasks_qs.filter(status='tamamlandi').count(),
    }

    call_logs = list(call_logs_qs[:20])
    sms_logs = list(sms_logs_qs[:20])
    whatsapp_logs = list(whatsapp_logs_qs[:20])
    activities = list(customer.activities.select_related('user').all()[:50])
    available_properties = Property.objects.filter(is_active=True).order_by('-created_at')[:100]

    context = {
        'customer': customer,
        'notes': notes, 'tasks': tasks, 'notes_stats': notes_stats,
        'workflows': workflows, 'workflow_stats': workflow_stats,
        'offers': offers, 'offer_stats': offer_stats,
        'demands': demands, 'demand_stats': demand_stats,
        'call_logs': call_logs, 'sms_logs': sms_logs, 'whatsapp_logs': whatsapp_logs,
        'call_stats': call_stats, 'sms_stats': sms_stats, 'wa_stats': wa_stats, 'action_stats': action_stats,
        'activities': activities,
        'available_properties': available_properties,
        'workflow_type_choices': CustomerWorkflow.WORKFLOW_TYPE_CHOICES,
        'priority_choices': CustomerWorkflow.PRIORITY_CHOICES,
        'currency_choices': CustomerOffer.CURRENCY_CHOICES,
    }
    return render(request, 'customers/customer_detail.html', context)


@login_required
@require_POST
def customer_workflow_create(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    title = request.POST.get('title', '').strip()
    if not title:
        messages.error(request, "Baslik zorunludur.")
        return redirect('customer_detail', pk=pk)
    CustomerWorkflow.objects.create(
        customer=customer, created_by=request.user, title=title,
        workflow_type=request.POST.get('workflow_type', 'diger'),
        priority=request.POST.get('priority', 'normal'),
        description=request.POST.get('description', '').strip(),
        due_date=request.POST.get('due_date') or None,
        related_property_id=request.POST.get('property_id') or None,
    )
    CustomerActivity.objects.create(customer=customer, user=request.user, activity_type='surec_baslatildi', source_label='Manuel', description=f"Surec baslatildi: {title}")
    messages.success(request, "Surec basariyla baslatildi.")
    return redirect('customer_detail', pk=pk)


@login_required
@require_POST
def customer_offer_create(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    property_id = request.POST.get('property_id')
    if not property_id:
        messages.error(request, "Portfoy secimi zorunludur.")
        return redirect('customer_detail', pk=pk)
    try:
        offer_price_decimal = float(request.POST.get('offer_price', '0'))
    except (TypeError, ValueError):
        messages.error(request, "Gecerli bir teklif fiyati giriniz.")
        return redirect('customer_detail', pk=pk)
    CustomerOffer.objects.create(
        customer=customer, related_property_id=property_id, created_by=request.user,
        title=request.POST.get('title', '').strip(),
        offer_price=offer_price_decimal,
        currency=request.POST.get('currency', 'TRY'),
        notes=request.POST.get('notes', '').strip(),
        matterport_url=request.POST.get('matterport_url', '').strip() or None,
    )
    CustomerActivity.objects.create(customer=customer, user=request.user, activity_type='teklif_olusturuldu', source_label='Manuel', description=f"Yeni teklif: {offer_price_decimal}")
    messages.success(request, "Teklif basariyla olusturuldu.")
    return redirect('customer_detail', pk=pk)


@login_required
@require_POST
def customer_note_create(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'success': False, 'error': 'Icerik zorunludur.'}, status=400)
    note = CustomerNote.objects.create(
        customer=customer, user=request.user, content=content,
        note_type=request.POST.get('note_type', 'not'),
        priority=request.POST.get('priority', 'normal'),
    )
    CustomerActivity.objects.create(customer=customer, user=request.user, activity_type='not_eklendi', source_label='Manuel', description=f"Not eklendi: {content[:60]}")
    return JsonResponse({'success': True, 'note': {'id': note.id, 'content': note.content, 'created_at': note.created_at.strftime('%d.%m.%Y %H:%M')}})


def customer_reminders_processor(request):
    if not request.user.is_authenticated:
        return {'customer_reminders': [], 'customer_reminders_count': 0}
    try:
        reminders = CustomerReminder.objects.filter(customer__consultant=request.user, is_read=False).select_related('customer')[:10]
        return {'customer_reminders': list(reminders), 'customer_reminders_count': reminders.count()}
    except Exception:
        return {'customer_reminders': [], 'customer_reminders_count': 0}


def _kullanici_tum_musterileri_gorebilir(user):
    """Yönetici, Santral veya Santral/Sekreter rolündeki kullanıcılar tüm müşterileri görebilir."""
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=['Yönetici', 'Santral', 'Santral/Sekreter']).exists()


@login_required
def customer_list(request):
    """Musteri listesi sayfasi"""
    qs = Customer.objects.select_related('consultant', 'neighborhood', 'real_estate').prefetch_related(
        'offers__related_property__neighborhood'
    ).all()

    # Danışman sadece kendi müşterilerini görsün
    sadece_kendisi = not _kullanici_tum_musterileri_gorebilir(request.user)
    if sadece_kendisi:
        qs = qs.filter(consultant=request.user)

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        qs = qs.filter(status=status_filter)

    meeting_filter = request.GET.get('meeting_status', '').strip()
    if meeting_filter:
        qs = qs.filter(meeting_status=meeting_filter)

    consultant_filter = request.GET.get('consultant', '').strip()
    if consultant_filter:
        qs = qs.filter(consultant_id=consultant_filter)

    source_filter = request.GET.get('source', '').strip()
    if source_filter:
        qs = qs.filter(source=source_filter)

    reminder_only = request.GET.get('reminder') == '1'
    if reminder_only:
        qs = qs.filter(reminder_date__lte=timezone.now().date())

    search_query = request.GET.get('q', '').strip()
    if search_query:
        qs = qs.filter(
            Q(full_name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(city__icontains=search_query)
        )

    qs = qs.order_by('-created_at')

    all_customers = Customer.objects.filter(consultant=request.user) if sadece_kendisi else Customer.objects.all()
    now = timezone.now()
    stats = {
        'total': all_customers.count(),
        'active': all_customers.filter(status='aktif').count(),
        'potential': all_customers.filter(status='potansiyel').count(),
        'this_month': all_customers.filter(created_at__year=now.year, created_at__month=now.month).count(),
    }

    qs = qs.annotate(offer_count=Count('offers'))

    page_size = int(request.GET.get('page_size', 20))
    paginator = Paginator(qs, page_size)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    User = get_user_model()
    consultants = User.objects.filter(customers__isnull=False).distinct().order_by('first_name', 'username')

    context = {
        'page_obj': page_obj,
        'customers': page_obj.object_list,
        'stats': stats,
        'consultants': consultants,
        'all_neighborhoods': Neighborhood.objects.all().order_by('name'),
        'all_properties': Property.objects.all()[:300],
        'status_choices': Customer.STATUS_CHOICES,
        'meeting_status_choices': Customer.MEETING_STATUS_CHOICES,
        'source_choices': Customer.SOURCE_CHOICES,
        'sadece_kendisi': sadece_kendisi,
        'current_filters': {
            'status': status_filter,
            'meeting_status': meeting_filter,
            'consultant': consultant_filter,
            'source': source_filter,
            'reminder': reminder_only,
            'q': search_query,
        },
    }
    return render(request, 'customers/customer_list_page.html', context)


from django.http import JsonResponse
from django.views.decorators.http import require_POST


@login_required
@require_POST
def customer_quick_update(request, pk):
    """AJAX: Listeden hizli alan guncelleme (danisman, arama durumu vb.)"""
    try:
        customer = Customer.objects.get(pk=pk)
    except Customer.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Musteri bulunamadi'}, status=404)

    field = request.POST.get('field', '').strip()
    value = request.POST.get('value', '').strip()

    ALLOWED_FIELDS = {
        'consultant': 'consultant_id',
        'meeting_status': 'meeting_status',
        'status': 'status',
    }

    if field not in ALLOWED_FIELDS:
        return JsonResponse({'success': False, 'error': 'Gecersiz alan'}, status=400)

    db_field = ALLOWED_FIELDS[field]

    try:
        if field == 'consultant':
            if value == '' or value == 'None':
                setattr(customer, db_field, None)
            else:
                setattr(customer, db_field, int(value))
        else:
            setattr(customer, db_field, value if value else None)

        customer.save(update_fields=[db_field, 'updated_at'])
        return JsonResponse({'success': True, 'field': field, 'value': value})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def customer_quick_create(request):
    """Liste sayfasindan hizli musteri olusturma"""
    full_name = request.POST.get('full_name', '').strip()
    phone = request.POST.get('phone', '').strip()
    email = request.POST.get('email', '').strip()
    customer_type = request.POST.get('customer_type', 'bireysel').strip()
    source = request.POST.get('source', '').strip()
    consultant_id = request.POST.get('consultant', '').strip()
    neighborhood_id = request.POST.get('neighborhood', '').strip()
    real_estate_id = request.POST.get('real_estate', '').strip()
    notes = request.POST.get('notes', '').strip()

    if not phone:
        return JsonResponse({'success': False, 'error': 'Telefon numarasi zorunludur'}, status=400)

    if Customer.objects.filter(phone=phone).exists():
        return JsonResponse({
            'success': False,
            'error': f'Bu telefon numarasina ({phone}) sahip bir musteri zaten var'
        }, status=400)

    try:
        customer = Customer(
            full_name=full_name if full_name else None,
            phone=phone,
            customer_type=customer_type,
            status='potansiyel',
            meeting_status='bekliyor',
        )
        if email:
            customer.email = email
        if source:
            customer.source = source
        if notes:
            customer.notes = notes
        if consultant_id:
            customer.consultant_id = int(consultant_id)
        if neighborhood_id:
            customer.neighborhood_id = int(neighborhood_id)
        if real_estate_id:
            customer.real_estate_id = int(real_estate_id)

        customer.save()

        return JsonResponse({
            'success': True,
            'customer_id': customer.pk,
            'message': f'{customer.display_name} basariyla kaydedildi.',
            'redirect': f'/{customer.pk}/'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def customer_reminders_view(request):
    from django.utils import timezone as tz
    from datetime import date as date_cls
    user = request.user
    bugun = date_cls.today()

    is_manager = user.is_superuser or user.has_role('Mudur') or user.has_role('Yonetici')

    qs = CustomerReminder.objects.select_related('customer__consultant')
    if not is_manager:
        qs = qs.filter(customer__consultant=user)

    filtre = request.GET.get('filtre', 'hepsi')
    if filtre == 'bugun':
        qs = qs.filter(reminder_date=bugun)
    elif filtre == 'yaklasan':
        qs = qs.filter(reminder_date__gt=bugun, is_sent=False)
    elif filtre == 'gecmis':
        qs = qs.filter(reminder_date__lt=bugun, is_sent=False)
    elif filtre == 'okunmamis':
        qs = qs.filter(is_read=False)

    qs = qs.order_by('reminder_date')

    bugun_sayisi = CustomerReminder.objects.filter(reminder_date=bugun, is_sent=False)
    if not is_manager:
        bugun_sayisi = bugun_sayisi.filter(customer__consultant=user)
    bugun_sayisi = bugun_sayisi.count()

    gecmis_sayisi = CustomerReminder.objects.filter(reminder_date__lt=bugun, is_sent=False)
    if not is_manager:
        gecmis_sayisi = gecmis_sayisi.filter(customer__consultant=user)
    gecmis_sayisi = gecmis_sayisi.count()

    return render(request, 'customers/hatirlatmalar.html', {
        'segment': 'musteri',
        'hatirlatmalar': qs,
        'filtre': filtre,
        'bugun': bugun,
        'bugun_sayisi': bugun_sayisi,
        'gecmis_sayisi': gecmis_sayisi,
        'is_manager': is_manager,
    })


# ─── MAHALLE YÖNETİMİ ──────────────────────────────────────────────

@login_required
def neighborhood_list(request):
    """Mahalle listesi ve yönetimi"""
    from .models import Neighborhood
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # Tüm danışmanlar (dropdown için)
    try:
        from apps.employees.models import EmployeeProfile
        consultants = User.objects.filter(
            employeeprofile__role__in=['consultant', 'bolge_uzmani', 'employee']
        ).order_by('first_name', 'last_name')
    except Exception:
        consultants = User.objects.filter(is_active=True).order_by('first_name', 'last_name')

    neighborhoods = Neighborhood.objects.select_related('consultant').order_by('district', 'name')

    # Filtre
    ilce_filter = request.GET.get('ilce', '').strip()
    danisman_filter = request.GET.get('danisman', '').strip()
    q = request.GET.get('q', '').strip()

    if ilce_filter:
        neighborhoods = neighborhoods.filter(district__iexact=ilce_filter)
    if danisman_filter:
        if danisman_filter == '__bos__':
            neighborhoods = neighborhoods.filter(consultant__isnull=True)
        else:
            neighborhoods = neighborhoods.filter(consultant_id=danisman_filter)
    if q:
        neighborhoods = neighborhoods.filter(name__icontains=q)

    ilceler = Neighborhood.objects.values_list('district', flat=True).exclude(district='').distinct().order_by('district')

    context = {
        'segment': 'mahalleler',
        'neighborhoods': neighborhoods,
        'consultants': consultants,
        'ilceler': ilceler,
        'ilce_filter': ilce_filter,
        'danisman_filter': danisman_filter,
        'q': q,
        'total': neighborhoods.count(),
        'bos_count': Neighborhood.objects.filter(consultant__isnull=True).count(),
    }
    return render(request, 'customers/neighborhood_list.html', context)


@login_required
def neighborhood_create(request):
    from .models import Neighborhood
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        district = request.POST.get('district', '').strip()
        consultant_id = request.POST.get('consultant_id') or None
        if name:
            obj, created = Neighborhood.objects.get_or_create(
                name=name,
                defaults={'district': district, 'consultant_id': consultant_id}
            )
            if not created:
                obj.district = district
                obj.consultant_id = consultant_id
                obj.save()
            messages.success(request, f"'{name}' mahallesi {'oluşturuldu' if created else 'güncellendi'}.")
        else:
            messages.error(request, 'Mahalle adı zorunludur.')
    return redirect('neighborhood_list')


@login_required
def neighborhood_update(request, pk):
    from .models import Neighborhood
    obj = get_object_or_404(Neighborhood, pk=pk)
    if request.method == 'POST':
        obj.name = request.POST.get('name', obj.name).strip()
        obj.district = request.POST.get('district', obj.district).strip()
        consultant_id = request.POST.get('consultant_id') or None
        obj.consultant_id = consultant_id
        obj.save()
        messages.success(request, f"'{obj.name}' güncellendi.")
    return redirect('neighborhood_list')


@login_required
def neighborhood_delete(request, pk):
    from .models import Neighborhood
    obj = get_object_or_404(Neighborhood, pk=pk)
    if request.method == 'POST':
        name = obj.name
        obj.delete()
        messages.success(request, f"'{name}' silindi.")
    return redirect('neighborhood_list')
