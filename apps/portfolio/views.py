# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Portföy Görünümleri
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.urls import reverse
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Property, PropertyEnvironment, PropertyImage, PropertyNote, PortalNotification
from apps.customers.models import Neighborhood
from apps.employees.models import EmployeeProfile
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
import json
from apps.employees.decorators import (
    can_view_portfolio,
    can_add_portfolio,
    can_edit_portfolio,
    can_delete_portfolio,
    require_portfolio_permission
)
from django.views.decorators.http import require_http_methods, require_POST

def get_user_role(user):
    """Kullanıcının rolünü döndürür"""
    # Superuser ise admin rolünü döndür
    if user.is_superuser:
        return 'admin'
    
    try:
        return user.employee_profile.role
    except EmployeeProfile.DoesNotExist:
        return None

@login_required(login_url="/login/")
@can_view_portfolio
def property_list(request):
    """Gayrimenkul listesi görünümü"""
    
    role = get_user_role(request.user)
    
    # Filtreleme
    search = request.GET.get('search', '')
    query = request.GET.get('q', search)  # Modern template için 'q' parametresi
    property_type = request.GET.get('type', '') or request.GET.get('property_type', '')
    status = request.GET.get('status', '')
    neighborhood_id = request.GET.get('neighborhood', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    price_range = request.GET.get('price_range', '')  # Yeni eklenen
    consultant_id = request.GET.get('consultant', '')
    category = request.GET.get('category', '')
    listing_type = request.GET.get('listing_type', '')
    banner_status = request.GET.get('banner_status', '')
    poster_status = request.GET.get('poster_status', '')
    usage_status = request.GET.get('usage_status', '')
    is_furnished = request.GET.get('is_furnished', '')
    is_in_site = request.GET.get('is_in_site', '')
    photo_status = request.GET.get('photo_status', '')
    is_suitable_for_credit = request.GET.get('is_suitable_for_credit', '')
    is_bargainable = request.GET.get('is_bargainable', '')
    
    # Danışman mahalle ID'leri ve kendi portföy ID'leri (sadece consultant için doldurulur)
    consultant_neighborhood_ids = []
    own_ids = []

    requested_tab = request.GET.get('tab', 'own')
    is_admin_or_manager = request.user.is_superuser or role in ['admin', 'manager']

    # Arşiv sekmesi: sadece admin/manager
    if requested_tab == 'archive' and is_admin_or_manager:
        properties_list = Property.objects.filter(is_archived=True)\
            .select_related('neighborhood', 'consultant', 'archived_by')\
            .prefetch_related('images')\
            .order_by('-archived_at')
    # Başlangıç sorgusu - yetki kontrolü ile
    elif is_admin_or_manager:
        properties_list = Property.objects.filter(is_active=True, is_archived=False)\
            .select_related('neighborhood', 'consultant')\
            .prefetch_related('images')
    elif role == 'secretary':
        properties_list = Property.objects.filter(is_active=True, is_archived=False)\
            .select_related('neighborhood', 'consultant')\
            .prefetch_related('images')
    elif role == 'consultant':
        consultant_neighborhood_ids = list(
            Neighborhood.objects.filter(consultant=request.user).values_list('id', flat=True)
        )
        # "Kendi" portföy ID'leri: atanmış mahalledekiler VEYA danışman olarak atanmış portföyler
        own_ids = list(
            Property.objects.filter(is_active=True, is_archived=False).filter(
                Q(neighborhood_id__in=consultant_neighborhood_ids) | Q(consultant=request.user)
            ).values_list('id', flat=True)
        )
        if requested_tab == 'office':
            # Ofis portföyleri: kendi portföy ID'leri dışındaki TÜM aktif portföyler
            properties_list = Property.objects.filter(is_active=True, is_archived=False).exclude(
                id__in=own_ids
            ).select_related('neighborhood', 'consultant').prefetch_related('images')
        else:
            # Kendi portföyleri: atanmış mahallelerdekiler + consultant olarak atanmışlar
            properties_list = Property.objects.filter(
                is_active=True, is_archived=False, id__in=own_ids
            ).select_related('neighborhood', 'consultant').prefetch_related('images')
    else:
        properties_list = Property.objects.none()
        messages.warning(request, "Gayrimenkul listesini görüntüleme yetkiniz sınırlıdır.")
    
    # Arama sorgusu - hem search hem query parametresini destekle
    search_term = query or search
    if search_term:
        properties_list = properties_list.filter(
            Q(apartment_name__icontains=search_term) | 
            Q(web_title__icontains=search_term) |
            Q(description__icontains=search_term) | 
            Q(address__icontains=search_term) | 
            Q(owner_name__icontains=search_term) | 
            Q(owner_listing_number__icontains=search_term) |
            Q(emlakjet_listing_number__icontains=search_term) |
            Q(hepsiemlak_listing_number__icontains=search_term)
        )
    
    # Filtreleri uygula
    if property_type:
        properties_list = properties_list.filter(property_type=property_type)
    if status:
        properties_list = properties_list.filter(status=status)
    if neighborhood_id:
        if role == 'consultant':
            consultant_neighborhoods = Neighborhood.objects.filter(consultant=request.user)
            if consultant_neighborhoods.filter(id=neighborhood_id).exists():
                properties_list = properties_list.filter(neighborhood_id=neighborhood_id)
        else:
            properties_list = properties_list.filter(neighborhood_id=neighborhood_id)
    
    # Fiyat filtresi - min/max veya price_range
    if price_range:
        if price_range == '0-500000':
            properties_list = properties_list.filter(price__lte=500000)
        elif price_range == '500000-1000000':
            properties_list = properties_list.filter(price__gte=500000, price__lte=1000000)
        elif price_range == '1000000-2000000':
            properties_list = properties_list.filter(price__gte=1000000, price__lte=2000000)
        elif price_range == '2000000-':
            properties_list = properties_list.filter(price__gte=2000000)
    else:
        if min_price:
            try:
                properties_list = properties_list.filter(price__gte=float(min_price))
            except ValueError:
                pass
        if max_price:
            try:
                properties_list = properties_list.filter(price__lte=float(max_price))
            except ValueError:
                pass
    
    if consultant_id:
        if request.user.is_superuser or role in ['admin', 'manager']:
            properties_list = properties_list.filter(consultant_id=consultant_id)
    if category:
        properties_list = properties_list.filter(category=category)
    if listing_type:
        properties_list = properties_list.filter(listing_type=listing_type)
    if banner_status:
        properties_list = properties_list.filter(banner_status=banner_status)
    if poster_status:
        properties_list = properties_list.filter(poster_status=poster_status)
    if usage_status:
        properties_list = properties_list.filter(usage_status=usage_status)
    if is_furnished == 'true':
        properties_list = properties_list.filter(is_furnished=True)
    elif is_furnished == 'false':
        properties_list = properties_list.filter(is_furnished=False)
    if is_in_site == 'true':
        properties_list = properties_list.filter(is_in_site=True)
    elif is_in_site == 'false':
        properties_list = properties_list.filter(is_in_site=False)
    if photo_status:
        properties_list = properties_list.filter(photo_status=photo_status)
    if is_suitable_for_credit == 'true':
        properties_list = properties_list.filter(is_suitable_for_credit=True)
    if is_bargainable == 'true':
        properties_list = properties_list.filter(is_bargainable=True)
    
    # Sıralama
    properties_list = properties_list.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(properties_list, 12)  # Modern template için 12 kayıt
    page = request.GET.get('page', 1)
    
    try:
        properties = paginator.page(page)
    except PageNotAnInteger:
        properties = paginator.page(1)
    except EmptyPage:
        properties = paginator.page(paginator.num_pages)
    
    # İlgili mahalleler - yetki kontrolü ile
    if request.user.is_superuser or role in ['admin', 'manager', 'secretary']:
        neighborhoods = Neighborhood.objects.all().order_by('name')
    elif role == 'consultant':
        neighborhoods = Neighborhood.objects.filter(consultant=request.user).order_by('name')
    else:
        neighborhoods = Neighborhood.objects.none()
    
    # Danışman listesi - yetki kontrolü ile
    if request.user.is_superuser or role in ['admin', 'manager']:
        consultants = EmployeeProfile.objects.filter(role='consultant', is_active=True).select_related('user')
    else:
        consultants = EmployeeProfile.objects.none()
    
    context = {
        'segment': 'gayrimenkul',
        'properties': properties,
        'total_properties': Property.objects.filter(is_archived=False).count(),
        'active_properties': Property.objects.filter(is_active=True, is_archived=False).count(),
        'satilik_count': Property.objects.filter(status='satilik', is_active=True, is_archived=False).count(),
        'kiralik_count': Property.objects.filter(status='kiralik', is_active=True, is_archived=False).count(),
        # Dan\u0131\u015fman i\u00e7in Kendi/Ofis portf\u00f6y sekmesi say\u0131lar\u0131
        'own_count': (len(own_ids) if role == 'consultant' else 0),
        'office_count': (
            Property.objects.filter(is_active=True, is_archived=False).exclude(id__in=own_ids).count()
            if role == 'consultant' else 0
        ),
        'archive_count': Property.objects.filter(is_archived=True).count() if is_admin_or_manager else 0,
        'active_tab': requested_tab,
        'is_office_view': (role == 'consultant' and requested_tab == 'office'),
        'is_archive_view': (requested_tab == 'archive' and is_admin_or_manager),
        'is_consultant': (role == 'consultant'),
        'is_admin_or_manager': is_admin_or_manager,

        'neighborhoods': neighborhoods,
        'consultants': consultants,
        'user_role': role,
        'query': search_term,
        'status': status,
        'property_type': property_type,
        'price_range': price_range,
        'neighborhood': neighborhood_id,
        'filters': {
            'search': search_term,
            'property_type': property_type,
            'status': status,
            'neighborhood_id': neighborhood_id,
            'min_price': min_price,
            'max_price': max_price,
            'consultant_id': consultant_id,
            'category': category,
            'listing_type': listing_type,
            'banner_status': banner_status,
            'poster_status': poster_status,
            'usage_status': usage_status,
            'is_furnished': is_furnished,
            'is_in_site': is_in_site,
            'photo_status': photo_status,
            'is_suitable_for_credit': is_suitable_for_credit,
            'is_bargainable': is_bargainable,
        }
    }
    
    html_template = loader.get_template('portfolio/property_list.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def property_detail(request, property_id):
    """Gayrimenkul detay görünümü"""
    property_obj = get_object_or_404(Property, id=property_id)
    role = get_user_role(request.user)
    
    # Yetki kontrolü
    is_own_property = True  # Varsayılan: mülk sahibi bilgileri görünür
    if not request.user.is_superuser and role not in ['admin', 'manager', 'secretary']:
        if role == 'consultant':
            # Danışman tüm portföyleri görebilir, ama iletişim bilgileri şu durumlarda görünür:
            # 1) Portföy, danışmanın atandığı mahallede
            # 2) Portföy, danışmanın kendisine atanmış (consultant alanı)
            consultant_neighborhood_ids = list(
                Neighborhood.objects.filter(consultant=request.user).values_list('id', flat=True)
            )
            in_own_neighborhood = (
                property_obj.neighborhood_id is not None
                and property_obj.neighborhood_id in consultant_neighborhood_ids
            )
            is_own_consultant = (property_obj.consultant_id == request.user.id)
            is_own_property = in_own_neighborhood or is_own_consultant
        else:
            messages.error(request, f"Gayrimenkul detaylarını görüntüleme yetkiniz bulunmamaktadır. Mevcut rolünüz: {role or 'Tanımsız'}")
            return redirect('property_list')

    # Çevre bilgileri
    environments = property_obj.environments.all()

    # Resimler
    images = property_obj.images.all().order_by('order')

    # Sunulan müşteriler
    customer_presentations = property_obj.customer_presentations.select_related(
        'customer', 'created_by'
    ).order_by('-created_at')

    # Bu portföye sunum yapılan müşterilerin çağrıları
    from apps.calls.models import CallLog
    presented_customer_ids = list(
        property_obj.customer_presentations.values_list('customer_id', flat=True).distinct()
    )
    property_calls = CallLog.objects.filter(
        customer_id__in=presented_customer_ids
    ).select_related('customer', 'user').order_by('-start_time')

    # Son Aktiviteler — tüm kaynakları birleştir
    activities = []

    for note in property_obj.notes.select_related('user').all():
        activities.append({
            'type': 'note', 'icon': 'fas fa-sticky-note',
            'color': '#f59e0b', 'bg': '#fef3c7',
            'title': 'Not eklendi',
            'description': note.note[:120] + ('…' if len(note.note) > 120 else ''),
            'user': note.user.get_full_name() if note.user else '—',
            'date': note.created_at,
        })

    for pres in customer_presentations:
        name = pres.customer.display_name if pres.customer else '?'
        activities.append({
            'type': 'presentation', 'icon': 'fas fa-home',
            'color': '#8b5cf6', 'bg': '#ede9fe',
            'title': 'Daire sunumu yapıldı',
            'description': f'{name} müşterisine sunum yapıldı.',
            'user': pres.created_by.get_full_name() if pres.created_by else '—',
            'date': pres.created_at,
        })

    for call in property_calls:
        direction = 'Gelen' if call.direction == 'inbound' else 'Giden'
        cname = call.customer.display_name if call.customer else call.caller
        activities.append({
            'type': 'call',
            'icon': 'fas fa-phone-volume' if call.direction == 'inbound' else 'fas fa-phone-alt',
            'color': '#ef4444' if call.status == 'missed' else ('#3b82f6' if call.direction == 'inbound' else '#10b981'),
            'bg': '#fee2e2' if call.status == 'missed' else ('#dbeafe' if call.direction == 'inbound' else '#d1fae5'),
            'title': f'{direction} çağrı — {call.get_status_display()}',
            'description': f'{cname} · {call.caller} → {call.called}',
            'user': call.user.get_full_name() if call.user else '—',
            'date': call.start_time,
        })

    for notif in property_obj.portal_notifications.select_related('user').all():
        activities.append({
            'type': 'portal', 'icon': 'fas fa-bell',
            'color': '#64748b', 'bg': '#f1f5f9',
            'title': f'{notif.get_portal_display()} portal bildirimi',
            'description': 'İlan süresi dolumu bildirimi alındı.',
            'user': notif.user.get_full_name() if notif.user else '—',
            'date': notif.created_at,
        })

    activities.append({
        'type': 'created', 'icon': 'fas fa-plus-circle',
        'color': '#10b981', 'bg': '#d1fae5',
        'title': 'Portföy oluşturuldu',
        'description': f'{property_obj.apartment_name or "Portföy"} sisteme eklendi.',
        'user': '—',
        'date': property_obj.created_at,
    })

    activities.sort(key=lambda x: x['date'], reverse=True)

    context = {
        'segment': 'gayrimenkul',
        'property': property_obj,
        'environments': environments,
        'images': images,
        'user_role': role,
        'is_own_property': is_own_property,
        'customer_presentations': customer_presentations,
        'property_calls': property_calls,
        'activities': activities,
    }

    html_template = loader.get_template('portfolio/property_detail.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
@can_add_portfolio
def property_create(request):
    """Yeni gayrimenkul ekleme"""
    role = get_user_role(request.user)
    
    # Yetki kontrolü - Sadece Yönetici, Müdür, Danışman ve Santral ekleme yapabilir
    if not request.user.is_superuser and role not in ['admin', 'manager', 'consultant', 'secretary']:
        messages.error(request, f"Gayrimenkul ekleme yetkiniz bulunmamaktadır. Mevcut rolünüz: {role or 'Tanımsız'}. Sadece Yönetici, Müdür, Danışman ve Santral gayrimenkul ekleyebilir.")
        return redirect('property_list')
    
    # Mahalleler - yetki kontrolü ile
    if request.user.is_superuser or role in ['admin', 'manager', 'secretary']:
        neighborhoods = Neighborhood.objects.all().order_by('name')
    elif role == 'consultant':
        neighborhoods = Neighborhood.objects.filter(consultant=request.user).order_by('name')
    else:
        neighborhoods = Neighborhood.objects.none()
    
    if request.method == 'POST':
        # POST verilerini detaylı yazdır
        print("============= YENİ GAYRİMENKUL EKLE - POST VERİLERİ =============")
        print(f"POST içeriği alındı - tarih/saat: {timezone.now().strftime('%d.%m.%Y %H:%M:%S')}")
        print(f"apartment_name: {request.POST.get('apartment_name', 'Boş')}")
        print(f"web_title: {request.POST.get('web_title', 'Boş')}")
        print(f"description: {request.POST.get('description', 'Boş')[:30]}{'...' if len(request.POST.get('description', '')) > 30 else ''}")
        print(f"property_type: {request.POST.get('property_type', 'Boş')}")
        print(f"status: {request.POST.get('status', 'Boş')}")
        print(f"price: {request.POST.get('price', 'Boş')}")
        print(f"neighborhood: {request.POST.get('neighborhood', 'Boş')}")
        print(f"address: {request.POST.get('address', 'Boş')[:30]}{'...' if len(request.POST.get('address', '')) > 30 else ''}")
        print(f"map_coordinates: {request.POST.get('map_coordinates', 'Boş')}")
        print(f"room_count: {request.POST.get('room_count', 'Boş')}")
        print(f"gross_area: {request.POST.get('gross_area', 'Boş')}")
        print(f"net_area: {request.POST.get('net_area', 'Boş')}")
        print(f"floor: {request.POST.get('floor', 'Boş')}")
        print(f"building_age: {request.POST.get('building_age', 'Boş')}")
        print(f"heating: {request.POST.get('heating', 'Boş')}")
        print(f"balcony: {request.POST.get('balcony', 'Boş')}")
        print(f"dues: {request.POST.get('dues', 'Boş')}")
        print(f"deed_status: {request.POST.get('deed_status', 'Boş')}")
        print(f"is_suitable_for_credit: {'is_suitable_for_credit' in request.POST}")
        print(f"is_bargainable: {'is_bargainable' in request.POST}")
        print(f"owner_name: {request.POST.get('owner_name', 'Boş')}")
        print(f"owner_phone: {request.POST.get('owner_phone', 'Boş')}")
        print(f"owner_listing_number: {request.POST.get('owner_listing_number', 'Boş')}")
        print(f"emlakjet_listing_number: {request.POST.get('emlakjet_listing_number', 'Boş')}")
        print(f"hepsiemlak_listing_number: {request.POST.get('hepsiemlak_listing_number', 'Boş')}")
        print(f"website_listing_number: {request.POST.get('website_listing_number', 'Boş')}")
        print(f"has_banner: {request.POST.get('has_banner', 'Boş')}")
        print(f"has_photos: {request.POST.get('has_photos', 'Boş')}")
        print(f"key_holder: {request.POST.get('key_holder', 'Boş')}")
        print(f"listing_date: {request.POST.get('listing_date', 'Boş')}")
        print(f"floor_count: {request.POST.get('floor_count', 'Boş')}")
        print(f"usage_status: {request.POST.get('usage_status', 'Boş')}")
        
        # Resim sayısı
        if request.FILES:
            print(f"Yüklenen resim sayısı: {len(request.FILES.getlist('photos[]'))}")
        
        print("================================================================")
        
        # Temel bilgiler
        apartment_name = request.POST.get('apartment_name', '')
        web_title = request.POST.get('web_title', '')
        description = request.POST.get('description', '')
        property_type = request.POST.get('property_type', '')
        status = request.POST.get('status', '')
        price = request.POST.get('price', '')
        neighborhood_id = request.POST.get('neighborhood', '')
        address = request.POST.get('address', '')
        map_coordinates = request.POST.get('map_coordinates', '')
        room_count = request.POST.get('room_count', '')
        usage_status = request.POST.get('usage_status', '')
        floor_count = request.POST.get('floor_count', '')
        floor = request.POST.get('floor', '')
        
        # Branda/Fotoğraf durumu
        has_banner = request.POST.get('has_banner', '')
        banner_status = 'asildi' if has_banner == 'var' else 'asilmadi'
        
        has_photos = request.POST.get('has_photos', '')
        photo_status = 'cekildi' if has_photos == 'var' else 'cekilmedi'
        
        # Balkon kontrolü
        balcony = request.POST.get('balcony', '')
        has_balcony = balcony == 'var'
        
        # Validation
        if not apartment_name or not property_type or not status or not price or not neighborhood_id:
            messages.error(request, "Lütfen zorunlu alanları doldurun.")
            return redirect('property_create')
        
        try:
            price = float(price.replace(',', '.'))
            neighborhood = Neighborhood.objects.get(id=neighborhood_id)
            
            # Mahalle yetki kontrolü
            if role == 'consultant':
                if not neighborhoods.filter(id=neighborhood_id).exists():
                    messages.error(request, "Bu mahalleye gayrimenkul ekleme yetkiniz yok.")
                    return redirect('property_create')
            
            # Yeni portföy oluştur
            property_obj = Property(
                apartment_name=apartment_name,
                web_title=web_title,
                description=description,
                property_type=property_type,
                status=status,
                price=price,
                neighborhood=neighborhood,
                address=address,
                map_coordinates=map_coordinates,
                room_count=room_count,
                usage_status=usage_status,
                floor_count=floor_count,
                floor=floor,
                consultant=request.user,
                banner_status=banner_status,
                photo_status=photo_status,
            )
            
            # Detay bilgileri
            if property_type == 'daire' or property_type == 'mustakil' or property_type == 'dublex':
                property_obj.gross_area = request.POST.get('gross_area', None)
                property_obj.net_area = request.POST.get('net_area', None)
                property_obj.heating = request.POST.get('heating', '')
                property_obj.has_balcony = has_balcony
                property_obj.dues = request.POST.get('dues', None)
            
            # Diğer bilgiler
            property_obj.deed_status = request.POST.get('deed_status', '')
            property_obj.is_suitable_for_credit = 'is_suitable_for_credit' in request.POST
            property_obj.is_bargainable = 'is_bargainable' in request.POST
            property_obj.is_furnished = 'is_furnished' in request.POST
            property_obj.is_in_site = 'is_in_site' in request.POST
            property_obj.is_exchangeable = 'is_exchangeable' in request.POST
            
            # Portföy sahibi bilgileri
            property_obj.owner_name = request.POST.get('owner_name', '')
            property_obj.owner_phone = request.POST.get('owner_phone', '')
            property_obj.owner_listing_number = request.POST.get('owner_listing_number', '')
            property_obj.emlakjet_listing_number = request.POST.get('emlakjet_listing_number', '')
            property_obj.hepsiemlak_listing_number = request.POST.get('hepsiemlak_listing_number', '')
            property_obj.website_listing_number = request.POST.get('website_listing_number', '')
            property_obj.branda_number = request.POST.get('branda_number', '')
            property_obj.yetki_numarasi = request.POST.get('yetki_numarasi', '')
            yetki_suresi = request.POST.get('yetki_suresi', '')
            if yetki_suresi:
                property_obj.yetki_suresi = yetki_suresi
            else:
                property_obj.yetki_suresi = None

            # Operasyonel bilgiler
            property_obj.key_holder = request.POST.get('key_holder', '')
            listing_date = request.POST.get('listing_date', '')
            if listing_date:
                property_obj.listing_date = listing_date
            
            property_obj.save()
            
            # Debug için kaydedilen property değerlerini göster
            print("============= KAYIT İŞLEMİ SONRASI GAYRİMENKUL BİLGİLERİ =============")
            print(f"ID: {property_obj.id}")
            print(f"Daire Adı: {property_obj.apartment_name}")
            print(f"Web Başlığı: {property_obj.web_title}")
            print(f"Açıklama: {property_obj.description[:50]}{'...' if len(property_obj.description) > 50 else ''}")
            print(f"Emlak Tipi: {property_obj.property_type}")
            print(f"Durum: {property_obj.status}")
            print(f"Fiyat: {property_obj.price}")
            print(f"Mahalle: {property_obj.neighborhood.name}")
            print(f"Adres: {property_obj.address[:50]}{'...' if len(property_obj.address) > 50 else ''}")
            print(f"Harita Koordinatları: {property_obj.map_coordinates}")
            print(f"Brüt Alan: {property_obj.gross_area}")
            print(f"Net Alan: {property_obj.net_area}")
            print(f"Oda Sayısı: {property_obj.room_count}")
            print(f"Kat Sayısı: {property_obj.floor_count}")
            print(f"Bulunduğu Kat: {property_obj.floor}")
            print(f"Isıtma: {property_obj.heating}")
            print(f"Balkon: {'var' if property_obj.has_balcony else 'yok'}")
            print(f"Aidat: {property_obj.dues}")
            print(f"Tapu Durumu: {property_obj.deed_status}")
            print(f"Krediye Uygun: {'Evet' if property_obj.is_suitable_for_credit else 'Hayır'}")
            print(f"Pazarlık Payı: {'Var' if property_obj.is_bargainable else 'Yok'}")
            print(f"Mal Sahibi: {property_obj.owner_name}")
            print(f"Mal Sahibi Telefon: {property_obj.owner_phone}")
            print(f"Sahibinden İlan No: {property_obj.owner_listing_number}")
            print(f"Emlakjet İlan No: {property_obj.emlakjet_listing_number}")
            print(f"Hepsiemlak İlan No: {property_obj.hepsiemlak_listing_number}")
            print(f"Web Sitesi İlan No: {property_obj.website_listing_number}")
            print(f"Branda No: {property_obj.branda_number}")
            print(f"Anahtar Kimde: {property_obj.key_holder}")
            print(f"İlan Tarihi: {property_obj.listing_date}")
            print(f"Branda Durumu: {property_obj.banner_status}")
            print(f"Fotoğraf Durumu: {property_obj.photo_status}")
            print(f"Danışman: {property_obj.consultant.get_full_name() if property_obj.consultant else 'Belirtilmemiş'}")
            print(f"Oluşturulma Tarihi: {property_obj.created_at}")
            print(f"Aktif: {'Evet' if property_obj.is_active else 'Hayır'}")
            print("=================================================================")
            
            # Fotoğrafları doğrudan işle
            if request.FILES:
                photos = request.FILES.getlist('photos[]')
                new_main_photo_order = request.POST.get('new_main_photo_order', None)
                
                print(f"Yüklenen yeni resim sayısı: {len(photos)}")
                if new_main_photo_order:
                    print(f"Yeni ana fotoğraf sırası: {new_main_photo_order}")
                
                # Mevcut fotoğraf sayısını al (sıralama için)
                existing_photos_count = property_obj.images.count()
                
                for index, photo in enumerate(photos):
                    # Dosya boyutu kontrolü (5MB)
                    if photo.size > 5 * 1024 * 1024:
                        print(f"Fotoğraf çok büyük, atlanıyor: {photo.name}")
                        continue
                    
                    # Dosya tipi kontrolü
                    if photo.content_type not in ['image/jpeg', 'image/png', 'image/jpg']:
                        print(f"Desteklenmeyen format, atlanıyor: {photo.name}")
                        continue
                    
                    # Başlık oluştur
                    title = photo.name.split('.')[0][:50]
                    
                    # Ana fotoğraf mı kontrol et (sadece mevcut ana fotoğraf yoksa)
                    has_existing_main = property_obj.images.filter(is_main_photo=True).exists()
                    is_main_photo = False
                    if not has_existing_main and new_main_photo_order and (str(index + 1) == str(new_main_photo_order)):
                        is_main_photo = True
                    
                    # Fotoğrafı kaydet ve property ile ilişkilendir
                    PropertyImage.objects.create(
                        property=property_obj,
                        image=photo,
                        title=title,
                        order=existing_photos_count + index + 1,
                        is_main_photo=is_main_photo
                    )
                    
                    print(f"Fotoğraf kaydedildi: {photo.name}, Sıra: {existing_photos_count + index + 1}, Ana fotoğraf: {is_main_photo}")
            
            # Ayrıca halihazırda yüklenmiş fotoğrafları da ilişkilendir (eski mekanizma için)
            image_ids = request.POST.getlist('image_ids[]')
            if image_ids:
                for image_id in image_ids:
                    try:
                        image = PropertyImage.objects.get(id=image_id)
                        if not image.property or image.property != property_obj:
                            image.property = property_obj
                            image.save()
                    except PropertyImage.DoesNotExist:
                        pass
            
            messages.success(request, "Gayrimenkul başarıyla eklendi.")
            return redirect('property_detail', property_id=property_obj.id)
            
        except Exception as e:
            messages.error(request, f"Bir hata oluştu: {str(e)}")
            print(f"GAYRİMENKUL EKLEME HATASI: {str(e)}")
    
    context = {
        'segment': 'gayrimenkul_ekle',
        'neighborhoods': neighborhoods,
        'property_types': Property.PROPERTY_TYPE_CHOICES,
        'status_choices': Property.STATUS_CHOICES,
        'heating_choices': Property.HEATING_CHOICES,
        'deed_status_choices': Property.DEED_STATUS_CHOICES,
        'key_holder_choices': Property.KEY_HOLDER_CHOICES,
    }
    
    html_template = loader.get_template('portfolio/property_create.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
@can_edit_portfolio
def property_update(request, property_id):
    """Gayrimenkul güncelleme"""
    property_obj = get_object_or_404(Property, id=property_id)
    role = get_user_role(request.user)
    
    # Yetki kontrolü
    if not request.user.is_superuser and role not in ['admin', 'manager']:
        if role == 'consultant':
            # Danışman sadece kendi mahallelerindeki gayrimenkulleri güncelleyebilir
            consultant_neighborhoods = Neighborhood.objects.filter(consultant=request.user)
            if property_obj.neighborhood not in consultant_neighborhoods:
                messages.error(request, f"Bu gayrimenkul {property_obj.neighborhood.name} mahallesinde bulunuyor ve bu mahalleyi düzenleme yetkiniz bulunmamaktadır.")
                return redirect('property_list')
        else:
            messages.error(request, f"Gayrimenkul düzenleme yetkiniz bulunmamaktadır. Mevcut rolünüz: {role or 'Tanımsız'}. Sadece Yönetici ve Müdür düzenleme yapabilir.")
            return redirect('property_list')
    
    # Mahalleler - yetki kontrolü ile
    if request.user.is_superuser or role in ['admin', 'manager']:
        neighborhoods = Neighborhood.objects.all().order_by('name')
    elif role == 'consultant':
        neighborhoods = Neighborhood.objects.filter(consultant=request.user).order_by('name')
    else:
        neighborhoods = Neighborhood.objects.none()
    
    # Debug için property değerlerini yazdır
    print("============= GAYRİMENKUL GÜNCELLEME SAYFASI AÇILDI =============")
    print(f"Güncelleme sayfası açıldı - ID: {property_obj.id} - Tarih/Saat: {timezone.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"ID: {property_obj.id}")
    print(f"Başlık: {property_obj.apartment_name}")
    print(f"Web Başlığı: {property_obj.web_title}")
    print(f"Açıklama: {property_obj.description[:100]}{'...' if len(property_obj.description) > 100 else ''}")
    print(f"Emlak Tipi: {property_obj.property_type}")
    print(f"Durum: {property_obj.status}")
    print(f"Fiyat: {property_obj.price}")
    print(f"Mahalle: {property_obj.neighborhood.name if property_obj.neighborhood else 'Yok'}")
    print(f"Adres: {property_obj.address[:100]}{'...' if len(property_obj.address) > 100 else ''}")
    print(f"Brüt Alan: {property_obj.gross_area}")
    print(f"Net Alan: {property_obj.net_area}")
    print(f"Oda Sayısı: {property_obj.room_count}")
    print(f"Bulunduğu Kat: {property_obj.floor}")
    print(f"Kat Sayısı: {property_obj.floor_count}")
    print(f"Bina Yaşı: {property_obj.building_age}")
    print(f"Isıtma: {property_obj.heating}")
    print(f"Balkon: {'var' if property_obj.has_balcony else 'yok'}")
    print(f"Aidat: {property_obj.dues}")
    print(f"Kullanım Durumu: {property_obj.usage_status}")
    print(f"Tapu Durumu: {property_obj.deed_status}")
    print(f"Krediye Uygun: {'Evet' if property_obj.is_suitable_for_credit else 'Hayır'}")
    print(f"Pazarlık Payı: {'Var' if property_obj.is_bargainable else 'Yok'}")
    print(f"Eşyalı: {'Evet' if property_obj.is_furnished else 'Hayır'}")
    print(f"Site İçerisinde: {'Evet' if property_obj.is_in_site else 'Hayır'}")
    print(f"Takas: {'Evet' if property_obj.is_exchangeable else 'Hayır'}")
    print(f"Kategori: {property_obj.category}")
    print(f"İlan Türü: {property_obj.listing_type}")
    print(f"Mal Sahibi: {property_obj.owner_name}")
    print(f"Mal Sahibi Telefon: {property_obj.owner_phone}")
    print(f"Mal Sahibi İlan No: {property_obj.owner_listing_number}")
    print(f"Branda No: {property_obj.branda_number}")
    print(f"Anahtar Kimde: {property_obj.key_holder}")
    print(f"İlan Tarihi: {property_obj.listing_date}")
    print(f"Branda Durumu: {property_obj.banner_status}")
    print(f"Fotoğraf Durumu: {property_obj.photo_status}")
    print(f"Danışman: {property_obj.consultant.get_full_name() if property_obj.consultant else 'Belirtilmemiş'}")
    print(f"Oluşturulma Tarihi: {property_obj.created_at}")
    print(f"Güncellenme Tarihi: {property_obj.updated_at}")
    print(f"Aktif: {'Evet' if property_obj.is_active else 'Hayır'}")
    
    # Resim sayısı
    images_count = property_obj.images.count()
    print(f"Mevcut Resim Sayısı: {images_count}")
    
    # Çevre bilgileri
    environments = property_obj.environments.all()
    if environments:
        print("Çevre Bilgileri:")
        for env in environments:
            print(f"  - {env.place_name}: {env.distance}")
    
    print("=================================================================")
    
    if request.method == 'POST':
        # POST verilerini detaylı yazdır
        print("============= GAYRİMENKUL GÜNCELLEME - POST VERİLERİ =============")
        print(f"POST içeriği alındı - tarih/saat: {timezone.now().strftime('%d.%m.%Y %H:%M:%S')}")
        print(f"apartment_name: {request.POST.get('apartment_name', 'Boş')}")
        print(f"web_title: {request.POST.get('web_title', 'Boş')}")
        print(f"description: {request.POST.get('description', 'Boş')[:30]}{'...' if len(request.POST.get('description', '')) > 30 else ''}")
        print(f"property_type: {request.POST.get('property_type', 'Boş')}")
        print(f"status: {request.POST.get('status', 'Boş')}")
        print(f"price: {request.POST.get('price', 'Boş')}")
        print(f"neighborhood: {request.POST.get('neighborhood', 'Boş')}")
        print(f"address: {request.POST.get('address', 'Boş')[:30]}{'...' if len(request.POST.get('address', '')) > 30 else ''}")
        print(f"map_coordinates: {request.POST.get('map_coordinates', 'Boş')}")
        print(f"room_count: {request.POST.get('room_count', 'Boş')}")
        print(f"gross_area: {request.POST.get('gross_area', 'Boş')}")
        print(f"net_area: {request.POST.get('net_area', 'Boş')}")
        print(f"floor: {request.POST.get('floor', 'Boş')}")
        print(f"building_age: {request.POST.get('building_age', 'Boş')}")
        print(f"heating: {request.POST.get('heating', 'Boş')}")
        print(f"balcony: {request.POST.get('balcony', 'Boş')}")
        print(f"dues: {request.POST.get('dues', 'Boş')}")
        print(f"deed_status: {request.POST.get('deed_status', 'Boş')}")
        print(f"is_suitable_for_credit: {'is_suitable_for_credit' in request.POST}")
        print(f"is_bargainable: {'is_bargainable' in request.POST}")
        print(f"owner_name: {request.POST.get('owner_name', 'Boş')}")
        print(f"owner_phone: {request.POST.get('owner_phone', 'Boş')}")
        print(f"owner_listing_number: {request.POST.get('owner_listing_number', 'Boş')}")
        print(f"emlakjet_listing_number: {request.POST.get('emlakjet_listing_number', 'Boş')}")
        print(f"hepsiemlak_listing_number: {request.POST.get('hepsiemlak_listing_number', 'Boş')}")
        print(f"website_listing_number: {request.POST.get('website_listing_number', 'Boş')}")
        print(f"has_banner: {request.POST.get('has_banner', 'Boş')}")
        print(f"has_photos: {request.POST.get('has_photos', 'Boş')}")
        print(f"key_holder: {request.POST.get('key_holder', 'Boş')}")
        print(f"listing_date: {request.POST.get('listing_date', 'Boş')}")
        print(f"floor_count: {request.POST.get('floor_count', 'Boş')}")
        print(f"floor: {request.POST.get('floor', 'Boş')}")
        print(f"usage_status: {request.POST.get('usage_status', 'Boş')}")
        
        # Çevre bilgileri
        place_names = request.POST.getlist('place_name')
        distances = request.POST.getlist('distance')
        if place_names:
            print("Yeni Çevre Bilgileri:")
            for i in range(len(place_names)):
                if place_names[i]:
                    print(f"  - {place_names[i]}: {distances[i] if i < len(distances) else 'Mesafe belirtilmemiş'}")
        
        # Resim sayısı
        if request.FILES:
            print(f"Yüklenen yeni resim sayısı: {len(request.FILES.getlist('photos[]'))}")
        
        print("=================================================================")
        
        # Temel bilgileri güncelle
        property_obj.apartment_name = request.POST.get('apartment_name', '')
        property_obj.web_title = request.POST.get('web_title', '')
        property_obj.description = request.POST.get('description', '')
        property_obj.status = request.POST.get('status', '')
        property_obj.price = request.POST.get('price', '').replace(',', '.')
        property_obj.neighborhood_id = request.POST.get('neighborhood', '')
        property_obj.address = request.POST.get('address', '')
        property_obj.property_type = request.POST.get('property_type', '')
        property_obj.room_count = request.POST.get('room_count', '')
        property_obj.usage_status = request.POST.get('usage_status', '')
        property_obj.floor_count = request.POST.get('floor_count', '')
        property_obj.floor = request.POST.get('floor', '')
        property_obj.map_coordinates = request.POST.get('map_coordinates', '')
        
        # Branda/Fotoğraf durumu
        has_banner = request.POST.get('has_banner', '')
        if has_banner == 'var':
            property_obj.banner_status = 'asildi'
        elif has_banner == 'yok':
            property_obj.banner_status = 'asilmadi'
            
        has_photos = request.POST.get('has_photos', '')
        if has_photos == 'var':
            property_obj.photo_status = 'cekildi'
        elif has_photos == 'yok':
            property_obj.photo_status = 'cekilmedi'
        
        # Detay bilgileri güncelle
        if property_obj.property_type in ['daire', 'mustakil', 'dublex']:
            property_obj.gross_area = request.POST.get('gross_area', None) or None
            property_obj.net_area = request.POST.get('net_area', None) or None
            property_obj.heating = request.POST.get('heating', '')
            property_obj.dues = request.POST.get('dues', None) or None
            
            # Balkon düzeltmesi (balcony form alanı -> has_balcony model alanı)
            balcony = request.POST.get('balcony', '')
            property_obj.has_balcony = balcony == 'var'
        
        # Diğer bilgileri güncelle
        property_obj.deed_status = request.POST.get('deed_status', '')
        property_obj.is_suitable_for_credit = 'is_suitable_for_credit' in request.POST
        property_obj.is_bargainable = 'is_bargainable' in request.POST
        property_obj.is_furnished = 'is_furnished' in request.POST
        property_obj.is_in_site = 'is_in_site' in request.POST
        property_obj.is_exchangeable = 'is_exchangeable' in request.POST
        
        # Portföy sahibi bilgilerini güncelle
        property_obj.owner_name = request.POST.get('owner_name', '')
        property_obj.owner_phone = request.POST.get('owner_phone', '')
        property_obj.owner_listing_number = request.POST.get('owner_listing_number', '')
        property_obj.emlakjet_listing_number = request.POST.get('emlakjet_listing_number', '')
        property_obj.hepsiemlak_listing_number = request.POST.get('hepsiemlak_listing_number', '')
        property_obj.website_listing_number = request.POST.get('website_listing_number', '')
        property_obj.branda_number = request.POST.get('branda_number', '')
        
        # Operasyonel bilgileri güncelle
        property_obj.key_holder = request.POST.get('key_holder', '')
        listing_date = request.POST.get('listing_date', '')
        if listing_date:
            property_obj.listing_date = listing_date
        
        property_obj.save()
        
        # Form işlendikten sonra değerleri kontrol et
        print("============= GÜNCELLEME SONRASI GAYRİMENKUL BİLGİLERİ =============")
        print(f"ID: {property_obj.id}")
        print(f"Başlık: {property_obj.apartment_name}")
        print(f"Web Başlığı: {property_obj.web_title}")
        print(f"Açıklama: {property_obj.description[:50]}{'...' if len(property_obj.description) > 50 else ''}")
        print(f"Emlak Tipi: {property_obj.property_type}")
        print(f"Durum: {property_obj.status}")
        print(f"Fiyat: {property_obj.price}")
        print(f"Mahalle: {property_obj.neighborhood.name if property_obj.neighborhood else 'Yok'}")
        print(f"Adres: {property_obj.address[:50]}{'...' if len(property_obj.address) > 50 else ''}")
        print(f"Harita Koordinatları: {property_obj.map_coordinates}")
        print(f"Brüt Alan: {property_obj.gross_area}")
        print(f"Net Alan: {property_obj.net_area}")
        print(f"Oda Sayısı: {property_obj.room_count}")
        print(f"Bulunduğu Kat: {property_obj.floor}")
        print(f"Kat Sayısı: {property_obj.floor_count}")
        print(f"Bina Yaşı: {property_obj.building_age}")
        print(f"Isıtma: {property_obj.heating}")
        print(f"Balkon: {'var' if property_obj.has_balcony else 'yok'}")
        print(f"Aidat: {property_obj.dues}")
        print(f"Kullanım Durumu: {property_obj.usage_status}")
        print(f"Tapu Durumu: {property_obj.deed_status}")
        print(f"Krediye Uygun: {'Evet' if property_obj.is_suitable_for_credit else 'Hayır'}")
        print(f"Pazarlık Payı: {'Var' if property_obj.is_bargainable else 'Yok'}")
        print(f"Eşyalı: {'Evet' if property_obj.is_furnished else 'Hayır'}")
        print(f"Site İçerisinde: {'Evet' if property_obj.is_in_site else 'Hayır'}")
        print(f"Takas: {'Evet' if property_obj.is_exchangeable else 'Hayır'}")
        print(f"Mal Sahibi: {property_obj.owner_name}")
        print(f"Mal Sahibi Telefon: {property_obj.owner_phone}")
        print(f"Sahibinden İlan No: {property_obj.owner_listing_number}")
        print(f"Emlakjet İlan No: {property_obj.emlakjet_listing_number}")
        print(f"Hepsiemlak İlan No: {property_obj.hepsiemlak_listing_number}")
        print(f"Web Sitesi İlan No: {property_obj.website_listing_number}")
        print(f"Branda No: {property_obj.branda_number}")
        print(f"Anahtar Kimde: {property_obj.key_holder}")
        print(f"İlan Tarihi: {property_obj.listing_date}")
        print(f"Branda Durumu: {property_obj.banner_status}")
        print(f"Fotoğraf Durumu: {property_obj.photo_status}")
        print(f"Danışman: {property_obj.consultant.get_full_name() if property_obj.consultant else 'Belirtilmemiş'}")
        print(f"Güncellenme Tarihi: {property_obj.updated_at}")
        print("====================================================================")
        
        # Çevre bilgilerini güncelle
        # Önce mevcut çevre bilgilerini sil
        property_obj.environments.all().delete()
        
        # Sonra yenilerini ekle
        place_names = request.POST.getlist('place_name')
        distances = request.POST.getlist('distance')
        
        for i in range(len(place_names)):
            if place_names[i] and distances[i]:
                PropertyEnvironment.objects.create(
                    property=property_obj,
                    place_name=place_names[i],
                    distance=distances[i]
                )
        
        # Fotoğrafları doğrudan işle
        if request.FILES:
            photos = request.FILES.getlist('photos[]')
            new_main_photo_order = request.POST.get('new_main_photo_order', None)
            
            print(f"Yüklenen yeni resim sayısı: {len(photos)}")
            if new_main_photo_order:
                print(f"Yeni ana fotoğraf sırası: {new_main_photo_order}")
            
            # Mevcut fotoğraf sayısını al (sıralama için)
            existing_photos_count = property_obj.images.count()
            
            for index, photo in enumerate(photos):
                # Dosya boyutu kontrolü (5MB)
                if photo.size > 5 * 1024 * 1024:
                    print(f"Fotoğraf çok büyük, atlanıyor: {photo.name}")
                    continue
                
                # Dosya tipi kontrolü
                if photo.content_type not in ['image/jpeg', 'image/png', 'image/jpg']:
                    print(f"Desteklenmeyen format, atlanıyor: {photo.name}")
                    continue
                
                # Başlık oluştur
                title = photo.name.split('.')[0][:50]
                
                # Ana fotoğraf mı kontrol et (sadece mevcut ana fotoğraf yoksa)
                has_existing_main = property_obj.images.filter(is_main_photo=True).exists()
                is_main_photo = False
                if not has_existing_main and new_main_photo_order and (str(index + 1) == str(new_main_photo_order)):
                    is_main_photo = True
                
                # Fotoğrafı kaydet ve property ile ilişkilendir
                PropertyImage.objects.create(
                    property=property_obj,
                    image=photo,
                    title=title,
                    order=existing_photos_count + index + 1,
                    is_main_photo=is_main_photo
                )
                
                print(f"Fotoğraf kaydedildi: {photo.name}, Sıra: {existing_photos_count + index + 1}, Ana fotoğraf: {is_main_photo}")
        
        # Ayrıca halihazırda yüklenmiş fotoğrafları da ilişkilendir (eski mekanizma için)
        image_ids = request.POST.getlist('image_ids[]')
        if image_ids:
            for image_id in image_ids:
                try:
                    image = PropertyImage.objects.get(id=image_id)
                    if not image.property or image.property != property_obj:
                        image.property = property_obj
                        image.save()
                except PropertyImage.DoesNotExist:
                    pass
        
        # Mevcut fotoğrafların sıralama bilgilerini güncelle
        existing_image_orders = request.POST.getlist('existing_image_orders[]')
        if existing_image_orders:
            print("Mevcut fotoğraf sıralaması güncelleniyor...")
            for order_data in existing_image_orders:
                if ':' in order_data:
                    image_id, order = order_data.split(':')
                    try:
                        image = PropertyImage.objects.get(id=int(image_id), property=property_obj)
                        image.order = int(order)
                        image.save()
                        print(f"Fotoğraf {image_id} sıralaması {order} olarak güncellendi")
                    except (PropertyImage.DoesNotExist, ValueError):
                        print(f"Fotoğraf {image_id} bulunamadı veya geçersiz order değeri")
                        pass
        
        # Ana fotoğraf bilgisini güncelle
        main_image_id = request.POST.get('main_image_id')
        if main_image_id:
            print(f"Ana fotoğraf güncelleniyor: {main_image_id}")
            # Önce tüm fotoğrafları ana fotoğraf olmaktan çıkar
            PropertyImage.objects.filter(property=property_obj).update(is_main_photo=False)
            
            # Seçilen fotoğrafı ana fotoğraf yap
            try:
                main_image = PropertyImage.objects.get(id=int(main_image_id), property=property_obj)
                main_image.is_main_photo = True
                main_image.save()
                print(f"Fotoğraf {main_image_id} ana fotoğraf olarak ayarlandı")
            except (PropertyImage.DoesNotExist, ValueError):
                print(f"Ana fotoğraf {main_image_id} bulunamadı")
                pass
        
        messages.success(request, "Gayrimenkul başarıyla güncellendi.")
        return redirect('property_detail', property_id=property_obj.id)
    
    context = {
        'segment': 'gayrimenkul',
        'property': property_obj,
        'neighborhoods': neighborhoods,
        'environments': property_obj.environments.all(),
        'images': property_obj.images.all().order_by('order'),
        'property_types': Property.PROPERTY_TYPE_CHOICES,
        'status_choices': Property.STATUS_CHOICES,
        'heating_choices': Property.HEATING_CHOICES,
        'deed_status_choices': Property.DEED_STATUS_CHOICES,
        'key_holder_choices': Property.KEY_HOLDER_CHOICES,
    }
    
    html_template = loader.get_template('portfolio/property_update.html')
    return HttpResponse(html_template.render(context, request))

# Yeni eklenen görsel yükleme ve silme görünümleri
@login_required(login_url="/login/")
def property_image_upload(request):
    """AJAX ile görsel yükleme"""
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            image = request.FILES.get('image')
            
            # Dosya boyutu kontrolü
            if image.size > 5242880:  # 5MB
                return JsonResponse({
                    'success': False, 
                    'error': 'Dosya boyutu 5MB\'dan büyük olamaz.'
                })
            
            # Dosya tipi kontrolü
            allowed_types = ['image/jpeg', 'image/png', 'image/jpg']
            if image.content_type not in allowed_types:
                return JsonResponse({
                    'success': False, 
                    'error': 'Sadece JPG ve PNG formatları kabul edilmektedir.'
                })
                
            title = image.name.split('.')[0][:50]  # Dosya adını başlık olarak kullan (maks 50 karakter)
            
            # Geçici kaydet (henüz bir gayrimenkul atanmadı)
            property_image = PropertyImage(
                image=image,
                title=title,
                order=0  # Sıralama daha sonra ayarlanacak
            )
            property_image.save()
            
            # Başarılı yanıt döndür
            return JsonResponse({
                'success': True,
                'image_id': property_image.id,
                'image_url': property_image.image.url
            })
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Geçersiz istek veya dosya gönderilmedi'}, status=400)

@login_required(login_url="/login/")
def property_image_delete(request):
    """AJAX ile görsel silme"""
    if request.method == 'POST':
        try:
            image_id = request.POST.get('image_id')
            if not image_id:
                return JsonResponse({'success': False, 'error': 'Görsel ID gerekli'})
            
            try:
                image = PropertyImage.objects.get(id=image_id)
            except PropertyImage.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Görsel bulunamadı'})
            
            # Eğer görsel bir gayrimenkule atanmışsa, sadece gayrimenkulün sahibi veya admin silebilir
            if image.property and not request.user.is_superuser and image.property.consultant != request.user:
                return JsonResponse({'success': False, 'error': 'Bu görseli silme yetkiniz yok'})
            
            # Dosya bilgilerini saklayalım
            image_url = image.image.url
            
            # Görseli sil
            image.delete()
            
            return JsonResponse({
                'success': True, 
                'message': 'Görsel başarıyla silindi',
                'deleted_image': image_url
            })
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Geçersiz istek'}, status=400)

@login_required(login_url="/login/")
@can_edit_portfolio
@csrf_exempt
def property_update_field(request):
    """AJAX ile gayrimenkul alanlarını güncelleme"""
    if request.method == 'POST':
        try:
            property_id = request.POST.get('property_id')
            field = request.POST.get('field')
            value = request.POST.get('value')
            
            if not property_id or not field:
                return JsonResponse({'success': False, 'error': 'Gayrimenkul ID ve alan adı gerekli'})
            
            try:
                property_obj = Property.objects.get(id=property_id)
            except Property.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Gayrimenkul bulunamadı'})
            
            # Yetki kontrolü
            role = get_user_role(request.user)
            if not request.user.is_superuser and role not in ['admin', 'manager']:
                if role == 'consultant':
                    # Danışman sadece kendi mahallelerindeki gayrimenkulleri güncelleyebilir
                    consultant_neighborhoods = Neighborhood.objects.filter(consultant=request.user)
                    if property_obj.neighborhood not in consultant_neighborhoods:
                        return JsonResponse({
                            'success': False, 
                            'error': f'Bu gayrimenkul {property_obj.neighborhood.name} mahallesinde bulunuyor ve bu mahalleyi düzenleme yetkiniz bulunmamaktadır.'
                        })
                else:
                    return JsonResponse({
                        'success': False, 
                        'error': f'Bu gayrimenkulü düzenleme yetkiniz bulunmamaktadır. Mevcut rolünüz: {role or "Tanımsız"}. Sadece Yönetici, Müdür ve ilgili Danışman düzenleme yapabilir.'
                    })
            
            # Alan türüne göre değer dönüşümü
            if field == 'consultant':
                try:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    consultant = User.objects.get(id=value)
                    property_obj.consultant = consultant
                except User.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Danışman bulunamadı'})
            elif field == 'neighborhood':
                try:
                    neighborhood = Neighborhood.objects.get(id=value)
                    property_obj.neighborhood = neighborhood
                except Neighborhood.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Mahalle bulunamadı'})
            elif field == 'photo_status':
                # Fotoğraf durumu için geçerli değerleri kontrol et
                valid_photo_statuses = dict(Property.PHOTO_STATUS_CHOICES).keys()
                if value in valid_photo_statuses:
                    property_obj.photo_status = value
                else:
                    return JsonResponse({'success': False, 'error': f'Geçersiz fotoğraf durumu. Geçerli değerler: {", ".join(valid_photo_statuses)}'})
            elif field in ['banner_status', 'usage_status', 'category', 'listing_type']:
                setattr(property_obj, field, value)
            elif field in ['is_furnished', 'is_in_site', 'is_exchangeable']:
                setattr(property_obj, field, value.lower() == 'true')
            else:
                return JsonResponse({'success': False, 'error': 'Geçersiz alan adı'})
            
            property_obj.save()
            
            # Başarılı yanıt
            display_value = value
            if field == 'consultant':
                display_value = f"{consultant.first_name} {consultant.last_name}"
            elif field == 'neighborhood':
                display_value = neighborhood.name
            elif field == 'photo_status':
                display_value = dict(Property.PHOTO_STATUS_CHOICES).get(value, value)
            
            return JsonResponse({
                'success': True, 
                'message': 'Alan başarıyla güncellendi',
                'display_value': display_value
            })
            
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Geçersiz istek'}, status=400)

@login_required(login_url="/login/")
@can_delete_portfolio
@csrf_exempt
def property_delete(request, property_id):
    """Gayrimenkul arşivleme (soft delete)"""
    if request.method == 'POST':
        try:
            try:
                property_obj = Property.objects.get(id=property_id)
            except Property.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Gayrimenkul bulunamadı'})

            from django.utils import timezone
            property_title = property_obj.apartment_name or 'İsimsiz Gayrimenkul'

            # Arşive taşı
            property_obj.is_archived = True
            property_obj.is_active = False
            property_obj.archived_at = timezone.now()
            property_obj.archived_by = request.user
            property_obj.save(update_fields=['is_archived', 'is_active', 'archived_at', 'archived_by'])

            return JsonResponse({
                'success': True,
                'message': f'"{property_title}" arşive taşındı'
            })
            
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Geçersiz istek'}, status=400)

@login_required(login_url="/login/")
def api_properties(request):
    """Tüm gayrimenkullerin JSON olarak verileri"""
    properties = Property.objects.filter(is_active=True)
    
    # Filtreleme
    property_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    
    if property_type:
        properties = properties.filter(property_type=property_type)
    if status:
        properties = properties.filter(status=status)
    
    result = []
    
    for prop in properties:
        # İlk görsel varsa onu al
        image = prop.images.first()
        image_url = image.image.url if image else None
        
        # Property type display adını al
        property_type_display = dict(Property.PROPERTY_TYPE_CHOICES).get(prop.property_type, prop.property_type)
        
        # Fiyat formatlaması
        price_formatted = "{:,.0f} TL".format(prop.price)
        
        result.append({
            'id': prop.id,
            'apartment_name': prop.apartment_name,
            'property_type': prop.property_type,
            'property_type_display': property_type_display,
            'status': prop.status,
            'price': float(prop.price),
            'price_formatted': price_formatted,
            'address': prop.address,
            'map_coordinates': prop.map_coordinates,
            'neighborhood': prop.neighborhood.name if prop.neighborhood else '',
            'is_bargainable': prop.is_bargainable,
            'image_url': image_url,
        })
    
    return JsonResponse(result, safe=False)

@csrf_exempt
@require_http_methods(["POST"])
def image_update_main(request):
    """Ana fotoğraf seçimi güncelleme"""
    try:
        image_id = request.POST.get('image_id')
        if not image_id:
            return JsonResponse({'success': False, 'error': 'Image ID gerekli'})
        
        # Seçilen resmi al
        image = get_object_or_404(PropertyImage, id=image_id)
        
        # Aynı property'ye ait diğer resimlerin ana fotoğraf durumunu kaldır
        PropertyImage.objects.filter(property=image.property).update(is_main_photo=False)
        
        # Seçilen resmi ana fotoğraf yap
        image.is_main_photo = True
        image.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def image_update_order(request):
    """Fotoğraf sıralaması güncelleme"""
    try:
        orders_json = request.POST.get('orders')
        if not orders_json:
            return JsonResponse({'success': False, 'error': 'Orders gerekli'})
        
        orders = json.loads(orders_json)
        
        for order_data in orders:
            image_id = order_data.get('id')
            order = order_data.get('order')
            
            if image_id and order is not None:
                image = PropertyImage.objects.get(id=image_id)
                image.order = order
                image.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



@login_required(login_url="/login/")
@require_http_methods(["POST"])
def move_property_to_group(request):
    """Portföyü gruba taşı"""
    
    try:
        data = json.loads(request.body)
        prop.hepsiemlak_active = data.get('active', False)
        if 'url' in data:
            prop.hepsiemlak_url = data.get('url', '')
        prop.save(update_fields=['hepsiemlak_active', 'hepsiemlak_url'])
        return JR({'success': True, 'active': prop.hepsiemlak_active})
    except Property.DoesNotExist:
        return JR({'error': 'Bulunamıyor'}, status=404)
    except Exception as e:
        return JR({'error': str(e)}, status=500)


@login_required
@require_POST
def move_property_to_group(request):
    import json
    data = json.loads(request.body)
    try:
        property_id = data.get('property_id')
        target_group = data.get('group')
        
        property_obj = Property.objects.get(id=property_id)
        
        if target_group == 'yeni-gelenler':
            property_obj.created_at = timezone.now()
            property_obj.save()
        else:
            parts = target_group.split(' - ')
            if len(parts) == 2:
                neighborhood_name = parts[0]
                room_count = parts[1]
                
                neighborhood = Neighborhood.objects.filter(name=neighborhood_name).first()
                if neighborhood:
                    property_obj.neighborhood = neighborhood
                
                if room_count != "Belirtilmemiş":
                    property_obj.room_count = room_count
                
                from datetime import timedelta
                property_obj.created_at = timezone.now() - timedelta(days=8)
                property_obj.save()
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# Bu kodu mevcut views.py dosyanıza ekleyin

@login_required(login_url="/login/")
@can_view_portfolio
def property_list_grouped(request):
    """Gayrimenkul listesi - Akıllı Gruplu Görünüm"""
    
    role = get_user_role(request.user)
    
    # Yetki kontrolü
    if request.user.is_superuser or role in ['admin', 'manager']:
        all_properties = Property.objects.filter(is_active=True)\
            .select_related('neighborhood', 'consultant')\
            .prefetch_related('images')\
            .order_by('-created_at')
    elif role == 'secretary':
        all_properties = Property.objects.filter(is_active=True)\
            .select_related('neighborhood', 'consultant')\
            .prefetch_related('images')\
            .order_by('-created_at')
    elif role == 'consultant':
        consultant_neighborhoods = Neighborhood.objects.filter(consultant=request.user)
        all_properties = Property.objects.filter(
            is_active=True,
            neighborhood__in=consultant_neighborhoods
        ).select_related('neighborhood', 'consultant')\
         .prefetch_related('images')\
         .order_by('-created_at')
    else:
        all_properties = Property.objects.none()

    # ── FİLTRELEME ──────────────────────────────────────────────────────────
    search          = request.GET.get('search', '').strip()
    neighborhood_id = request.GET.get('neighborhood', '').strip()
    min_price       = request.GET.get('min_price', '').strip()
    max_price       = request.GET.get('max_price', '').strip()
    consultant_id   = request.GET.get('consultant', '').strip()
    status          = request.GET.get('status', '').strip()
    banner_status   = request.GET.get('banner_status', '').strip()
    photo_status    = request.GET.get('photo_status', '').strip()

    if search:
        all_properties = all_properties.filter(
            Q(apartment_name__icontains=search) |
            Q(web_title__icontains=search) |
            Q(owner_name__icontains=search) |
            Q(address__icontains=search)
        )
    if neighborhood_id:
        all_properties = all_properties.filter(neighborhood_id=neighborhood_id)
    if min_price:
        try:
            all_properties = all_properties.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            all_properties = all_properties.filter(price__lte=float(max_price))
        except ValueError:
            pass
    if consultant_id and (request.user.is_superuser or role in ['admin', 'manager', 'secretary']):
        all_properties = all_properties.filter(consultant_id=consultant_id)
    if status:
        all_properties = all_properties.filter(status=status)
    if banner_status:
        all_properties = all_properties.filter(banner_status=banner_status)
    if photo_status:
        all_properties = all_properties.filter(photo_status=photo_status)
    # ────────────────────────────────────────────────────────────────────────

    # Filtre dropdown verileri
    from django.contrib.auth import get_user_model
    _User = get_user_model()
    if request.user.is_superuser or role in ['admin', 'manager', 'secretary']:
        neighborhoods_qs = Neighborhood.objects.all().order_by('name')
        consultants_qs   = _User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    else:
        neighborhoods_qs = Neighborhood.objects.filter(consultant=request.user).order_by('name')
        consultants_qs   = _User.objects.none()

    # AKILLI GRUPLAMA ALGORİTMASI
    from collections import defaultdict
    from datetime import timedelta
    
    # Son 7 gün içinde eklenen portföyler
    seven_days_ago = timezone.now() - timedelta(days=7)
    new_properties = all_properties.filter(created_at__gte=seven_days_ago)
    other_properties = all_properties.filter(created_at__lt=seven_days_ago)
    
    # Mahalle bazlı ana gruplama
    neighborhood_groups = defaultdict(list)
    for prop in other_properties:
        neighborhood_name = prop.neighborhood.name if prop.neighborhood else "Belirtilmemiş"
        neighborhood_groups[neighborhood_name].append(prop)
    
    # Her mahalle içinde akıllı alt gruplama
    final_grouped = {}
    
    for neighborhood, properties in neighborhood_groups.items():
        # Bina + Oda + Kat Tipi kombinasyonlarını say
        combinations = defaultdict(list)
        
        for prop in properties:
            # Bina adı
            building_name = prop.apartment_name if prop.apartment_name else "Belirtilmemiş"
            
            # Oda sayısı
            room_count = prop.room_count if prop.room_count else "Belirtilmemiş"
            
            # Kat tipini belirle
            try:
                floor_num = int(prop.floor) if prop.floor and str(prop.floor).isdigit() else None
                total_floors = int(prop.floor_count) if prop.floor_count and str(prop.floor_count).isdigit() else None
                
                if floor_num is not None:
                    if floor_num == 0:
                        floor_type = "Giriş Kat"
                    elif floor_num == 1:
                        floor_type = "1. Kat"
                    elif total_floors and floor_num == total_floors:
                        floor_type = "En Üst Kat"
                    else:
                        floor_type = "Ara Kat"
                else:
                    floor_type = str(prop.floor) if prop.floor else "Belirtilmemiş"
            except:
                floor_type = str(prop.floor) if prop.floor else "Belirtilmemiş"
            
            # Kombination key: Bina + Oda + Kat Tipi
            combo_key = f"{building_name}|{room_count}|{floor_type}"
            combinations[combo_key].append(prop)
        
        # Grup oluşturma mantığı
        grouped_items = []
        standalone_items = []
        
        for combo_key, props_in_combo in combinations.items():
            building_name, room_count, floor_type = combo_key.split('|')
            
            if len(props_in_combo) >= 2:
                # 2+ kayıt varsa grup oluştur
                # En ucuz olanı başa al
                sorted_props = sorted(props_in_combo, key=lambda x: x.price)
                
                grouped_items.append({
                    'type': 'group',
                    'header': f"{building_name} - {room_count} - {floor_type}",
                    'main_property': sorted_props[0],  # En ucuz
                    'sub_properties': sorted_props[1:],  # Diğerleri
                    'count': len(sorted_props)
                })
            else:
                # Tek kayıt ise ayrı satır
                standalone_items.extend(props_in_combo)
        
        # Mahalle grubu için liste oluştur
        # Önce gruplar, sonra tek satırlar
        final_grouped[neighborhood] = {
            'grouped_items': grouped_items,
            'standalone_items': standalone_items,
            'total_count': len(properties)
        }
    
    # Mahalle isimlerine göre alfabetik sırala
    final_grouped = dict(sorted(final_grouped.items()))
    
    # İstatistikler
    total_count = all_properties.count()
    satilik_count = all_properties.filter(status='satilik').count()
    kiralik_count = all_properties.filter(status='kiralik').count()
    
    context = {
        'segment': 'gayrimenkul',
        'new_properties': new_properties,
        'grouped_properties': final_grouped,
        'total_count': total_count,
        'satilik_count': satilik_count,
        'kiralik_count': kiralik_count,
        'user_role': role,
        # Filtre dropdown verileri
        'neighborhoods': neighborhoods_qs,
        'consultants': consultants_qs,
        # Aktif filtre değerleri (formu dolu tutmak için)
        'filter_search': search,
        'filter_neighborhood': neighborhood_id,
        'filter_min_price': min_price,
        'filter_max_price': max_price,
        'filter_consultant': consultant_id,
        'filter_status': status,
        'filter_banner_status': banner_status,
        'filter_photo_status': photo_status,
        'has_active_filter': any([search, neighborhood_id, min_price, max_price,
                                   consultant_id, status, banner_status, photo_status]),
    }
    
    return render(request, 'portfolio/property_list_grouped.html', context)


@login_required(login_url="/login/")
@require_http_methods(["POST"])
def move_property_to_group(request):
    """Portföyü gruba taşı"""
    import json
    
    try:
        data = json.loads(request.body)
        prop.hepsiemlak_active = data.get('active', False)
        if 'url' in data:
            prop.hepsiemlak_url = data.get('url', '')
        prop.save(update_fields=['hepsiemlak_active', 'hepsiemlak_url'])
        return JR({'success': True, 'active': prop.hepsiemlak_active})
    except Property.DoesNotExist:
        return JR({'error': 'Bulunamıyor'}, status=404)
    except Exception as e:
        return JR({'error': str(e)}, status=500)


@login_required
@require_POST
def move_property_to_group(request):
    import json
    data = json.loads(request.body)
    try:
        property_id = data.get('property_id')
        target_group = data.get('group')
        
        property_obj = Property.objects.get(id=property_id)
        
        # Eğer "yeni-gelenler" grubuna taşınıyorsa, created_at'ı güncelle
        if target_group == 'yeni-gelenler':
            property_obj.created_at = timezone.now()
            property_obj.save()
        else:
            # Grup formatı: "MAHALLE - ODA SAYISI"
            parts = target_group.split(' - ')
            if len(parts) == 2:
                neighborhood_name = parts[0]
                room_count = parts[1]
                
                # Mahalleyi bul veya oluştur
                neighborhood = Neighborhood.objects.filter(name=neighborhood_name).first()
                if neighborhood:
                    property_obj.neighborhood = neighborhood
                
                # Oda sayısını güncelle
                if room_count != "Belirtilmemiş":
                    property_obj.room_count = room_count
                
                # created_at'ı güncelle (yeni gelenler dışına çıksın)
                from datetime import timedelta
                property_obj.created_at = timezone.now() - timedelta(days=8)
                property_obj.save()
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required(login_url="/login/")
def property_map(request):
    """Harita görünümü - Tüm gayrimenkulleri Google Maps üzerinde göster"""
    
    role = get_user_role(request.user)
    from django.contrib.auth import get_user_model
    _User = get_user_model()

    # Kullanıcı rolüne göre gayrimenkulleri filtrele
    if role in ['admin', 'manager', 'secretary']:
        properties = Property.objects.filter(is_active=True)
    elif role == 'consultant':
        consultant_neighborhoods = Neighborhood.objects.filter(consultant=request.user)
        properties = Property.objects.filter(is_active=True, neighborhood__in=consultant_neighborhoods)
    else:
        properties = Property.objects.none()

    # Sadece koordinatı olanları al
    properties = properties.filter(
        map_coordinates__isnull=False
    ).exclude(map_coordinates='').select_related('neighborhood', 'consultant').order_by('-created_at')

    # Filtre dropdown verileri
    if role in ['admin', 'manager', 'secretary']:
        neighborhoods_qs = Neighborhood.objects.all().order_by('name')
        consultants_qs = _User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    else:
        neighborhoods_qs = Neighborhood.objects.filter(consultant=request.user).order_by('name')
        consultants_qs = _User.objects.none()

    total_all = Property.objects.filter(is_active=True)
    if role == 'consultant':
        total_all = total_all.filter(neighborhood__in=Neighborhood.objects.filter(consultant=request.user))

    context = {
        'properties': properties,
        'total_count': total_all.count(),
        'satilik_count': total_all.filter(status='satilik').count(),
        'kiralik_count': total_all.filter(status='kiralik').count(),
        'neighborhoods': neighborhoods_qs,
        'consultants': consultants_qs,
        'user_role': role,
        'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY,
    }
    
    return render(request, 'portfolio/property_map.html', context)

@login_required(login_url="/login/")
@require_POST
def update_portal_link(request):
    """Portal linklerini güncelle (Sahibinden, Emlakjet, Hepsiemlak, Sosyal Medya)"""
    property_id = request.POST.get('property_id')
    portal = request.POST.get('portal')
    link = request.POST.get('link', '').strip()
    
    try:
        prop = Property.objects.get(id=property_id)
        
        # Portal'e göre field'ı güncelle + tarihi kaydet
        now = timezone.now()
        if portal == 'sahibinden':
            prop.owner_listing_number = link
            prop.owner_listing_updated_at = now if link else None
        elif portal == 'emlakjet':
            prop.emlakjet_listing_number = link
            prop.emlakjet_listing_updated_at = now if link else None
        elif portal == 'hepsiemlak':
            prop.hepsiemlak_listing_number = link
            prop.hepsiemlak_listing_updated_at = now if link else None
        elif portal == 'social_media':
            pass

        prop.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Link başarıyla güncellendi'
        })
    except Property.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': 'Gayrimenkul bulunamadı'
        })
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e)
        })

@login_required(login_url="/login/")
@require_POST
def update_photo_status(request):
    """Fotoğraf durumunu güncelle"""
    property_id = request.POST.get('property_id')
    status = request.POST.get('status')
    
    try:
        prop = Property.objects.get(id=property_id)
        prop.photo_status = status
        prop.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Fotoğraf durumu güncellendi'
        })
    except Property.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': 'Gayrimenkul bulunamadı'
        })
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e)
        })

@login_required(login_url="/login/")
@require_POST
def update_banner_status(request):
    """Branda durumunu güncelle"""
    property_id = request.POST.get('property_id')
    status = request.POST.get('status')
    
    try:
        prop = Property.objects.get(id=property_id)
        prop.banner_status = status
        prop.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Branda durumu güncellendi'
        })
    except Property.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': 'Gayrimenkul bulunamadı'
        })
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e)
        })

@login_required(login_url="/login/")
@require_http_methods(["GET"])
def property_notes(request, property_id):
    """Gayrimenkul notlarını getir"""
    try:
        prop = get_object_or_404(Property, id=property_id, is_active=True)
        notes = prop.notes.select_related('user').order_by('-created_at')
        data = [
            {
                'id': n.id,
                'note': n.note,
                'user': n.user.get_full_name() or n.user.username if n.user else 'Bilinmiyor',
                'created_at': n.created_at.strftime('%d.%m.%Y %H:%M'),
            }
            for n in notes
        ]
        return JsonResponse({'success': True, 'notes': data, 'property_name': str(prop)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required(login_url="/login/")
@require_http_methods(["POST"])
def property_note_add(request, property_id):
    """Gayrimenkule not ekle"""
    try:
        prop = get_object_or_404(Property, id=property_id, is_active=True)
        note_text = request.POST.get('note', '').strip()
        if not note_text:
            return JsonResponse({'success': False, 'error': 'Not boş olamaz.'})
        note = PropertyNote.objects.create(
            property=prop,
            user=request.user,
            note=note_text,
        )
        return JsonResponse({
            'success': True,
            'note': {
                'id': note.id,
                'note': note.note,
                'user': note.user.get_full_name() or note.user.username,
                'created_at': note.created_at.strftime('%d.%m.%Y %H:%M'),
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required(login_url="/login/")
@require_http_methods(["POST"])
def property_note_delete(request, note_id):
    """Not sil (sadece sahibi veya admin)"""
    try:
        note = get_object_or_404(PropertyNote, id=note_id)
        role = get_user_role(request.user)
        if note.user != request.user and not (request.user.is_superuser or role in ['admin', 'manager']):
            return JsonResponse({'success': False, 'error': 'Bu notu silme yetkiniz yok.'})
        note.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required(login_url="/login/")
@require_http_methods(["GET"])
def portal_notifications(request):
    """Kullanıcının okunmamış portal bildirimlerini getir"""
    notifs = PortalNotification.objects.filter(
        user=request.user,
        is_read=False
    ).select_related('property').order_by('-created_at')[:20]

    data = [
        {
            'id': n.id,
            'property_name': str(n.property),
            'property_id': n.property.id,
            'portal': n.get_portal_display(),
            'created_at': n.created_at.strftime('%d.%m.%Y'),
        }
        for n in notifs
    ]
    return JsonResponse({'success': True, 'notifications': data, 'count': len(data)})


@login_required(login_url="/login/")
@require_http_methods(["POST"])
def portal_notification_read(request, notification_id):
    """Bildirimi okundu olarak işaretle"""
    try:
        notif = PortalNotification.objects.get(id=notification_id, user=request.user)
        notif.is_read = True
        notif.save()
        return JsonResponse({'success': True})
    except PortalNotification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Bildirim bulunamadı'})


@login_required(login_url="/login/")
@require_http_methods(["POST"])
def portal_notifications_read_all(request):
    """Tüm bildirimleri okundu olarak işaretle"""
    PortalNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})

# ============ PROPERTY NOTE AJAX API ============
from django.http import JsonResponse as _JR
from django.views.decorators.http import require_POST as _rp, require_GET as _rg
from django.utils import timezone as _tz

@login_required
@_rg
def property_notes_api(request, property_id):
    """Bir portfoyun tum notlarini JSON olarak dondur"""
    try:
        prop = Property.objects.get(id=property_id)
    except Property.DoesNotExist:
        return _JR({'success': False, 'error': 'Portfoy bulunamadi'}, status=404)

    notes_qs = prop.notes.select_related('user').all()

    notes = []
    for n in notes_qs:
        notes.append({
            'id': n.id,
            'note': n.note,
            'priority': n.priority,
            'priority_display': n.get_priority_display(),
            'is_reminder': n.is_reminder,
            'reminder_date': n.reminder_date.isoformat() if n.reminder_date else None,
            'is_completed': n.is_completed,
            'user_name': n.user.get_full_name() if n.user and n.user.get_full_name() else (n.user.username if n.user else 'Bilinmeyen'),
            'created_at': n.created_at.isoformat(),
            'created_at_display': n.created_at.strftime('%d.%m.%Y %H:%M'),
        })

    stats = {
        'total': len(notes),
        'important': sum(1 for n in notes if n['priority'] in ['onemli', 'acil']),
        'reminders': sum(1 for n in notes if n['is_reminder']),
        'completed': sum(1 for n in notes if n['is_completed']),
    }

    return _JR({
        'success': True,
        'property_name': prop.apartment_name or prop.web_title or 'Isimsiz',
        'notes': notes,
        'stats': stats,
    })


@login_required
@_rp
def property_note_add_api(request, property_id):
    """Yeni not ekle - AJAX"""
    try:
        prop = Property.objects.get(id=property_id)
    except Property.DoesNotExist:
        return _JR({'success': False, 'error': 'Portfoy bulunamadi'}, status=404)

    note_text = request.POST.get('note', '').strip()
    priority = request.POST.get('priority', 'normal')
    is_reminder = request.POST.get('is_reminder', 'false').lower() == 'true'
    reminder_date = request.POST.get('reminder_date', '').strip()

    if not note_text:
        return _JR({'success': False, 'error': 'Not bos olamaz'}, status=400)

    try:
        from apps.portfolio.models import PropertyNote
        n = PropertyNote(
            property=prop,
            user=request.user,
            note=note_text,
            priority=priority if priority in ['normal', 'onemli', 'acil'] else 'normal',
            is_reminder=is_reminder,
        )
        if is_reminder and reminder_date:
            from django.utils.dateparse import parse_datetime, parse_date
            parsed = parse_datetime(reminder_date) or parse_date(reminder_date)
            if parsed:
                n.reminder_date = parsed
        n.save()

        return _JR({
            'success': True,
            'note': {
                'id': n.id,
                'note': n.note,
                'priority': n.priority,
                'priority_display': n.get_priority_display(),
                'is_reminder': n.is_reminder,
                'reminder_date': n.reminder_date.isoformat() if n.reminder_date else None,
                'is_completed': n.is_completed,
                'user_name': request.user.get_full_name() or request.user.username,
                'created_at': n.created_at.isoformat(),
                'created_at_display': n.created_at.strftime('%d.%m.%Y %H:%M'),
            }
        })
    except Exception as e:
        return _JR({'success': False, 'error': str(e)}, status=500)


@login_required
@_rp
def property_note_toggle_complete(request, note_id):
    """Notu tamamlandi/tamamlanmadi olarak isaretle"""
    try:
        from apps.portfolio.models import PropertyNote
        n = PropertyNote.objects.get(id=note_id)
        n.is_completed = not n.is_completed
        n.save(update_fields=['is_completed'])
        return _JR({'success': True, 'is_completed': n.is_completed})
    except Exception as e:
        return _JR({'success': False, 'error': str(e)}, status=500)


@login_required
@_rp
def property_note_delete_api(request, note_id):
    """Notu sil (AJAX)"""
    try:
        from apps.portfolio.models import PropertyNote
        n = PropertyNote.objects.get(id=note_id)
        n.delete()
        return _JR({'success': True})
    except Exception as e:
        return _JR({'success': False, 'error': str(e)}, status=500)


@login_required
def price_history_api(request, property_id):
    """Gayrimenkul fiyat geçmişi API"""
    from .models import Property, PropertyPriceHistory
    try:
        prop = Property.objects.get(pk=property_id)
    except Property.DoesNotExist:
        from django.http import JsonResponse
        return JsonResponse({'error': 'Bulunamadı'}, status=404)

    history = PropertyPriceHistory.objects.filter(property=prop).order_by('-created_at')[:20]

    total_change = 0
    if history.exists():
        first = history.last()
        total_change = float(prop.price) - float(first.old_price)

    rows = []
    for h in history:
        rows.append({
            'old_price': float(h.old_price),
            'new_price': float(h.new_price),
            'change': float(h.change_amount()),
            'change_percent': h.change_percent(),
            'note': h.note,
            'changed_by': h.changed_by.get_full_name() if h.changed_by else '',
            'date': h.created_at.strftime('%d.%m.%Y %H:%M'),
        })

    from django.http import JsonResponse
    return JsonResponse({
        'property_id': prop.id,
        'name': prop.apartment_name or str(prop),
        'current_price': float(prop.price),
        'total_change': total_change,
        'history': rows,
    })


@login_required
def property_restore(request, property_id):
    """Arşivden geri al"""
    from django.http import JsonResponse
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Geçersiz istek'})
    role = get_user_role(request.user)
    if not request.user.is_superuser and role not in ['admin', 'manager']:
        return JsonResponse({'success': False, 'error': 'Yetkiniz yok'})
    try:
        prop = Property.objects.get(pk=property_id)
    except Property.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Bulunamadı'})
    prop.is_archived = False
    prop.is_active = True
    prop.archived_at = None
    prop.archived_by = None
    prop.save(update_fields=['is_archived', 'is_active', 'archived_at', 'archived_by'])
    return JsonResponse({'success': True, 'message': f'"{prop.apartment_name or "Portföy"}" geri alındı'})


@login_required
def social_media_page(request, property_id):
    """Gayrimenkul sosyal medya şablonları sayfası"""
    property_obj = get_object_or_404(Property, id=property_id)
    images = property_obj.images.all().order_by('order')
    context = {
        'property': property_obj,
        'images': images,
        'segment': 'gayrimenkuller',
    }
    return render(request, 'portfolio/social_media.html', context)


@login_required
def property_sunum_musteriler_api(request, property_id):
    """Gayrimenkule sunum yapılan müşteriler API"""
    from apps.customers.models import CustomerPresentation
    from django.http import JsonResponse
    try:
        prop = Property.objects.get(pk=property_id)
    except Property.DoesNotExist:
        return JsonResponse({'error': 'Bulunamadı'}, status=404)

    qs = CustomerPresentation.objects.filter(property=prop).select_related(
        'customer', 'created_by'
    ).order_by('-created_at')

    rows = []
    for cp in qs:
        rows.append({
            'id': cp.id,
            'customer_name': cp.customer.display_name,
            'customer_phone': cp.customer.phone or '',
            'consultant': cp.created_by.get_full_name() if cp.created_by else (cp.created_by.username if cp.created_by else ''),
            'meeting_notes': cp.meeting_notes or '',
            'created_at': cp.created_at.strftime('%d.%m.%Y'),
            'customer_url': f'/musteriler/{cp.customer.id}/',
        })

    return JsonResponse({
        'total': len(rows),
        'rows': rows,
    })


@login_required
def sahibinden_export(request):
    """Sahibinden XML export sayfası"""
    from .models import Property, PropertyImage
    properties = Property.objects.filter(
        is_active=True, sahibinden_active=True
    ).select_related('neighborhood__city').prefetch_related('images').order_by('-created_at')

    all_properties = Property.objects.filter(
        is_active=True
    ).select_related('neighborhood').prefetch_related('images').order_by('-created_at')

    context = {
        'segment': 'gayrimenkuller',
        'properties': properties,
        'all_properties': all_properties,
        'total_active': properties.count(),
        'total_all': all_properties.count(),
    }
    return render(request, 'portfolio/sahibinden_export.html', context)


@login_required
def sahibinden_xml_feed(request):
    """Sahibinden XML dosyası üret ve indir"""
    from .models import Property, PropertyImage
    from django.http import HttpResponse
    import xml.etree.ElementTree as ET
    from xml.dom import minidom

    properties = Property.objects.filter(
        is_active=True, sahibinden_active=True
    ).select_related('neighborhood').prefetch_related('images').order_by('-created_at')

    root = ET.Element('Listings')

    # Sahibinden kategori mapping
    PROP_TYPE_MAP = {
        'daire': 'Daire', 'villa': 'Villa', 'mustakil': 'Müstakil Ev',
        'arsa': 'Arsa', 'bina': 'Bina', 'dukkan': 'Dükkan/Mağaza',
        'ofis': 'Ofis', 'depo': 'Depo/Ardiye', 'other': 'Diğer',
    }
    STATUS_MAP = {
        'satilik': 'Satılık', 'kiralik': 'Kiralık', 'devren': 'Devren',
    }

    for prop in properties:
        listing = ET.SubElement(root, 'Listing')

        def tag(parent, name, value):
            el = ET.SubElement(parent, name)
            el.text = str(value) if value is not None else ''
            return el

        tag(listing, 'Id', prop.id)
        tag(listing, 'Title', prop.web_title or prop.apartment_name or f'İlan #{prop.id}')
        tag(listing, 'Description', prop.description or '')
        tag(listing, 'Price', int(prop.price))
        tag(listing, 'Currency', 'TRY')

        # Konum
        loc = ET.SubElement(listing, 'Location')
        tag(loc, 'City', prop.neighborhood.city.name if hasattr(prop.neighborhood, 'city') and prop.neighborhood.city else 'Gaziantep')
        tag(loc, 'District', prop.neighborhood.name if prop.neighborhood else '')
        tag(loc, 'Neighborhood', prop.neighborhood.name if prop.neighborhood else '')

        # Özellikler
        attrs = ET.SubElement(listing, 'Attributes')
        if prop.net_area:
            a = ET.SubElement(attrs, 'Attribute')
            tag(a, 'Key', 'net_m2'); tag(a, 'Value', int(prop.net_area))
        if prop.gross_area:
            a = ET.SubElement(attrs, 'Attribute')
            tag(a, 'Key', 'gross_m2'); tag(a, 'Value', int(prop.gross_area))
        if prop.room_count:
            a = ET.SubElement(attrs, 'Attribute')
            tag(a, 'Key', 'room_count'); tag(a, 'Value', prop.room_count)
        if prop.floor:
            a = ET.SubElement(attrs, 'Attribute')
            tag(a, 'Key', 'floor'); tag(a, 'Value', prop.floor)
        if prop.floor_count:
            a = ET.SubElement(attrs, 'Attribute')
            tag(a, 'Key', 'floor_count'); tag(a, 'Value', prop.floor_count)
        if prop.bathroom_count:
            a = ET.SubElement(attrs, 'Attribute')
            tag(a, 'Key', 'bathroom_count'); tag(a, 'Value', prop.bathroom_count)
        if prop.usage_status:
            a = ET.SubElement(attrs, 'Attribute')
            tag(a, 'Key', 'usage_status'); tag(a, 'Value', prop.usage_status)

        prop_type = PROP_TYPE_MAP.get(prop.property_type, prop.property_type)
        a = ET.SubElement(attrs, 'Attribute')
        tag(a, 'Key', 'property_type'); tag(a, 'Value', prop_type)

        # Görseller
        imgs = ET.SubElement(listing, 'Images')
        for img in prop.images.all()[:10]:
            if img.image:
                img_url = request.build_absolute_uri(img.image.url)
                tag(imgs, 'Image', img_url)

        # İlan linki
        if prop.sahibinden_url:
            tag(listing, 'ExternalUrl', prop.sahibinden_url)
        if prop.owner_listing_number:
            tag(listing, 'ExternalId', prop.owner_listing_number)

    # Güzel formatlı XML
    xml_str = minidom.parseString(ET.tostring(root, encoding='unicode')).toprettyxml(indent='  ', encoding='UTF-8')
    response = HttpResponse(xml_str, content_type='application/xml; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="sahibinden_ilanlar.xml"'
    return response



@login_required
def sahibinden_toggle(request, property_id):
    """Gayrimenkulü Sahibinden'de yayına al/kaldır"""
    from django.http import JsonResponse as JR
    if request.method != 'POST':
        return JR({'error': 'POST gerekli'}, status=405)
    try:
        prop = Property.objects.get(pk=property_id)
        import json
        data = json.loads(request.body)
        prop.sahibinden_active = data.get('active', False)
        if 'url' in data:
            prop.sahibinden_url = data.get('url', '')
        prop.save(update_fields=['sahibinden_active', 'sahibinden_url'])
        return JR({'success': True, 'active': prop.sahibinden_active})
    except Property.DoesNotExist:
        return JR({'error': 'Bulunamadı'}, status=404)
    except Exception as e:
        return JR({'error': str(e)}, status=500)


@login_required
def emlakjet_export(request):
    all_properties = Property.objects.filter(is_active=True).select_related('neighborhood').prefetch_related('images').order_by('-created_at')
    total_active = all_properties.filter(emlakjet_active=True).count()
    context = {'all_properties': all_properties, 'total_active': total_active, 'total_all': all_properties.count()}
    return render(request, 'portfolio/emlakjet_export.html', context)


@login_required
def emlakjet_toggle(request, property_id):
    from django.http import JsonResponse as JR
    if request.method != 'POST':
        return JR({'error': 'POST gerekli'}, status=405)
    try:
        prop = Property.objects.get(pk=property_id)
        import json
        data = json.loads(request.body)
        prop.emlakjet_active = data.get('active', False)
        if 'url' in data:
            prop.emlakjet_url = data.get('url', '')
        prop.save(update_fields=['emlakjet_active', 'emlakjet_url'])
        return JR({'success': True, 'active': prop.emlakjet_active})
    except Property.DoesNotExist:
        return JR({'error': 'Bulunamadı'}, status=404)
    except Exception as e:
        return JR({'error': str(e)}, status=500)


@login_required
def hepsiemlak_export(request):
    all_properties = Property.objects.filter(is_active=True).select_related('neighborhood').prefetch_related('images').order_by('-created_at')
    total_active = all_properties.filter(hepsiemlak_active=True).count()
    context = {'all_properties': all_properties, 'total_active': total_active, 'total_all': all_properties.count()}
    return render(request, 'portfolio/hepsiemlak_export.html', context)


@login_required
def hepsiemlak_toggle(request, property_id):
    from django.http import JsonResponse as JR
    if request.method != 'POST':
        return JR({'error': 'POST gerekli'}, status=405)
    try:
        prop = Property.objects.get(pk=property_id)
        import json
        data = json.loads(request.body)
        prop.hepsiemlak_active = data.get('active', False)
        if 'url' in data:
            prop.hepsiemlak_url = data.get('url', '')
        prop.save(update_fields=['hepsiemlak_active', 'hepsiemlak_url'])
        return JR({'success': True, 'active': prop.hepsiemlak_active})
    except Property.DoesNotExist:
        return JR({'error': 'Bulunamadı'}, status=404)
    except Exception as e:
        return JR({'error': str(e)}, status=500)
