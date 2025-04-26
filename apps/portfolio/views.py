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

@login_required(login_url="/login/")
def property_list(request):
    """Gayrimenkul listesi görünümü"""
    
    # Filtreleme
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
    
    # Başlangıç sorgusu
    properties_list = Property.objects.filter(is_active=True)
    
    # Filtreleri uygula
    if property_type:
        properties_list = properties_list.filter(property_type=property_type)
    if status:
        properties_list = properties_list.filter(status=status)
    if neighborhood_id:
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
    
    # İlgili mahalleler
    neighborhoods = Neighborhood.objects.all().order_by('name')
    
    # Danışman listesi
    consultants = EmployeeProfile.objects.filter(role='consultant', is_active=True).select_related('user')
    
    context = {
        'segment': 'gayrimenkul',
        'properties': properties,
        'neighborhoods': neighborhoods,
        'consultants': consultants,
        'filters': {
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
        }
    }
    
    html_template = loader.get_template('portfolio/property_list.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def property_detail(request, property_id):
    """Gayrimenkul detay görünümü"""
    property_obj = get_object_or_404(Property, id=property_id)
    
    # Çevre bilgileri
    environments = property_obj.environments.all()
    
    # Resimler
    images = property_obj.images.all().order_by('order')
    
    context = {
        'segment': 'gayrimenkul',
        'property': property_obj,
        'environments': environments,
        'images': images,
    }
    
    html_template = loader.get_template('portfolio/property_detail.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def property_create(request):
    """Yeni gayrimenkul ekleme"""
    neighborhoods = Neighborhood.objects.all().order_by('name')
    
    if request.method == 'POST':
        # POST verilerini detaylı yazdır
        print("============= YENİ GAYRİMENKUL EKLE - POST VERİLERİ =============")
        print(f"POST içeriği alındı - tarih/saat: {timezone.now().strftime('%d.%m.%Y %H:%M:%S')}")
        print(f"title: {request.POST.get('title', 'Boş')}")
        print(f"description: {request.POST.get('description', 'Boş')[:30]}{'...' if len(request.POST.get('description', '')) > 30 else ''}")
        print(f"property_type: {request.POST.get('property_type', 'Boş')}")
        print(f"status: {request.POST.get('status', 'Boş')}")
        print(f"price: {request.POST.get('price', 'Boş')}")
        print(f"neighborhood: {request.POST.get('neighborhood', 'Boş')}")
        print(f"address: {request.POST.get('address', 'Boş')[:30]}{'...' if len(request.POST.get('address', '')) > 30 else ''}")
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
        print(f"from_who (listing_from): {request.POST.get('from_who', 'Boş')}")
        print(f"customer_tag: {request.POST.get('customer_tag', 'Boş')}")
        print(f"customer_source: {request.POST.get('customer_source', 'Boş')}")
        print(f"has_banner: {request.POST.get('has_banner', 'Boş')}")
        print(f"has_poster: {request.POST.get('has_poster', 'Boş')}")
        print(f"has_photos: {request.POST.get('has_photos', 'Boş')}")
        print(f"key_holder: {request.POST.get('key_holder', 'Boş')}")
        print(f"listing_date: {request.POST.get('listing_date', 'Boş')}")
        
        # Çevre bilgileri
        place_names = request.POST.getlist('place_name')
        distances = request.POST.getlist('distance')
        if place_names:
            print("Çevre Bilgileri:")
            for i in range(len(place_names)):
                if place_names[i]:
                    print(f"  - {place_names[i]}: {distances[i] if i < len(distances) else 'Mesafe belirtilmemiş'}")
        
        # Resim sayısı
        if request.FILES:
            print(f"Yüklenen resim sayısı: {len(request.FILES.getlist('photos[]'))}")
        
        print("================================================================")
        
        # Temel bilgiler
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        property_type = request.POST.get('property_type', '')
        status = request.POST.get('status', '')
        price = request.POST.get('price', '')
        neighborhood_id = request.POST.get('neighborhood', '')
        address = request.POST.get('address', '')
        room_count = request.POST.get('room_count', '')
        usage_status = request.POST.get('usage_status', '')
        floor_count = request.POST.get('floor_count', '')
        
        # Müşteri bilgileri
        customer_tag = request.POST.get('customer_tag', '')
        customer_source = request.POST.get('customer_source', '')
        listing_from = request.POST.get('from_who', '')
        
        # Branda/Afiş/Fotoğraf durumu
        has_banner = request.POST.get('has_banner', '')
        banner_status = 'asildi' if has_banner == 'var' else 'asilmadi'
        
        has_poster = request.POST.get('has_poster', '')
        poster_status = 'asildi' if has_poster == 'var' else 'asilmadi'
        
        has_photos = request.POST.get('has_photos', '')
        photo_status = 'cekildi' if has_photos == 'var' else 'cekilmedi'
        
        # Balkon kontrolü
        balcony = request.POST.get('balcony', '')
        has_balcony = balcony == 'var'
        
        # Validation
        if not title or not property_type or not status or not price or not neighborhood_id:
            messages.error(request, "Lütfen zorunlu alanları doldurun.")
            return redirect('property_create')
        
        try:
            price = float(price.replace(',', '.'))
            neighborhood = Neighborhood.objects.get(id=neighborhood_id)
            
            # Yeni portföy oluştur
            property_obj = Property(
                title=title,
                description=description,
                property_type=property_type,
                status=status,
                price=price,
                neighborhood=neighborhood,
                address=address,
                room_count=room_count,
                usage_status=usage_status,
                floor_count=floor_count,
                floor=request.POST.get('floor', ''),
                consultant=request.user,
                customer_tag=customer_tag,
                customer_source=customer_source,
                listing_from=listing_from,
                banner_status=banner_status,
                poster_status=poster_status,
                photo_status=photo_status,
            )
            
            # Detay bilgileri
            if property_type == 'daire':
                property_obj.gross_area = request.POST.get('gross_area', None)
                property_obj.net_area = request.POST.get('net_area', None)
                property_obj.heating = request.POST.get('heating', '')
                property_obj.has_balcony = has_balcony
                property_obj.dues = request.POST.get('dues', None)
            
            # Diğer bilgiler
            property_obj.deed_status = request.POST.get('deed_status', '')
            property_obj.is_suitable_for_credit = 'is_suitable_for_credit' in request.POST
            property_obj.is_bargainable = 'is_bargainable' in request.POST
            
            # Portföy sahibi bilgileri
            property_obj.owner_name = request.POST.get('owner_name', '')
            property_obj.owner_phone = request.POST.get('owner_phone', '')
            property_obj.owner_listing_number = request.POST.get('owner_listing_number', '')
            property_obj.branda_number = request.POST.get('branda_number', '')
            
            # Operasyonel bilgiler
            property_obj.key_holder = request.POST.get('key_holder', '')
            listing_date = request.POST.get('listing_date', '')
            if listing_date:
                property_obj.listing_date = listing_date
            
            # Analiz bilgileri
            property_obj.swot_analysis = request.POST.get('swot_analysis', '')
            property_obj.target_audience = request.POST.get('target_audience', '')
            
            property_obj.save()
            
            # Debug için kaydedilen property değerlerini göster
            print("============= KAYIT İŞLEMİ SONRASI GAYRİMENKUL BİLGİLERİ =============")
            print(f"ID: {property_obj.id}")
            print(f"Başlık: {property_obj.title}")
            print(f"Açıklama: {property_obj.description[:50]}{'...' if len(property_obj.description) > 50 else ''}")
            print(f"Emlak Tipi: {property_obj.property_type}")
            print(f"Durum: {property_obj.status}")
            print(f"Fiyat: {property_obj.price}")
            print(f"Mahalle: {property_obj.neighborhood.name}")
            print(f"Adres: {property_obj.address[:50]}{'...' if len(property_obj.address) > 50 else ''}")
            print(f"Brüt Alan: {property_obj.gross_area}")
            print(f"Net Alan: {property_obj.net_area}")
            print(f"Oda Sayısı: {property_obj.room_count}")
            print(f"Kat Sayısı: {property_obj.floor_count}")
            print(f"Isıtma: {property_obj.heating}")
            print(f"Balkon: {'var' if property_obj.has_balcony else 'yok'}")
            print(f"Aidat: {property_obj.dues}")
            print(f"Tapu Durumu: {property_obj.deed_status}")
            print(f"Krediye Uygun: {'Evet' if property_obj.is_suitable_for_credit else 'Hayır'}")
            print(f"Pazarlık Payı: {'Var' if property_obj.is_bargainable else 'Yok'}")
            print(f"Mal Sahibi: {property_obj.owner_name}")
            print(f"Mal Sahibi Telefon: {property_obj.owner_phone}")
            print(f"Mal Sahibi İlan No: {property_obj.owner_listing_number}")
            print(f"Branda No: {property_obj.branda_number}")
            print(f"Kimden: {property_obj.listing_from}")
            print(f"Müşteri Etiketi: {property_obj.customer_tag}")
            print(f"Müşteri Kaynağı: {property_obj.customer_source}")
            print(f"Anahtar Kimde: {property_obj.key_holder}")
            print(f"İlan Tarihi: {property_obj.listing_date}")
            print(f"Branda Durumu: {property_obj.banner_status}")
            print(f"Afiş Durumu: {property_obj.poster_status}")
            print(f"Fotoğraf Durumu: {property_obj.photo_status}")
            print(f"SWOT Analizi: {property_obj.swot_analysis[:50]}{'...' if len(property_obj.swot_analysis) > 50 else ''}")
            print(f"Hedef Kitle: {property_obj.target_audience}")
            print(f"Danışman: {property_obj.consultant.get_full_name() if property_obj.consultant else 'Belirtilmemiş'}")
            print(f"Oluşturulma Tarihi: {property_obj.created_at}")
            print(f"Aktif: {'Evet' if property_obj.is_active else 'Hayır'}")
            print("=================================================================")
            
            # Çevre bilgilerini ekle
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
                for photo in photos:
                    # Dosya boyutu kontrolü (5MB)
                    if photo.size > 5 * 1024 * 1024:
                        continue
                    
                    # Dosya tipi kontrolü
                    if photo.content_type not in ['image/jpeg', 'image/png', 'image/jpg']:
                        continue
                    
                    # Başlık oluştur
                    title = photo.name.split('.')[0][:50]
                    
                    # Fotoğrafı kaydet ve property ile ilişkilendir
                    PropertyImage.objects.create(
                        property=property_obj,
                        image=photo,
                        title=title,
                        order=0
                    )
            
            # Ayrıca halihazırda yüklenmiş fotoğrafları da ilişkilendir (eski mekanizma için)
            image_ids = request.POST.getlist('image_ids[]')
            if image_ids:
                for image_id in image_ids:
                    try:
                        image = PropertyImage.objects.get(id=image_id)
                        if not image.property:  # Eğer bir gayrimenkule atanmamışsa
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
def property_update(request, property_id):
    """Gayrimenkul güncelleme"""
    property_obj = get_object_or_404(Property, id=property_id)
    neighborhoods = Neighborhood.objects.all().order_by('name')
    
    # Debug için property değerlerini yazdır
    print("============= GAYRİMENKUL GÜNCELLEME SAYFASI AÇILDI =============")
    print(f"Güncelleme sayfası açıldı - ID: {property_obj.id} - Tarih/Saat: {timezone.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"ID: {property_obj.id}")
    print(f"Başlık: {property_obj.title}")
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
    print(f"Kimden: {property_obj.listing_from}")
    print(f"Müşteri Etiketi: {property_obj.customer_tag}")
    print(f"Müşteri Kaynağı: {property_obj.customer_source}")
    print(f"Anahtar Kimde: {property_obj.key_holder}")
    print(f"İlan Tarihi: {property_obj.listing_date}")
    print(f"Branda Durumu: {property_obj.banner_status}")
    print(f"Afiş Durumu: {property_obj.poster_status}")
    print(f"Fotoğraf Durumu: {property_obj.photo_status}")
    print(f"SWOT Analizi: {property_obj.swot_analysis[:100]}{'...' if len(property_obj.swot_analysis) > 100 else ''}")
    print(f"Hedef Kitle: {property_obj.target_audience}")
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
    
    # Sadece süper kullanıcı veya portföyün danışmanı güncelleyebilir
    if not request.user.is_superuser and property_obj.consultant != request.user:
        messages.error(request, "Bu gayrimenkulü düzenleme yetkiniz yok.")
        return redirect('property_list')
    
    if request.method == 'POST':
        # POST verilerini detaylı yazdır
        print("============= GAYRİMENKUL GÜNCELLEME - POST VERİLERİ =============")
        print(f"POST içeriği alındı - tarih/saat: {timezone.now().strftime('%d.%m.%Y %H:%M:%S')}")
        print(f"title: {request.POST.get('title', 'Boş')}")
        print(f"description: {request.POST.get('description', 'Boş')[:30]}{'...' if len(request.POST.get('description', '')) > 30 else ''}")
        print(f"property_type: {request.POST.get('property_type', 'Boş')}")
        print(f"status: {request.POST.get('status', 'Boş')}")
        print(f"price: {request.POST.get('price', 'Boş')}")
        print(f"neighborhood: {request.POST.get('neighborhood', 'Boş')}")
        print(f"address: {request.POST.get('address', 'Boş')[:30]}{'...' if len(request.POST.get('address', '')) > 30 else ''}")
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
        print(f"from_who (listing_from): {request.POST.get('from_who', 'Boş')}")
        print(f"customer_tag: {request.POST.get('customer_tag', 'Boş')}")
        print(f"customer_source: {request.POST.get('customer_source', 'Boş')}")
        print(f"has_banner: {request.POST.get('has_banner', 'Boş')}")
        print(f"has_poster: {request.POST.get('has_poster', 'Boş')}")
        print(f"has_photos: {request.POST.get('has_photos', 'Boş')}")
        print(f"key_holder: {request.POST.get('key_holder', 'Boş')}")
        print(f"listing_date: {request.POST.get('listing_date', 'Boş')}")
        
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
        property_obj.title = request.POST.get('title', '')
        property_obj.description = request.POST.get('description', '')
        property_obj.status = request.POST.get('status', '')
        property_obj.price = request.POST.get('price', '').replace(',', '.')
        property_obj.neighborhood_id = request.POST.get('neighborhood', '')
        property_obj.address = request.POST.get('address', '')
        property_obj.property_type = request.POST.get('property_type', '')
        property_obj.room_count = request.POST.get('room_count', '')
        property_obj.usage_status = request.POST.get('usage_status', '')
        property_obj.floor_count = request.POST.get('floor_count', '')
        
        # Müşteri Bilgileri
        property_obj.customer_tag = request.POST.get('customer_tag', '')
        property_obj.customer_source = request.POST.get('customer_source', '')
        property_obj.listing_from = request.POST.get('from_who', '')
        
        # Branda/Afiş/Fotoğraf durumu
        has_banner = request.POST.get('has_banner', '')
        if has_banner == 'var':
            property_obj.banner_status = 'asildi'
        elif has_banner == 'yok':
            property_obj.banner_status = 'asilmadi'
            
        has_poster = request.POST.get('has_poster', '')
        if has_poster == 'var':
            property_obj.poster_status = 'asildi' 
        elif has_poster == 'yok':
            property_obj.poster_status = 'asilmadi'
            
        has_photos = request.POST.get('has_photos', '')
        if has_photos == 'var':
            property_obj.photo_status = 'cekildi'
        elif has_photos == 'yok':
            property_obj.photo_status = 'cekilmedi'
        
        # Detay bilgileri güncelle
        if property_obj.property_type == 'daire':
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
        
        # Portföy sahibi bilgilerini güncelle
        property_obj.owner_name = request.POST.get('owner_name', '')
        property_obj.owner_phone = request.POST.get('owner_phone', '')
        property_obj.owner_listing_number = request.POST.get('owner_listing_number', '')
        property_obj.branda_number = request.POST.get('branda_number', '')
        
        # Operasyonel bilgileri güncelle
        property_obj.key_holder = request.POST.get('key_holder', '')
        listing_date = request.POST.get('listing_date', '')
        if listing_date:
            property_obj.listing_date = listing_date
        
        # Analiz bilgilerini güncelle
        property_obj.swot_analysis = request.POST.get('swot_analysis', '')
        property_obj.target_audience = request.POST.get('target_audience', '')
        
        property_obj.save()
        
        # Form işlendikten sonra değerleri kontrol et
        print("============= GÜNCELLEME SONRASI GAYRİMENKUL BİLGİLERİ =============")
        print(f"ID: {property_obj.id}")
        print(f"Başlık: {property_obj.title}")
        print(f"Açıklama: {property_obj.description[:50]}{'...' if len(property_obj.description) > 50 else ''}")
        print(f"Emlak Tipi: {property_obj.property_type}")
        print(f"Durum: {property_obj.status}")
        print(f"Fiyat: {property_obj.price}")
        print(f"Mahalle: {property_obj.neighborhood.name if property_obj.neighborhood else 'Yok'}")
        print(f"Adres: {property_obj.address[:50]}{'...' if len(property_obj.address) > 50 else ''}")
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
        print(f"Mal Sahibi İlan No: {property_obj.owner_listing_number}")
        print(f"Branda No: {property_obj.branda_number}")
        print(f"Kimden: {property_obj.listing_from}")
        print(f"Müşteri Etiketi: {property_obj.customer_tag}")
        print(f"Müşteri Kaynağı: {property_obj.customer_source}")
        print(f"Anahtar Kimde: {property_obj.key_holder}")
        print(f"İlan Tarihi: {property_obj.listing_date}")
        print(f"Branda Durumu: {property_obj.banner_status}")
        print(f"Afiş Durumu: {property_obj.poster_status}")
        print(f"Fotoğraf Durumu: {property_obj.photo_status}")
        print(f"SWOT Analizi: {property_obj.swot_analysis[:50]}{'...' if len(property_obj.swot_analysis) > 50 else ''}")
        print(f"Hedef Kitle: {property_obj.target_audience}")
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
            for photo in photos:
                # Dosya boyutu kontrolü (5MB)
                if photo.size > 5 * 1024 * 1024:
                    continue
                
                # Dosya tipi kontrolü
                if photo.content_type not in ['image/jpeg', 'image/png', 'image/jpg']:
                    continue
                
                # Başlık oluştur
                title = photo.name.split('.')[0][:50]
                
                # Fotoğrafı kaydet ve property ile ilişkilendir
                PropertyImage.objects.create(
                    property=property_obj,
                    image=photo,
                    title=title,
                    order=0
                )
        
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
            
            # Güvenlik kontrolü
            if not request.user.is_superuser and property_obj.consultant != request.user:
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
            elif field in ['banner_status', 'poster_status', 'usage_status', 'category', 'listing_type']:
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
@csrf_exempt
def property_delete(request, property_id):
    """AJAX ile gayrimenkul silme"""
    if request.method == 'POST':
        try:
            try:
                property_obj = Property.objects.get(id=property_id)
            except Property.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Gayrimenkul bulunamadı'})
            
            # Güvenlik kontrolü
            if not request.user.is_superuser and property_obj.consultant != request.user:
                return JsonResponse({'success': False, 'error': 'Bu gayrimenkulü silme yetkiniz yok'})
            
            # Gayrimenkulün başlığını sakla
            property_title = property_obj.title
            
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
