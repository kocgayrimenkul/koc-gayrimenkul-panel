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
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import (
    Position, EmployeeProfile, 
    Permission, ActivityLog
)
from .serializers import EmployeeProfileSerializer, ExtensionUpdateSerializer

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
        'roles': EmployeeProfile.ROLE_CHOICES,
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
        extension_number = request.POST.get('extension_number', '')
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
            
            # Extension number validasyonu
            if extension_number:
                extension_number = int(extension_number) if extension_number.isdigit() else None
                if extension_number and (extension_number < 101 or extension_number > 999):
                    messages.error(request, "Dahili numara 101-999 arasında olmalıdır.")
                    return redirect('employee_create')
                
                # Extension number benzersizlik kontrolü
                if extension_number and EmployeeProfile.objects.filter(extension_number=extension_number).exists():
                    messages.error(request, f"Dahili numara {extension_number} zaten kullanılıyor.")
                    return redirect('employee_create')
            else:
                extension_number = None
            
            # Çalışan profili oluştur
            employee = EmployeeProfile.objects.create(
                user=user,
                phone=phone,
                extension_number=extension_number,
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
    
    # Durum değiştirme (toggle) işlemi
    if request.GET.get('toggle_status') == 'true':
        old_status = employee.is_active
        employee.is_active = not employee.is_active
        
        # Eğer deaktif ediyorsak, kullanıcıyı da deaktif et
        if not employee.is_active:
            employee.user.is_active = False
        else:
            employee.user.is_active = True
        
        employee.save()
        employee.user.save()
        
        # Aktivite logu oluştur
        status_text = "aktif" if employee.is_active else "pasif"
        ActivityLog.objects.create(
            user=request.user,
            action=f"{employee.user.get_full_name()} durumu {status_text} olarak değiştirildi",
            details=f"Önceki durum: {'aktif' if old_status else 'pasif'}"
        )
        
        status_msg = "aktif edildi" if employee.is_active else "deaktif edildi"
        messages.success(request, f"{employee.user.get_full_name()} başarıyla {status_msg}.")
        return redirect('employee_list')
    
    if request.method == 'POST':
        # Form verilerini al
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        extension_number = request.POST.get('extension_number', '')
        role = request.POST.get('role')
        is_active = request.POST.get('is_active') == 'on'
        
        # Validasyon
        if not all([first_name, last_name, email, role]):
            messages.error(request, "Lütfen zorunlu alanları doldurun.")
            return redirect('employee_edit', employee_id=employee_id)
        
        try:
            # Extension number validasyonu
            if extension_number:
                extension_number = int(extension_number) if extension_number.isdigit() else None
                if extension_number and (extension_number < 101 or extension_number > 999):
                    messages.error(request, "Dahili numara 101-999 arasında olmalıdır.")
                    return redirect('employee_edit', employee_id=employee_id)
                
                # Extension number benzersizlik kontrolü (mevcut çalışan hariç)
                if extension_number and EmployeeProfile.objects.filter(extension_number=extension_number).exclude(id=employee.id).exists():
                    messages.error(request, f"Dahili numara {extension_number} zaten kullanılıyor.")
                    return redirect('employee_edit', employee_id=employee_id)
            else:
                extension_number = None
            
            # Kullanıcı bilgilerini güncelle
            user = employee.user
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            
            # Eğer çalışan deaktif ediliyorsa, kullanıcıyı da deaktif et
            if not is_active:
                user.is_active = False
            else:
                user.is_active = True
            
            user.save()
            
            # Çalışan profilini güncelle
            old_role = employee.role
            old_active_status = employee.is_active
            old_extension = employee.extension_number
            
            employee.phone = phone
            employee.extension_number = extension_number
            employee.role = role
            employee.is_active = is_active
            
            employee.save()
            
            # Aktivite logları oluştur
            changes = []
            if old_role != role:
                changes.append(f"Rol değiştirildi: {dict(EmployeeProfile.ROLE_CHOICES)[old_role]} → {dict(EmployeeProfile.ROLE_CHOICES)[role]}")
                
            if old_active_status != is_active:
                changes.append(f"Durum değiştirildi: {'aktif' if old_active_status else 'pasif'} → {'aktif' if is_active else 'pasif'}")
            
            if old_extension != extension_number:
                old_ext_text = str(old_extension) if old_extension else 'Yok'
                new_ext_text = str(extension_number) if extension_number else 'Yok'
                changes.append(f"Dahili numara değiştirildi: {old_ext_text} → {new_ext_text}")
            
            if changes:
                ActivityLog.objects.create(
                    user=request.user,
                    action=f"{user.get_full_name()} bilgileri güncellendi",
                    details=", ".join(changes)
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
        
        # Müşteri Yönetimi İzinleri
        permission.can_view_customers = 'can_view_customers' in request.POST
        permission.can_add_customers = 'can_add_customers' in request.POST
        permission.can_edit_customers = 'can_edit_customers' in request.POST
        permission.can_delete_customers = 'can_delete_customers' in request.POST
        
        # Portföy Yönetimi İzinleri
        permission.can_view_portfolio = 'can_view_portfolio' in request.POST
        permission.can_add_portfolio = 'can_add_portfolio' in request.POST
        permission.can_edit_portfolio = 'can_edit_portfolio' in request.POST
        permission.can_delete_portfolio = 'can_delete_portfolio' in request.POST
        
        # Takvim İzinleri
        permission.can_view_calendar = 'can_view_calendar' in request.POST
        permission.can_add_calendar = 'can_add_calendar' in request.POST
        permission.can_edit_calendar = 'can_edit_calendar' in request.POST
        permission.can_delete_calendar = 'can_delete_calendar' in request.POST
        
        # FSBO İzinleri
        permission.can_view_fsbo = 'can_view_fsbo' in request.POST
        permission.can_add_fsbo = 'can_add_fsbo' in request.POST
        permission.can_edit_fsbo = 'can_edit_fsbo' in request.POST
        permission.can_delete_fsbo = 'can_delete_fsbo' in request.POST
        
        # Prezentasyon İzinleri
        permission.can_view_presentation = 'can_view_presentation' in request.POST
        permission.can_add_presentation = 'can_add_presentation' in request.POST
        permission.can_edit_presentation = 'can_edit_presentation' in request.POST
        permission.can_delete_presentation = 'can_delete_presentation' in request.POST
        
        # Kariyer İzinleri
        permission.can_view_careers = 'can_view_careers' in request.POST
        permission.can_add_careers = 'can_add_careers' in request.POST
        permission.can_edit_careers = 'can_edit_careers' in request.POST
        permission.can_delete_careers = 'can_delete_careers' in request.POST
        
        # Çalışan Yönetimi İzinleri
        permission.can_view_employees = 'can_view_employees' in request.POST
        permission.can_add_employees = 'can_add_employees' in request.POST
        permission.can_edit_employees = 'can_edit_employees' in request.POST
        permission.can_delete_employees = 'can_delete_employees' in request.POST
        
        # Sistem İzinleri
        permission.can_view_reports = 'can_view_reports' in request.POST
        permission.can_manage_settings = 'can_manage_settings' in request.POST
        permission.can_access_api = 'can_access_api' in request.POST
        
        permission.save()
        
        ActivityLog.objects.create(
            user=request.user,
            action=f"{employee.user.get_full_name()} için izinler güncellendi",
            details=permission.permissions_summary
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

@login_required(login_url="/login/")
@user_passes_test(is_admin_or_manager, login_url='/')
def employee_delete(request, employee_id):
    """Çalışan silme (Sadece süper admin)"""

    if not request.user.is_superuser:
        messages.error(request, "Bu işlem için yetkiniz bulunmuyor.")
        return redirect('employee_list')

    try:
        employee = EmployeeProfile.objects.get(id=employee_id)
    except EmployeeProfile.DoesNotExist:
        messages.error(request, "Çalışan bulunamadı veya zaten silinmiş.")
        return redirect('employee_list')
    
    if request.method == 'POST':
        user_name = employee.user.get_full_name()
        user = employee.user
        
        # Önce profili sil, sonra kullanıcıyı
        employee.delete()
        user.delete()
        
        ActivityLog.objects.create(
            user=request.user,
            action=f"Çalışan silindi: {user_name}",
            details="Kullanıcı tamamen sistemden kaldırıldı"
        )
        
        messages.success(request, f"{user_name} sistemden tamamen kaldırıldı.")
        return redirect('employee_list')
    
    context = {
        'segment': 'employee',
        'employee': employee,
    }
    
    html_template = loader.get_template('employees/employee_delete.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
@user_passes_test(is_admin_or_manager, login_url='/')
def revoke_all_permissions(request, employee_id):
    """Çalışanın tüm özel yetkilerini kaldır"""
    
    employee = get_object_or_404(EmployeeProfile, id=employee_id)
    
    if request.method == 'POST':
        # Özel izinleri sıfırla
        permission, created = Permission.objects.get_or_create(employee=employee)
        
        # Tüm izinleri False yap
        permission.can_view_customers = False
        permission.can_add_customers = False
        permission.can_edit_customers = False
        permission.can_delete_customers = False
        permission.can_view_portfolio = False
        permission.can_add_portfolio = False
        permission.can_edit_portfolio = False
        permission.can_delete_portfolio = False
        permission.can_view_calendar = False
        permission.can_add_calendar = False
        permission.can_edit_calendar = False
        permission.can_delete_calendar = False
        permission.can_view_fsbo = False
        permission.can_add_fsbo = False
        permission.can_edit_fsbo = False
        permission.can_delete_fsbo = False
        permission.can_view_presentation = False
        permission.can_add_presentation = False
        permission.can_edit_presentation = False
        permission.can_delete_presentation = False
        permission.can_view_careers = False
        permission.can_add_careers = False
        permission.can_edit_careers = False
        permission.can_delete_careers = False
        permission.can_view_employees = False
        permission.can_add_employees = False
        permission.can_edit_employees = False
        permission.can_delete_employees = False
        permission.can_view_reports = False
        permission.can_manage_settings = False
        permission.can_access_api = False
        
        permission.save()
        
        # Kullanıcıyı tüm gruplardan çıkar
        employee.user.groups.clear()
        
        # Rolü en alt seviyeye indir
        employee.role = 'employee'
        employee.save()
        
        ActivityLog.objects.create(
            user=request.user,
            action=f"{employee.user.get_full_name()} tüm yetkileri kaldırıldı",
            details="Özel izinler sıfırlandı, gruplardan çıkarıldı, rol 'çalışan' olarak ayarlandı"
        )
        
        messages.success(request, f"{employee.user.get_full_name()} adlı çalışanın tüm yetkileri kaldırıldı.")
        return redirect('employee_list')
    
    context = {
        'segment': 'employee',
        'employee': employee,
    }
    
    return JsonResponse({'success': True, 'message': 'Yetkiler kaldırıldı'})

@login_required(login_url="/login/")
@user_passes_test(is_admin_or_manager, login_url='/')
def bulk_employee_actions(request):
    """Toplu çalışan işlemleri"""
    
    if request.method == 'POST':
        action = request.POST.get('action')
        employee_ids = request.POST.getlist('employee_ids')
        
        if not employee_ids:
            return JsonResponse({'success': False, 'message': 'Hiç çalışan seçilmedi'})
        
        employees = EmployeeProfile.objects.filter(id__in=employee_ids)
        
        if action == 'activate':
            # Toplu aktifleştirme
            for employee in employees:
                employee.is_active = True
                employee.user.is_active = True
                employee.save()
                employee.user.save()
            
            ActivityLog.objects.create(
                user=request.user,
                action=f"{len(employees)} çalışan toplu olarak aktifleştirildi",
                details=f"Aktifleştirilen çalışanlar: {', '.join([emp.user.get_full_name() for emp in employees])}"
            )
            
            messages.success(request, f"{len(employees)} çalışan başarıyla aktifleştirildi.")
            
        elif action == 'deactivate':
            # Toplu deaktifleştirme
            for employee in employees:
                employee.is_active = False
                employee.user.is_active = False
                employee.save()
                employee.user.save()
            
            ActivityLog.objects.create(
                user=request.user,
                action=f"{len(employees)} çalışan toplu olarak deaktifleştirildi",
                details=f"Deaktifleştirilen çalışanlar: {', '.join([emp.user.get_full_name() for emp in employees])}"
            )
            
            messages.success(request, f"{len(employees)} çalışan başarıyla deaktifleştirildi.")
            
        elif action == 'revoke_permissions':
            # Toplu yetki kaldırma
            for employee in employees:
                permission, created = Permission.objects.get_or_create(employee=employee)
                
                # Tüm izinleri False yap
                permission.can_view_customers = False
                permission.can_add_customers = False
                permission.can_edit_customers = False
                permission.can_delete_customers = False
                permission.can_view_portfolio = False
                permission.can_add_portfolio = False
                permission.can_edit_portfolio = False
                permission.can_delete_portfolio = False
                permission.can_view_calendar = False
                permission.can_add_calendar = False
                permission.can_edit_calendar = False
                permission.can_delete_calendar = False
                permission.can_view_fsbo = False
                permission.can_add_fsbo = False
                permission.can_edit_fsbo = False
                permission.can_delete_fsbo = False
                permission.can_view_presentation = False
                permission.can_add_presentation = False
                permission.can_edit_presentation = False
                permission.can_delete_presentation = False
                permission.can_view_careers = False
                permission.can_add_careers = False
                permission.can_edit_careers = False
                permission.can_delete_careers = False
                permission.can_view_employees = False
                permission.can_add_employees = False
                permission.can_edit_employees = False
                permission.can_delete_employees = False
                permission.can_view_reports = False
                permission.can_manage_settings = False
                permission.can_access_api = False
                
                permission.save()
                
                # Kullanıcıyı tüm gruplardan çıkar
                employee.user.groups.clear()
            
            ActivityLog.objects.create(
                user=request.user,
                action=f"{len(employees)} çalışanın yetkileri toplu olarak kaldırıldı",
                details=f"Yetkileri kaldırılan çalışanlar: {', '.join([emp.user.get_full_name() for emp in employees])}"
            )
            
            messages.success(request, f"{len(employees)} çalışanın yetkileri başarıyla kaldırıldı.")
            
        elif action == 'change_role':
            # Toplu rol değişikliği
            new_role = request.POST.get('new_role')
            if new_role in dict(EmployeeProfile.ROLE_CHOICES):
                for employee in employees:
                    old_role = employee.role
                    employee.role = new_role
                    employee.save()
                
                ActivityLog.objects.create(
                    user=request.user,
                    action=f"{len(employees)} çalışanın rolü toplu olarak değiştirildi",
                    details=f"Yeni rol: {dict(EmployeeProfile.ROLE_CHOICES)[new_role]}, Çalışanlar: {', '.join([emp.user.get_full_name() for emp in employees])}"
                )
                
                messages.success(request, f"{len(employees)} çalışanın rolü '{dict(EmployeeProfile.ROLE_CHOICES)[new_role]}' olarak değiştirildi.")
            else:
                messages.error(request, "Geçersiz rol seçimi.")
                
        return redirect('employee_list')
    
    return JsonResponse({'success': False, 'message': 'Geçersiz istek'})

@login_required(login_url="/login/")
@user_passes_test(is_admin_or_manager, login_url='/')
def employee_permissions_reset(request, employee_id):
    """Çalışan izinlerini varsayılana sıfırla"""
    
    employee = get_object_or_404(EmployeeProfile, id=employee_id)
    
    if request.method == 'POST':
        # İzin nesnesini al veya oluştur
        permission, created = Permission.objects.get_or_create(employee=employee)
        
        # Varsayılan izinleri role göre ayarla
        if employee.role == 'admin':
            # Yönetici - Tüm izinler
            permission.can_view_customers = True
            permission.can_add_customers = True
            permission.can_edit_customers = True
            permission.can_delete_customers = True
            permission.can_view_portfolio = True
            permission.can_add_portfolio = True
            permission.can_edit_portfolio = True
            permission.can_delete_portfolio = True
            permission.can_view_calendar = True
            permission.can_add_calendar = True
            permission.can_edit_calendar = True
            permission.can_delete_calendar = True
            permission.can_view_fsbo = True
            permission.can_add_fsbo = True
            permission.can_edit_fsbo = True
            permission.can_delete_fsbo = True
            permission.can_view_presentation = True
            permission.can_add_presentation = True
            permission.can_edit_presentation = True
            permission.can_delete_presentation = True
            permission.can_view_careers = True
            permission.can_add_careers = True
            permission.can_edit_careers = True
            permission.can_delete_careers = True
            permission.can_view_employees = True
            permission.can_add_employees = True
            permission.can_edit_employees = True
            permission.can_delete_employees = True
            permission.can_view_reports = True
            permission.can_manage_settings = True
            permission.can_access_api = True
            
        elif employee.role == 'manager':
            # Müdür - Kısıtlı yönetici izinleri
            permission.can_view_customers = True
            permission.can_add_customers = True
            permission.can_edit_customers = True
            permission.can_delete_customers = False
            permission.can_view_portfolio = True
            permission.can_add_portfolio = True
            permission.can_edit_portfolio = True
            permission.can_delete_portfolio = False
            permission.can_view_calendar = True
            permission.can_add_calendar = True
            permission.can_edit_calendar = True
            permission.can_delete_calendar = True
            permission.can_view_fsbo = True
            permission.can_add_fsbo = True
            permission.can_edit_fsbo = True
            permission.can_delete_fsbo = False
            permission.can_view_presentation = True
            permission.can_add_presentation = True
            permission.can_edit_presentation = True
            permission.can_delete_presentation = False
            permission.can_view_careers = True
            permission.can_add_careers = True
            permission.can_edit_careers = True
            permission.can_delete_careers = False
            permission.can_view_employees = True
            permission.can_add_employees = False
            permission.can_edit_employees = False
            permission.can_delete_employees = False
            permission.can_view_reports = True
            permission.can_manage_settings = False
            permission.can_access_api = False
            
        elif employee.role == 'consultant':
            # Danışman - Müşteri ve portföy odaklı
            permission.can_view_customers = True
            permission.can_add_customers = True
            permission.can_edit_customers = True
            permission.can_delete_customers = False
            permission.can_view_portfolio = True
            permission.can_add_portfolio = True
            permission.can_edit_portfolio = False
            permission.can_delete_portfolio = False
            permission.can_view_calendar = True
            permission.can_add_calendar = True
            permission.can_edit_calendar = False
            permission.can_delete_calendar = False
            permission.can_view_fsbo = True
            permission.can_add_fsbo = True
            permission.can_edit_fsbo = False
            permission.can_delete_fsbo = False
            permission.can_view_presentation = True
            permission.can_add_presentation = True
            permission.can_edit_presentation = True
            permission.can_delete_presentation = False
            permission.can_view_careers = True
            permission.can_add_careers = False
            permission.can_edit_careers = False
            permission.can_delete_careers = False
            permission.can_view_employees = False
            permission.can_add_employees = False
            permission.can_edit_employees = False
            permission.can_delete_employees = False
            permission.can_view_reports = False
            permission.can_manage_settings = False
            permission.can_access_api = False
            
        elif employee.role == 'secretary':
            # Santral - Müşteri ve takvim odaklı
            permission.can_view_customers = True
            permission.can_add_customers = True
            permission.can_edit_customers = True
            permission.can_delete_customers = False
            permission.can_view_portfolio = True
            permission.can_add_portfolio = False
            permission.can_edit_portfolio = False
            permission.can_delete_portfolio = False
            permission.can_view_calendar = True
            permission.can_add_calendar = True
            permission.can_edit_calendar = True
            permission.can_delete_calendar = False
            permission.can_view_fsbo = True
            permission.can_add_fsbo = False
            permission.can_edit_fsbo = False
            permission.can_delete_fsbo = False
            permission.can_view_presentation = True
            permission.can_add_presentation = True  # True olarak değiştirildi
            permission.can_edit_presentation = True  # True olarak değiştirildi
            permission.can_delete_presentation = False
            permission.can_view_careers = True
            permission.can_add_careers = False
            permission.can_edit_careers = False
            permission.can_delete_careers = False
            permission.can_view_employees = False
            permission.can_add_employees = False
            permission.can_edit_employees = False
            permission.can_delete_employees = False
            permission.can_view_reports = False
            permission.can_manage_settings = False
            permission.can_access_api = False
            
        else:  # employee
            # Çalışan - Temel izinler
            permission.can_view_customers = True
            permission.can_add_customers = False
            permission.can_edit_customers = False
            permission.can_delete_customers = False
            permission.can_view_portfolio = True
            permission.can_add_portfolio = False
            permission.can_edit_portfolio = False
            permission.can_delete_portfolio = False
            permission.can_view_calendar = True
            permission.can_add_calendar = False
            permission.can_edit_calendar = False
            permission.can_delete_calendar = False
            permission.can_view_fsbo = True
            permission.can_add_fsbo = False
            permission.can_edit_fsbo = False
            permission.can_delete_fsbo = False
            permission.can_view_presentation = True
            permission.can_add_presentation = False
            permission.can_edit_presentation = False
            permission.can_delete_presentation = False
            permission.can_view_careers = True
            permission.can_add_careers = False
            permission.can_edit_careers = False
            permission.can_delete_careers = False
            permission.can_view_employees = False
            permission.can_add_employees = False
            permission.can_edit_employees = False
            permission.can_delete_employees = False
            permission.can_view_reports = False
            permission.can_manage_settings = False
            permission.can_access_api = False
        
        permission.save()
        
        ActivityLog.objects.create(
            user=request.user,
            action=f"{employee.user.get_full_name()} izinleri varsayılana sıfırlandı",
            details=f"Rol: {employee.get_role_display()}, Yeni izinler: {permission.permissions_summary}"
        )
        
        messages.success(request, f"{employee.user.get_full_name()} için izinler varsayılan değerlere sıfırlandı.")
        return redirect('manage_permissions', employee_id=employee_id)
    
    return JsonResponse({'success': False, 'message': 'Geçersiz istek'})

@login_required(login_url="/login/")
@user_passes_test(is_admin_or_manager, login_url='/')
def employee_status_toggle(request, employee_id):
    """Çalışanın durumunu değiştirme"""
    
    employee = get_object_or_404(EmployeeProfile, id=employee_id)
    
    if request.method == 'POST':
        old_status = employee.is_active
        employee.is_active = not employee.is_active
        
        # Eğer deaktif ediyorsak, kullanıcıyı da deaktif et
        if not employee.is_active:
            employee.user.is_active = False
        else:
            employee.user.is_active = True
        
        employee.save()
        employee.user.save()
        
        # Aktivite logu oluştur
        status_text = "aktif" if employee.is_active else "pasif"
        ActivityLog.objects.create(
            user=request.user,
            action=f"{employee.user.get_full_name()} durumu {status_text} olarak değiştirildi",
            details=f"Önceki durum: {'aktif' if old_status else 'pasif'}"
        )
        
        status_msg = "aktif edildi" if employee.is_active else "deaktif edildi"
        messages.success(request, f"{employee.user.get_full_name()} başarıyla {status_msg}.")
        return redirect('employee_list')
    
    return JsonResponse({'success': False, 'message': 'Geçersiz istek'})


# API Endpoints for Extension Management

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def employee_extensions_api(request):
    """Tüm çalışanların extension bilgilerini getir"""
    try:
        employees = EmployeeProfile.objects.select_related('user', 'position').filter(is_active=True)
        serializer = EmployeeProfileSerializer(employees, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Çalışan extension bilgileri başarıyla getirildi.'
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Hata oluştu: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_extension_api(request, employee_id):
    """Çalışana extension numarası ata"""
    try:
        # Sadece admin veya manager extension atayabilir
        if not is_admin_or_manager(request.user):
            return Response({
                'success': False,
                'message': 'Bu işlem için yetkiniz bulunmamaktadır.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        employee = get_object_or_404(EmployeeProfile, id=employee_id)
        serializer = ExtensionUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            extension_number = serializer.validated_data['extension_number']
            
            # Mevcut extension kontrolü (kendisi hariç)
            existing = EmployeeProfile.objects.filter(
                extension_number=extension_number
            ).exclude(id=employee_id)
            
            if existing.exists():
                return Response({
                    'success': False,
                    'message': f'Bu dahili numara ({extension_number}) zaten kullanılıyor.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Extension ata
            old_extension = employee.extension_number
            employee.extension_number = extension_number
            employee.save()
            
            # Activity log
            ActivityLog.objects.create(
                user=request.user,
                action='extension_assigned',
                description=f'{employee.user.get_full_name()} kullanıcısına {extension_number} dahili numarası atandı. (Eski: {old_extension or "Yok"})'
            )
            
            return Response({
                'success': True,
                'message': f'{employee.user.get_full_name()} kullanıcısına {extension_number} dahili numarası başarıyla atandı.',
                'data': {
                    'employee_id': employee.id,
                    'employee_name': employee.user.get_full_name(),
                    'extension_number': extension_number,
                    'old_extension': old_extension
                }
            })
        else:
            return Response({
                'success': False,
                'message': 'Geçersiz veri.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Hata oluştu: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_extension_api(request, employee_id):
    """Çalışanın extension numarasını kaldır"""
    try:
        # Sadece admin veya manager extension kaldırabilir
        if not is_admin_or_manager(request.user):
            return Response({
                'success': False,
                'message': 'Bu işlem için yetkiniz bulunmamaktadır.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        employee = get_object_or_404(EmployeeProfile, id=employee_id)
        
        if not employee.extension_number:
            return Response({
                'success': False,
                'message': 'Bu çalışanın zaten dahili numarası bulunmamaktadır.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        old_extension = employee.extension_number
        employee.extension_number = None
        employee.save()
        
        # Activity log
        ActivityLog.objects.create(
            user=request.user,
            action='extension_removed',
            description=f'{employee.user.get_full_name()} kullanıcısının {old_extension} dahili numarası kaldırıldı.'
        )
        
        return Response({
            'success': True,
            'message': f'{employee.user.get_full_name()} kullanıcısının dahili numarası başarıyla kaldırıldı.',
            'data': {
                'employee_id': employee.id,
                'employee_name': employee.user.get_full_name(),
                'removed_extension': old_extension
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Hata oluştu: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_extensions_api(request):
    """Kullanılabilir extension numaralarını getir"""
    try:
        # Kullanılan extension'ları al
        used_extensions = set(
            EmployeeProfile.objects.filter(
                extension_number__isnull=False
            ).values_list('extension_number', flat=True)
        )
        
        # 101-199 arası önerilen extension'lar
        suggested_extensions = []
        for i in range(101, 200):
            ext_str = str(i)
            if ext_str not in used_extensions:
                suggested_extensions.append(ext_str)
                if len(suggested_extensions) >= 20:  # İlk 20 tanesini göster
                    break
        
        return Response({
            'success': True,
            'data': {
                'used_extensions': sorted(list(used_extensions)),
                'available_extensions': suggested_extensions,
                'total_used': len(used_extensions),
                'total_available': len(suggested_extensions)
            },
            'message': 'Kullanılabilir extension numaraları başarıyla getirildi.'
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Hata oluştu: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
