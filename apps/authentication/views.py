# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Kimlik Doğrulama Görünümleri
"""

from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy

from .forms import LoginForm, UserUpdateForm, CustomPasswordChangeForm

User = get_user_model()

def login_view(request):
    form = LoginForm(request.POST or None)

    msg = None

    if request.method == "POST":

        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("/")
            else:
                msg = 'Geçersiz kullanıcı adı veya şifre.'
        else:
            msg = 'Hata! Form geçersiz.'

    return render(request, "accounts/login.html", {"form": form, "msg": msg})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    """Kullanıcı profilini görüntüleme ve düzenleme"""
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profiliniz başarıyla güncellendi.')
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user)
    
    context = {
        'form': form,
        'segment': 'profile'
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def change_password(request):
    """Şifre değiştirme görünümü"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Şifreniz başarıyla güncellendi!')
            return redirect('profile')
        else:
            messages.error(request, 'Lütfen hataları düzeltin.')
    else:
        form = CustomPasswordChangeForm(user=request.user)
    
    context = {
        'form': form,
        'segment': 'change_password'
    }
    return render(request, 'accounts/change_password.html', context)


class RoleListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Kullanıcı rollerini listeleyen view"""
    model = Group
    template_name = 'accounts/role_list.html'
    context_object_name = 'roles'
    permission_required = 'auth.view_group'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['segment'] = 'roles'
        return context


class RoleCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Yeni rol oluşturma view'i"""
    model = Group
    template_name = 'accounts/role_form.html'
    fields = ['name', 'permissions']
    success_url = reverse_lazy('role-list')
    permission_required = 'auth.add_group'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['segment'] = 'roles'
        context['title'] = 'Yeni Rol Ekle'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Rol başarıyla oluşturuldu!')
        return super().form_valid(form)


class RoleUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Rol düzenleme view'i"""
    model = Group
    template_name = 'accounts/role_form.html'
    fields = ['name', 'permissions']
    success_url = reverse_lazy('role-list')
    permission_required = 'auth.change_group'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['segment'] = 'roles'
        context['title'] = 'Rol Düzenle'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Rol başarıyla güncellendi!')
        return super().form_valid(form)


class UserListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Kullanıcıları listeleyen view"""
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    permission_required = 'auth.view_user'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['segment'] = 'users'
        return context


class UserDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Kullanıcı detaylarını gösteren view"""
    model = User
    template_name = 'accounts/user_detail.html'
    context_object_name = 'user_detail'
    
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.id == self.kwargs['pk']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['segment'] = 'users'
        return context


class UserUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = User
    template_name = 'accounts/user_form.html'
    fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'position', 'department', 'groups', 'is_active']
    success_url = reverse_lazy('user-list')
    permission_required = 'auth.change_user'
