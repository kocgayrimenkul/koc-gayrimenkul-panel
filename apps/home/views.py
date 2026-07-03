# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Home Views (MySQL Uyumlu)
"""

from django import forms
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
from django.template.exceptions import TemplateDoesNotExist
from django.urls import reverse
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.contrib import messages
from datetime import timedelta, datetime, date
from django.db.models import Count, Q, Avg, Min, Max, Sum
import json

from apps.employees.models import EmployeeProfile
from apps.customers.models import Customer, Neighborhood, CustomerOffer, CustomerNote
from apps.portfolio.models import Property
from apps.presentation.models import Presentation
from apps.calendar.models import Event, TodoItem
from apps.fsbo.models import FSBO
from apps.home.dashboard_helpers import get_phase2_dashboard_context
try:
    from apps.sales_process.models import Lead
    HAS_LEAD = True
except Exception:
    HAS_LEAD = False


# Tarih filtresi için form
class DateFilterForm(forms.Form):
    date_filter = forms.ChoiceField(
        choices=[
            ('week', 'Hafta'),
            ('month', 'Ay'),
            ('quarter', 'Çeyrek'),
            ('year', 'Yıl')
        ],
        required=False
    )


def get_user_role(user):
    """Kullanıcının rolünü döndürür"""
    try:
        return user.employee_profile.role
    except (AttributeError, EmployeeProfile.DoesNotExist):
        return None


def get_date_range(date_filter):
    """Tarih filtresine göre başlangıç tarihini döndürür"""
    today = timezone.now().date()
    date_ranges = {
        'week': today - timedelta(days=7),
        'month': today - timedelta(days=30),
        'quarter': today - timedelta(days=90),
        'year': today - timedelta(days=365),
    }
    return date_ranges.get(date_filter, date_ranges['month'])


@login_required(login_url="/login/")
def index(request):
    """Ana dashboard view - MySQL Uyumlu Versiyon"""
    user = request.user
    role = get_user_role(user)
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    
    # Tarih filtresi
    form = DateFilterForm(request.GET)
    date_filter = 'month'
    if form.is_valid():
        date_filter = form.cleaned_data.get('date_filter', 'month')
    
    date_from = get_date_range(date_filter)

    # Context başlangıç
    context = {
        'segment': 'index',
        'role': role,
        'user': user,
        'today': today,
        'form': form,
        'date_filter': date_filter,
    }

    # Son 6 ay etiketleri (grafik için)
    last_months_labels = []
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30 * i)
        last_months_labels.append(month_date.strftime('%b'))
    context['last_months_labels'] = json.dumps(last_months_labels)

    # Ortak istatistikler
    context['total_properties'] = Property.objects.filter(is_active=True).count()
    context['total_customers'] = Customer.objects.count()

    # Lead sayısı
    if HAS_LEAD:
        lead_qs = Lead.objects.filter(status='active') if role == 'consultant' else Lead.objects.filter(status='active')
        if role == 'consultant':
            lead_qs = lead_qs.filter(assigned_staff=user)
        context['active_leads'] = lead_qs.count()
        # Satış hunisi (admin/manager için)
        context['leads_total'] = Lead.objects.count() if role != 'consultant' else Lead.objects.filter(assigned_staff=user).count()
        context['leads_active'] = Lead.objects.filter(status='active').count() if role != 'consultant' else Lead.objects.filter(assigned_staff=user, status='active').count()
    else:
        context['active_leads'] = 0
        context['leads_total'] = 0
        context['leads_active'] = 0

    # Bekleyen teklifler
    offer_qs = CustomerOffer.objects.filter(status='bekliyor')
    if role == 'consultant':
        offer_qs = offer_qs.filter(created_by=user)
    context['pending_offers'] = offer_qs.count()
    context['accepted_offers'] = CustomerOffer.objects.filter(status='kabul').count() if role != 'consultant' else CustomerOffer.objects.filter(created_by=user, status='kabul').count()

    # Açık görevler
    todo_qs = TodoItem.objects.filter(is_completed=False)
    if role == 'consultant':
        todo_qs = todo_qs.filter(Q(user=user) | Q(consultant=user))
    context['open_todos'] = todo_qs.count()

    # Bugünün yer gösterimler
    context['today_presentations'] = Presentation.objects.filter(
        presentation_date=today
    ).select_related('property', 'presenter').order_by('presentation_date')[:10]

    # Bugünün yapılacakları
    context['today_todos'] = TodoItem.objects.filter(
        is_completed=False,
        due_date=today
    ).order_by('due_date')[:10]

    # Müşteri notları (en güncel)
    context['upcoming_reminders'] = CustomerNote.objects.filter(
        note_type='hatirlatici',
    ).select_related('customer').order_by('-created_at')[:10]

    # Son 6 ay müşteri trendi (grafik)
    monthly_customers = []
    monthly_labels = []
    for i in range(5, -1, -1):
        month_date = today.replace(day=1) - timedelta(days=30*i)
        y, m = month_date.year, month_date.month
        cnt = Customer.objects.filter(created_at__year=y, created_at__month=m).count()
        monthly_customers.append(cnt)
        monthly_labels.append(month_date.strftime('%b %y'))
    context['monthly_customers'] = json.dumps(monthly_customers)
    context['monthly_labels'] = json.dumps(monthly_labels)

    # Rol bazlı veriler
    if role == 'consultant':
        # Müşteri verileri
        my_customers = Customer.objects.filter(consultant=user).select_related('neighborhood')
        context['my_customers'] = my_customers.order_by('-created_at')[:10]
        context['my_customer_count'] = my_customers.count()
        
        # Portföy verileri
        my_properties = Property.objects.filter(
            consultant=user, 
            is_active=True
        ).select_related('neighborhood')
        context['my_properties'] = my_properties.order_by('-created_at')[:10]
        context['my_property_count'] = my_properties.count()
        
        # Sunum verileri
        context['my_presentations'] = Presentation.objects.filter(
            presenter=user,
            presentation_date__gte=today
        ).select_related('property', 'presenter').order_by('presentation_date')[:5]
        
        # Sunum istatistikleri
        recent_presentations = Presentation.objects.filter(
            presenter=user,
            presentation_date__gte=date_from
        )
        context['completed_presentations'] = recent_presentations.filter(status='tamamlandi').count()
        context['pending_presentations'] = recent_presentations.filter(status='bekliyor').count()
        context['cancelled_presentations'] = recent_presentations.filter(status='iptal').count()
        context['total_presentations'] = recent_presentations.count()
        
        # Yapılacaklar listesi
        context['my_todos'] = TodoItem.objects.filter(
            Q(user=user) | Q(consultant=user),
            is_completed=False
        ).select_related('customer').order_by('due_date')[:10]
        
        # Bugünün ve yarının randevuları
        context['today_events'] = Event.objects.filter(
            consultant=user,
            start_time__date=today
        ).select_related('customer').order_by('start_time')[:5]
        
        context['tomorrow_events'] = Event.objects.filter(
            consultant=user,
            start_time__date=tomorrow
        ).select_related('customer').order_by('start_time')[:5]
        
        # FSBO kayıtları
        context['my_fsbos'] = FSBO.objects.filter(
            consultant=user
        ).order_by('-created_at')[:5]
        
        # Performans metrikleri
        all_todos = TodoItem.objects.filter(
            Q(user=user) | Q(consultant=user),
            created_at__gte=date_from
        )
        completed_todos = all_todos.filter(is_completed=True)
        context['todo_completion_rate'] = (
            round((completed_todos.count() / all_todos.count()) * 100) 
            if all_todos.count() > 0 else 0
        )
        
        all_customers = my_customers.filter(created_at__gte=date_from)
        positive_customers = all_customers.filter(meeting_status='olumlu')
        context['customer_conversion_rate'] = (
            round((positive_customers.count() / all_customers.count()) * 100) 
            if all_customers.count() > 0 else 0
        )

    elif role in ['admin', 'manager'] or user.is_superuser:
        # Aktif danışmanlar
        consultants = EmployeeProfile.objects.filter(
            role='consultant', 
            is_active=True
        ).select_related('user')
        context['consultants'] = consultants
        
        # Leaderboard hesaplaması
        consultant_data = []
        for consultant_profile in consultants:
            consultant = consultant_profile.user
            
            # Basit sayımlar
            presentations_count = Presentation.objects.filter(
                presenter=consultant, 
                presentation_date__gte=date_from
            ).count()
            
            completed_presentations = Presentation.objects.filter(
                presenter=consultant,
                presentation_date__gte=date_from,
                status='tamamlandi'
            ).count()
            
            customers_count = Customer.objects.filter(
                consultant=consultant, 
                created_at__gte=date_from
            ).count()
            
            positive_customers = Customer.objects.filter(
                consultant=consultant,
                created_at__gte=date_from,
                meeting_status='olumlu'
            ).count()
            
            properties_count = Property.objects.filter(
                consultant=consultant, 
                created_at__gte=date_from, 
                is_active=True
            ).count()
            
            # Performans skoru
            performance_score = 0
            
            if presentations_count > 0:
                completion_rate = (completed_presentations / presentations_count) * 100
                performance_score += completion_rate * 0.4
            
            if customers_count > 0:
                conversion_rate = (positive_customers / customers_count) * 100
                performance_score += conversion_rate * 0.3
            
            property_score = min(properties_count * 2, 100)
            performance_score += property_score * 0.3
            
            consultant_data.append({
                'name': consultant.get_full_name(),
                'performance_score': round(performance_score),
                'presentations': presentations_count,
                'customers': customers_count,
                'properties': properties_count,
            })
        
        consultant_data.sort(key=lambda x: x['performance_score'], reverse=True)
        context['leaderboard'] = consultant_data[:10]
        
        # Genel istatistikler
        context['total_completed_presentations'] = Presentation.objects.filter(
            status='tamamlandi',
            presentation_date__gte=date_from
        ).count()
        
        context['total_pending_presentations'] = Presentation.objects.filter(
            status='bekliyor',
            presentation_date__gte=date_from
        ).count()


    # ====== FAZ 2: Cagri istatistikleri + performans grafigi ======
    context.update(get_phase2_dashboard_context(user, today, date_from))

    return render(request, 'home/index.html', context)


@login_required(login_url="/login/")
def pages(request):
    """Genel sayfa yönlendirmesi"""
    context = {}
    try:
        load_template = request.path.split('/')[-1]
        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))
        context['segment'] = load_template
        html_template = loader.get_template('home/' + load_template)
        return HttpResponse(html_template.render(context, request))
    except TemplateDoesNotExist:
        html_template = loader.get_template('home/page-404.html')
        return HttpResponse(html_template.render(context, request))
    except Exception as e:
        html_template = loader.get_template('home/page-500.html')
        return HttpResponse(html_template.render(context, request))


@cache_page(60 * 5)
@login_required(login_url="/login/")
def consultant_performance(request):
    """Danışman performans API endpoint"""
    user = request.user
    date_filter = request.GET.get('date_filter', 'month')
    date_from = get_date_range(date_filter)
    
    metrics = {
        'total_customers': Customer.objects.filter(
            consultant=user, 
            created_at__gte=date_from
        ).count(),
        'total_presentations': Presentation.objects.filter(
            presenter=user,
            presentation_date__gte=date_from
        ).count(),
        'completed_presentations': Presentation.objects.filter(
            presenter=user,
            presentation_date__gte=date_from,
            status='tamamlandi'
        ).count(),
        'positive_customers': Customer.objects.filter(
            consultant=user,
            created_at__gte=date_from,
            meeting_status='olumlu'
        ).count(),
    }
    
    return JsonResponse({'metrics': metrics})


@cache_page(60 * 5)
@login_required(login_url="/login/")
def neighborhood_analytics(request):
    """Mahalle analitikleri"""
    user = request.user
    role = get_user_role(user)
    
    if role not in ['admin', 'manager'] and not user.is_superuser:
        return JsonResponse({'error': 'Yetkisiz erişim'}, status=403)
    
    date_filter = request.GET.get('date_filter', 'month')
    date_from = get_date_range(date_filter)
    today = timezone.now().date()
    
    neighborhoods = Neighborhood.objects.all()
    neighborhood_data = []
    
    for neighborhood in neighborhoods:
        properties = Property.objects.filter(neighborhood=neighborhood, is_active=True)
        properties_count = properties.count()
        customers_count = Customer.objects.filter(neighborhood=neighborhood).count()
        
        if properties_count > 0 or customers_count > 0:
            presentations = Presentation.objects.filter(
                property__neighborhood=neighborhood,
                presentation_date__gte=date_from
            )
            presentations_count = presentations.count()
            completed_presentations = presentations.filter(status='tamamlandi').count()
            
            # Fiyat istatistikleri
            avg_price = properties.aggregate(Avg('price'))['price__avg'] or 0
            min_price = properties.aggregate(Min('price'))['price__min'] or 0
            max_price = properties.aggregate(Max('price'))['price__max'] or 0
            
            for_sale = properties.filter(status='satilik').count()
            for_rent = properties.filter(status='kiralik').count()
            
            # Ortalama piyasada kalma süresi
            total_days = 0
            for prop in properties:
                if hasattr(prop, 'listing_date'):
                    total_days += (today - prop.listing_date).days
            avg_days_on_market = round(total_days / properties_count) if properties_count > 0 else 0
            
            success_rate = round((completed_presentations / presentations_count) * 100) if presentations_count > 0 else 0
            
            neighborhood_data.append({
                'id': neighborhood.id,
                'name': neighborhood.name,
                'consultant': (
                    neighborhood.consultant.get_full_name() 
                    if hasattr(neighborhood, 'consultant') and neighborhood.consultant 
                    else "Atanmamış"
                ),
                'properties_count': properties_count,
                'customers_count': customers_count,
                'presentations_count': presentations_count,
                'completed_presentations': completed_presentations,
                'avg_price': int(avg_price),
                'min_price': int(min_price),
                'max_price': int(max_price),
                'for_sale': for_sale,
                'for_rent': for_rent,
                'avg_days_on_market': avg_days_on_market,
                'success_rate': success_rate
            })
    
    neighborhood_data.sort(key=lambda x: x['properties_count'], reverse=True)
    return JsonResponse({'neighborhoods': neighborhood_data})


@login_required(login_url="/login/")
def map_view(request):
    """Harita görünümü"""
    context = {'segment': 'map'}
    return render(request, 'home/map.html', context)


@login_required(login_url="/login/")
def dashboard_stats_api(request):
    """Dashboard için API endpoint"""
    user = request.user
    role = get_user_role(user)
    
    stats = {
        'user': {
            'name': user.get_full_name(),
            'role': role,
        }
    }
    
    if role == 'consultant':
        stats['consultant'] = {
            'customers': Customer.objects.filter(consultant=user).count(),
            'properties': Property.objects.filter(consultant=user, is_active=True).count(),
            'presentations': Presentation.objects.filter(presenter=user).count(),
        }
    elif role in ['admin', 'manager'] or user.is_superuser:
        stats['manager'] = {
            'total_customers': Customer.objects.count(),
            'total_properties': Property.objects.filter(is_active=True).count(),
            'total_presentations': Presentation.objects.count(),
            'active_consultants': EmployeeProfile.objects.filter(
                role='consultant', 
                is_active=True
            ).count(),
        }
    
    return JsonResponse(stats)


# ============================================
# MÜŞTERİ CRUD İŞLEMLERİ
# ============================================

@login_required(login_url="/login/")
def customer_list(request):
    """Müşteri listesi"""
    user = request.user
    role = get_user_role(user)
    
    if role == 'consultant':
        customers = Customer.objects.filter(consultant=user)
    else:
        customers = Customer.objects.all()
    
    customers = customers.select_related('neighborhood', 'consultant').order_by('-created_at')
    
    context = {
        'segment': 'customers',
        'customers': customers,
        'role': role,
    }
    return render(request, 'home/customer_list.html', context)


@login_required(login_url="/login/")
def customer_create(request):
    """Yeni müşteri oluştur"""
    if request.method == 'POST':
        try:
            customer = Customer.objects.create(
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                phone=request.POST.get('phone'),
                email=request.POST.get('email', ''),
                address=request.POST.get('address', ''),
                neighborhood_id=request.POST.get('neighborhood') if request.POST.get('neighborhood') else None,
                consultant=request.user,
                notes=request.POST.get('notes', ''),
                budget_min=request.POST.get('budget_min', 0),
                budget_max=request.POST.get('budget_max', 0),
                property_type=request.POST.get('property_type', 'apartment'),
                meeting_status=request.POST.get('meeting_status', 'yeni'),
            )
            messages.success(request, f'{customer.get_full_name()} başarıyla eklendi!')
            return redirect('customer_list')
        except Exception as e:
            messages.error(request, f'Hata: {str(e)}')
    
    neighborhoods = Neighborhood.objects.all()
    context = {
        'segment': 'customer_create',
        'neighborhoods': neighborhoods,
    }
    return render(request, 'home/customer_form.html', context)


@login_required(login_url="/login/")
def customer_detail(request, pk):
    """Müşteri detayı"""
    customer = get_object_or_404(Customer, pk=pk)
    
    role = get_user_role(request.user)
    if role == 'consultant' and customer.consultant != request.user:
        messages.error(request, 'Bu müşteriye erişim yetkiniz yok!')
        return redirect('customer_list')
    
    presentations = Presentation.objects.filter(customer_name__icontains=customer.get_full_name()).select_related('property', 'presenter')
    
    context = {
        'segment': 'customer_detail',
        'customer': customer,
        'presentations': presentations,
    }
    return render(request, 'home/customer_detail.html', context)


@login_required(login_url="/login/")
def customer_edit(request, pk):
    """Müşteri düzenle"""
    customer = get_object_or_404(Customer, pk=pk)
    
    role = get_user_role(request.user)
    if role == 'consultant' and customer.consultant != request.user:
        messages.error(request, 'Bu müşteriyi düzenleme yetkiniz yok!')
        return redirect('customer_list')
    
    if request.method == 'POST':
        try:
            customer.first_name = request.POST.get('first_name')
            customer.last_name = request.POST.get('last_name')
            customer.phone = request.POST.get('phone')
            customer.email = request.POST.get('email', '')
            customer.address = request.POST.get('address', '')
            
            neighborhood_id = request.POST.get('neighborhood')
            customer.neighborhood_id = neighborhood_id if neighborhood_id else None
            
            customer.notes = request.POST.get('notes', '')
            customer.budget_min = request.POST.get('budget_min', 0)
            customer.budget_max = request.POST.get('budget_max', 0)
            customer.property_type = request.POST.get('property_type', 'apartment')
            customer.meeting_status = request.POST.get('meeting_status', 'yeni')
            
            customer.save()
            messages.success(request, f'{customer.get_full_name()} güncellendi!')
            return redirect('customer_detail', pk=customer.pk)
        except Exception as e:
            messages.error(request, f'Hata: {str(e)}')
    
    neighborhoods = Neighborhood.objects.all()
    context = {
        'segment': 'customer_edit',
        'customer': customer,
        'neighborhoods': neighborhoods,
    }
    return render(request, 'home/customer_form.html', context)


@login_required(login_url="/login/")
def customer_delete(request, pk):
    """Müşteri sil"""
    customer = get_object_or_404(Customer, pk=pk)
    
    role = get_user_role(request.user)
    if role == 'consultant' and customer.consultant != request.user:
        messages.error(request, 'Bu müşteriyi silme yetkiniz yok!')
        return redirect('customer_list')
    
    if request.method == 'POST':
        customer_name = customer.get_full_name()
        customer.delete()
        messages.success(request, f'{customer_name} silindi!')
        return redirect('customer_list')
    
    context = {
        'segment': 'customer_delete',
        'customer': customer,
    }
    return render(request, 'home/customer_confirm_delete.html', context)


# ============================================
# EMLAK CRUD İŞLEMLERİ
# ============================================

@login_required(login_url="/login/")
def property_list(request):
    """Emlak listesi"""
    user = request.user
    role = get_user_role(user)
    
    if role == 'consultant':
        properties = Property.objects.filter(consultant=user)
    else:
        properties = Property.objects.all()
    
    properties = properties.select_related('neighborhood', 'consultant').order_by('-created_at')
    
    context = {
        'segment': 'properties',
        'properties': properties,
        'role': role,
    }
    return render(request, 'home/property_list.html', context)


@login_required(login_url="/login/")
def property_create(request):
    """Yeni emlak oluştur"""
    if request.method == 'POST':
        try:
            property_obj = Property.objects.create(
                title=request.POST.get('title'),
                description=request.POST.get('description', ''),
                property_type=request.POST.get('property_type', 'apartment'),
                status=request.POST.get('status', 'satilik'),
                price=request.POST.get('price', 0),
                size=request.POST.get('size', 0),
                rooms=request.POST.get('rooms', '2+1'),
                floor=request.POST.get('floor', 0),
                total_floors=request.POST.get('total_floors', 0),
                building_age=request.POST.get('building_age', 0),
                address=request.POST.get('address', ''),
                neighborhood_id=request.POST.get('neighborhood') if request.POST.get('neighborhood') else None,
                consultant=request.user,
                is_active=True,
            )
            messages.success(request, f'{property_obj.title} başarıyla eklendi!')
            return redirect('property_list')
        except Exception as e:
            messages.error(request, f'Hata: {str(e)}')
    
    neighborhoods = Neighborhood.objects.all()
    context = {
        'segment': 'property_create',
        'neighborhoods': neighborhoods,
    }
    return render(request, 'home/property_form.html', context)


@login_required(login_url="/login/")
def property_detail(request, pk):
    """Emlak detayı"""
    property_obj = get_object_or_404(Property, pk=pk)
    
    role = get_user_role(request.user)
    if role == 'consultant' and property_obj.consultant != request.user:
        messages.error(request, 'Bu emlaka erişim yetkiniz yok!')
        return redirect('property_list')
    
    presentations = Presentation.objects.filter(property=property_obj).select_related('presenter')
    
    context = {
        'segment': 'property_detail',
        'property': property_obj,
        'presentations': presentations,
    }
    return render(request, 'home/property_detail.html', context)


@login_required(login_url="/login/")
def property_edit(request, pk):
    """Emlak düzenle"""
    property_obj = get_object_or_404(Property, pk=pk)
    
    role = get_user_role(request.user)
    if role == 'consultant' and property_obj.consultant != request.user:
        messages.error(request, 'Bu emlağı düzenleme yetkiniz yok!')
        return redirect('property_list')
    
    if request.method == 'POST':
        try:
            property_obj.title = request.POST.get('title')
            property_obj.description = request.POST.get('description', '')
            property_obj.property_type = request.POST.get('property_type', 'apartment')
            property_obj.status = request.POST.get('status', 'satilik')
            property_obj.price = request.POST.get('price', 0)
            property_obj.size = request.POST.get('size', 0)
            property_obj.rooms = request.POST.get('rooms', '2+1')
            property_obj.floor = request.POST.get('floor', 0)
            property_obj.total_floors = request.POST.get('total_floors', 0)
            property_obj.building_age = request.POST.get('building_age', 0)
            property_obj.address = request.POST.get('address', '')
            
            neighborhood_id = request.POST.get('neighborhood')
            property_obj.neighborhood_id = neighborhood_id if neighborhood_id else None
            
            property_obj.save()
            messages.success(request, f'{property_obj.title} güncellendi!')
            return redirect('property_detail', pk=property_obj.pk)
        except Exception as e:
            messages.error(request, f'Hata: {str(e)}')
    
    neighborhoods = Neighborhood.objects.all()
    context = {
        'segment': 'property_edit',
        'property': property_obj,
        'neighborhoods': neighborhoods,
    }
    return render(request, 'home/property_form.html', context)


@login_required(login_url="/login/")
def property_delete(request, pk):
    """Emlak sil"""
    property_obj = get_object_or_404(Property, pk=pk)
    
    role = get_user_role(request.user)
    if role == 'consultant' and property_obj.consultant != request.user:
        messages.error(request, 'Bu emlağı silme yetkiniz yok!')
        return redirect('property_list')
    
    if request.method == 'POST':
        property_title = property_obj.title
        property_obj.delete()
        messages.success(request, f'{property_title} silindi!')
        return redirect('property_list')
    
    context = {
        'segment': 'property_delete',
        'property': property_obj,
    }
    return render(request, 'home/property_confirm_delete.html', context)


# ============================================
# SUNUM CRUD İŞLEMLERİ
# ============================================

@login_required(login_url="/login/")
def presentation_list(request):
    """Sunum listesi"""
    user = request.user
    role = get_user_role(user)
    
    if role == 'consultant':
        presentations = Presentation.objects.filter(presenter=user)
    else:
        presentations = Presentation.objects.all()
    
    presentations = presentations.select_related('property', 'presenter').order_by('-presentation_date')
    
    context = {
        'segment': 'presentations',
        'presentations': presentations,
        'role': role,
    }
    return render(request, 'home/presentation_list.html', context)


@login_required(login_url="/login/")
def presentation_create(request):
    """Yeni sunum oluştur"""
    user = request.user
    role = get_user_role(user)
    
    if request.method == 'POST':
        try:
            presentation = Presentation.objects.create(
                customer_id=request.POST.get('customer'),
                property_id=request.POST.get('property'),
                presenter=user,
                presentation_date=request.POST.get('presentation_date'),
                status=request.POST.get('status', 'bekliyor'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Sunum başarıyla oluşturuldu!')
            return redirect('presentation_list')
        except Exception as e:
            messages.error(request, f'Hata: {str(e)}')
    
    if role == 'consultant':
        customers = Customer.objects.filter(consultant=user)
        properties = Property.objects.filter(consultant=user, is_active=True)
    else:
        customers = Customer.objects.all()
        properties = Property.objects.filter(is_active=True)
    
    context = {
        'segment': 'presentation_create',
        'customers': customers,
        'properties': properties,
    }
    return render(request, 'home/presentation_form.html', context)


@login_required(login_url="/login/")
def presentation_edit(request, pk):
    """Sunum düzenle"""
    presentation = get_object_or_404(Presentation, pk=pk)
    
    role = get_user_role(request.user)
    if role == 'consultant' and presentation.presenter != request.user:
        messages.error(request, 'Bu sunumu düzenleme yetkiniz yok!')
        return redirect('presentation_list')
    
    if request.method == 'POST':
        try:
            presentation.customer_id = request.POST.get('customer')
            presentation.property_id = request.POST.get('property')
            presentation.presentation_date = request.POST.get('presentation_date')
            presentation.status = request.POST.get('status', 'bekliyor')
            presentation.notes = request.POST.get('notes', '')
            presentation.save()
            
            messages.success(request, 'Sunum güncellendi!')
            return redirect('presentation_list')
        except Exception as e:
            messages.error(request, f'Hata: {str(e)}')
    
    if role == 'consultant':
        customers = Customer.objects.filter(consultant=request.user)
        properties = Property.objects.filter(consultant=request.user, is_active=True)
    else:
        customers = Customer.objects.all()
        properties = Property.objects.filter(is_active=True)
    
    context = {
        'segment': 'presentation_edit',
        'presentation': presentation,
        'customers': customers,
        'properties': properties,
    }
    return render(request, 'home/presentation_form.html', context)


@login_required(login_url="/login/")
def presentation_delete(request, pk):
    """Sunum sil"""
    presentation = get_object_or_404(Presentation, pk=pk)
    
    role = get_user_role(request.user)
    if role == 'consultant' and presentation.presenter != request.user:
        messages.error(request, 'Bu sunumu silme yetkiniz yok!')
        return redirect('presentation_list')
    
    if request.method == 'POST':
        presentation.delete()
        messages.success(request, 'Sunum silindi!')
        return redirect('presentation_list')
    
    context = {
        'segment': 'presentation_delete',
        'presentation': presentation,
    }
    return render(request, 'home/presentation_confirm_delete.html', context)