# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Çalışan Yönetimi Görünümleri
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.urls import reverse
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone

from .models import (
    Position, EmployeeProfile, 
    Permission, ActivityLog
)

User = get_user_model()

def is_admin_or_manager(user):
    """Kullanıcının admin veya müdür olup olmadığını kontrol et"""
    return user.is_superuser or user.groups.filter(name__in=['Yönetici', 'Müdür']).exists()

@login_required(login_url="/login/")
@user_passes_test(is_admin_or_manager, login_url='/')
def employee_list(request):
    """Çalışan listesi görünümü"""
    
    # Sayfa verilerini hazırla
    employees = EmployeeProfile.objects.select_related('user', 'position').all()
    
    # En son aktiviteler
    recent_activities = ActivityLog.objects.select_related('user').order_by('-timestamp')[:5]
    
    # Rol sayıları
    role_counts = {
        'admin': EmployeeProfile.objects.filter(role='admin', is_active=True).count(),
        'manager': EmployeeProfile.objects.filter(role='manager', is_active=True).count(),
        'consultant': EmployeeProfile.objects.filter(role='consultant', is_active=True).count(),
        'secretary': EmployeeProfile.objects.filter(role='secretary', is_active=True).count(),
        'employee': EmployeeProfile.objects.filter(role='employee', is_active=True).count(),
    }
    
    context = {
        'segment': 'employee',
        'employees': employees,
        'activities': recent_activities,
        'role_counts': role_counts,
    }
    
    html_template = loader.get_template('employees/employee_list.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
@user_passes_test(is_admin_or_manager, login_url='/')
def employee_create(request):
    """Yeni çalışan oluşturma"""
    
    if request.method == 'POST':
        # Form verilerini al
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        role = request.POST.get('role')
        password = request.POST.get('password')
        
        # Validasyon
        if not all([first_name, last_name, email, role, password]):
            messages.error(request, "Lütfen zorunlu alanları doldurun.")
            return redirect('employee_create')
        
        # Kullanıcı oluştur
        try:
            # Username için email kullan (@ öncesi)
            username = email.split('@')[0]
            
            # Kullanıcı adı eşsiz olmalı
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Kullanıcı oluştur
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Çalışan profili oluştur
            employee = EmployeeProfile.objects.create(
                user=user,
                phone=phone,
                role=role
            )
            
            # Aktivite logu oluştur
            ActivityLog.objects.create(
                user=request.user,
                action=f"Yeni çalışan eklendi: {user.get_full_name()}",
                details=f"Rol: {employee.get_role_display()}"
            )
            
            messages.success(request, f"{user.get_full_name()} başarıyla eklendi.")
            return redirect('employee_list')
            
        except Exception as e:
            messages.error(request, f"Hata oluştu: {str(e)}")
    
    # Form verilerini hazırla
    context = {
        'segment': 'employee',
        'roles': EmployeeProfile.ROLE_CHOICES,
    }
    
    html_template = loader.get_template('employees/employee_create.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
@user_passes_test(is_admin_or_manager, login_url='/')
def employee_edit(request, employee_id):
    """Çalışan düzenleme"""
    
    employee = get_object_or_404(EmployeeProfile, id=employee_id)
    
    if request.method == 'POST':
        # Form verilerini al
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        role = request.POST.get('role')
        is_active = request.POST.get('is_active') == 'on'
        
        # Validasyon
        if not all([first_name, last_name, email, role]):
            messages.error(request, "Lütfen zorunlu alanları doldurun.")
            return redirect('employee_edit', employee_id=employee_id)
        
        try:
            # Kullanıcı bilgilerini güncelle
            user = employee.user
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()
            
            # Çalışan profilini güncelle
            old_role = employee.role
            employee.phone = phone
            employee.role = role
            employee.is_active = is_active
            
            # İşten ayrılma tarihi kontrolü
            if not is_active and not employee.end_date:
                employee.end_date = timezone.now().date()
            elif is_active and employee.end_date:
                employee.end_date = None
                
            employee.save()
            
            # Rol değiştiyse log oluştur
            if old_role != role:
                ActivityLog.objects.create(
                    user=request.user,
                    action=f"{user.get_full_name()} rolü değiştirildi",
                    details=f"{employee.get_role_display()} olarak güncellendi"
                )
            else:
                ActivityLog.objects.create(
                    user=request.user,
                    action=f"{user.get_full_name()} bilgileri güncellendi",
                    details=""
                )
            
            messages.success(request, "Çalışan bilgileri başarıyla güncellendi.")
            return redirect('employee_list')
            
        except Exception as e:
            messages.error(request, f"Hata oluştu: {str(e)}")
    
    context = {
        'segment': 'employee',
        'employee': employee,
        'roles': EmployeeProfile.ROLE_CHOICES,
    }
    
    html_template = loader.get_template('employees/employee_edit.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
@user_passes_test(is_admin_or_manager, login_url='/')
def manage_permissions(request, employee_id):
    """Çalışan izinlerini yönet"""
    
    employee = get_object_or_404(EmployeeProfile, id=employee_id)
    
    if request.method == 'POST':
        # İzin nesnesi oluştur veya al
        permission, created = Permission.objects.get_or_create(employee=employee)
        
        # İzinleri güncelle
        permission.can_view_customers = 'can_view_customers' in request.POST
        permission.can_add_customers = 'can_add_customers' in request.POST
        permission.can_edit_customers = 'can_edit_customers' in request.POST
        permission.can_delete_customers = 'can_delete_customers' in request.POST
        
        permission.can_view_properties = 'can_view_properties' in request.POST
        permission.can_add_properties = 'can_add_properties' in request.POST
        permission.can_edit_properties = 'can_edit_properties' in request.POST
        
        permission.can_view_calendar = 'can_view_calendar' in request.POST
        permission.can_create_events = 'can_create_events' in request.POST
        permission.can_edit_events = 'can_edit_events' in request.POST
        
        permission.can_view_reports = 'can_view_reports' in request.POST
        permission.can_manage_employees = 'can_manage_employees' in request.POST
        permission.can_manage_settings = 'can_manage_settings' in request.POST
        
        permission.save()
        
        ActivityLog.objects.create(
            user=request.user,
            action=f"{employee.user.get_full_name()} için izinler güncellendi",
            details=""
        )
        
        messages.success(request, "İzinler başarıyla güncellendi.")
        return redirect('employee_list')
    
    # Mevcut izinleri veya varsayılan değerleri getir
    try:
        permissions = employee.custom_permissions
    except:
        permissions = None
    
    context = {
        'segment': 'employee',
        'employee': employee,
        'permissions': permissions,
    }
    
    html_template = loader.get_template('employees/manage_permissions.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def reset_password(request, employee_id):
    """Çalışan şifresini sıfırla"""
    
    # Sadece admin veya kendisi sıfırlayabilir
    employee = get_object_or_404(EmployeeProfile, id=employee_id)
    
    if not (request.user.is_superuser or request.user.groups.filter(name='Yönetici').exists()) and request.user != employee.user:
        messages.error(request, "Bu işlem için yetkiniz bulunmuyor.")
        return redirect('employee_list')
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not new_password or new_password != confirm_password:
            messages.error(request, "Şifreler eşleşmiyor veya boş.")
            return redirect('reset_password', employee_id=employee_id)
        
        # Şifreyi güncelle
        user = employee.user
        user.set_password(new_password)
        user.save()
        
        ActivityLog.objects.create(
            user=request.user,
            action=f"{employee.user.get_full_name()} şifresi sıfırlandı",
            details=""
        )
        
        messages.success(request, "Şifre başarıyla sıfırlandı.")
        return redirect('employee_list')
    
    context = {
        'segment': 'employee',
        'employee': employee,
    }
    
    html_template = loader.get_template('employees/reset_password.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
@user_passes_test(is_admin_or_manager, login_url='/')
def position_list(request):
    """Pozisyon listesi"""
    
    positions = Position.objects.all()
    
    if request.method == 'POST':
        name = request.POST.get('name')
        position_id = request.POST.get('position_id')
        
        if not name:
            messages.error(request, "Pozisyon adı gereklidir.")
            return redirect('position_list')
        
        try:
            if position_id:  # Düzenleme
                position = get_object_or_404(Position, id=position_id)
                position.name = name
                position.save()
                messages.success(request, "Pozisyon başarıyla güncellendi.")
            else:  # Yeni ekleme
                Position.objects.create(name=name)
                messages.success(request, "Pozisyon başarıyla eklendi.")
            
        except Exception as e:
            messages.error(request, f"Bir hata oluştu: {str(e)}")
            
        return redirect('position_list')
    
    context = {
        'segment': 'employee',
        'positions': positions,
    }
    
    html_template = loader.get_template('employees/position_list.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
@user_passes_test(is_admin_or_manager, login_url='/')
def role_list(request):
    """Rol listesi ve yetki şablonları"""
    
    # Rol tabanlı kullanıcı sayıları
    role_stats = {
        'admin': {
            'count': EmployeeProfile.objects.filter(role='admin', is_active=True).count(),
            'title': 'Yönetici',
            'description': 'Tüm yetkilere sahip en üst düzey rol.'
        },
        'manager': {
            'count': EmployeeProfile.objects.filter(role='manager', is_active=True).count(),
            'title': 'Müdür',
            'description': 'Raporlama ve çalışan yönetimi yetkileri.'
        },
        'consultant': {
            'count': EmployeeProfile.objects.filter(role='consultant', is_active=True).count(),
            'title': 'Danışman',
            'description': 'Müşteri ve portföy yönetimi yetkileri.'
        },
        'secretary': {
            'count': EmployeeProfile.objects.filter(role='secretary', is_active=True).count(),
            'title': 'Santral/Sekreter',
            'description': 'Müşteri kaydı ve ajanda yönetimi.'
        },
        'employee': {
            'count': EmployeeProfile.objects.filter(role='employee', is_active=True).count(),
            'title': 'Çalışan',
            'description': 'Temel operasyonel yetkiler.'
        }
    }
    
    context = {
        'segment': 'employee',
        'role_stats': role_stats,
    }
    
    html_template = loader.get_template('employees/role_list.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
@user_passes_test(is_admin_or_manager, login_url='/')
def activity_log(request):
    """Aktivite kayıtları"""
    
    activities = ActivityLog.objects.select_related('user').order_by('-timestamp')
    
    # Filtreleme
    user_id = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if user_id:
        activities = activities.filter(user_id=user_id)
    
    if date_from:
        activities = activities.filter(timestamp__date__gte=date_from)
    
    if date_to:
        activities = activities.filter(timestamp__date__lte=date_to)
    
    users = User.objects.filter(is_active=True)
    
    context = {
        'segment': 'employee',
        'activities': activities,
        'users': users,
        'filter_user': user_id,
        'filter_date_from': date_from,
        'filter_date_to': date_to,
    }
    
    html_template = loader.get_template('employees/activity_log.html')
    return HttpResponse(html_template.render(context, request))
