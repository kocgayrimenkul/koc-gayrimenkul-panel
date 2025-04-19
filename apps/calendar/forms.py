# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Takvim/Ajanda Formları
"""

from django import forms
from .models import Event, TodoItem
from apps.customers.models import Customer
from apps.portfolio.models import Property
from django.contrib.auth.models import User


class EventForm(forms.ModelForm):
    """Etkinlik formu"""
    
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "form-control select2"}),
        label="Müşteri"
    )
    
    property = forms.ModelChoiceField(
        queryset=Property.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={"class": "form-control select2"}),
        label="Gayrimenkul"
    )
    
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control datepicker", "placeholder": "Başlangıç Tarihi"}),
        label="Başlangıç Tarihi"
    )
    
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={"class": "form-control", "placeholder": "Başlangıç Saati"}),
        label="Başlangıç Saati"
    )
    
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control datepicker", "placeholder": "Bitiş Tarihi"}),
        required=False,
        label="Bitiş Tarihi"
    )
    
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={"class": "form-control", "placeholder": "Bitiş Saati"}),
        required=False,
        label="Bitiş Saati"
    )
    
    class Meta:
        model = Event
        fields = ['title', 'description', 'event_type', 'location', 'customer', 'property']
        widgets = {
            'title': forms.TextInput(attrs={"class": "form-control", "placeholder": "Etkinlik Başlığı"}),
            'description': forms.Textarea(attrs={"class": "form-control", "placeholder": "Açıklama", "rows": 4}),
            'event_type': forms.Select(attrs={"class": "form-control"}),
            'location': forms.TextInput(attrs={"class": "form-control", "placeholder": "Konum"}),
        }


class TodoItemForm(forms.ModelForm):
    """Yapılacak görevi formu"""
    
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control datepicker", "placeholder": "Son Tarih"}),
        required=False,
        label="Son Tarih"
    )
    
    consultant = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name='Danışman').distinct(),
        required=False,
        widget=forms.Select(attrs={"class": "form-control select2"}),
        label="Atanan Danışman"
    )
    
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "form-control select2"}),
        label="Müşteri"
    )
    
    property = forms.ModelChoiceField(
        queryset=Property.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={"class": "form-control select2"}),
        label="Gayrimenkul"
    )
    
    class Meta:
        model = TodoItem
        fields = ['title', 'description', 'priority', 'due_date', 'consultant', 'customer', 'property']
        widgets = {
            'title': forms.TextInput(attrs={"class": "form-control", "placeholder": "Başlık"}),
            'description': forms.Textarea(attrs={"class": "form-control", "placeholder": "Açıklama", "rows": 3}),
            'priority': forms.Select(attrs={"class": "form-control"}),
        } 