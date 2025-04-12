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
from .models import Customer, Neighborhood
from apps.portfolio.models import Property  # Property modelini ekledik
from django.utils import timezone
from datetime import datetime, timedelta

@login_required(login_url="/login/")
def customer_list(request):
    """Danışmanın kendi müşterilerini listelemesi"""
    
    # Eğer kullanıcı süper kullanıcı ise tüm müşterileri göster
    if request.user.is_superuser:
        customers = Customer.objects.all()
    else:
        # Sadece danışmanın kendi müşterilerini göster
        customers = Customer.objects.filter(consultant=request.user)
    
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
    
    # İstatistikler için sayıları hesapla
    all_customers = customers
    olumlu_musteri_sayisi = all_customers.filter(meeting_status='olumlu').count()
    olumsuz_musteri_sayisi = all_customers.filter(meeting_status='olumsuz').count()
    bekleyen_musteri_sayisi = all_customers.filter(meeting_status='bekliyor').count()
    
    context = {
        'segment': 'musteri',
        'customers': customers,
        'filter_status': filter_status,
        'filter_date': filter_date,
        'olumlu_musteri_sayisi': olumlu_musteri_sayisi,
        'olumsuz_musteri_sayisi': olumsuz_musteri_sayisi,
        'bekleyen_musteri_sayisi': bekleyen_musteri_sayisi,
    }
    
    html_template = loader.get_template('customers/customer_list.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def customer_detail(request, customer_id):
    """Müşteri detay sayfası"""
    
    # Müşteri kaydını çek
    customer = get_object_or_404(Customer, id=customer_id)
    
    # Süper kullanıcı değilse ve müşteri danışmanın değilse erişimi engelle
    if not request.user.is_superuser and customer.consultant != request.user:
        messages.error(request, "Bu müşteri kaydını görüntüleme yetkiniz yok.")
        return redirect('customer_list')
    
    # Eğer POST isteği ise görüşme sonucunu güncelle
    if request.method == 'POST':
        meeting_result = request.POST.get('meeting_result', '')
        meeting_status = request.POST.get('meeting_status', 'bekliyor')
        
        # Görüşme sonucunu güncelle
        customer.meeting_result = meeting_result
        customer.meeting_status = meeting_status
        customer.save()
        
        messages.success(request, "Görüşme sonucu başarıyla kaydedildi.")
        return redirect('customer_list')
    
    context = {
        'segment': 'musteri',
        'customer': customer,
    }
    
    html_template = loader.get_template('customers/customer_detail.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def customer_edit(request, customer_id):
    """Müşteri düzenleme sayfası"""
    
    # Müşteri kaydını çek
    customer = get_object_or_404(Customer, id=customer_id)
    
    # Süper kullanıcı değilse ve müşteri danışmanın değilse erişimi engelle
    if not request.user.is_superuser and customer.consultant != request.user:
        messages.error(request, "Bu müşteri kaydını düzenleme yetkiniz yok.")
        return redirect('customer_list')
    
    neighborhoods = Neighborhood.objects.all().order_by('name')
    
    # Eğer POST isteği ise müşteri bilgilerini güncelle
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '')
        phone = request.POST.get('phone', '')
        apartment = request.POST.get('apartment', '')
        neighborhood_id = request.POST.get('neighborhood', '')
        notes = request.POST.get('notes', '')
        
        # Validation
        if not full_name or not phone or not neighborhood_id:
            messages.error(request, "Lütfen tüm zorunlu alanları doldurun.")
            return render(request, 'customers/customer_edit.html', {
                'segment': 'musteri',
                'customer': customer,
                'neighborhoods': neighborhoods
            })
        
        try:
            neighborhood = Neighborhood.objects.get(id=neighborhood_id)
            
            # Müşteriyi güncelle
            customer.full_name = full_name
            customer.phone = phone
            customer.apartment = apartment
            customer.neighborhood = neighborhood
            customer.notes = notes
            customer.save()
            
            messages.success(request, "Müşteri bilgileri başarıyla güncellendi.")
            return redirect('customer_detail', customer_id=customer.id)
        
        except Exception as e:
            messages.error(request, f"Bir hata oluştu: {str(e)}")
    
    context = {
        'segment': 'musteri',
        'customer': customer,
        'neighborhoods': neighborhoods,
    }
    
    html_template = loader.get_template('customers/customer_edit.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def customer_register(request):
    """Santral tarafından müşteri kayıt ekranı"""
    
    # Sadece süper kullanıcı veya santral rolü olan kişiler erişebilir
    if not request.user.is_superuser and not request.user.groups.filter(name='Santral').exists():
        messages.error(request, "Bu sayfaya erişim yetkiniz bulunmamaktadır.")
        return redirect('home')
    
    neighborhoods = Neighborhood.objects.all().order_by('name')
    
    # Eğer POST isteği ise yeni müşteri kaydı oluştur
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '')
        phone = request.POST.get('phone', '')
        apartment = request.POST.get('apartment', '')
        neighborhood_id = request.POST.get('neighborhood', '')
        
        # Validation
        if not full_name or not phone or not neighborhood_id:
            messages.error(request, "Lütfen tüm zorunlu alanları doldurun.")
            return render(request, 'customers/customer_register.html', {
                'segment': 'musteri_kayit',
                'neighborhoods': neighborhoods,
                'form_data': request.POST,
            })
        
        try:
            neighborhood = Neighborhood.objects.get(id=neighborhood_id)
            
            # Yeni müşteri oluştur
            customer = Customer(
                full_name=full_name,
                phone=phone,
                apartment=apartment,
                neighborhood=neighborhood,
                # Danışman otomatik olarak model save metodunda atanacak
            )
            customer.save()
            
            messages.success(request, "Müşteri başarıyla kaydedildi ve ilgili danışmana atandı.")
            return redirect('customer_register')
        
        except Exception as e:
            messages.error(request, f"Bir hata oluştu: {str(e)}")
    
    context = {
        'segment': 'musteri_kayit',
        'neighborhoods': neighborhoods,
    }
    
    html_template = loader.get_template('customers/customer_register.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def customer_create(request):
    """Danışmanların yeni müşteri oluşturma ekranı"""
    
    # Danışman veya süper kullanıcı olmayanlar erişemez
    if not request.user.is_superuser and not request.user.groups.filter(name='Danışman').exists():
        messages.error(request, "Bu sayfaya erişim yetkiniz bulunmamaktadır.")
        return redirect('home')
    
    neighborhoods = Neighborhood.objects.all().order_by('name')
    
    # Daire tipi portföyleri getir
    properties = Property.objects.filter(property_type='daire', is_active=True).order_by('-created_at')
    
    # Eğer POST isteği ise yeni müşteri kaydı oluştur
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '')
        phone = request.POST.get('phone', '')
        apartment = request.POST.get('apartment', '')
        property_id = request.POST.get('property_id', '')  # Seçilen daire ID'si
        neighborhood_id = request.POST.get('neighborhood', '')
        notes = request.POST.get('notes', '')
        
        # Validation
        if not full_name or not phone or not neighborhood_id:
            messages.error(request, "Lütfen tüm zorunlu alanları doldurun.")
            return render(request, 'customers/customer_create.html', {
                'segment': 'musteri_ekle',
                'neighborhoods': neighborhoods,
                'properties': properties,
                'form_data': request.POST,
            })
        
        try:
            neighborhood = Neighborhood.objects.get(id=neighborhood_id)
            
            # Eğer daire seçilmişse, daire bilgilerini kullan
            apartment_info = apartment
            if property_id:
                try:
                    property_obj = Property.objects.get(id=property_id)
                    # Daire bilgisini otomatik oluştur
                    apartment_info = f"{property_obj.title} - {property_obj.address}"
                except Property.DoesNotExist:
                    pass
            
            # Yeni müşteri oluştur
            customer = Customer(
                full_name=full_name,
                phone=phone,
                apartment=apartment_info,
                neighborhood=neighborhood,
                consultant=request.user,  # Müşteriyi oluşturan danışmana doğrudan ata
                notes=notes
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
    }
    
    html_template = loader.get_template('customers/customer_create.html')
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
def neighborhood_list(request):
    """Mahalle listesi görüntüleme (sadece admin için)"""
    if not request.user.is_superuser:
        messages.error(request, "Bu sayfaya erişim yetkiniz bulunmamaktadır.")
        return redirect('home')
    
    neighborhoods = Neighborhood.objects.all().order_by('name')
    
    context = {
        'segment': 'mahalleler',
        'neighborhoods': neighborhoods,
    }
    
    html_template = loader.get_template('customers/neighborhood_list.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def neighborhood_edit(request, neighborhood_id=None):
    """Mahalle ekleme/düzenleme (sadece admin için)"""
    if not request.user.is_superuser:
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
    
    # Danışmanları çek
    from django.contrib.auth.models import User, Group
    consultant_group = Group.objects.filter(name='Danışman').first()
    if consultant_group:
        consultants = User.objects.filter(groups=consultant_group)
    else:
        consultants = User.objects.filter(is_staff=True)
    
    context = {
        'segment': 'mahalleler',
        'neighborhood': neighborhood,
        'consultants': consultants,
    }
    
    html_template = loader.get_template('customers/neighborhood_edit.html')
    return HttpResponse(html_template.render(context, request))

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
                from django.contrib.auth.models import Group
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
