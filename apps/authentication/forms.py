# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Kimlik Doğrulama Formları
"""

from django import forms
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model

User = get_user_model()


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Kullanıcı adı veya e-posta",
                "class": "form-control"
            }
        ))
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Şifre",
                "class": "form-control"
            }
        ))


class UserUpdateForm(forms.ModelForm):
    """Kullanıcı bilgilerini güncelleme formu"""
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'position', 'department', 'profile_photo')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control-file'})
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    """Özelleştirilmiş şifre değiştirme formu"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class CustomPasswordResetForm(PasswordResetForm):
    """Özelleştirilmiş şifre sıfırlama formu"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class CustomSetPasswordForm(SetPasswordForm):
    """Özelleştirilmiş şifre belirleme formu"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
