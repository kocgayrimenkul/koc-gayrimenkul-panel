# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Daire Sunumu Görünümleri
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.urls import reverse
from django.contrib import messages
from .models import Presentation, PresentationFeedback
from .forms import PresentationForm, PresentationFeedbackForm
from apps.portfolio.models import Property
from apps.customers.models import Neighborhood
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.db.models import Count, Avg, Q
from apps.employees.models import EmployeeProfile
from apps.employees.decorators import (
    can_view_presentation,
    can_add_presentation,
    can_edit_presentation,
    can_delete_presentation,
    require_presentation_permission
)

def get_user_role(user):
    """Kullanıcının rolünü döndürür"""
    # Superuser ise admin rolünü döndür
    if user.is_superuser:
        return 'admin'
    
    try:
        return user.employee_profile.role
    except (EmployeeProfile.DoesNotExist, AttributeError):
        return None

@login_required(login_url="/login/")
@can_view_presentation
def presentation_list(request):
    """Sunum listesi görüntüleme"""
    
    role = get_user_role(request.user)
    
    # Yönetici, Müdür, Santral veya superuser ise tüm sunumları göster
    if request.user.is_superuser or role in ['admin', 'manager', 'secretary']:
        presentations = Presentation.objects.all()
    else:
        # Danışmanın atandığı mahalleleri bul
        consultant_neighborhoods = Neighborhood.objects.filter(consultant=request.user)
        # Bu mahallelerdeki sunumları getir
        presentations = Presentation.objects.filter(
            Q(neighborhood__in=consultant_neighborhoods) | Q(presenter=request.user)
        ).distinct()
    
    # Filtreleme işlemleri
    filter_property = request.GET.get('property', '')
    if filter_property:
        presentations = presentations.filter(property_id=filter_property)

    filter_status = request.GET.get('status', '')
    if filter_status:
        presentations = presentations.filter(status=filter_status)

    filter_date = request.GET.get('date', '')
    if filter_date == 'today':
        today = timezone.now().date()
        presentations = presentations.filter(presentation_date__date=today)
    elif filter_date == 'week':
        week_ago = timezone.now().date() - timedelta(days=7)
        presentations = presentations.filter(presentation_date__date__gte=week_ago)
    elif filter_date == 'month':
        month_ago = timezone.now().date() - timedelta(days=30)
        presentations = presentations.filter(presentation_date__date__gte=month_ago)
    
    # Sıralama
    presentations = presentations.select_related('property', 'presenter', 'neighborhood').order_by('-presentation_date')
    
    # Pagination
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    page = request.GET.get('page', 1)
    paginator = Paginator(presentations, 15)  # Sayfa başına 15 kayıt
    
    try:
        presentations_page = paginator.page(page)
    except PageNotAnInteger:
        presentations_page = paginator.page(1)
    except EmptyPage:
        presentations_page = paginator.page(paginator.num_pages)
    
    # İstatistikler (filtrelenmemiş tüm veriler üzerinden)
    if request.user.is_superuser or role in ['admin', 'manager', 'secretary']:
        all_presentations = Presentation.objects.all()
    else:
        consultant_neighborhoods = Neighborhood.objects.filter(consultant=request.user)
        all_presentations = Presentation.objects.filter(
            Q(neighborhood__in=consultant_neighborhoods) | Q(presenter=request.user)
        ).distinct()
    
    bekleyen_sunum_sayisi = all_presentations.filter(status='bekliyor').count()
    tamamlanan_sunum_sayisi = all_presentations.filter(status='tamamlandi').count()
    iptal_sunum_sayisi = all_presentations.filter(status='iptal').count()
    
    # Filtrelenen gayrimenkul bilgisi
    filtered_property = None
    if filter_property:
        from apps.portfolio.models import Property
        try:
            filtered_property = Property.objects.get(pk=filter_property)
        except Property.DoesNotExist:
            pass

    context = {
        'segment': 'daire_sunumu',
        'presentations': presentations_page,
        'filter_status': filter_status,
        'filter_date': filter_date,
        'filter_property': filter_property,
        'filtered_property': filtered_property,
        'bekleyen_sunum_sayisi': bekleyen_sunum_sayisi,
        'tamamlanan_sunum_sayisi': tamamlanan_sunum_sayisi,
        'iptal_sunum_sayisi': iptal_sunum_sayisi,
    }
    
    html_template = loader.get_template('presentation/presentation_list.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
@can_view_presentation
def presentation_detail(request, presentation_id):
    """Sunum detay sayfası"""
    
    # Sunum kaydını çek
    presentation = get_object_or_404(Presentation, id=presentation_id)
    
    role = get_user_role(request.user)
    
    # Yönetici, Müdür, Santral veya superuser değilse ve sunum ile ilişkisi yoksa erişimi engelle
    if not request.user.is_superuser and role not in ['admin', 'manager', 'secretary']:
        consultant_neighborhoods = Neighborhood.objects.filter(consultant=request.user)
        if not (presentation.neighborhood in consultant_neighborhoods or presentation.presenter == request.user):
            messages.error(request, "Bu sunum kaydını görüntüleme yetkiniz yok.")
            return redirect('presentation_list')
    
    # Sunum geri bildirimleri
    feedbacks = presentation.feedbacks.all()
    avg_rating = feedbacks.aggregate(Avg('rating'))['rating__avg'] if feedbacks.exists() else 0
    
    # Geri bildirim formu
    if request.method == 'POST':
        feedback_form = PresentationFeedbackForm(request.POST)
        if feedback_form.is_valid():
            feedback = feedback_form.save(commit=False)
            feedback.presentation = presentation
            feedback.save()
            messages.success(request, "Geri bildiriminiz başarıyla kaydedildi.")
            return redirect('presentation_detail', presentation_id=presentation.id)
    else:
        feedback_form = PresentationFeedbackForm()
    
    context = {
        'segment': 'daire_sunumu',
        'presentation': presentation,
        'feedbacks': feedbacks,
        'avg_rating': avg_rating,
        'feedback_form': feedback_form,
    }
    
    html_template = loader.get_template('presentation/presentation_detail.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def presentation_create(request):
    """Yeni sunum oluşturma"""
    
    role = get_user_role(request.user)
    
    # İlk olarak temel yetki kontrolü yap - logout atmadan
    if not request.user.is_superuser:
        # Employee profili var mı kontrol et
        try:
            employee = request.user.employee_profile
            if not employee.is_active:
                messages.error(request, "Hesabınız deaktif edilmiştir.")
                return redirect('presentation_list')
        except:
            messages.error(request, "Çalışan profili bulunamadı.")
            return redirect('presentation_list')
        
        # Permission modülünden yetki kontrolü
        from apps.employees.decorators import has_module_permission
        
        if not has_module_permission(request.user, 'presentation', 'add'):
            messages.error(request, "Daire sunumu oluşturma yetkiniz bulunmamaktadır.")
            return redirect('presentation_list')
    
    # Danışmanın erişebileceği mahalleleri getir
    if request.user.is_superuser or role in ['admin', 'manager']:
        neighborhoods = Neighborhood.objects.all().order_by('name')
    else:
        neighborhoods = Neighborhood.objects.filter(consultant=request.user).order_by('name')
    
    # Eğer POST isteği ise form verilerini işle
    if request.method == 'POST':
        form = PresentationForm(request.POST)
        if form.is_valid():
            presentation = form.save(commit=False)
            
            # Danışman sadece kendi mahallelerine sunum ekleyebilir
            if role == 'consultant':
                if not neighborhoods.filter(id=presentation.neighborhood.id).exists():
                    messages.error(request, "Bu mahalleye sunum ekleme yetkiniz yok.")
                    return redirect('presentation_list')
                
                # Sunan kişi olarak mahallenin danışmanını ata
                presentation.presenter = presentation.neighborhood.consultant
            
            presentation.save()
            messages.success(request, "Sunum başarıyla oluşturuldu.")
            return redirect('presentation_detail', presentation_id=presentation.id)
    else:
        # Eğer yönetici, müdür veya superuser değilse presenter alanını otomatik doldur
        if not request.user.is_superuser and role not in ['admin', 'manager']:
            form = PresentationForm(initial={'presenter': request.user})
            form.fields['presenter'].widget.attrs['readonly'] = True
        else:
            form = PresentationForm()
            
    # Properties artık AJAX ile yüklenecek, context'ten kaldır
    context = {
        'segment': 'daire_sunumu',
        'form': form,
        'neighborhoods': neighborhoods,
    }
    
    html_template = loader.get_template('presentation/presentation_create.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def presentation_edit(request, presentation_id):
    """Sunum düzenleme"""
    
    # Sunum kaydını çek
    presentation = get_object_or_404(Presentation, id=presentation_id)
    
    role = get_user_role(request.user)
    
    # İlk olarak temel yetki kontrolü yap - logout atmadan
    if not request.user.is_superuser:
        # Employee profili var mı kontrol et
        try:
            employee = request.user.employee_profile
            if not employee.is_active:
                messages.error(request, "Hesabınız deaktif edilmiştir.")
                return redirect('presentation_list')
        except:
            messages.error(request, "Çalışan profili bulunamadı.")
            return redirect('presentation_list')
        
        # Permission modülünden yetki kontrolü
        from apps.employees.decorators import has_module_permission
        
        if not has_module_permission(request.user, 'presentation', 'edit'):
            messages.error(request, "Daire sunumu düzenleme yetkiniz bulunmamaktadır.")
            return redirect('presentation_list')
    
    # Sunum ile ilişki kontrolü
    if not request.user.is_superuser and role not in ['admin', 'manager', 'secretary']:
        consultant_neighborhoods = Neighborhood.objects.filter(consultant=request.user)
        if not (presentation.neighborhood in consultant_neighborhoods or presentation.presenter == request.user):
            messages.error(request, "Bu sunum kaydını düzenleme yetkiniz yok.")
            return redirect('presentation_list')
    
    # Danışmanın erişebileceği mahalleleri getir
    if request.user.is_superuser or role in ['admin', 'manager']:
        neighborhoods = Neighborhood.objects.all().order_by('name')
    else:
        neighborhoods = Neighborhood.objects.filter(consultant=request.user).order_by('name')
    
    # Eğer POST isteği ise form verilerini işle
    if request.method == 'POST':
        form = PresentationForm(request.POST, instance=presentation)
        if form.is_valid():
            presentation = form.save(commit=False)
            
            # Danışman sadece kendi mahallelerine sunum atayabilir
            if role == 'consultant':
                if not neighborhoods.filter(id=presentation.neighborhood.id).exists():
                    messages.error(request, "Bu mahalleye sunum atama yetkiniz yok.")
                    return redirect('presentation_list')
                
                # Sunan kişi olarak mahallenin danışmanını ata
                presentation.presenter = presentation.neighborhood.consultant
            
            presentation.save()
            messages.success(request, "Sunum başarıyla güncellendi.")
            return redirect('presentation_detail', presentation_id=presentation.id)
    else:
        form = PresentationForm(instance=presentation)
        
        # Eğer yönetici, müdür veya superuser değilse presenter alanını readonly yap
        if not request.user.is_superuser and role not in ['admin', 'manager']:
            form.fields['presenter'].widget.attrs['readonly'] = True
    
    # Properties artık AJAX ile yüklenecek, context'ten kaldır
    context = {
        'segment': 'daire_sunumu',
        'form': form,
        'presentation': presentation,
        'neighborhoods': neighborhoods,
    }
    
    html_template = loader.get_template('presentation/presentation_edit.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def presentation_delete(request, presentation_id):
    """Sunum silme"""
    
    # Sunum kaydını çek
    presentation = get_object_or_404(Presentation, id=presentation_id)
    
    role = get_user_role(request.user)
    
    # İlk olarak temel yetki kontrolü yap - logout atmadan
    if not request.user.is_superuser:
        # Employee profili var mı kontrol et
        try:
            employee = request.user.employee_profile
            if not employee.is_active:
                messages.error(request, "Hesabınız deaktif edilmiştir.")
                return redirect('presentation_list')
        except:
            messages.error(request, "Çalışan profili bulunamadı.")
            return redirect('presentation_list')
        
        # Permission modülünden yetki kontrolü
        from apps.employees.decorators import has_module_permission
        
        if not has_module_permission(request.user, 'presentation', 'delete'):
            messages.error(request, "Daire sunumu silme yetkiniz bulunmamaktadır.")
            return redirect('presentation_list')
    
    if request.method == 'POST':
        presentation.delete()
        messages.success(request, "Sunum başarıyla silindi.")
        return redirect('presentation_list')
    
    context = {
        'segment': 'daire_sunumu',
        'presentation': presentation,
    }
    
    html_template = loader.get_template('presentation/presentation_delete.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def update_presentation_status(request, presentation_id):
    """AJAX ile sunum durumunu güncelleme"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        presentation = get_object_or_404(Presentation, id=presentation_id)
        
        # Süper kullanıcı değilse ve sunum ile ilişkisi yoksa erişimi engelle
        if not request.user.is_superuser and presentation.presenter != request.user:
            return JsonResponse({'status': 'error', 'message': 'Yetkiniz yok'}, status=403)
        
        status = request.POST.get('status', 'bekliyor')
        notes = request.POST.get('notes', '')
        
        presentation.status = status
        presentation.notes = notes
        presentation.save()
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error', 'message': 'Geçersiz istek'}, status=400)

@login_required(login_url="/login/")
def get_neighborhood_consultant(request):
    """AJAX ile mahalle danışmanını getirme"""
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        neighborhood_id = request.GET.get('neighborhood_id')
        
        if neighborhood_id:
            try:
                neighborhood = Neighborhood.objects.get(id=neighborhood_id)
                if neighborhood.consultant:
                    return JsonResponse({
                        'status': 'success',
                        'consultant_id': neighborhood.consultant.id,
                        'consultant_name': f"{neighborhood.consultant.first_name} {neighborhood.consultant.last_name}"
                    })
                else:
                    return JsonResponse({'status': 'info', 'message': 'Bu mahalleye atanmış danışman bulunmuyor.'})
            except Neighborhood.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Mahalle bulunamadı.'}, status=404)
        
        return JsonResponse({'status': 'error', 'message': 'Mahalle ID eksik.'}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Geçersiz istek'}, status=400)

@login_required(login_url="/login/")
def property_search_ajax(request):
    """AJAX ile daire arama - Select2 için"""
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        search_term = request.GET.get('q', '').strip()
        page = int(request.GET.get('page', 1))
        page_size = 20  # Her seferde 20 kayıt
        
        # Base queryset
        properties = Property.objects.filter(
            is_active=True
        ).select_related('neighborhood')
        
        # Arama filtresi
        if search_term:
            from django.db.models import Q
            # Türkçe karakter normalleştirme için
            search_terms = []
            
            # Arama terimini kelimelere böl
            words = search_term.strip().split()
            
            # Her kelime için Q objesi oluştur
            q_objects = Q()
            
            for word in words:
                # Orijinal kelime
                search_terms.append(word)
                
                # Türkçe karakterleri dönüştür
                normalized_word = word.lower()
                char_map = {
                    'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u',
                    'Ç': 'c', 'Ğ': 'g', 'İ': 'i', 'Ö': 'o', 'Ş': 's', 'Ü': 'u'
                }
                
                for char, replacement in char_map.items():
                    normalized_word = normalized_word.replace(char, replacement)
                
                if normalized_word != word.lower():
                    search_terms.append(normalized_word)
            
            # Tüm arama terimleri için sorgu oluştur
            for term in search_terms:
                q_objects |= (
                    Q(apartment_name__icontains=term) |  # Daire adında arama (öncelik)
                    Q(web_title__icontains=term) |
                    Q(neighborhood__name__icontains=term) |
                    Q(owner_listing_number__icontains=term) |  # property_code yerine owner_listing_number
                    Q(address__icontains=term)  # Adres araması da eklendi
                )
            
            properties = properties.filter(q_objects)
        
        # Pagination
        from django.core.paginator import Paginator
        paginator = Paginator(properties, page_size)
        
        try:
            current_page = paginator.page(page)
        except:
            current_page = paginator.page(1)
        
        # Results formatı
        results = []
        for property_obj in current_page:
            title = f"[{property_obj.property_type.upper()}] "
            
            # Önce apartment_name'i kullan
            title += property_obj.apartment_name
            
            # Web title varsa parantez içinde ekle
            if property_obj.web_title and property_obj.web_title != property_obj.apartment_name:
                title += f" ({property_obj.web_title})"
            
            title += f" - {property_obj.neighborhood.name}"
            
            if property_obj.price:
                title += f" ({property_obj.price:,.0f} ₺)"
            
            results.append({
                'id': property_obj.id,
                'text': title
            })
        
        # Response formatı Select2 için
        response_data = {
            'results': results,
            'pagination': {
                'more': current_page.has_next()
            }
        }
        
        return JsonResponse(response_data)
    
    return JsonResponse({'results': [], 'pagination': {'more': False}})


from django.contrib.auth.decorators import login_required
from django.http import JsonResponse as _JR2

@login_required
def property_presentations_api(request, property_id):
    """Bir gayrimenkule ait tüm yer göstermeleri döndür"""
    from apps.portfolio.models import Property
    try:
        prop = Property.objects.get(pk=property_id)
    except Property.DoesNotExist:
        return _JR2({'error': 'Bulunamadı'}, status=404)

    qs = Presentation.objects.filter(property=prop).select_related('presenter').order_by('-presentation_date')

    STATUS_MAP = {
        'bekliyor':    'Planlandı',
        'tamamlandi':  'Gösterildi',
        'satis':       'Satışa Gönderildi',
        'iptal':       'İptal/Gelmedi',
    }
    COLOR_MAP = {
        'bekliyor':   '#3b82f6',
        'tamamlandi': '#10b981',
        'satis':      '#8b5cf6',
        'iptal':      '#ef4444',
    }

    rows = []
    for p in qs:
        rows.append({
            'id': p.id,
            'customer_name': p.customer_name,
            'customer_phone': p.customer_phone,
            'presenter': p.presenter.get_full_name() or p.presenter.username if p.presenter else '',
            'status': p.status,
            'status_label': STATUS_MAP.get(p.status, p.get_status_display()),
            'status_color': COLOR_MAP.get(p.status, '#64748b'),
            'date': p.presentation_date.strftime('%d.%m.%Y') if p.presentation_date else '',
            'notes': p.notes or '',
            'is_completed': p.is_completed,
            'detail_url': f'/daire-sunumu/{p.id}/',
        })

    stats = {
        'total':     qs.count(),
        'planned':   qs.filter(status='bekliyor').count(),
        'shown':     qs.filter(status='tamamlandi').count(),
        'sale':      qs.filter(status='satis').count(),
        'cancelled': qs.filter(status='iptal').count(),
    }

    return _JR2({
        'property_name': prop.apartment_name or str(prop),
        'property_id': prop.id,
        'stats': stats,
        'presentations': rows,
    })
