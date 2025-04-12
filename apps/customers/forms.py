# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Müşteri Yönetimi Formları
"""

from django import forms
from .models import Customer, Neighborhood
from django.contrib.auth.models import User


class CustomerForm(forms.ModelForm):
    """Müşteri kayıt formu"""
    
    class Meta:
        model = Customer
        fields = ['full_name', 'phone', 'neighborhood', 'apartment', 'meeting_status', 'meeting_result', 'notes']
        widgets = {
            'full_name': forms.TextInput(attrs={"class": "form-control", "placeholder": "Adı Soyadı"}),
            'phone': forms.TextInput(attrs={"class": "form-control", "placeholder": "Telefon"}),
            'neighborhood': forms.Select(attrs={"class": "form-control"}),
            'apartment': forms.TextInput(attrs={"class": "form-control", "placeholder": "Daire Bilgisi"}),
            'meeting_status': forms.Select(attrs={"class": "form-control"}),
            'meeting_result': forms.Textarea(attrs={"class": "form-control", "placeholder": "Görüşme Sonucu", "rows": 4}),
            'notes': forms.Textarea(attrs={"class": "form-control", "placeholder": "Müşteri ile ilgili notlar", "rows": 4}),
        }


class NeighborhoodForm(forms.ModelForm):
    """Mahalle ekleme/düzenleme formu"""
    
    consultant = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name='Danışman') | User.objects.filter(is_staff=True),
        required=False,
        widget=forms.Select(attrs={"class": "form-control select2"}),
        label="Bağlı Danışman"
    )
    
    class Meta:
        model = Neighborhood
        fields = ['name', 'district', 'consultant']
        widgets = {
            'name': forms.TextInput(attrs={"class": "form-control", "placeholder": "Mahalle Adı"}),
            'district': forms.TextInput(attrs={"class": "form-control", "placeholder": "İlçe"}),
        } 