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
    
    context = {
        'segment': 'gayrimenkul',
        'properties': properties,
        'neighborhoods': neighborhoods,
        'filters': {
            'property_type': property_type,
            'status': status,
            'neighborhood_id': neighborhood_id,
            'min_price': min_price,
            'max_price': max_price,
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
        # Temel bilgiler
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        property_type = request.POST.get('property_type', '')
        status = request.POST.get('status', '')
        price = request.POST.get('price', '')
        neighborhood_id = request.POST.get('neighborhood', '')
        address = request.POST.get('address', '')
        
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
                consultant=request.user,
            )
            
            # Detay bilgileri
            if property_type == 'daire':
                property_obj.gross_area = request.POST.get('gross_area', None)
                property_obj.net_area = request.POST.get('net_area', None)
                property_obj.room_count = request.POST.get('room_count', '')
                property_obj.floor = request.POST.get('floor', '')
                property_obj.building_age = request.POST.get('building_age', None)
                property_obj.heating = request.POST.get('heating', '')
                property_obj.has_balcony = 'has_balcony' in request.POST
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
            property_obj.photo_status = 'photo_status' in request.POST
            listing_date = request.POST.get('listing_date', '')
            if listing_date:
                property_obj.listing_date = listing_date
            
            # Analiz bilgileri
            property_obj.swot_analysis = request.POST.get('swot_analysis', '')
            property_obj.target_audience = request.POST.get('target_audience', '')
            
            property_obj.save()
            
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
            
            # Yüklenen fotoğrafları gayrimenkulle ilişkilendir
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
    
    # Sadece süper kullanıcı veya portföyün danışmanı güncelleyebilir
    if not request.user.is_superuser and property_obj.consultant != request.user:
        messages.error(request, "Bu gayrimenkulü düzenleme yetkiniz yok.")
        return redirect('property_list')
    
    if request.method == 'POST':
        # Temel bilgileri güncelle
        property_obj.title = request.POST.get('title', '')
        property_obj.description = request.POST.get('description', '')
        property_obj.status = request.POST.get('status', '')
        property_obj.price = request.POST.get('price', '').replace(',', '.')
        property_obj.neighborhood_id = request.POST.get('neighborhood', '')
        property_obj.address = request.POST.get('address', '')
        
        # Detay bilgileri güncelle
        if property_obj.property_type == 'daire':
            property_obj.gross_area = request.POST.get('gross_area', None) or None
            property_obj.net_area = request.POST.get('net_area', None) or None
            property_obj.room_count = request.POST.get('room_count', '')
            property_obj.floor = request.POST.get('floor', '')
            property_obj.building_age = request.POST.get('building_age', None) or None
            property_obj.heating = request.POST.get('heating', '')
            property_obj.has_balcony = 'has_balcony' in request.POST
            property_obj.dues = request.POST.get('dues', None) or None
        
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
        property_obj.photo_status = 'photo_status' in request.POST
        listing_date = request.POST.get('listing_date', '')
        if listing_date:
            property_obj.listing_date = listing_date
        
        # Analiz bilgilerini güncelle
        property_obj.swot_analysis = request.POST.get('swot_analysis', '')
        property_obj.target_audience = request.POST.get('target_audience', '')
        
        property_obj.save()
        
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
        
        # Yüklenen fotoğrafları gayrimenkulle ilişkilendir
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
