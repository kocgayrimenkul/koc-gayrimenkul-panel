# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Kimlik Doğrulama URL'leri
"""

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import CustomPasswordResetForm, CustomSetPasswordForm

urlpatterns = [
    path('login/', views.login_view, name="login"),
    path('logout/', views.logout_view, name="logout"),
    path('profile/', views.profile_view, name='profile'),
    
    # Şifre sıfırlama
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             form_class=CustomPasswordResetForm
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             form_class=CustomSetPasswordForm
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ),
         name='password_reset_complete'),
    
    # Rol yönetimi
    path('roles/', views.RoleListView.as_view(), name='role-list'),
    path('roles/create/', views.RoleCreateView.as_view(), name='role-create'),
    path('roles/<int:pk>/update/', views.RoleUpdateView.as_view(), name='role-update'),
    
    # Kullanıcı yönetimi
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/update/', views.UserUpdateView.as_view(), name='user-update'),
]
