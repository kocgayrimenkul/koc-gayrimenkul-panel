# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Satış Süreç İzin Kontrol Decoratorları
"""

from functools import wraps
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from apps.employees.models import EmployeeProfile


# Role hierarchy tanımı (yüksek değer daha yüksek yetki)
ROLE_HIERARCHY = {
    'admin': 100,
    'manager': 80,
    'consultant': 60,
    'secretary': 40,
    'employee': 20
}

def has_sales_permission(user, permission_type):
    """Kullanıcının satış süreç izni olup olmadığını kontrol eder"""
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    try:
        employee = user.employee_profile
        if not employee.is_active:
            return False
        
        # Rol bazlı izin kontrolü
        return check_sales_role_permission(employee.role, permission_type)
    
    except EmployeeProfile.DoesNotExist:
        return False

def get_user_role_level(user):
    """Kullanıcının rol seviyesini döndürür"""
    if user.is_superuser:
        return 100
    
    try:
        employee = user.employee_profile
        return ROLE_HIERARCHY.get(employee.role, 0)
    except:
        return 0

def can_access_user_data(requesting_user, target_user):
    """Bir kullanıcının başka bir kullanıcının verilerine erişip erişemeyeceğini kontrol eder"""
    # Kendi verilerine her zaman erişebilir
    if requesting_user == target_user:
        return True
    
    requesting_level = get_user_role_level(requesting_user)
    target_level = get_user_role_level(target_user)
    
    # Üst seviye roller alt seviye rollerin verilerine erişebilir
    return requesting_level > target_level


def check_sales_role_permission(role, permission_type):
    """Satış süreç rol bazlı izin kontrolü"""
    
    # Admin tüm izinlere sahip
    if role == 'admin':
        return True
    
    # Müdür izinleri
    elif role == 'manager':
        # Müdürler tüm satış süreç işlemlerini yapabilir
        return permission_type in [
            'view_dashboard', 'view_staff_kanban', 'view_manager_kanban',
            'view_leads', 'add_leads', 'edit_leads', 'delete_leads',
            'move_stages', 'add_notes', 'view_reports', 'export_reports',
            'manage_contracts', 'manage_credit', 'manage_deed', 'close_cases'
        ]
    
    # Danışman izinleri
    elif role == 'consultant':
        # Danışmanlar sadece kendi lead'leriyle çalışabilir
        return permission_type in [
            'view_dashboard', 'view_staff_kanban',
            'view_leads', 'add_leads', 'edit_own_leads',
            'move_own_stages', 'add_notes', 'schedule_appointments',
            'send_whatsapp', 'make_calls'
        ]
    
    # Santral izinleri
    elif role == 'secretary':
        # Santral sadece lead ekleme ve görüntüleme
        return permission_type in [
            'view_dashboard', 'view_leads', 'add_leads', 'add_notes',
            'schedule_appointments', 'send_whatsapp'
        ]
    
    # Çalışan izinleri
    elif role == 'employee':
        # Çalışanlar sadece görüntüleme
        return permission_type in ['view_dashboard', 'view_leads']
    
    return False


def require_sales_permission(permission_type, check_ownership=False, allow_ajax=True):
    """
    Satış süreç izin kontrol decorator'ı
    
    Args:
        permission_type: İzin türü
        check_ownership: Lead sahipliği kontrolü yapılsın mı?
        allow_ajax: AJAX istekleri için JSON response döndürülsün mü?
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user
            
            # Süper admin her şeyi yapabilir
            if user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Giriş yapmamış kullanıcı
            if not user.is_authenticated:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and allow_ajax:
                    return JsonResponse({'error': 'Oturum açmanız gerekiyor.'}, status=401)
                return redirect('/login/')
            
            # Çalışan profili kontrolü
            try:
                employee = user.employee_profile
            except EmployeeProfile.DoesNotExist:
                error_msg = 'Çalışan profili bulunamadı.'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and allow_ajax:
                    return JsonResponse({'error': error_msg}, status=403)
                messages.error(request, error_msg)
                return redirect('/')
            
            # Deaktif çalışan
            if not employee.is_active:
                error_msg = 'Hesabınız deaktif edilmiştir.'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and allow_ajax:
                    return JsonResponse({'error': error_msg}, status=403)
                messages.error(request, error_msg)
                return redirect('/')
            
            # İzin kontrolü
            has_permission = check_sales_role_permission(employee.role, permission_type)
            
            if not has_permission:
                error_msg = f"Bu işlem için yetkiniz bulunmuyor: {permission_type}"
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and allow_ajax:
                    return JsonResponse({'error': error_msg}, status=403)
                messages.error(request, error_msg)
                return redirect('sales_process:dashboard')
            
            # Sahiplik kontrolü (danışmanlar için)
            if check_ownership and employee.role == 'consultant':
                lead_id = kwargs.get('lead_id') or kwargs.get('pk') or request.POST.get('lead_id') or request.GET.get('lead_id')
                if lead_id:
                    from .models import Lead
                    try:
                        lead = Lead.objects.get(lead_id=lead_id)
                        if lead.assigned_staff != user:
                            error_msg = "Bu müşteri size atanmamış."
                            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and allow_ajax:
                                return JsonResponse({'error': error_msg}, status=403)
                            messages.error(request, error_msg)
                            return redirect('sales_process:dashboard')
                    except Lead.DoesNotExist:
                        error_msg = 'Lead bulunamadı.'
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and allow_ajax:
                            return JsonResponse({'error': error_msg}, status=404)
                        messages.error(request, error_msg)
                        return redirect('sales_process:dashboard')
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


# ===============================
# DASHBOARD PERMISSIONS
# ===============================

def can_view_sales_dashboard(view_func):
    """Satış dashboard görüntüleme izni"""
    return require_sales_permission('view_dashboard')(view_func)

def can_view_staff_kanban(view_func):
    """Personel kanban görüntüleme izni"""
    return require_sales_permission('view_staff_kanban')(view_func)

def can_view_manager_kanban(view_func):
    """Müdür kanban görüntüleme izni"""
    return require_sales_permission('view_manager_kanban')(view_func)


# ===============================
# LEAD MANAGEMENT PERMISSIONS
# ===============================

def can_view_leads(view_func):
    """Lead görüntüleme izni"""
    return require_sales_permission('view_leads')(view_func)

def can_add_leads(view_func):
    """Lead ekleme izni"""
    return require_sales_permission('add_leads')(view_func)

def can_edit_leads(view_func):
    """Lead düzenleme izni (sahiplik kontrolü ile)"""
    return require_sales_permission('edit_own_leads', check_ownership=True)(view_func)

def can_edit_all_leads(view_func):
    """Tüm lead'leri düzenleme izni (sadece manager/admin)"""
    return require_sales_permission('edit_leads')(view_func)

def can_delete_leads(view_func):
    """Lead silme izni"""
    return require_sales_permission('delete_leads')(view_func)


# ===============================
# STAGE MANAGEMENT PERMISSIONS
# ===============================

def can_move_stages(view_func):
    """Aşama değiştirme izni (sahiplik kontrolü ile)"""
    return require_sales_permission('move_own_stages', check_ownership=True)(view_func)

def can_move_all_stages(view_func):
    """Tüm aşamaları değiştirme izni (sadece manager/admin)"""
    return require_sales_permission('move_stages')(view_func)


# ===============================
# COMMUNICATION PERMISSIONS
# ===============================

def can_add_notes(view_func):
    """Not ekleme izni"""
    return require_sales_permission('add_notes')(view_func)

def can_schedule_appointments(view_func):
    """Randevu planlama izni"""
    return require_sales_permission('schedule_appointments')(view_func)

def can_send_whatsapp(view_func):
    """WhatsApp gönderme izni"""
    return require_sales_permission('send_whatsapp')(view_func)

def can_make_calls(view_func):
    """Arama yapma izni"""
    return require_sales_permission('make_calls')(view_func)


# ===============================
# MANAGER SPECIFIC PERMISSIONS
# ===============================

def can_manage_contracts(view_func):
    """Sözleşme yönetimi izni"""
    return require_sales_permission('manage_contracts')(view_func)

def can_manage_credit(view_func):
    """Kredi işlemleri yönetimi izni"""
    return require_sales_permission('manage_credit')(view_func)

def can_manage_deed(view_func):
    """Tapu işlemleri yönetimi izni"""
    return require_sales_permission('manage_deed')(view_func)

def can_close_cases(view_func):
    """Dosya kapatma izni"""
    return require_sales_permission('close_cases')(view_func)


# ===============================
# REPORTING PERMISSIONS
# ===============================

def can_view_reports(view_func):
    """Rapor görüntüleme izni"""
    return require_sales_permission('view_reports')(view_func)

def can_export_reports(view_func):
    """Rapor dışa aktarma izni"""
    return require_sales_permission('export_reports')(view_func)


# ===============================
# COMBINED PERMISSIONS
# ===============================

# Hiyerarşik izin decorator'ları
def require_role_level(min_level, allow_ajax=True):
    """Minimum rol seviyesi gerektiren decorator"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and allow_ajax:
                    return JsonResponse({'error': 'Oturum açmanız gerekiyor.'}, status=401)
                return redirect('login')
            
            user_level = get_user_role_level(request.user)
            if user_level < min_level:
                error_msg = 'Bu işlem için yetkiniz bulunmamaktadır.'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and allow_ajax:
                    return JsonResponse({'error': error_msg}, status=403)
                messages.error(request, error_msg)
                return redirect('sales_dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def require_higher_role_than_target(allow_ajax=True):
    """Hedef kullanıcıdan daha yüksek rol gerektiren decorator"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and allow_ajax:
                    return JsonResponse({'error': 'Oturum açmanız gerekiyor.'}, status=401)
                return redirect('login')
            
            # Hedef kullanıcı ID'sini al
            target_user_id = kwargs.get('user_id') or request.GET.get('user_id') or request.POST.get('user_id')
            if target_user_id:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    target_user = User.objects.get(id=target_user_id)
                    if not can_access_user_data(request.user, target_user):
                        error_msg = 'Bu kullanıcının verilerine erişim yetkiniz bulunmamaktadır.'
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and allow_ajax:
                            return JsonResponse({'error': error_msg}, status=403)
                        messages.error(request, error_msg)
                        return redirect('sales_dashboard')
                except User.DoesNotExist:
                    error_msg = 'Kullanıcı bulunamadı.'
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and allow_ajax:
                        return JsonResponse({'error': error_msg}, status=404)
                    messages.error(request, error_msg)
                    return redirect('sales_dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def require_lead_access(action_type='view', allow_ajax=True):
    """Lead erişim kontrolü - hiyerarşik ve ownership tabanlı"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and allow_ajax:
                    return JsonResponse({'error': 'Oturum açmanız gerekiyor.'}, status=401)
                return redirect('login')
            
            try:
                profile = request.user.employee_profile
            except:
                error_msg = 'Çalışan profili bulunamadı.'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and allow_ajax:
                    return JsonResponse({'error': error_msg}, status=403)
                messages.error(request, error_msg)
                return redirect('home')
            
            # Lead ID'sini al
            lead_id = kwargs.get('lead_id') or kwargs.get('pk') or request.GET.get('lead_id') or request.POST.get('lead_id')
            if lead_id:
                from .models import Lead
                try:
                    lead = get_object_or_404(Lead, id=lead_id)
                    
                    # Admin ve manager her zaman erişebilir
                    if profile.role in ['admin', 'manager']:
                        return view_func(request, *args, **kwargs)
                    
                    # Secretary sadece görüntüleme yapabilir
                    if profile.role == 'secretary':
                        if action_type in ['view']:
                            return view_func(request, *args, **kwargs)
                        else:
                            error_msg = 'Bu işlem için yetkiniz bulunmamaktadır.'
                            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and allow_ajax:
                                return JsonResponse({'error': error_msg}, status=403)
                            messages.error(request, error_msg)
                            return redirect('sales_dashboard')
                    
                    # Consultant ve employee sadece kendi lead'lerine erişebilir
                    if profile.role in ['consultant', 'employee']:
                        if lead.assigned_staff == request.user:
                            return view_func(request, *args, **kwargs)
                        else:
                            error_msg = 'Bu lead\'e erişim yetkiniz bulunmamaktadır.'
                            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and allow_ajax:
                                return JsonResponse({'error': error_msg}, status=403)
                            messages.error(request, error_msg)
                            return redirect('sales_dashboard')
                    
                except Lead.DoesNotExist:
                    error_msg = 'Lead bulunamadı.'
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and allow_ajax:
                        return JsonResponse({'error': error_msg}, status=404)
                    messages.error(request, error_msg)
                    return redirect('sales_dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def require_manager_or_admin(view_func):
    """Sadece müdür veya admin erişimi"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        
        if user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        if not user.is_authenticated:
            return redirect('/login/')
        
        try:
            employee = user.employee_profile
            if employee.role in ['admin', 'manager'] and employee.is_active:
                return view_func(request, *args, **kwargs)
        except EmployeeProfile.DoesNotExist:
            pass
        
        messages.error(request, "Bu sayfaya erişim yetkiniz bulunmuyor.")
        return redirect('sales_process:dashboard')
    
    return wrapper


def require_admin_only(view_func):
    """Sadece admin erişimi"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        
        if user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        if not user.is_authenticated:
            return redirect('/login/')
        
        try:
            employee = user.employee_profile
            if employee.role == 'admin' and employee.is_active:
                return view_func(request, *args, **kwargs)
        except EmployeeProfile.DoesNotExist:
            pass
        
        messages.error(request, "Bu sayfaya sadece yöneticiler erişebilir.")
        return redirect('sales_process:dashboard')
    
    return wrapper

# Birleşik decorator'lar
require_manager_or_admin_level = require_role_level(80)  # Manager seviyesi ve üstü
require_admin_only_level = require_role_level(100)  # Sadece admin
require_consultant_or_above = require_role_level(60)  # Consultant seviyesi ve üstü


# Kanban view specific decorators
def require_kanban_access(view_type='staff'):
    """Kanban görünümü için özel erişim kontrolü"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Süper admin her şeye erişebilmeli
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            if not request.user.is_authenticated:
                return redirect('/login/')
            
            try:
                employee = request.user.employee_profile
            except EmployeeProfile.DoesNotExist:
                messages.error(request, 'Çalışan profili bulunamadı.')
                return redirect('sales_process:dashboard')
            
            if not employee.is_active:
                messages.error(request, 'Hesabınız deaktif edilmiştir.')
                return redirect('sales_process:dashboard')
            
            # Manager kanban - sadece manager ve admin
            if view_type == 'manager':
                if employee.role not in ['admin', 'manager']:
                    messages.error(request, 'Manager kanban görünümü için yönetici yetkisi gereklidir.')
                    return redirect('sales_process:staff_kanban')
            
            # Staff kanban - tüm roller erişebilir ama kendi verilerini görür
            elif view_type == 'staff':
                # Consultant sadece kendi lead'lerini görebilir
                if employee.role == 'consultant':
                    # View'da filtreleme yapılacak
                    pass
                # Secretary sadece görüntüleme yapabilir
                elif employee.role == 'secretary':
                    # View'da sadece okuma yetkisi verilecek
                    pass
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_lead_ownership_or_manager(allow_ajax=True):
    """Lead sahipliği veya manager yetkisi kontrolü"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and allow_ajax:
                    return JsonResponse({'error': 'Oturum açmanız gerekiyor.'}, status=401)
                return redirect('/login/')
            
            try:
                employee = request.user.employee_profile
            except EmployeeProfile.DoesNotExist:
                error_msg = 'Çalışan profili bulunamadı.'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and allow_ajax:
                    return JsonResponse({'error': error_msg}, status=403)
                messages.error(request, error_msg)
                return redirect('sales_process:dashboard')
            
            if not employee.is_active:
                error_msg = 'Hesabınız deaktif edilmiştir.'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and allow_ajax:
                    return JsonResponse({'error': error_msg}, status=403)
                messages.error(request, error_msg)
                return redirect('sales_process:dashboard')
            
            # Admin ve manager her şeye erişebilir
            if employee.role in ['admin', 'manager']:
                return view_func(request, *args, **kwargs)
            
            # Lead ID'yi al
            lead_id = kwargs.get('lead_id') or kwargs.get('pk') or request.GET.get('lead_id') or request.POST.get('lead_id')
            
            if lead_id:
                try:
                    from .models import Lead
                    lead = Lead.objects.get(lead_id=lead_id)
                    
                    # Consultant sadece kendi lead'lerine erişebilir
                    if employee.role == 'consultant' and lead.assigned_staff != request.user:
                        error_msg = 'Bu lead\'e erişim yetkiniz bulunmamaktadır.'
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and allow_ajax:
                            return JsonResponse({'error': error_msg}, status=403)
                        messages.error(request, error_msg)
                        return redirect('sales_process:lead_list')
                    
                except Lead.DoesNotExist:
                    error_msg = 'Lead bulunamadı.'
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and allow_ajax:
                        return JsonResponse({'error': error_msg}, status=404)
                    messages.error(request, error_msg)
                    return redirect('sales_process:lead_list')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator