# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - İzin Template Tag'leri
"""

from django import template
from ..decorators import check_role_permission, has_module_permission

register = template.Library()

@register.filter
def has_permission(user, permission_string):
    """
    Kullanıcının belirli bir izni olup olmadığını kontrol eder
    Kullanım: {% if user|has_permission:"view_customers" %}
    """
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    try:
        employee = user.employee_profile
        if not employee.is_active:
            return False
        
        # İzin string'ini parse et (örn: "view_customers")
        parts = permission_string.split('_', 1)
        if len(parts) != 2:
            return False
        
        permission_type, module = parts
        return has_module_permission(user, module, permission_type)
    
    except:
        return False

@register.filter
def can_view(user, module):
    """Görüntüleme izni kontrolü"""
    return has_module_permission(user, module, 'view')

@register.filter
def can_add(user, module):
    """Ekleme izni kontrolü"""
    return has_module_permission(user, module, 'add')

@register.filter
def can_edit(user, module):
    """Düzenleme izni kontrolü"""
    return has_module_permission(user, module, 'edit')

@register.filter
def can_delete(user, module):
    """Silme izni kontrolü"""
    return has_module_permission(user, module, 'delete')

@register.simple_tag
def check_module_permission(user, module, permission_type):
    """
    Modül ve izin tipine göre kontrol
    Kullanım: {% check_module_permission user "customers" "view" as can_view_customers %}
    """
    return has_module_permission(user, module, permission_type)

# ===============================
# CUSTOMER MODULE PERMISSIONS
# ===============================

@register.filter
def can_view_customers(user):
    """Müşteri görüntüleme izni"""
    return has_module_permission(user, 'customers', 'view')

@register.filter
def can_add_customers(user):
    """Müşteri ekleme izni"""
    return has_module_permission(user, 'customers', 'add')

@register.filter
def can_edit_customers(user):
    """Müşteri düzenleme izni"""
    return has_module_permission(user, 'customers', 'edit')

@register.filter
def can_delete_customers(user):
    """Müşteri silme izni"""
    return has_module_permission(user, 'customers', 'delete')

# ===============================
# PORTFOLIO MODULE PERMISSIONS
# ===============================

@register.filter
def can_view_portfolio(user):
    """Portföy görüntüleme izni"""
    return has_module_permission(user, 'portfolio', 'view')

@register.filter
def can_add_portfolio(user):
    """Portföy ekleme izni"""
    return has_module_permission(user, 'portfolio', 'add')

@register.filter
def can_edit_portfolio(user):
    """Portföy düzenleme izni"""
    return has_module_permission(user, 'portfolio', 'edit')

@register.filter
def can_delete_portfolio(user):
    """Portföy silme izni"""
    return has_module_permission(user, 'portfolio', 'delete')

# ===============================
# CALENDAR MODULE PERMISSIONS
# ===============================

@register.filter
def can_view_calendar(user):
    """Takvim görüntüleme izni"""
    return has_module_permission(user, 'calendar', 'view')

@register.filter
def can_add_calendar(user):
    """Takvim ekleme izni"""
    return has_module_permission(user, 'calendar', 'add')

@register.filter
def can_edit_calendar(user):
    """Takvim düzenleme izni"""
    return has_module_permission(user, 'calendar', 'edit')

@register.filter
def can_delete_calendar(user):
    """Takvim silme izni"""
    return has_module_permission(user, 'calendar', 'delete')

# ===============================
# FSBO MODULE PERMISSIONS
# ===============================

@register.filter
def can_view_fsbo(user):
    """FSBO görüntüleme izni"""
    return has_module_permission(user, 'fsbo', 'view')

@register.filter
def can_add_fsbo(user):
    """FSBO ekleme izni"""
    return has_module_permission(user, 'fsbo', 'add')

@register.filter
def can_edit_fsbo(user):
    """FSBO düzenleme izni"""
    return has_module_permission(user, 'fsbo', 'edit')

@register.filter
def can_delete_fsbo(user):
    """FSBO silme izni"""
    return has_module_permission(user, 'fsbo', 'delete')

# ===============================
# PRESENTATION MODULE PERMISSIONS
# ===============================

@register.filter
def can_view_presentation(user):
    """Sunum modülünü görüntüleme izni"""
    return has_module_permission(user, 'presentation', 'view')

@register.filter
def can_add_presentation(user):
    """Sunum ekleme izni"""
    return has_module_permission(user, 'presentation', 'add')

@register.filter
def can_edit_presentation(user):
    """Sunum düzenleme izni"""
    return has_module_permission(user, 'presentation', 'edit')

@register.filter
def can_delete_presentation(user):
    """Sunum silme izni"""
    return has_module_permission(user, 'presentation', 'delete')

# ===============================
# EMPLOYEES MODULE PERMISSIONS
# ===============================

@register.filter
def can_view_employees(user):
    """Çalışan görüntüleme izni"""
    return has_module_permission(user, 'employees', 'view')

@register.filter
def can_add_employees(user):
    """Çalışan ekleme izni"""
    return has_module_permission(user, 'employees', 'add')

@register.filter
def can_edit_employees(user):
    """Çalışan düzenleme izni"""
    return has_module_permission(user, 'employees', 'edit')

@register.filter
def can_delete_employees(user):
    """Çalışan silme izni"""
    return has_module_permission(user, 'employees', 'delete')

# ===============================
# CAREERS MODULE PERMISSIONS
# ===============================

@register.filter
def can_view_careers(user):
    """Kariyer modülünü görüntüleme izni"""
    return has_module_permission(user, 'careers', 'view')

@register.filter
def can_add_careers(user):
    """Kariyer ekleme izni"""
    return has_module_permission(user, 'careers', 'add')

@register.filter
def can_edit_careers(user):
    """Kariyer düzenleme izni"""
    return has_module_permission(user, 'careers', 'edit')

@register.filter
def can_delete_careers(user):
    """Kariyer silme izni"""
    return has_module_permission(user, 'careers', 'delete')

# ===============================
# SYSTEM PERMISSIONS
# ===============================

@register.filter
def can_manage_settings(user):
    """Sistem ayarları yönetme izni"""
    return has_module_permission(user, 'system', 'manage_settings')

@register.filter
def can_view_reports(user):
    """Rapor görüntüleme izni"""
    return has_module_permission(user, 'system', 'view_reports')

@register.filter
def can_access_api(user):
    """API erişim izni"""
    return has_module_permission(user, 'system', 'access_api')

# ===============================
# ROLE CHECK FUNCTIONS
# ===============================

@register.filter
def is_admin_or_manager(user):
    """Kullanıcının admin veya müdür olup olmadığını kontrol eder"""
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    try:
        employee = user.employee_profile
        return employee.role in ['admin', 'manager'] and employee.is_active
    except:
        return False

@register.filter
def is_admin(user):
    """Kullanıcının admin olup olmadığını kontrol eder"""
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    try:
        employee = user.employee_profile
        return employee.role == 'admin' and employee.is_active
    except:
        return False

@register.filter
def get_role_display(user):
    """Kullanıcının rol adını döndürür"""
    if not user.is_authenticated:
        return "Misafir"
    
    if user.is_superuser:
        return "Süper Admin"
    
    try:
        employee = user.employee_profile
        return employee.get_role_display()
    except:
        return "Tanımsız"

@register.filter
def get_permissions_summary(user):
    """Kullanıcının izin özetini döndürür"""
    if not user.is_authenticated:
        return "İzin yok"
    
    if user.is_superuser:
        return "Tüm izinler"
    
    try:
        employee = user.employee_profile
        permission = employee.permission
        return permission.permissions_summary
    except:
        return "Varsayılan izinler" 