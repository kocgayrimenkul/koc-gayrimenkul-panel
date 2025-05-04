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
from django.db.models import Count, Avg

@login_required(login_url="/login/")
def presentation_list(request):
    """Sunum listesi görüntüleme"""
    
    # Eğer kullanıcı süper kullanıcı ise tüm sunumları göster
    if request.user.is_superuser:
        presentations = Presentation.objects.all()
    else:
        # Sadece kullanıcının kendi sunumlarını göster
        presentations = Presentation.objects.filter(presenter=request.user)
    
    # Filtreleme işlemleri
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
    
    # İstatistikler
    bekleyen_sunum_sayisi = presentations.filter(status='bekliyor').count()
    tamamlanan_sunum_sayisi = presentations.filter(status='tamamlandi').count()
    iptal_sunum_sayisi = presentations.filter(status='iptal').count()
    
    context = {
        'segment': 'daire_sunumu',
        'presentations': presentations,
        'filter_status': filter_status,
        'filter_date': filter_date,
        'bekleyen_sunum_sayisi': bekleyen_sunum_sayisi,
        'tamamlanan_sunum_sayisi': tamamlanan_sunum_sayisi,
        'iptal_sunum_sayisi': iptal_sunum_sayisi,
    }
    
    html_template = loader.get_template('presentation/presentation_list.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def presentation_detail(request, presentation_id):
    """Sunum detay sayfası"""
    
    # Sunum kaydını çek
    presentation = get_object_or_404(Presentation, id=presentation_id)
    
    # Süper kullanıcı değilse ve sunum ile ilişkisi yoksa erişimi engelle
    if not request.user.is_superuser and presentation.presenter != request.user:
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
    
    # Eğer POST isteği ise form verilerini işle
    if request.method == 'POST':
        form = PresentationForm(request.POST)
        if form.is_valid():
            presentation = form.save()
            messages.success(request, "Sunum başarıyla oluşturuldu.")
            return redirect('presentation_detail', presentation_id=presentation.id)
    else:
        # Eğer süper kullanıcı değilse presenter alanını otomatik doldur
        if request.user.is_superuser:
            form = PresentationForm()
        else:
            form = PresentationForm(initial={'presenter': request.user})
            form.fields['presenter'].widget.attrs['readonly'] = True
            
    # Daireleri çek
    properties = Property.objects.filter(property_type='daire', is_active=True)
    
    context = {
        'segment': 'daire_sunumu',
        'form': form,
        'properties': properties,
    }
    
    html_template = loader.get_template('presentation/presentation_create.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def presentation_edit(request, presentation_id):
    """Sunum düzenleme"""
    
    # Sunum kaydını çek
    presentation = get_object_or_404(Presentation, id=presentation_id)
    
    # Süper kullanıcı değilse ve sunum ile ilişkisi yoksa erişimi engelle
    if not request.user.is_superuser and presentation.presenter != request.user:
        messages.error(request, "Bu sunum kaydını düzenleme yetkiniz yok.")
        return redirect('presentation_list')
    
    # Eğer POST isteği ise form verilerini işle
    if request.method == 'POST':
        form = PresentationForm(request.POST, instance=presentation)
        if form.is_valid():
            form.save()
            messages.success(request, "Sunum başarıyla güncellendi.")
            return redirect('presentation_detail', presentation_id=presentation.id)
    else:
        form = PresentationForm(instance=presentation)
        
        # Eğer süper kullanıcı değilse presenter alanını readonly yap
        if not request.user.is_superuser:
            form.fields['presenter'].widget.attrs['readonly'] = True
    
    context = {
        'segment': 'daire_sunumu',
        'form': form,
        'presentation': presentation,
    }
    
    html_template = loader.get_template('presentation/presentation_edit.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def presentation_delete(request, presentation_id):
    """Sunum silme"""
    
    # Sunum kaydını çek
    presentation = get_object_or_404(Presentation, id=presentation_id)
    
    # Sadece süper kullanıcılar sunumları silebilir
    if not request.user.is_superuser:
        messages.error(request, "Sunum silme yetkiniz yok.")
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
