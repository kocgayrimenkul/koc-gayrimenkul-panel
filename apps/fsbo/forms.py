# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - FSBO Formları
"""

from django import forms
from .models import FSBO
from django.contrib.auth import get_user_model
from apps.employees.models import EmployeeProfile

User = get_user_model()

class FSBOForm(forms.ModelForm):
    """FSBO kayıt/düzenleme formu"""
    
    # Danışmanları rolüne göre filtreleme
    consultant = forms.ModelChoiceField(
        queryset=User.objects.filter(employee_profile__role='consultant', is_active=True),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Danışmana Gönder"
    )
    
    class Meta:
        model = FSBO
        fields = ['full_name', 'phone', 'result', 'consultant', 
                 'link1', 'link2', 'reminder_status', 'reminder_date', 
                 'reminder_time', 'notes']
        widgets = {
            'full_name': forms.TextInput(attrs={"class": "form-control", "placeholder": "Adı Soyadı"}),
            'phone': forms.TextInput(attrs={"class": "form-control", "placeholder": "Telefon"}),
            'result': forms.Select(attrs={"class": "form-control"}),
            'link1': forms.URLInput(attrs={"class": "form-control", "placeholder": "https://"}),
            'link2': forms.URLInput(attrs={"class": "form-control", "placeholder": "https://"}),
            'reminder_status': forms.Select(attrs={"class": "form-control"}),
            'reminder_date': forms.DateInput(attrs={"class": "form-control", "type": "date", "placeholder": "gg.aa.yyyy"}),
            'reminder_time': forms.TimeInput(attrs={"class": "form-control", "type": "time", "placeholder": "--:--"}),
            'notes': forms.Textarea(attrs={"class": "form-control", "placeholder": "Görüşme Notları", "rows": 4}),
        }
        

class FSBOSearchForm(forms.Form):
    """FSBO arama formu"""
    phone = forms.CharField(
        max_length=20, 
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "5xxxxxxxxx"})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"})
    )
    result = forms.ChoiceField(
        choices=[('', 'Tümü')] + FSBO.RESULT_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-control"})
    )
    consultant = forms.ModelChoiceField(
        queryset=User.objects.filter(employee_profile__role='consultant', is_active=True),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Danışman"
    ) 