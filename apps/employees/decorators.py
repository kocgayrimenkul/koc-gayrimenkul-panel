# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - İzin Kontrol Decoratorları
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import Permission
from django.contrib.auth.decorators import user_passes_test

def has_module_permission(user, module, permission_type):
    """Kullanıcının modül izni olup olmadığını kontrol eder"""
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    try:
        employee = user.employee_profile
        if not employee.is_active:
            return False
        
        # Özel izinleri kontrol et
        try:
            permission = employee.permission
            permission_field = f"can_{permission_type}_{module}"
            return getattr(permission, permission_field, False)
        except:
            # Özel izin yoksa rol bazlı kontrol yap
            return check_role_permission(employee.role, permission_type, module)
    
    except:
        return False

def check_permission(permission_type, module):
    """
    İzin kontrol decorator'ı
    
    Args:
        permission_type: 'view', 'add', 'edit', 'delete'
        module: 'customers', 'portfolio', 'calendar', 'fsbo', 'presentation', 'careers', 'employees'
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
                return redirect('/login/')
            
            # Çalışan profili kontrolü
            try:
                employee = user.employee_profile
            except:
                messages.error(request, "Çalışan profili bulunamadı.")
                return redirect('/')
            
            # Deaktif çalışan
            if not employee.is_active:
                messages.error(request, "Hesabınız deaktif edilmiştir.")
                return redirect('/')
            
            # İzin kontrolü
            permission_field = f"can_{permission_type}_{module}"
            
            # Özel izinleri kontrol et
            try:
                custom_permissions = employee.permission
                has_permission = getattr(custom_permissions, permission_field, False)
            except:
                # Özel izin yoksa rol bazlı kontrol yap
                has_permission = check_role_permission(employee.role, permission_type, module)
            
            if has_permission:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, f"Bu işlem için yetkiniz bulunmuyor: {module} {permission_type}")
                return redirect('/')
        
        return wrapper
    return decorator

def check_role_permission(role, permission_type, module):
    """Rol bazlı izin kontrolü"""
    
    # Admin tüm izinlere sahip
    if role == 'admin':
        return True
    
    # Müdür izinleri
    elif role == 'manager':
        if permission_type == 'delete':
            return module in ['calendar']  # Sadece takvim silme
        else:
            return module in ['customers', 'portfolio', 'calendar', 'fsbo', 'presentation', 'careers', 'employees']
    
    # Danışman izinleri
    elif role == 'consultant':
        if permission_type == 'delete':
            return False  # Hiçbir şey silemez
        elif permission_type in ['view', 'add']:
            return module in ['customers', 'portfolio', 'calendar', 'fsbo', 'presentation']  # customers eklendi
        elif permission_type == 'edit':
            return module in ['customers', 'presentation']  # Müşteri ve presentation düzenleme izni eklendi
    
    # Santral izinleri
    elif role == 'secretary':
        if permission_type == 'delete':
            return False  # Hiçbir şey silemez
        elif permission_type == 'view':
            return module in ['customers', 'portfolio', 'calendar', 'fsbo', 'presentation', 'careers']
        elif permission_type == 'add':
            return module in ['customers', 'calendar', 'presentation']  # Müşteri, randevu ve presentation ekleyebilir
        elif permission_type == 'edit':
            return module in ['customers', 'calendar', 'presentation']  # Müşteri, takvim ve presentation düzenleyebilir
    
    # Çalışan izinleri
    elif role == 'employee':
        if permission_type == 'view':
            return module in ['customers', 'portfolio', 'calendar', 'fsbo', 'presentation', 'careers']
        else:
            return False  # Sadece görüntüleyebilir
    
    return False

# Modül bazlı decorator'lar
def require_customer_permission(permission_type):
    """Müşteri modülü izin kontrolü"""
    return check_permission(permission_type, 'customers')

def require_portfolio_permission(permission_type):
    """Portföy modülü izin kontrolü"""
    return check_permission(permission_type, 'portfolio')

def require_calendar_permission(permission_type):
    """Takvim modülü izin kontrolü"""
    return check_permission(permission_type, 'calendar')

def require_fsbo_permission(permission_type):
    """FSBO modülü izin kontrolü"""
    return check_permission(permission_type, 'fsbo')

def require_presentation_permission(permission_type):
    """Prezentasyon modülü izin kontrolü"""
    return check_permission(permission_type, 'presentation')

def require_careers_permission(permission_type):
    """Kariyer modülü izin kontrolü"""
    return check_permission(permission_type, 'careers')

def require_employee_permission(permission_type):
    """Çalışan modülü izin kontrolü"""
    return check_permission(permission_type, 'employees')

# ===============================
# CUSTOMERS MODULE DECORATORS
# ===============================

def can_view_customers(view_func):
    return require_customer_permission('view')(view_func)

def can_add_customers(view_func):
    return require_customer_permission('add')(view_func)

def can_edit_customers(view_func):
    return require_customer_permission('edit')(view_func)

def can_delete_customers(view_func):
    return require_customer_permission('delete')(view_func)

# ===============================
# PORTFOLIO MODULE DECORATORS
# ===============================

def can_view_portfolio(view_func):
    return require_portfolio_permission('view')(view_func)

def can_add_portfolio(view_func):
    return require_portfolio_permission('add')(view_func)

def can_edit_portfolio(view_func):
    return require_portfolio_permission('edit')(view_func)

def can_delete_portfolio(view_func):
    return require_portfolio_permission('delete')(view_func)

# ===============================
# CALENDAR MODULE DECORATORS
# ===============================

def can_view_calendar(view_func):
    return require_calendar_permission('view')(view_func)

def can_add_calendar(view_func):
    return require_calendar_permission('add')(view_func)

def can_edit_calendar(view_func):
    return require_calendar_permission('edit')(view_func)

def can_delete_calendar(view_func):
    return require_calendar_permission('delete')(view_func)

# ===============================
# FSBO MODULE DECORATORS
# ===============================

def can_view_fsbo(view_func):
    """FSBO görüntüleme izni kontrolü"""
    def check_permission(user):
        return has_module_permission(user, 'fsbo', 'view')
    
    return user_passes_test(check_permission, login_url='/login/')(view_func)

def can_add_fsbo(view_func):
    """FSBO ekleme izni kontrolü"""
    def check_permission(user):
        return has_module_permission(user, 'fsbo', 'add')
    
    return user_passes_test(check_permission, login_url='/login/')(view_func)

def can_edit_fsbo(view_func):
    """FSBO düzenleme izni kontrolü"""
    def check_permission(user):
        return has_module_permission(user, 'fsbo', 'edit')
    
    return user_passes_test(check_permission, login_url='/login/')(view_func)

def can_delete_fsbo(view_func):
    """FSBO silme izni kontrolü"""
    def check_permission(user):
        return has_module_permission(user, 'fsbo', 'delete')
    
    return user_passes_test(check_permission, login_url='/login/')(view_func)

# ===============================
# PRESENTATION MODULE DECORATORS  
# ===============================

def can_view_presentation(view_func):
    """Sunum görüntüleme izni kontrolü"""
    def check_permission(user):
        return has_module_permission(user, 'presentation', 'view')
    
    return user_passes_test(check_permission, login_url='/login/')(view_func)

def can_add_presentation(view_func):
    """Sunum ekleme izni kontrolü"""
    def check_permission(user):
        return has_module_permission(user, 'presentation', 'add')
    
    return user_passes_test(check_permission, login_url='/login/')(view_func)

def can_edit_presentation(view_func):
    """Sunum düzenleme izni kontrolü"""
    def check_permission(user):
        return has_module_permission(user, 'presentation', 'edit')
    
    return user_passes_test(check_permission, login_url='/login/')(view_func)

def can_delete_presentation(view_func):
    """Sunum silme izni kontrolü"""
    def check_permission(user):
        return has_module_permission(user, 'presentation', 'delete')
    
    return user_passes_test(check_permission, login_url='/login/')(view_func)

# ===============================
# EMPLOYEES MODULE DECORATORS
# ===============================

def can_view_employees(view_func):
    """Çalışan görüntüleme izni kontrolü"""
    def check_permission(user):
        return has_module_permission(user, 'employees', 'view')
    
    return user_passes_test(check_permission, login_url='/login/')(view_func)

def can_add_employees(view_func):
    """Çalışan ekleme izni kontrolü"""
    def check_permission(user):
        return has_module_permission(user, 'employees', 'add')
    
    return user_passes_test(check_permission, login_url='/login/')(view_func)

def can_edit_employees(view_func):
    """Çalışan düzenleme izni kontrolü"""
    def check_permission(user):
        return has_module_permission(user, 'employees', 'edit')
    
    return user_passes_test(check_permission, login_url='/login/')(view_func)

def can_delete_employees(view_func):
    """Çalışan silme izni kontrolü"""
    def check_permission(user):
        return has_module_permission(user, 'employees', 'delete')
    
    return user_passes_test(check_permission, login_url='/login/')(view_func)

# ===============================
# SYSTEM PERMISSIONS
# ===============================

def can_manage_settings(view_func):
    """Sistem ayarları yönetme izni"""
    def check_permission(user):
        return has_module_permission(user, 'system', 'manage_settings')
    
    return user_passes_test(check_permission, login_url='/login/')(view_func)

def can_view_reports(view_func):
    """Rapor görüntüleme izni"""
    def check_permission(user):
        return has_module_permission(user, 'system', 'view_reports')
    
    return user_passes_test(check_permission, login_url='/login/')(view_func)

def can_access_api(view_func):
    """API erişim izni"""
    def check_permission(user):
        return has_module_permission(user, 'system', 'access_api')
    
    return user_passes_test(check_permission, login_url='/login/')(view_func)

# ===============================
# LEGACY DECORATORS (Geriye uyumluluk için)
# ===============================

def require_admin_or_manager(view_func):
    """Sadece admin veya müdür erişebilir"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        
        if not user.is_authenticated:
            return redirect('/login/')
        
        if user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        try:
            employee = user.employee_profile
            if employee.role in ['admin', 'manager'] and employee.is_active:
                return view_func(request, *args, **kwargs)
        except:
            pass
        
        messages.error(request, "Bu sayfaya erişim yetkiniz bulunmuyor.")
        return redirect('/')
    
    return wrapper

def require_admin_only(view_func):
    """Sadece admin erişebilir"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        
        if not user.is_authenticated:
            return redirect('/login/')
        
        if user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        try:
            employee = user.employee_profile
            if employee.role == 'admin' and employee.is_active:
                return view_func(request, *args, **kwargs)
        except:
            pass
        
        messages.error(request, "Bu sayfaya erişim yetkiniz bulunmuyor.")
        return redirect('/')
    
    return wrapper 