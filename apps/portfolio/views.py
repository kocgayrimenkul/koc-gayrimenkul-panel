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
from .models import Property, PropertyEnvironment, PropertyImage
from apps.customers.models import Neighborhood
from apps.employees.models import EmployeeProfile
from django.utils import timezone
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
from django.views.decorators.http import require_http_methods

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
    property_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    neighborhood_id = request.GET.get('neighborhood', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
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
    
    # Başlangıç sorgusu - yetki kontrolü ile
    if request.user.is_superuser or role in ['admin', 'manager']:
        # Yönetici ve Müdür tüm gayrimenkulleri görebilir
        properties_list = Property.objects.filter(is_active=True)\
            .select_related('neighborhood', 'consultant')\
            .prefetch_related(
                'images'
            )
    elif role == 'secretary':
        # Santral tüm aktif gayrimenkulleri görebilir (okuma yetkisi)
        properties_list = Property.objects.filter(is_active=True)\
            .select_related('neighborhood', 'consultant')\
            .prefetch_related(
                'images'
            )
    elif role == 'consultant':
        # Danışman sadece kendi mahallelerindeki gayrimenkulleri görebilir
        consultant_neighborhoods = Neighborhood.objects.filter(consultant=request.user)
        properties_list = Property.objects.filter(
            is_active=True,
            neighborhood__in=consultant_neighborhoods
        ).select_related('neighborhood', 'consultant')\
         .prefetch_related(
             'images'
         )
    else:
        # Diğer roller için sınırlı erişim
        properties_list = Property.objects.none()
        messages.warning(request, "Gayrimenkul listesini görüntüleme yetkiniz sınırlıdır.")
    
    # Arama sorgusu
    if search:
        properties_list = properties_list.filter(
            Q(apartment_name__icontains=search) | 
            Q(description__icontains=search) | 
            Q(address__icontains=search) | 
            Q(owner_name__icontains=search) | 
            Q(owner_listing_number__icontains=search) |
            Q(website_listing_number__icontains=search) |
            Q(emlakjet_listing_number__icontains=search)
        )
    
    # Filtreleri uygula
    if property_type:
        properties_list = properties_list.filter(property_type=property_type)
    if status:
        properties_list = properties_list.filter(status=status)
    if neighborhood_id:
        # Danışman sadece kendi mahallelerini filtreleyebilir
        if role == 'consultant':
            consultant_neighborhoods = Neighborhood.objects.filter(consultant=request.user)
            if consultant_neighborhoods.filter(id=neighborhood_id).exists():
                properties_list = properties_list.filter(neighborhood_id=neighborhood_id)
        else:
            properties_list = properties_list.filter(neighborhood_id=neighborhood_id)
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
        # Sadece yönetici ve müdür başka danışmanları filtreleyebilir
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
    paginator = Paginator(properties_list, 9)  # Her sayfada 9 kayıt göster
    page = request.GET.get('page', 1)
    
    try:
        properties = paginator.page(page)
    except PageNotAnInteger:
        # Eğer sayfa sayı değilse, ilk sayfayı göster
        properties = paginator.page(1)
    except EmptyPage:
        # Eğer sayfa sayısı mevcut sayfa aralığını aşıyorsa, son sayfayı göster
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
        'neighborhoods': neighborhoods,
        'consultants': consultants,
        'user_role': role,
        'filters': {
            'search': search,
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
    if not request.user.is_superuser and role not in ['admin', 'manager', 'secretary']:
        if role == 'consultant':
            # Danışman sadece kendi mahallelerindeki gayrimenkulleri görebilir
            consultant_neighborhoods = Neighborhood.objects.filter(consultant=request.user)
            if property_obj.neighborhood not in consultant_neighborhoods:
                messages.error(request, "Bu gayrimenkul detaylarını görüntüleme yetkiniz yok.")
                return redirect('property_list')
        else:
            messages.error(request, "Bu sayfaya erişim yetkiniz bulunmamaktadır.")
            return redirect('property_list')
    
    # Çevre bilgileri
    environments = property_obj.environments.all()
    
    # Resimler
    images = property_obj.images.all().order_by('order')
    
    context = {
        'segment': 'gayrimenkul',
        'property': property_obj,
        'environments': environments,
        'images': images,
        'user_role': role,
    }
    
    html_template = loader.get_template('portfolio/property_detail.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
@can_add_portfolio
def property_create(request):
    """Yeni gayrimenkul ekleme"""
    role = get_user_role(request.user)
    
    # Yetki kontrolü - Sadece Yönetici, Müdür ve Danışman ekleme yapabilir
    if not request.user.is_superuser and role not in ['admin', 'manager', 'consultant']:
        messages.error(request, "Gayrimenkul ekleme yetkiniz bulunmamaktadır.")
        return redirect('property_list')
    
    # Mahalleler - yetki kontrolü ile
    if request.user.is_superuser or role in ['admin', 'manager']:
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
                messages.error(request, "Bu gayrimenkulü güncelleme yetkiniz yok.")
                return redirect('property_list')
        else:
            messages.error(request, "Gayrimenkul güncelleme yetkiniz bulunmamaktadır.")
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
                        return JsonResponse({'success': False, 'error': 'Bu gayrimenkulü düzenleme yetkiniz yok'})
                else:
                    return JsonResponse({'success': False, 'error': 'Bu gayrimenkulü düzenleme yetkiniz yok'})
            
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
    """Gayrimenkul silme"""
    if request.method == 'POST':
        try:
            try:
                property_obj = Property.objects.get(id=property_id)
            except Property.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Gayrimenkul bulunamadı'})
            
            # Yetki kontrolü - Sadece Yönetici ve Müdür silebilir
            role = get_user_role(request.user)
            if not request.user.is_superuser and role not in ['admin', 'manager']:
                return JsonResponse({'success': False, 'error': 'Gayrimenkul silme yetkiniz bulunmamaktadır'})
            
            # Gayrimenkulün başlığını sakla
            property_title = property_obj.apartment_name
            
            # Gayrimenkulle ilişkili çevre bilgilerini ve görselleri de sil
            property_obj.delete()
            
            return JsonResponse({
                'success': True, 
                'message': f'"{property_title}" gayrimenkulü başarıyla silindi'
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
