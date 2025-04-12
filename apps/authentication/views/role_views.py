# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Rol Yönetimi Görünümleri
"""

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import Group, Permission
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django import forms

class RoleForm(forms.ModelForm):
    """Rol oluşturma ve düzenleme formu"""
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="İzinler"
    )
    
    class Meta:
        model = Group
        fields = ['name', 'permissions']
        labels = {
            'name': 'Rol Adı',
        }
    
    def __init__(self, *args, **kwargs):
        super(RoleForm, self).__init__(*args, **kwargs)
        
        # İzinleri daha düzenli göstermek için kategorize et
        content_types = ContentType.objects.all()
        categorized_permissions = {}
        
        for ct in content_types:
            app_label = ct.app_label
            model = ct.model
            if app_label not in categorized_permissions:
                categorized_permissions[app_label] = {}
            
            perms = Permission.objects.filter(content_type=ct)
            if perms.exists():
                categorized_permissions[app_label][model] = perms
        
        self.categorized_permissions = categorized_permissions

@login_required
@permission_required('auth.view_group', raise_exception=True)
def role_list(request):
    """Rolleri listele"""
    roles = Group.objects.all()
    return render(request, 'accounts/role_list.html', {'roles': roles})

@login_required
@permission_required('auth.add_group', raise_exception=True)
def role_create(request):
    """Yeni rol oluştur"""
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rol başarıyla oluşturuldu.')
            return redirect('role_list')
    else:
        form = RoleForm()
    
    return render(request, 'accounts/role_form.html', {
        'form': form,
        'title': 'Yeni Rol Oluştur',
        'categorized_permissions': form.categorized_permissions
    })

@login_required
@permission_required('auth.change_group', raise_exception=True)
def role_edit(request, pk):
    """Rol düzenle"""
    role = get_object_or_404(Group, pk=pk)
    
    if request.method == 'POST':
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rol başarıyla güncellendi.')
            return redirect('role_list')
    else:
        form = RoleForm(instance=role)
    
    return render(request, 'accounts/role_form.html', {
        'form': form,
        'title': f'Rol Düzenle: {role.name}',
        'categorized_permissions': form.categorized_permissions
    })

@login_required
@permission_required('auth.delete_group', raise_exception=True)
def role_delete(request, pk):
    """Rol sil"""
    role = get_object_or_404(Group, pk=pk)
    
    if request.method == 'POST':
        # Kullanıcılarda bu role ait bir ilişki varsa güncelle
        if role.user_set.exists():
            messages.warning(request, 'Bu role sahip kullanıcılar var. Önce kullanıcılardan bu rolü kaldırın.')
            return redirect('role_list')
        
        role.delete()
        messages.success(request, 'Rol başarıyla silindi.')
        return redirect('role_list')
    
    return render(request, 'accounts/role_delete.html', {'role': role}) 