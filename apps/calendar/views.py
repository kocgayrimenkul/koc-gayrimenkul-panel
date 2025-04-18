# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Takvim/Ajanda Görünümleri
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.urls import reverse
from django.contrib import messages
from .models import Event, TodoItem
from apps.customers.models import Customer
from apps.portfolio.models import Property
from django.utils import timezone
from datetime import datetime, timedelta, date
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q

@login_required(login_url="/login/")
def calendar_view(request):
    """Takvim görünümü"""
    
    # Bugün ve sonraki etkinlikler
    today = timezone.now().date()
    
    # İlgili kullanıcıya ait etkinlikler
    if request.user.is_superuser:
        # Süper kullanıcı ise tüm etkinlikleri görebilir
        events = Event.objects.filter(start_time__date__gte=today)
    else:
        # Normal kullanıcı ise sadece kendi etkinliklerini görebilir
        events = Event.objects.filter(consultant=request.user, start_time__date__gte=today)
    
    # Tarih filtreleme
    filter_date = request.GET.get('date', '')
    if filter_date:
        try:
            filter_date = datetime.strptime(filter_date, '%Y-%m-%d').date()
            events = events.filter(start_time__date=filter_date)
        except ValueError:
            pass
    
    # Tip filtreleme
    filter_type = request.GET.get('type', '')
    if filter_type:
        events = events.filter(event_type=filter_type)
    
    # Yapılacaklar listesi
    todos = TodoItem.objects.filter(user=request.user, is_completed=False).order_by('priority', 'due_date')
    
    # Ek context
    customers = Customer.objects.filter(consultant=request.user)
    properties = Property.objects.filter(is_active=True)
    
    # JSON formatında etkinlik verisi oluştur
    events_json = []
    for event in events:
        color = ""
        if event.event_type == 'gorusme':
            color = "#2dce89"  # Yeşil
        elif event.event_type == 'gosterim':
            color = "#5e72e4"  # Mavi
        elif event.event_type == 'toplanti':
            color = "#fb6340"  # Turuncu
        else:
            color = "#f5365c"  # Kırmızı
        
        events_json.append({
            'id': event.id,
            'title': event.title,
            'start': event.start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'end': event.end_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'color': color,
            'url': reverse('event_detail', args=[event.id]),
            'description': event.description[:50] + '...' if len(event.description) > 50 else event.description,
            'is_completed': event.is_completed
        })
    
    context = {
        'segment': 'ajanda',
        'events': events,
        'events_json': json.dumps(events_json, cls=DjangoJSONEncoder),
        'todos': todos,
        'customers': customers,
        'properties': properties,
        'event_types': Event.EVENT_TYPE_CHOICES,
        'priority_choices': TodoItem.PRIORITY_CHOICES,
        'filter_date': filter_date if isinstance(filter_date, date) else '',
        'filter_type': filter_type,
    }
    
    html_template = loader.get_template('calendar/calendar.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def event_list(request):
    """Etkinlik listesi görünümü"""
    
    # Filtreleme parametreleri
    event_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    
    # Tüm etkinlikleri çek
    if request.user.is_superuser:
        events = Event.objects.all()
    else:
        events = Event.objects.filter(consultant=request.user)
    
    # Filtreleri uygula
    if event_type:
        events = events.filter(event_type=event_type)
    
    if status == 'completed':
        events = events.filter(is_completed=True)
    elif status == 'pending':
        events = events.filter(is_completed=False)
    
    if date_filter == 'today':
        today = timezone.now().date()
        events = events.filter(start_time__date=today)
    elif date_filter == 'tomorrow':
        tomorrow = timezone.now().date() + timedelta(days=1)
        events = events.filter(start_time__date=tomorrow)
    elif date_filter == 'week':
        week_start = timezone.now().date()
        week_end = week_start + timedelta(days=7)
        events = events.filter(start_time__date__gte=week_start, start_time__date__lt=week_end)
    elif date_filter == 'month':
        month_start = timezone.now().date()
        month_end = month_start + timedelta(days=30)
        events = events.filter(start_time__date__gte=month_start, start_time__date__lt=month_end)
    
    context = {
        'segment': 'event_list',
        'events': events,
        'filters': {
            'event_type': event_type,
            'status': status,
            'date': date_filter,
        }
    }
    
    html_template = loader.get_template('calendar/event_list.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def event_create_form(request):
    """Etkinlik oluşturma formu görünümü"""
    
    # Müşteriler ve gayrimenkul listesi
    if request.user.is_superuser:
        customers = Customer.objects.all()
    else:
        customers = Customer.objects.filter(consultant=request.user)
    
    properties = Property.objects.filter(is_active=True)
    
    context = {
        'segment': 'calendar',
        'customers': customers,
        'properties': properties,
        'event_types': Event.EVENT_TYPE_CHOICES,
    }
    
    html_template = loader.get_template('calendar/event_create.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def event_create(request):
    """Etkinlik oluşturma"""
    if request.method == 'POST':
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        event_type = request.POST.get('event_type', '')
        start_date = request.POST.get('start_date', '')
        start_time = request.POST.get('start_time', '')
        end_date = request.POST.get('end_date', '')
        end_time = request.POST.get('end_time', '')
        location = request.POST.get('location', '')
        customer_id = request.POST.get('customer', '')
        property_id = request.POST.get('property', '')
        
        # Validation
        if not title or not event_type or not start_date or not start_time:
            messages.error(request, "Lütfen zorunlu alanları doldurun.")
            return redirect('calendar')
        
        try:
            # Tarih ve saat bilgilerini birleştir
            start_datetime = datetime.strptime(f"{start_date} {start_time}", '%Y-%m-%d %H:%M')
            end_datetime = None
            
            if end_date and end_time:
                end_datetime = datetime.strptime(f"{end_date} {end_time}", '%Y-%m-%d %H:%M')
            else:
                # Eğer bitiş zamanı belirtilmemişse, başlangıç zamanından 1 saat sonra
                end_datetime = start_datetime + timedelta(hours=1)
            
            # Yeni etkinlik oluştur
            event = Event(
                title=title,
                description=description,
                event_type=event_type,
                start_time=start_datetime,
                end_time=end_datetime,
                location=location,
                consultant=request.user,
            )
            
            # İlişkili müşteri ve gayrimenkul ekle
            if customer_id:
                customer = Customer.objects.get(id=customer_id)
                event.customer = customer
            
            if property_id:
                property_obj = Property.objects.get(id=property_id)
                event.property = property_obj
            
            event.save()
            
            messages.success(request, "Etkinlik başarıyla oluşturuldu.")
            return redirect('calendar')
            
        except Exception as e:
            messages.error(request, f"Bir hata oluştu: {str(e)}")
            return redirect('calendar')
    
    # POST değilse form sayfasına yönlendir
    return redirect('event_create_form')

@login_required(login_url="/login/")
def event_detail(request, event_id):
    """Etkinlik detay görünümü"""
    event = get_object_or_404(Event, id=event_id)
    
    # Yetki kontrolü
    if not request.user.is_superuser and event.consultant != request.user:
        messages.error(request, "Bu etkinliği görüntüleme yetkiniz bulunmamaktadır.")
        return redirect('calendar')
    
    # İlişkili etkinlikleri bul (aynı müşteri veya gayrimenkul ile ilgili)
    related_events = []
    if event.customer:
        customer_events = Event.objects.filter(customer=event.customer).exclude(id=event.id)[:5]
        related_events.extend(customer_events)
    
    if event.property:
        property_events = Event.objects.filter(property=event.property).exclude(id=event.id)[:5]
        related_events.extend(property_events)
    
    # Tekrarları kaldır
    related_events = list({e.id: e for e in related_events}.values())
    
    context = {
        'segment': 'calendar',
        'event': event,
        'related_events': related_events[:5],  # En fazla 5 etkinlik göster
    }
    
    html_template = loader.get_template('calendar/event_detail.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def event_delete(request, event_id):
    """Etkinlik silme"""
    event = get_object_or_404(Event, id=event_id)
    
    # Yetki kontrolü
    if not request.user.is_superuser and event.consultant != request.user:
        messages.error(request, "Bu etkinliği silme yetkiniz bulunmamaktadır.")
        return redirect('calendar')
    
    if request.method == 'POST':
        event_title = event.title  # Silme mesajı için başlığı sakla
        event.delete()
        messages.success(request, f'"{event_title}" etkinliği başarıyla silindi.')
        return redirect('event_list')
    
    return redirect('event_detail', event_id=event.id)

@login_required(login_url="/login/")
def todo_create(request):
    """Yapılacak oluşturma"""
    if request.method == 'POST':
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        due_date = request.POST.get('due_date', None)
        priority = request.POST.get('priority', 'orta')
        customer_id = request.POST.get('customer', None)
        property_id = request.POST.get('property', None)
        
        if not title:
            messages.error(request, "Başlık alanı zorunludur.")
            return redirect('calendar')
        
        todo = TodoItem(
            title=title,
            description=description,
            priority=priority,
            user=request.user,
        )
        
        if due_date:
            todo.due_date = due_date
        
        if customer_id:
            todo.customer_id = customer_id
        
        if property_id:
            todo.property_id = property_id
        
        todo.save()
        
        messages.success(request, "Yapılacak başarıyla eklendi.")
    
    return redirect('calendar')

@login_required(login_url="/login/")
def todo_update(request, todo_id):
    """Yapılacak güncelleme"""
    todo = get_object_or_404(TodoItem, id=todo_id)
    
    # Sadece sahibi güncelleyebilir
    if todo.user != request.user:
        messages.error(request, "Bu yapılacağı güncelleme yetkiniz yok.")
        return redirect('calendar')
    
    if request.method == 'POST':
        todo.title = request.POST.get('title', '')
        todo.description = request.POST.get('description', '')
        todo.priority = request.POST.get('priority', 'orta')
        due_date = request.POST.get('due_date', None)
        
        if due_date:
            todo.due_date = due_date
        else:
            todo.due_date = None
        
        # Tamamlandı durumu
        todo.is_completed = 'is_completed' in request.POST
        
        todo.save()
        
        messages.success(request, "Yapılacak başarıyla güncellendi.")
    
    return redirect('calendar')

@login_required(login_url="/login/")
def todo_delete(request, todo_id):
    """Yapılacak silme"""
    todo = get_object_or_404(TodoItem, id=todo_id)
    
    # Sadece sahibi silebilir
    if todo.user != request.user:
        messages.error(request, "Bu yapılacağı silme yetkiniz yok.")
        return redirect('calendar')
    
    todo.delete()
    messages.success(request, "Yapılacak başarıyla silindi.")
    
    return redirect('calendar')

@login_required(login_url="/login/")
def toggle_todo_status(request, todo_id):
    """Yapılacak durumunu güncelleme (AJAX)"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        todo = get_object_or_404(TodoItem, id=todo_id)
        
        # Sadece sahibi güncelleyebilir
        if todo.user != request.user:
            return JsonResponse({'status': 'error', 'message': 'Yetki hatası'}, status=403)
        
        todo.is_completed = not todo.is_completed
        todo.save()
        
        return JsonResponse({
            'status': 'success',
            'is_completed': todo.is_completed
        })
    
    return JsonResponse({'status': 'error', 'message': 'Geçersiz istek'}, status=400)

@login_required(login_url="/login/")
def event_complete(request, event_id):
    """Etkinliği tamamlandı olarak işaretle"""
    event = get_object_or_404(Event, id=event_id)
    
    # Yetki kontrolü
    if not request.user.is_superuser and event.consultant != request.user:
        messages.error(request, "Bu etkinliği güncelleme yetkiniz bulunmamaktadır.")
        return redirect('calendar')
    
    if request.method == 'POST':
        event.is_completed = True
        event.completed_at = timezone.now()
        event.save()
        
        messages.success(request, "Etkinlik tamamlandı olarak işaretlendi.")
        
    return redirect('event_detail', event_id=event.id)

@login_required(login_url="/login/")
def event_reopen(request, event_id):
    """Tamamlanmış etkinliği yeniden aç"""
    event = get_object_or_404(Event, id=event_id)
    
    # Yetki kontrolü
    if not request.user.is_superuser and event.consultant != request.user:
        messages.error(request, "Bu etkinliği güncelleme yetkiniz bulunmamaktadır.")
        return redirect('calendar')
    
    if request.method == 'POST':
        event.is_completed = False
        event.completed_at = None
        event.save()
        
        messages.success(request, "Etkinlik yeniden açıldı.")
        
    return redirect('event_detail', event_id=event.id)

@login_required(login_url="/login/")
def event_update(request, event_id):
    """Etkinlik güncelleme"""
    event = get_object_or_404(Event, id=event_id)
    
    # Yetki kontrolü
    if not request.user.is_superuser and event.consultant != request.user:
        messages.error(request, "Bu etkinliği düzenleme yetkiniz bulunmamaktadır.")
        return redirect('calendar')
    
    if request.method == 'POST':
        # Form verilerini al
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        event_type = request.POST.get('event_type', '')
        start_date = request.POST.get('start_date', '')
        start_time = request.POST.get('start_time', '')
        end_date = request.POST.get('end_date', '')
        end_time = request.POST.get('end_time', '')
        location = request.POST.get('location', '')
        customer_id = request.POST.get('customer', '')
        property_id = request.POST.get('property', '')
        
        # Validation
        if not title or not event_type or not start_date or not start_time:
            messages.error(request, "Lütfen zorunlu alanları doldurun.")
            return redirect('event_update', event_id=event_id)
        
        try:
            # Tarih ve saat bilgilerini birleştir
            start_datetime = datetime.strptime(f"{start_date} {start_time}", '%Y-%m-%d %H:%M')
            
            # Etkinliği güncelle
            event.title = title
            event.description = description
            event.event_type = event_type
            event.start_time = start_datetime
            event.location = location
            event.updated_by = request.user
            
            # Bitiş zamanı
            if end_date and end_time:
                end_datetime = datetime.strptime(f"{end_date} {end_time}", '%Y-%m-%d %H:%M')
                event.end_time = end_datetime
            else:
                event.end_time = None
            
            # İlişkili kayıtları güncelle
            if customer_id:
                event.customer_id = customer_id
            else:
                event.customer = None
                
            if property_id:
                event.property_id = property_id
            else:
                event.property = None
            
            event.save()
            
            messages.success(request, "Etkinlik başarıyla güncellendi.")
            return redirect('event_detail', event_id=event.id)
            
        except Exception as e:
            messages.error(request, f"Bir hata oluştu: {str(e)}")
    
    # Müşteri ve gayrimenkul listelerini çek
    customers = Customer.objects.all()
    properties = Property.objects.filter(is_active=True)
    
    # Etkinliğin datetime alanlarını tarihe ve saate böl
    start_date = event.start_time.strftime('%Y-%m-%d')
    start_time = event.start_time.strftime('%H:%M')
    
    end_date = ''
    end_time = ''
    if event.end_time:
        end_date = event.end_time.strftime('%Y-%m-%d')
        end_time = event.end_time.strftime('%H:%M')
    
    context = {
        'segment': 'calendar',
        'event': event,
        'customers': customers,
        'properties': properties,
        'event_types': Event.EVENT_TYPE_CHOICES,
        'start_date': start_date,
        'start_time': start_time,
        'end_date': end_date,
        'end_time': end_time,
    }
    
    html_template = loader.get_template('calendar/event_update.html')
    return HttpResponse(html_template.render(context, request))
