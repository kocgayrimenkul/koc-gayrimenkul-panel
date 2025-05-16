# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, datetime, date
from django.db.models import Count, Q, Sum, Case, When, IntegerField, Value, Avg, F, Min, Max
from django.db.models.functions import TruncMonth, ExtractMonth, ExtractYear
import json

from apps.employees.models import EmployeeProfile
from apps.customers.models import Customer, Neighborhood
from apps.portfolio.models import Property
from apps.presentation.models import Presentation
from apps.calendar.models import Event, TodoItem
from apps.fsbo.models import FSBO

def get_user_role(user):
    """Kullanıcının rolünü döndürür"""
    try:
        return user.employee_profile.role
    except (AttributeError, EmployeeProfile.DoesNotExist):
        return None

@login_required(login_url="/login/")
def index(request):
    user = request.user
    role = get_user_role(user)
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    one_week_ago = today - timedelta(days=7)
    one_month_ago = today - timedelta(days=30)
    three_months_ago = today - timedelta(days=90)
    one_year_ago = today - timedelta(days=365)
    
    context = {
        'segment': 'index',
        'role': role,
        'user': user,
        'today': today,
    }
    
    # Tüm roller için ortak veriler
    context['total_properties'] = Property.objects.filter(is_active=True).count()
    context['total_customers'] = Customer.objects.all().count()
    
    # Tarih filtresi
    date_filter = request.GET.get('date_filter', 'month')
    if date_filter == 'week':
        date_from = one_week_ago
    elif date_filter == 'month':
        date_from = one_month_ago
    elif date_filter == 'quarter':
        date_from = three_months_ago
    elif date_filter == 'year':
        date_from = one_year_ago
    else:
        date_from = one_month_ago
    
    context['date_filter'] = date_filter
    
    # Son 6 ay için ay isimlerini hazırla
    last_months = []
    last_months_labels = []
    for i in range(5, -1, -1):
        month = today.month - i
        year = today.year
        while month <= 0:
            month += 12
            year -= 1
        last_months.append((year, month))
        last_months_labels.append(datetime(year, month, 1).strftime('%b'))
    
    context['last_months_labels'] = last_months_labels
    
    # Danışman rolü için verileri hazırla
    if role == 'consultant':
        # Danışmana atanan müşteriler
        context['my_customers'] = Customer.objects.filter(consultant=user).order_by('-created_at')[:10]
        context['my_customer_count'] = Customer.objects.filter(consultant=user).count()
        
        # Danışmanın ilgilendiği gayrimenkuller
        context['my_properties'] = Property.objects.filter(consultant=user, is_active=True).order_by('-created_at')[:10]
        context['my_property_count'] = Property.objects.filter(consultant=user, is_active=True).count()
        
        # Danışmanın yaklaşan sunumları
        context['my_presentations'] = Presentation.objects.filter(
            presenter=user, 
            presentation_date__gte=today
        ).order_by('presentation_date')[:5]
        
        # Son 30 gündeki sunumlar
        recent_presentations = Presentation.objects.filter(
            presenter=user,
            presentation_date__gte=date_from
        )
        context['completed_presentations'] = recent_presentations.filter(status='tamamlandi').count()
        context['pending_presentations'] = recent_presentations.filter(status='bekliyor').count()
        context['cancelled_presentations'] = recent_presentations.filter(status='iptal').count()
        
        # Yapılacaklar listesi
        context['my_todos'] = TodoItem.objects.filter(
            Q(user=user) | Q(consultant=user),
            is_completed=False
        ).order_by('due_date')[:10]
        
        # Bugünkü etkinlikler
        context['today_events'] = Event.objects.filter(
            consultant=user,
            start_time__date=today
        ).order_by('start_time')
        
        # Yarınki etkinlikler
        context['tomorrow_events'] = Event.objects.filter(
            consultant=user,
            start_time__date=tomorrow
        ).order_by('start_time')
        
        # FSBO aramaları
        context['my_fsbos'] = FSBO.objects.filter(consultant=user).order_by('-created_at')[:5]
        
        # Tamamlanma oranı
        all_todos = TodoItem.objects.filter(
            Q(user=user) | Q(consultant=user),
            created_at__gte=date_from
        )
        completed_todos = all_todos.filter(is_completed=True)
        if all_todos.count() > 0:
            context['todo_completion_rate'] = round((completed_todos.count() / all_todos.count()) * 100)
        else:
            context['todo_completion_rate'] = 0
            
        # Dönüştürme oranı
        all_customers = Customer.objects.filter(consultant=user, created_at__gte=date_from)
        positive_customers = all_customers.filter(meeting_status='olumlu')
        if all_customers.count() > 0:
            context['customer_conversion_rate'] = round((positive_customers.count() / all_customers.count()) * 100)
        else:
            context['customer_conversion_rate'] = 0
                
    # Yönetici, Müdür veya superuser için verileri hazırla
    elif role in ['admin', 'manager'] or user.is_superuser:
        # Tüm danışmanlar
        consultants = EmployeeProfile.objects.filter(
            role='consultant', 
            is_active=True
        ).select_related('user')
        
        context['consultants'] = consultants
        
        # Seçilen danışman (eğer yönetici özel olarak bir danışman seçmişse)
        selected_consultant_id = request.GET.get('consultant_id')
        selected_consultant = None
        
        if selected_consultant_id:
            try:
                consultant_profile = EmployeeProfile.objects.get(id=selected_consultant_id, role='consultant')
                selected_consultant = consultant_profile.user
                context['selected_consultant'] = selected_consultant
                
                # Seçilen danışman için detaylı veri hazırla
                # Danışmanın ilgilendiği müşteriler
                context['consultant_customers'] = Customer.objects.filter(consultant=selected_consultant).order_by('-created_at')[:10]
                context['consultant_customer_count'] = Customer.objects.filter(consultant=selected_consultant).count()
                
                # Danışmanın ilgilendiği gayrimenkuller
                context['consultant_properties'] = Property.objects.filter(consultant=selected_consultant, is_active=True).order_by('-created_at')[:10]
                context['consultant_property_count'] = Property.objects.filter(consultant=selected_consultant, is_active=True).count()
                
                # Danışmanın yaklaşan sunumları
                context['consultant_presentations'] = Presentation.objects.filter(
                    presenter=selected_consultant, 
                    presentation_date__gte=today
                ).order_by('presentation_date')[:5]
                
                # Son 30 gündeki sunumlar
                recent_presentations = Presentation.objects.filter(
                    presenter=selected_consultant,
                    presentation_date__gte=date_from
                )
                context['consultant_completed_presentations'] = recent_presentations.filter(status='tamamlandi').count()
                context['consultant_pending_presentations'] = recent_presentations.filter(status='bekliyor').count()
                context['consultant_cancelled_presentations'] = recent_presentations.filter(status='iptal').count()
                
                # Bugünkü etkinlikler
                context['consultant_events'] = Event.objects.filter(
                    consultant=selected_consultant,
                    start_time__date=today
                ).order_by('start_time')
                
                # Tamamlanma oranı
                all_todos = TodoItem.objects.filter(
                    Q(user=selected_consultant) | Q(consultant=selected_consultant),
                    created_at__gte=date_from
                )
                completed_todos = all_todos.filter(is_completed=True)
                if all_todos.count() > 0:
                    context['consultant_todo_completion_rate'] = round((completed_todos.count() / all_todos.count()) * 100)
                else:
                    context['consultant_todo_completion_rate'] = 0
                
                # Dönüştürme oranı
                all_customers = Customer.objects.filter(consultant=selected_consultant, created_at__gte=date_from)
                positive_customers = all_customers.filter(meeting_status='olumlu')
                if all_customers.count() > 0:
                    context['consultant_conversion_rate'] = round((positive_customers.count() / all_customers.count()) * 100)
                else:
                    context['consultant_conversion_rate'] = 0
                
                # Çalışma etkinliği
                total_events = Event.objects.filter(consultant=selected_consultant, start_time__date__gte=date_from).count()
                work_days = (today - date_from).days + 1
                if work_days > 0:
                    context['consultant_activity_rate'] = round(total_events / work_days, 2)
                else:
                    context['consultant_activity_rate'] = 0
                
            except EmployeeProfile.DoesNotExist:
                pass
                
        # Performance Scorecard için veriler
        consultant_data = []
        all_consultants = consultants
        
        for consultant_profile in all_consultants:
            consultant = consultant_profile.user
            presentations = Presentation.objects.filter(
                presenter=consultant,
                presentation_date__gte=date_from
            )
            
            customers = Customer.objects.filter(
                consultant=consultant,
                created_at__gte=date_from
            )
            
            events = Event.objects.filter(
                consultant=consultant,
                start_time__gte=date_from
            )
            
            todos = TodoItem.objects.filter(
                Q(user=consultant) | Q(consultant=consultant),
                created_at__gte=date_from
            )
            
            properties = Property.objects.filter(
                consultant=consultant,
                created_at__gte=date_from,
                is_active=True
            )
            
            fsbo_calls = FSBO.objects.filter(
                consultant=consultant,
                created_at__gte=date_from
            )
            
            # Performans puanı hesaplama
            completed_presentations = presentations.filter(status='tamamlandi').count()
            positive_customers = customers.filter(meeting_status='olumlu').count()
            completed_todos = todos.filter(is_completed=True).count()
            
            # Sunumlar için ağırlık: 40%
            presentation_score = 0
            if presentations.count() > 0:
                presentation_score = (completed_presentations / presentations.count()) * 40
            
            # Müşteriler için ağırlık: 30%
            customer_score = 0
            if customers.count() > 0:
                customer_score = (positive_customers / customers.count()) * 30
            
            # Görevler için ağırlık: 20%
            todo_score = 0
            if todos.count() > 0:
                todo_score = (completed_todos / todos.count()) * 20
            
            # Portföy için ağırlık: 10%
            portfolio_score = min(properties.count() * 2, 20)  # Her 5 portföy için 10 puan, max 20 puan
            
            # Toplam performans puanı (0-100 arası)
            performance_score = round(presentation_score + customer_score + todo_score + portfolio_score)
            
            consultant_info = {
                'consultant': consultant,
                'profile': consultant_profile,
                'total_presentations': presentations.count(),
                'completed_presentations': completed_presentations,
                'pending_presentations': presentations.filter(status='bekliyor').count(),
                'cancelled_presentations': presentations.filter(status='iptal').count(),
                'customers_count': customers.count(),
                'positive_customers': positive_customers,
                'properties_count': properties.count(),
                'events_count': events.count(),
                'todos_count': todos.count(),
                'completed_todos': completed_todos,
                'fsbo_calls': fsbo_calls.count(),
                'performance_score': performance_score
            }
            
            # Başarı oranı
            if consultant_info['total_presentations'] > 0:
                consultant_info['success_rate'] = round((consultant_info['completed_presentations'] / consultant_info['total_presentations']) * 100)
            else:
                consultant_info['success_rate'] = 0
                
            # Müşteri dönüştürme oranı
            if consultant_info['customers_count'] > 0:
                consultant_info['conversion_rate'] = round((consultant_info['positive_customers'] / consultant_info['customers_count']) * 100)
            else:
                consultant_info['conversion_rate'] = 0
                
            # Görev tamamlama oranı
            if consultant_info['todos_count'] > 0:
                consultant_info['todo_completion_rate'] = round((consultant_info['completed_todos'] / consultant_info['todos_count']) * 100)
            else:
                consultant_info['todo_completion_rate'] = 0
                
            consultant_data.append(consultant_info)
        
        # Performansa göre sırala
        consultant_data.sort(key=lambda x: x['performance_score'], reverse=True)
        context['consultant_data'] = consultant_data
        
        # Ekibe Genel Bakış Metrikleri
        context['avg_performance_score'] = round(sum(c['performance_score'] for c in consultant_data) / len(consultant_data)) if consultant_data else 0
        context['avg_success_rate'] = round(sum(c['success_rate'] for c in consultant_data) / len(consultant_data)) if consultant_data else 0
        context['avg_conversion_rate'] = round(sum(c['conversion_rate'] for c in consultant_data) / len(consultant_data)) if consultant_data else 0
        context['total_presentations'] = sum(c['total_presentations'] for c in consultant_data)
        context['total_completed_presentations'] = sum(c['completed_presentations'] for c in consultant_data)
        context['total_pending_presentations'] = sum(c['pending_presentations'] for c in consultant_data)
        context['avg_properties_per_consultant'] = round(sum(c['properties_count'] for c in consultant_data) / len(consultant_data), 1) if consultant_data else 0
        
        # Performans lider tablosu (Top 3)
        context['performance_leaders'] = sorted(consultant_data, key=lambda x: x['performance_score'], reverse=True)[:3]
        context['conversion_leaders'] = sorted(consultant_data, key=lambda x: x['conversion_rate'], reverse=True)[:3]
        context['presentation_leaders'] = sorted(consultant_data, key=lambda x: x['completed_presentations'], reverse=True)[:3]
        
        # Son eklenen gayrimenkuller
        context['recent_properties'] = Property.objects.filter(is_active=True).order_by('-created_at')[:10]
        
        # Son eklenen müşteriler
        context['recent_customers'] = Customer.objects.all().order_by('-created_at')[:10]
        
        # Yaklaşan sunumlar
        context['upcoming_presentations'] = Presentation.objects.filter(
            presentation_date__gte=today
        ).order_by('presentation_date')[:10]
        
        # Mahalle bazlı analizler
        neighborhoods = Neighborhood.objects.all()
        neighborhood_data = []
        
        for neighborhood in neighborhoods:
            properties = Property.objects.filter(neighborhood=neighborhood, is_active=True)
            properties_count = properties.count()
            customers_count = Customer.objects.filter(neighborhood=neighborhood).count()
            
            if properties_count > 0 or customers_count > 0:
                # Sunumlar
                presentations = Presentation.objects.filter(
                    property__neighborhood=neighborhood,
                    presentation_date__gte=date_from
                )
                
                presentations_count = presentations.count()
                completed_presentations = presentations.filter(status='tamamlandi').count()
                
                # Fiyat ortalaması ve dağılımı
                avg_price = properties.aggregate(Avg('price'))['price__avg'] or 0
                min_price = properties.aggregate(Min('price'))['price__min'] or 0
                max_price = properties.aggregate(Max('price'))['price__max'] or 0
                
                # Satış/kira durumu
                for_sale = properties.filter(status='satilik').count()
                for_rent = properties.filter(status='kiralik').count()
                
                # Satış hızı (ne kadar zamandır portföyde)
                total_days = 0
                for prop in properties:
                    days_on_market = (today - prop.listing_date).days
                    total_days += days_on_market
                
                avg_days_on_market = round(total_days / properties_count) if properties_count > 0 else 0
                
                # Başarı oranı
                success_rate = round((completed_presentations / presentations_count) * 100) if presentations_count > 0 else 0
                
                neighborhood_data.append({
                    'id': neighborhood.id,
                    'name': neighborhood.name,
                    'consultant': neighborhood.consultant.get_full_name() if neighborhood.consultant else "Atanmamış",
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
        
        # Çeşitli kriterlere göre sıralama
        neighborhood_data.sort(key=lambda x: x['properties_count'], reverse=True)
        context['neighborhood_data'] = neighborhood_data
        
        # İstatistiksel analizler
        total_presentations = Presentation.objects.filter(presentation_date__gte=date_from).count()
        completed_presentations = Presentation.objects.filter(
            presentation_date__gte=date_from,
            status='tamamlandi'
        ).count()
        
        if total_presentations > 0:
            context['general_success_rate'] = round((completed_presentations / total_presentations) * 100)
        else:
            context['general_success_rate'] = 0
        
        # Kategori bazlı gayrimenkul dağılımı
        property_categories = Property.objects.filter(
            is_active=True
        ).values('category').annotate(count=Count('id'))
        
        categories_data = {}
        for item in property_categories:
            category = item['category'] or 'tanımsız'
            categories_data[category] = item['count']
        
        context['property_categories'] = categories_data
        
        # Durum bazlı gayrimenkul dağılımı (Satılık/Kiralık)
        property_status = Property.objects.filter(
            is_active=True
        ).values('status').annotate(count=Count('id'))
        
        status_data = {}
        for item in property_status:
            status = item['status'] or 'tanımsız'
            status_data[status] = item['count']
        
        context['property_status'] = status_data
        
        # En çok sunum yapılan mahalleler
        top_neighborhoods = Presentation.objects.filter(
            presentation_date__gte=date_from
        ).values('property__neighborhood__name').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        context['top_presentation_neighborhoods'] = top_neighborhoods
        
        # Aylık başarı oranı trendi
        monthly_success_trend = []
        
        for year, month in last_months:
            month_presentations = Presentation.objects.filter(
                presentation_date__year=year,
                presentation_date__month=month
            )
            
            total = month_presentations.count()
            completed = month_presentations.filter(status='tamamlandi').count()
            
            if total > 0:
                success_rate = round((completed / total) * 100)
            else:
                success_rate = 0
                
            monthly_success_trend.append(success_rate)
        
        context['monthly_success_trend'] = monthly_success_trend
    
    # Santral/Sekreter rolü için
    elif role == 'secretary':
        # Bugünkü etkinlikler (tüm danışmanlar)
        context['today_events'] = Event.objects.filter(
            start_time__date=today
        ).order_by('start_time')
        
        # Yaklaşan sunumlar
        context['upcoming_presentations'] = Presentation.objects.filter(
            presentation_date__gte=today
        ).order_by('presentation_date')[:10]
        
        # Son eklenen müşteriler
        context['recent_customers'] = Customer.objects.all().order_by('-created_at')[:10]
        
        # Danışman bazlı bugünkü etkinlik sayıları
        consultant_events = Event.objects.filter(
            start_time__date=today
        ).values('consultant__first_name', 'consultant__last_name').annotate(
            count=Count('id')
        ).order_by('consultant__last_name')
        
        context['consultant_events'] = consultant_events
        
        # Bugün çıkılan sunumlar
        context['today_presentations'] = Presentation.objects.filter(
            presentation_date__date=today
        ).order_by('presentation_date')
        
        # Yarınki sunumlar
        context['tomorrow_presentations'] = Presentation.objects.filter(
            presentation_date__date=tomorrow
        ).order_by('presentation_date')
        
        # Tüm danışmanlar
        context['all_consultants'] = EmployeeProfile.objects.filter(
            role='consultant',
            is_active=True
        ).select_related('user')
        
        # Danışmanların telefon numaraları
        consultant_phones = EmployeeProfile.objects.filter(
            role='consultant',
            is_active=True
        ).select_related('user').values('user__first_name', 'user__last_name', 'phone')
        
        context['consultant_phones'] = consultant_phones

    html_template = loader.get_template('home/index.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:

        load_template = request.path.split('/')[-1]

        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))
        context['segment'] = load_template

        html_template = loader.get_template('home/' + load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:

        html_template = loader.get_template('home/page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('home/page-500.html')
        return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def consultant_performance(request):
    """Danışman performans verilerini JSON olarak döndürür"""
    user = request.user
    role = get_user_role(user)
    
    # Sadece yönetici, müdür veya superuser erişebilir
    if role not in ['admin', 'manager'] and not user.is_superuser:
        return JsonResponse({'error': 'Yetkisiz erişim'}, status=403)
    
    today = timezone.now().date()
    one_month_ago = today - timedelta(days=30)
    
    # Tarih filtresi
    date_filter = request.GET.get('date_filter', 'month')
    if date_filter == 'week':
        date_from = today - timedelta(days=7)
    elif date_filter == 'month':
        date_from = one_month_ago
    elif date_filter == 'quarter':
        date_from = today - timedelta(days=90)
    elif date_filter == 'year':
        date_from = today - timedelta(days=365)
    else:
        date_from = one_month_ago
    
    # Tüm danışmanlar
    consultants = EmployeeProfile.objects.filter(
        role='consultant', 
        is_active=True
    ).select_related('user')
    
    consultant_data = []
    
    for consultant_profile in consultants:
        consultant = consultant_profile.user
        presentations = Presentation.objects.filter(
            presenter=consultant,
            presentation_date__gte=date_from
        )
        
        customers = Customer.objects.filter(
            consultant=consultant,
            created_at__gte=date_from
        )
        
        properties = Property.objects.filter(
            consultant=consultant,
            created_at__gte=date_from,
            is_active=True
        )
        
        # Diğer metrikleri hesapla
        completed_presentations = presentations.filter(status='tamamlandi').count()
        pending_presentations = presentations.filter(status='bekliyor').count()
        cancelled_presentations = presentations.filter(status='iptal').count()
        
        positive_customers = customers.filter(meeting_status='olumlu').count()
        waiting_customers = customers.filter(meeting_status='bekliyor').count()
        negative_customers = customers.filter(meeting_status='olumsuz').count()
        
        # Performans puanı hesapla
        performance_score = 0
        success_rate = 0
        conversion_rate = 0
        
        if presentations.count() > 0:
            success_rate = round((completed_presentations / presentations.count()) * 100)
            performance_score += success_rate * 0.4  # 40% ağırlık
        
        if customers.count() > 0:
            conversion_rate = round((positive_customers / customers.count()) * 100)
            performance_score += conversion_rate * 0.3  # 30% ağırlık
        
        # Portföy sayısı
        if properties.count() > 0:
            portfolio_score = min(properties.count() * 2, 20)  # Her 5 portföy için 10 puan, max 20 puan
            performance_score += portfolio_score
        
        consultant_data.append({
            'id': consultant.id,
            'name': consultant.get_full_name(),
            'presentations_total': presentations.count(),
            'presentations_completed': completed_presentations,
            'presentations_pending': pending_presentations,
            'presentations_cancelled': cancelled_presentations,
            'customers_total': customers.count(),
            'customers_positive': positive_customers,
            'customers_waiting': waiting_customers,
            'customers_negative': negative_customers,
            'properties_count': properties.count(),
            'success_rate': success_rate,
            'conversion_rate': conversion_rate,
            'performance_score': round(performance_score)
        })
    
    # Performansa göre sırala
    consultant_data.sort(key=lambda x: x['performance_score'], reverse=True)
    
    return JsonResponse({'consultants': consultant_data})

@login_required(login_url="/login/")
def neighborhood_analytics(request):
    """Mahalle bazlı analiz verilerini JSON olarak döndürür"""
    user = request.user
    role = get_user_role(user)
    
    # Sadece yönetici, müdür veya superuser erişebilir
    if role not in ['admin', 'manager'] and not user.is_superuser:
        return JsonResponse({'error': 'Yetkisiz erişim'}, status=403)
    
    today = timezone.now().date()
    
    # Tarih filtresi
    date_filter = request.GET.get('date_filter', 'month')
    if date_filter == 'week':
        date_from = today - timedelta(days=7)
    elif date_filter == 'month':
        date_from = today - timedelta(days=30)
    elif date_filter == 'quarter':
        date_from = today - timedelta(days=90)
    elif date_filter == 'year':
        date_from = today - timedelta(days=365)
    else:
        date_from = today - timedelta(days=30)
    
    # Mahalle bazlı analizler
    neighborhoods = Neighborhood.objects.all()
    neighborhood_data = []
    
    for neighborhood in neighborhoods:
        properties = Property.objects.filter(neighborhood=neighborhood, is_active=True)
        properties_count = properties.count()
        customers_count = Customer.objects.filter(neighborhood=neighborhood).count()
        
        if properties_count > 0 or customers_count > 0:
            # Sunumlar
            presentations = Presentation.objects.filter(
                property__neighborhood=neighborhood,
                presentation_date__gte=date_from
            )
            
            presentations_count = presentations.count()
            completed_presentations = presentations.filter(status='tamamlandi').count()
            
            # Fiyat ortalaması ve dağılımı
            avg_price = properties.aggregate(Avg('price'))['price__avg'] or 0
            min_price = properties.aggregate(Min('price'))['price__min'] or 0
            max_price = properties.aggregate(Max('price'))['price__max'] or 0
            
            # Satış/kira durumu
            for_sale = properties.filter(status='satilik').count()
            for_rent = properties.filter(status='kiralik').count()
            
            # Satış hızı (ne kadar zamandır portföyde)
            total_days = 0
            for prop in properties:
                days_on_market = (today - prop.listing_date).days
                total_days += days_on_market
            
            avg_days_on_market = round(total_days / properties_count) if properties_count > 0 else 0
            
            # Başarı oranı
            success_rate = round((completed_presentations / presentations_count) * 100) if presentations_count > 0 else 0
            
            neighborhood_data.append({
                'id': neighborhood.id,
                'name': neighborhood.name,
                'consultant': neighborhood.consultant.get_full_name() if neighborhood.consultant else "Atanmamış",
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
    
    # Portföy sayısına göre sırala
    neighborhood_data.sort(key=lambda x: x['properties_count'], reverse=True)
    
    return JsonResponse({'neighborhoods': neighborhood_data})
