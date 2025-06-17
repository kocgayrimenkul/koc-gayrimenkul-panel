# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - FSBO (For Sale By Owner) Görünümleri
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.urls import reverse
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta, date
from .models import FSBO, FSBOLog
from .forms import FSBOForm, FSBOSearchForm
from apps.employees.models import EmployeeProfile
from django.db import connection
from apps.employees.decorators import (
    can_view_fsbo,
    can_add_fsbo,
    can_edit_fsbo,
    can_delete_fsbo,
    require_fsbo_permission
)

def get_user_role(user):
    """Kullanıcının rolünü döndürür"""
    # Superuser ise admin rolünü döndür
    if user.is_superuser:
        return 'admin'  # Superuser her zaman admin yetkilerine sahip olacak
    
    try:
        return user.employee_profile.role
    except (EmployeeProfile.DoesNotExist, AttributeError):
        return None

@login_required(login_url="/login/")
@can_view_fsbo
def fsbo_list(request):
    """FSBO listesi görünümü"""
    
    role = get_user_role(request.user)
    
    # Debug: Mevcut tüm FSBO ID'lerini listele
    all_fsbo_ids = list(FSBO.objects.values_list('id', flat=True))
    print(f"Mevcut FSBO kayıtları: {all_fsbo_ids}")
    
    # Arama formu
    form = FSBOSearchForm(request.GET or None)
    
    # Varsayılan filtreleme - son 30 günlük kayıtlar
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    
    # Yetkiye göre FSBO kayıtlarını getir
    if request.user.is_superuser:
        # Superuser tüm kayıtları görebilir, zaman sınırı olmadan
        fsbo_records = FSBO.objects.all()
    elif role in ['admin', 'manager', 'secretary']:
        # Yönetici, Müdür ve Santral son 30 günlük kayıtları görebilir
        fsbo_records = FSBO.objects.filter(created_at__date__gte=thirty_days_ago)
    elif role == 'consultant':
        # Danışman sadece kendisine yönlendirilen kayıtları görebilir
        fsbo_records = FSBO.objects.filter(
            Q(consultant=request.user) | Q(created_by=request.user),
            created_at__date__gte=thirty_days_ago
        )
    else:
        # Diğer roller veya rolü olmayanlar sadece görüntüleyebilir ama işlem yapamaz
        fsbo_records = FSBO.objects.filter(created_at__date__gte=thirty_days_ago)
        if role != 'employee' and role is not None:
            messages.warning(request, "Sınırlı erişim modu: Sadece görüntüleme yapabilirsiniz.")
    
    # Form geçerliyse filtreleme yap
    if form.is_valid():
        # Telefon numarası filtreleme
        phone = form.cleaned_data.get('phone')
        if phone:
            fsbo_records = fsbo_records.filter(phone__icontains=phone)
        
        # Tarih aralığı filtreleme
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        
        if start_date:
            fsbo_records = fsbo_records.filter(created_at__date__gte=start_date)
        if end_date:
            # Son günü de dahil etmek için
            end_date = end_date + timedelta(days=1)
            fsbo_records = fsbo_records.filter(created_at__date__lt=end_date)
        
        # Sonuç filtreleme
        result = form.cleaned_data.get('result')
        if result:
            fsbo_records = fsbo_records.filter(result=result)
        
        # Danışman filtreleme (sadece yönetici ve müdür için)
        consultant = form.cleaned_data.get('consultant')
        if consultant and (request.user.is_superuser or role in ['admin', 'manager']):
            fsbo_records = fsbo_records.filter(consultant=consultant)
    
    # İstatistikler
    total_count = fsbo_records.count()
    positive_count = fsbo_records.filter(result='olumlu').count()
    negative_count = fsbo_records.filter(result='olumsuz').count()
    waiting_count = fsbo_records.filter(result='bekliyor').count()
    not_called_count = fsbo_records.filter(result='aranmadi').count()
    
    # İstatistik yüzdeleri
    if total_count > 0:
        positive_percent = int((positive_count / total_count) * 100)
        negative_percent = int((negative_count / total_count) * 100)
        waiting_percent = int((waiting_count / total_count) * 100)
        not_called_percent = int((not_called_count / total_count) * 100)
    else:
        positive_percent = negative_percent = waiting_percent = not_called_percent = 0
    
    context = {
        'segment': 'fsbo',
        'fsbo_records': fsbo_records,
        'form': form,
        'user_role': role,
        'total_count': total_count,
        'positive_count': positive_count,
        'negative_count': negative_count,
        'waiting_count': waiting_count,
        'not_called_count': not_called_count,
        'positive_percent': positive_percent,
        'negative_percent': negative_percent,
        'waiting_percent': waiting_percent,
        'not_called_percent': not_called_percent,
    }
    
    html_template = loader.get_template('fsbo/fsbo_list.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
@can_add_fsbo
def fsbo_create(request):
    """Yeni FSBO kaydı oluşturma"""
    
    role = get_user_role(request.user)
    
    # Rol kontrolü - Superuser her zaman oluşturabilir
    if not request.user.is_superuser and role not in ['admin', 'manager', 'secretary', 'consultant']:
        messages.error(request, "FSBO kaydı oluşturma yetkiniz bulunmamaktadır.")
        return redirect('fsbo_list')
    
    if request.method == 'POST':
        form = FSBOForm(request.POST)
        if form.is_valid():
            fsbo = form.save(commit=False)
            fsbo.created_by = request.user
            fsbo.save()
            
            # Log ekle
            FSBOLog.objects.create(
                fsbo=fsbo,
                user=request.user,
                action="Yeni kayıt oluşturuldu",
                details=f"Sonuç: {fsbo.get_result_display()}"
            )
            
            messages.success(request, "FSBO kaydı başarıyla oluşturuldu.")
            return redirect('fsbo_list')
    else:
        form = FSBOForm()
    
    context = {
        'segment': 'fsbo',
        'form': form,
        'user_role': role,
    }
    
    html_template = loader.get_template('fsbo/fsbo_create.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
@can_edit_fsbo
def fsbo_edit(request, fsbo_id):
    """FSBO kaydı düzenleme"""
    
    role = get_user_role(request.user)
    fsbo = get_object_or_404(FSBO, id=fsbo_id)
    
    # Superuser her zaman düzenleyebilir
    if not request.user.is_superuser:
        if role not in ['admin', 'manager']:
            if role == 'secretary' and fsbo.created_by != request.user:
                messages.error(request, "Bu FSBO kaydını düzenleme yetkiniz bulunmamaktadır.")
                return redirect('fsbo_list')
            elif role == 'consultant' and fsbo.consultant != request.user and fsbo.created_by != request.user:
                messages.error(request, "Bu FSBO kaydını düzenleme yetkiniz bulunmamaktadır.")
                return redirect('fsbo_list')
    
    if request.method == 'POST':
        # Önceki değerleri kaydet
        previous_result = fsbo.result
        previous_consultant = fsbo.consultant
        
        form = FSBOForm(request.POST, instance=fsbo)
        if form.is_valid():
            updated_fsbo = form.save()
            
            # Değişiklik logunu ekle
            changes = []
            if previous_result != updated_fsbo.result:
                changes.append(f"Sonuç: {previous_result} -> {updated_fsbo.result}")
            if previous_consultant != updated_fsbo.consultant:
                changes.append(f"Danışman değişikliği")
            
            log_details = ", ".join(changes) if changes else "Bilgiler güncellendi"
            
            FSBOLog.objects.create(
                fsbo=updated_fsbo,
                user=request.user,
                action="Kayıt güncellendi",
                details=log_details
            )
            
            messages.success(request, "FSBO kaydı başarıyla güncellendi.")
            return redirect('fsbo_list')
    else:
        form = FSBOForm(instance=fsbo)
    
    # İşlem günlüğünü al
    logs = FSBOLog.objects.filter(fsbo=fsbo).order_by('-timestamp')
    
    context = {
        'segment': 'fsbo',
        'form': form,
        'fsbo': fsbo,
        'logs': logs,
        'user_role': role,
    }
    
    html_template = loader.get_template('fsbo/fsbo_edit.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
@can_view_fsbo
def fsbo_detail(request, fsbo_id):
    """FSBO kaydı detay görünümü"""
    
    role = get_user_role(request.user)
    fsbo = get_object_or_404(FSBO, id=fsbo_id)
    
    # Yetki kontrolü - Superuser her zaman erişebilir
    if not request.user.is_superuser:
        if role not in ['admin', 'manager', 'secretary']:
            if role == 'consultant' and fsbo.consultant != request.user and fsbo.created_by != request.user:
                messages.error(request, "Bu FSBO kaydını görüntüleme yetkiniz bulunmamaktadır.")
                return redirect('fsbo_list')
    
    # İşlem günlüğünü al
    logs = FSBOLog.objects.filter(fsbo=fsbo).order_by('-timestamp')
    
    context = {
        'segment': 'fsbo',
        'fsbo': fsbo,
        'logs': logs,
        'user_role': role,
    }
    
    html_template = loader.get_template('fsbo/fsbo_detail.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
@can_delete_fsbo
def fsbo_delete(request, fsbo_id):
    """FSBO kaydı silme"""
    
    # Silme başlamadan önce tüm FSBO ID'lerini kontrol et
    all_fsbo_ids = list(FSBO.objects.values_list('id', flat=True))
    print(f"Silme öncesi mevcut FSBO kayıtları: {all_fsbo_ids}")
    
    # Yetki kontrolü
    if not request.user.is_superuser:
        role = get_user_role(request.user)
        if role not in ['admin', 'manager']:
            messages.error(request, "FSBO kayıtlarını silme yetkiniz bulunmamaktadır.")
            return redirect('fsbo_list')
    
    try:
        # Silinecek kaydı bul
        fsbo = FSBO.objects.get(id=fsbo_id)
        fsbo_name = fsbo.full_name
        
        print(f"Silinecek FSBO: ID={fsbo_id}, Ad={fsbo_name}, Sonuç={fsbo.result}")
        
        if request.method == 'POST':
            # Doğrudan SQL ile bağlantılı kayıtları ve ana kaydı silme
            with connection.cursor() as cursor:
                # İlk olarak bağlı log kayıtlarını sil
                cursor.execute("DELETE FROM fsbo_fsbolog WHERE fsbo_id = %s", [fsbo_id])
                affected_logs = cursor.rowcount
                print(f"Silinen log kayıtları: {affected_logs}")
                
                # Ana FSBO kaydını sil
                cursor.execute("DELETE FROM fsbo_fsbo WHERE id = %s", [fsbo_id])
                affected_rows = cursor.rowcount
                print(f"Silinen FSBO kayıtları: {affected_rows}")
                
                if affected_rows > 0:
                    print(f"FSBO başarıyla SQL ile silindi: {fsbo_name}")
                    messages.success(request, f"{fsbo_name} adlı FSBO kaydı başarıyla silindi.")
                else:
                    print(f"UYARI: FSBO SQL ile silinemedi: ID={fsbo_id}")
                    messages.error(request, f"{fsbo_name} kaydı silinemedi. Lütfen sistem yöneticisiyle iletişime geçin.")
            
            # Silme sonrası tüm kayıtları kontrol et
            connection.close()  # Bağlantıyı kapat ve yeniden aç
            remaining_fsbo_ids = list(FSBO.objects.values_list('id', flat=True))
            print(f"Kalan FSBO kayıtları: {remaining_fsbo_ids}")
            
            # Sayfayı tarayıcı önbelleğini temizleyerek yeniden yükle
            response = redirect('fsbo_list')
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response
        
        return redirect('fsbo_list')
    except FSBO.DoesNotExist:
        print(f"FSBO bulunamadı: ID={fsbo_id}")
        messages.error(request, f"ID: {fsbo_id} olan FSBO kaydı bulunamadı.")
        return redirect('fsbo_list')
    except Exception as e:
        print(f"FSBO silme hatası: {str(e)}")
        messages.error(request, f"Silme işlemi sırasında bir hata oluştu: {str(e)}")
        return redirect('fsbo_list')

@login_required(login_url="/login/")
def fsbo_search(request):
    """AJAX ile FSBO arama"""
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        phone = request.GET.get('phone', '')
        
        role = get_user_role(request.user)
        
        if not phone:
            return JsonResponse({'error': 'Telefon numarası gerekli.'}, status=400)
        
        # Rol kontrolü - Superuser her zaman erişebilir
        if request.user.is_superuser or role in ['admin', 'manager', 'secretary']:
            results = FSBO.objects.filter(phone__icontains=phone)[:10]
        elif role == 'consultant':
            results = FSBO.objects.filter(
                Q(consultant=request.user) | Q(created_by=request.user),
                phone__icontains=phone
            )[:10]
        else:
            return JsonResponse({'error': 'Yetki hatası'}, status=403)
        
        data = [{
            'id': record.id,
            'full_name': record.full_name,
            'phone': record.phone,
            'result': record.get_result_display(),
            'created_at': record.created_at.strftime('%d.%m.%Y')
        } for record in results]
        
        return JsonResponse({'results': data})
    
    return JsonResponse({'error': 'Geçersiz istek'}, status=400)

@login_required(login_url="/login/")
def fsbo_reminders_today(request):
    """Bugünkü FSBO hatırlatıcıları"""
    
    role = get_user_role(request.user)
    
    # Rolü olmayan kullanıcılar için hata - Superuser her zaman erişebilir
    if not request.user.is_superuser and not role:
        messages.error(request, "Bu sayfaya erişim yetkiniz bulunmamaktadır.")
        return redirect('home')
    
    today = timezone.now().date()
    
    # Kullanıcı rolüne göre filtreleme
    if request.user.is_superuser or role in ['admin', 'manager', 'secretary']:
        reminders = FSBO.objects.filter(
            reminder_status='acik',
            reminder_date=today
        ).order_by('reminder_time')
    elif role == 'consultant':
        reminders = FSBO.objects.filter(
            Q(consultant=request.user) | Q(created_by=request.user),
            reminder_status='acik',
            reminder_date=today
        ).order_by('reminder_time')
    else:
        messages.error(request, "Bu sayfaya erişim yetkiniz bulunmamaktadır.")
        return redirect('home')
    
    # İstatistikleri hesapla
    waiting_count = reminders.filter(result='bekliyor').count()
    positive_count = reminders.filter(result='olumlu').count()
    negative_count = reminders.filter(result='olumsuz').count()
    
    context = {
        'segment': 'fsbo_hatirlatici',
        'reminders': reminders,
        'today': today,
        'user_role': role,
        'waiting_count': waiting_count,
        'positive_count': positive_count,
        'negative_count': negative_count,
    }
    
    html_template = loader.get_template('fsbo/fsbo_reminders.html')
    return HttpResponse(html_template.render(context, request))
