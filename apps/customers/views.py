# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Müşteriler Görünümleri
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.urls import reverse
from django.db.models import Q
from django.contrib import messages
from .models import Customer, Neighborhood, CustomerReminder
from apps.portfolio.models import Property
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.db.models import Count
from django.contrib.auth.models import Group
from apps.authentication.models import CustomUser
from apps.employees.models import EmployeeProfile

def get_user_role(user):
    """Kullanıcının rolünü döndürür"""
    # Superuser ise admin rolünü döndür
    if user.is_superuser:
        return 'admin'
    
    try:
        return user.employee_profile.role
    except EmployeeProfile.DoesNotExist:
        return None

# Context Processor - Müşteri hatırlatmalarını tüm şablonlarda kullanılabilir hale getirir
def customer_reminders_processor(request):
    """Giriş yapmış kullanıcının müşteri hatırlatmalarını context'e ekler"""
    if hasattr(request, 'user') and request.user.is_authenticated:
        today = timezone.now().date()
        
        # Kullanıcının rolünü al
        role = get_user_role(request.user)
        
        # Bugün ve gelecekteki hatırlatmaları getir
        if request.user.is_superuser or role in ['admin', 'manager']:
            # Yöneticiler ve müdürler tüm hatırlatmaları görebilir
            reminders = CustomerReminder.objects.filter(
                reminder_date__gte=today,
                is_sent=False
            ).order_by('reminder_date')[:10]  # Sadece ilk 10 hatırlatma
        else:
            # Danışmanlar sadece kendi müşterilerine ait hatırlatmaları görebilir
            reminders = CustomerReminder.objects.filter(
                reminder_date__gte=today,
                is_sent=False,
                customer__consultant=request.user
            ).order_by('reminder_date')[:10]  # Sadece ilk 10 hatırlatma
        
        return {
            'customer_reminders': reminders
        }
    return {
        'customer_reminders': []
    }

@login_required(login_url="/login/")
def customer_list(request):
    """Müşteri listesi görünümü"""
    
    role = get_user_role(request.user)
    
    # Role göre müşterileri getir
    if request.user.is_superuser or role in ['admin', 'manager', 'secretary']:
        # Yönetici, Müdür ve Santral tüm müşterileri görebilir
        customers = Customer.objects.all()
    else:
        # Danışman sadece kendi mahallelerindeki müşterileri görebilir
        consultant_neighborhoods = Neighborhood.objects.filter(consultant=request.user)
        customers = Customer.objects.filter(neighborhood__in=consultant_neighborhoods)
    
    # Filtreleme işlemleri
    filter_status = request.GET.get('status', '')
    if filter_status:
        customers = customers.filter(meeting_status=filter_status)
    
    filter_date = request.GET.get('date', '')
    if filter_date == 'today':
        today = timezone.now().date()
        customers = customers.filter(created_at__date=today)
    elif filter_date == 'week':
        week_ago = timezone.now().date() - timedelta(days=7)
        customers = customers.filter(created_at__date__gte=week_ago)
    elif filter_date == 'month':
        month_ago = timezone.now().date() - timedelta(days=30)
        customers = customers.filter(created_at__date__gte=month_ago)
    
    # Geri dönüş tarihi filtreleme
    filter_response = request.GET.get('response', '')
    today = timezone.now().date()
    if filter_response == 'yes':
        customers = customers.filter(response_date__isnull=False)
    elif filter_response == 'no':
        customers = customers.filter(response_date__isnull=True)
    elif filter_response == 'today':
        customers = customers.filter(response_date=today)
    elif filter_response == 'week':
        week_ago = today - timedelta(days=7)
        customers = customers.filter(response_date__gte=week_ago, response_date__lte=today)
    
    # Hatırlatma tarihi filtreleme
    has_reminder = request.GET.get('has_reminder', '') == 'true'
    if has_reminder:
        customers = customers.filter(reminder_date__isnull=False)
    
    # Mahalle filtresi
    if role in ['admin', 'manager', 'secretary']:
        neighborhoods = Neighborhood.objects.all()
    else:
        neighborhoods = Neighborhood.objects.filter(consultant=request.user)
    
    filter_neighborhood = request.GET.get('neighborhood', '')
    if filter_neighborhood:
        if role == 'consultant':
            if neighborhoods.filter(id=filter_neighborhood).exists():
                customers = customers.filter(neighborhood_id=filter_neighborhood)
        else:
            customers = customers.filter(neighborhood_id=filter_neighborhood)
    
    # Kaynak filtresi
    filter_source = request.GET.get('source', '')
    if filter_source:
        customers = customers.filter(source=filter_source)
    
    # İstatistikler
    all_customers = customers
    olumlu_musteri_sayisi = all_customers.filter(meeting_status='olumlu').count()
    olumsuz_musteri_sayisi = all_customers.filter(meeting_status='olumsuz').count()
    bekleyen_musteri_sayisi = all_customers.filter(meeting_status='bekliyor').count()
    
    # Müşteri kaynakları için istatistik
    kaynak_istatistikleri = all_customers.values('source').annotate(toplam=Count('id')).order_by('-toplam')
    
    context = {
        'segment': 'musteri',
        'customers': customers,
        'neighborhoods': neighborhoods,
        'filter_status': filter_status,
        'filter_date': filter_date,
        'filter_response': filter_response,
        'filter_neighborhood': filter_neighborhood,
        'filter_source': filter_source,
        'has_reminder': has_reminder,
        'olumlu_musteri_sayisi': olumlu_musteri_sayisi,
        'olumsuz_musteri_sayisi': olumsuz_musteri_sayisi,
        'bekleyen_musteri_sayisi': bekleyen_musteri_sayisi,
        'kaynak_istatistikleri': kaynak_istatistikleri,
        'user_role': role,
    }
    
    html_template = loader.get_template('customers/customer_list.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def customer_detail(request, customer_id):
    """Müşteri detay sayfası"""
    
    customer = get_object_or_404(Customer, id=customer_id)
    role = get_user_role(request.user)
    
    # Yetki kontrolü
    if not request.user.is_superuser and role not in ['admin', 'manager', 'secretary']:
        if not Neighborhood.objects.filter(consultant=request.user, id=customer.neighborhood.id).exists():
            messages.error(request, "Bu müşteri kaydını görüntüleme yetkiniz yok.")
            return redirect('customer_list')
    
    # Görüşme sonucu güncelleme
    if request.method == 'POST':
        if not request.user.is_superuser and role not in ['admin', 'manager', 'consultant']:
            messages.error(request, "Müşteri bilgilerini güncelleme yetkiniz yok.")
            return redirect('customer_list')
            
        meeting_result = request.POST.get('meeting_result', '')
        meeting_status = request.POST.get('meeting_status', 'bekliyor')
        response_date_str = request.POST.get('response_date', '')
        
        customer.meeting_result = meeting_result
        customer.meeting_status = meeting_status
        
        if response_date_str:
            try:
                response_date = timezone.datetime.strptime(response_date_str, '%Y-%m-%d').date()
                customer.response_date = response_date
            except ValueError:
                messages.warning(request, "Geri dönüş tarihi geçerli bir format değil. Tarih bilgisi güncellenmedi.")
        else:
            customer.response_date = None
            
        customer.save()
        messages.success(request, "Görüşme sonucu başarıyla kaydedildi.")
        return redirect('customer_list')
    
    context = {
        'segment': 'musteri',
        'customer': customer,
        'user_role': role,
    }
    
    html_template = loader.get_template('customers/customer_detail.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def customer_edit(request, customer_id):
    """Müşteri düzenleme sayfası"""
    
    customer = get_object_or_404(Customer, id=customer_id)
    role = get_user_role(request.user)
    
    # Yetki kontrolü
    if not request.user.is_superuser and role not in ['admin', 'manager']:
        if not Neighborhood.objects.filter(consultant=request.user, id=customer.neighborhood.id).exists():
            messages.error(request, "Bu müşteri kaydını düzenleme yetkiniz yok.")
            return redirect('customer_list')
    
    # Erişilebilir mahalleler
    if request.user.is_superuser or role in ['admin', 'manager']:
        neighborhoods = Neighborhood.objects.all().order_by('name')
    else:
        neighborhoods = Neighborhood.objects.filter(consultant=request.user).order_by('name')
    
    # Daire tipi portföyleri getir
    properties = Property.objects.filter(property_type='daire', is_active=True).order_by('-created_at')
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '')
        phone = request.POST.get('phone', '')
        neighborhood_id = request.POST.get('neighborhood', '')
        source = request.POST.get('source', '')
        notes = request.POST.get('notes', '')
        meeting_status = request.POST.get('meeting_status', 'bekliyor')
        response_date_str = request.POST.get('response_date', '')
        
        # Validation
        if not full_name or not phone or not neighborhood_id:
            messages.error(request, "Lütfen tüm zorunlu alanları doldurun.")
            return render(request, 'customers/customer_edit.html', {
                'segment': 'musteri',
                'customer': customer,
                'neighborhoods': neighborhoods,
                'properties': properties,
                'user_role': role,
            })
        
        try:
            # Danışman sadece kendi mahallelerindeki müşterileri düzenleyebilir
            if role == 'consultant':
                if not neighborhoods.filter(id=neighborhood_id).exists():
                    messages.error(request, "Bu mahalleye müşteri atama yetkiniz yok.")
                    return redirect('customer_list')
            
            neighborhood = Neighborhood.objects.get(id=neighborhood_id)
            
            # Müşteriyi güncelle
            customer.full_name = full_name
            customer.phone = phone
            customer.neighborhood = neighborhood
            customer.source = source
            customer.notes = notes
            customer.meeting_status = meeting_status
            
            if response_date_str:
                try:
                    response_date = timezone.datetime.strptime(response_date_str, '%Y-%m-%d').date()
                    customer.response_date = response_date
                except ValueError:
                    messages.warning(request, "Geri dönüş tarihi geçerli bir format değil. Tarih bilgisi güncellenmedi.")
            else:
                customer.response_date = None
                
            customer.save()
            
            messages.success(request, "Müşteri bilgileri başarıyla güncellendi.")
            return redirect('customer_detail', customer_id=customer.id)
        
        except Exception as e:
            messages.error(request, f"Bir hata oluştu: {str(e)}")
    
    context = {
        'segment': 'musteri',
        'customer': customer,
        'neighborhoods': neighborhoods,
        'properties': properties,
        'user_role': role,
    }
    
    html_template = loader.get_template('customers/customer_edit.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def customer_register(request):
    """Santral tarafından müşteri kayıt ekranı"""
    
    role = get_user_role(request.user)
    
    # Sadece Yönetici, Müdür ve Santral erişebilir
    if not request.user.is_superuser and role not in ['admin', 'manager', 'secretary']:
        messages.error(request, "Bu sayfaya erişim yetkiniz bulunmamaktadır.")
        return redirect('home')
    
    neighborhoods = Neighborhood.objects.all().order_by('name')
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '')
        phone = request.POST.get('phone', '')
        neighborhood_id = request.POST.get('neighborhood', '')
        source = request.POST.get('source', '')
        
        # Validation
        if not full_name or not phone or not neighborhood_id:
            messages.error(request, "Lütfen tüm zorunlu alanları doldurun.")
            return render(request, 'customers/customer_register.html', {
                'segment': 'musteri_kayit',
                'neighborhoods': neighborhoods,
                'form_data': request.POST,
                'user_role': role,
            })
        
        try:
            neighborhood = Neighborhood.objects.get(id=neighborhood_id)
            
            # Yeni müşteri oluştur
            customer = Customer(
                full_name=full_name,
                phone=phone,
                neighborhood=neighborhood,
                source=source,
            )
            customer.save()
            
            messages.success(request, "Müşteri başarıyla kaydedildi ve ilgili danışmana atandı.")
            return redirect('customer_register')
        
        except Exception as e:
            messages.error(request, f"Bir hata oluştu: {str(e)}")
    
    context = {
        'segment': 'musteri_kayit',
        'neighborhoods': neighborhoods,
        'user_role': role,
    }
    
    html_template = loader.get_template('customers/customer_register.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def customer_create(request):
    """Danışmanların yeni müşteri oluşturma ekranı"""
    
    role = get_user_role(request.user)
    
    # Sadece Yönetici, Müdür ve Danışman erişebilir
    if not request.user.is_superuser and role not in ['admin', 'manager', 'consultant']:
        messages.error(request, "Bu sayfaya erişim yetkiniz bulunmamaktadır.")
        return redirect('home')
    
    # Erişilebilir mahalleler
    if request.user.is_superuser or role in ['admin', 'manager']:
        neighborhoods = Neighborhood.objects.all().order_by('name')
    else:
        neighborhoods = Neighborhood.objects.filter(consultant=request.user).order_by('name')
    
    # Daire tipi portföyleri getir
    properties = Property.objects.filter(property_type='daire', is_active=True).order_by('-created_at')
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '')
        phone = request.POST.get('phone', '')
        property_id = request.POST.get('property_id', '')
        neighborhood_id = request.POST.get('neighborhood', '')
        source = request.POST.get('source', '')
        notes = request.POST.get('notes', '')
        
        # Validation
        if not full_name or not phone or not neighborhood_id or not source:
            messages.error(request, "Lütfen tüm zorunlu alanları doldurun.")
            return render(request, 'customers/customer_create.html', {
                'segment': 'musteri_ekle',
                'neighborhoods': neighborhoods,
                'properties': properties,
                'form_data': request.POST,
                'user_role': role,
            })
        
        try:
            # Danışman sadece kendi mahallelerindeki müşterileri ekleyebilir
            if role == 'consultant':
                if not neighborhoods.filter(id=neighborhood_id).exists():
                    messages.error(request, "Bu mahalleye müşteri ekleme yetkiniz yok.")
                    return redirect('customer_list')
            
            neighborhood = Neighborhood.objects.get(id=neighborhood_id)
            
            # Yeni müşteri oluştur
            customer = Customer(
                full_name=full_name,
                phone=phone,
                neighborhood=neighborhood,
                consultant=neighborhood.consultant,
                source=source,
                notes=notes,
                meeting_status='bekliyor',
            )
            customer.save()
            
            messages.success(request, "Müşteri başarıyla oluşturuldu.")
            return redirect('customer_list')
        
        except Exception as e:
            messages.error(request, f"Bir hata oluştu: {str(e)}")
    
    context = {
        'segment': 'musteri_ekle',
        'neighborhoods': neighborhoods,
        'properties': properties,
        'user_role': role,
    }
    
    html_template = loader.get_template('customers/customer_create.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def neighborhood_list(request):
    """Mahalle listesi görüntüleme"""
    
    role = get_user_role(request.user)
    
    # Sadece Yönetici ve Müdür erişebilir
    if role not in ['admin', 'manager']:
        messages.error(request, "Bu sayfaya erişim yetkiniz bulunmamaktadır.")
        return redirect('home')
    
    neighborhoods = Neighborhood.objects.all().order_by('name')
    
    context = {
        'segment': 'mahalleler',
        'neighborhoods': neighborhoods,
        'user_role': role,
    }
    
    html_template = loader.get_template('customers/neighborhood_list.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def neighborhood_edit(request, neighborhood_id=None):
    """Mahalle ekleme/düzenleme"""
    
    role = get_user_role(request.user)
    
    # Sadece Yönetici ve Müdür erişebilir
    if role not in ['admin', 'manager']:
        messages.error(request, "Bu sayfaya erişim yetkiniz bulunmamaktadır.")
        return redirect('home')
    
    neighborhood = None
    if neighborhood_id:
        neighborhood = get_object_or_404(Neighborhood, id=neighborhood_id)
    
    if request.method == 'POST':
        name = request.POST.get('name', '')
        district = request.POST.get('district', '')
        consultant_id = request.POST.get('consultant', '')
        
        if not name:
            messages.error(request, "Mahalle adı zorunludur.")
            return redirect('neighborhood_edit', neighborhood_id=neighborhood_id)
        
        if neighborhood:
            # Mevcut mahalleyi güncelle
            neighborhood.name = name
            neighborhood.district = district
            if consultant_id:
                neighborhood.consultant_id = consultant_id
            else:
                neighborhood.consultant = None
            neighborhood.save()
            messages.success(request, "Mahalle başarıyla güncellendi.")
        else:
            # Yeni mahalle oluştur
            new_neighborhood = Neighborhood(
                name=name,
                district=district,
            )
            if consultant_id:
                new_neighborhood.consultant_id = consultant_id
            new_neighborhood.save()
            messages.success(request, "Mahalle başarıyla eklendi.")
        
        return redirect('neighborhood_list')
    
    # Danışmanları getir
    consultants = CustomUser.objects.filter(
        employee_profile__role='consultant',
        is_active=True
    ).distinct()
    
    context = {
        'segment': 'mahalleler',
        'neighborhood': neighborhood,
        'consultants': consultants,
        'user_role': role,
    }
    
    html_template = loader.get_template('customers/neighborhood_edit.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def update_meeting_status(request, customer_id):
    """AJAX ile görüşme durumunu güncelleme"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        customer = get_object_or_404(Customer, id=customer_id)
        
        # Süper kullanıcı değilse ve müşteri danışmanın değilse erişimi engelle
        if not request.user.is_superuser and customer.consultant != request.user:
            return JsonResponse({'status': 'error', 'message': 'Yetkiniz yok'}, status=403)
        
        meeting_result = request.POST.get('meeting_result', '')
        meeting_status = request.POST.get('meeting_status', 'bekliyor')
        
        customer.meeting_result = meeting_result
        customer.meeting_status = meeting_status
        customer.save()
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error', 'message': 'Geçersiz istek'}, status=400)

@login_required(login_url="/login/")
def consultants_by_neighborhood(request, neighborhood_id):
    """Belirli bir mahalleye ait danışmanları JSON olarak döndürür"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            neighborhood = Neighborhood.objects.get(id=neighborhood_id)
            
            # Eğer mahalleye özel bir danışman atanmışsa
            if neighborhood.consultant:
                consultants = [{
                    'id': neighborhood.consultant.id,
                    'name': neighborhood.consultant.get_full_name() or neighborhood.consultant.username
                }]
            else:
                # Tüm danışmanları getir
                consultant_group = Group.objects.filter(name='Danışman').first()
                if consultant_group:
                    users = consultant_group.user_set.all()
                    consultants = [{
                        'id': user.id, 
                        'name': user.get_full_name() or user.username
                    } for user in users]
                else:
                    consultants = []
            
            return JsonResponse({'consultants': consultants})
        except Neighborhood.DoesNotExist:
            return JsonResponse({'error': 'Mahalle bulunamadı'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Geçersiz istek'}, status=400)

@login_required(login_url="/login/")
def customer_reminders(request):
    """Müşteri hatırlatmaları görünümü"""
    
    role = get_user_role(request.user)
    today = timezone.now().date()
    
    # Role göre hatırlatmaları getir
    if request.user.is_superuser or role in ['admin', 'manager', 'secretary']:
        # Yönetici, Müdür ve Santral tüm hatırlatmaları görebilir
        reminders = CustomerReminder.objects.all().order_by('reminder_date')
    else:
        # Danışman sadece kendi müşterilerine ait hatırlatmaları görebilir
        reminders = CustomerReminder.objects.filter(
            customer__consultant=request.user
        ).order_by('reminder_date')
    
    # Duruma göre filtreleme
    status = request.GET.get('status', '')
    if status == 'today':
        reminders = reminders.filter(reminder_date=today)
    elif status == 'upcoming':
        reminders = reminders.filter(reminder_date__gt=today)
    elif status == 'past':
        reminders = reminders.filter(reminder_date__lt=today)
    elif status == 'sent':
        reminders = reminders.filter(is_sent=True)
    elif status == 'unsent':
        reminders = reminders.filter(is_sent=False)
    
    context = {
        'segment': 'musteri_hatirlatmalari',
        'reminders': reminders,
        'filter_status': status,
        'today': today,
        'user_role': role,
    }
    
    html_template = loader.get_template('customers/customer_reminders.html')
    return HttpResponse(html_template.render(context, request))
