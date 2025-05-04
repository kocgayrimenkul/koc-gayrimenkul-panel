# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Daire Sunumu Formları
"""

from django import forms
from .models import Presentation, PresentationFeedback
from apps.portfolio.models import Property
from apps.customers.models import Neighborhood
from django.contrib.auth import get_user_model

User = get_user_model()

class PresentationForm(forms.ModelForm):
    """Daire sunumu oluşturma ve düzenleme formu"""
    
    property = forms.ModelChoiceField(
        queryset=Property.objects.filter(property_type='daire', is_active=True),
        widget=forms.Select(attrs={"class": "form-control select2"}),
        label="Daire"
    )
    
    presenter = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.Select(attrs={"class": "form-control select2"}),
        label="Sunan Kişi"
    )
    
    neighborhood = forms.ModelChoiceField(
        queryset=Neighborhood.objects.all(),
        widget=forms.Select(attrs={"class": "form-control select2"}),
        label="Mahalle",
        required=False
    )
    
    other_property1 = forms.ModelChoiceField(
        queryset=Property.objects.filter(property_type='daire', is_active=True),
        widget=forms.Select(attrs={"class": "form-control select2"}),
        label="Diğer Gezdirilen Daire 1",
        required=False
    )
    
    other_property2 = forms.ModelChoiceField(
        queryset=Property.objects.filter(property_type='daire', is_active=True),
        widget=forms.Select(attrs={"class": "form-control select2"}),
        label="Diğer Gezdirilen Daire 2",
        required=False
    )
    
    other_property3 = forms.ModelChoiceField(
        queryset=Property.objects.filter(property_type='daire', is_active=True),
        widget=forms.Select(attrs={"class": "form-control select2"}),
        label="Diğer Gezdirilen Daire 3",
        required=False
    )
    
    class Meta:
        model = Presentation
        fields = ['title', 'property', 'presenter', 'presentation_date', 'customer_name', 
                 'customer_phone', 'customer_source', 'neighborhood', 
                 'other_property1', 'other_property2', 'other_property3', 'other_properties_notes',
                 'notes', 'status']
        widgets = {
            'title': forms.TextInput(attrs={"class": "form-control", "placeholder": "Sunum Başlığı"}),
            'presentation_date': forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            'customer_name': forms.TextInput(attrs={"class": "form-control", "placeholder": "Müşteri Adı"}),
            'customer_phone': forms.TextInput(attrs={"class": "form-control", "placeholder": "Müşteri Telefonu"}),
            'customer_source': forms.Select(attrs={"class": "form-control"}),
            'other_properties_notes': forms.Textarea(attrs={"class": "form-control", "placeholder": "Gezdirilen daireler hakkında notlar", "rows": 3}),
            'notes': forms.Textarea(attrs={"class": "form-control", "placeholder": "Sunum ile ilgili notlar", "rows": 4}),
            'status': forms.Select(attrs={"class": "form-control"}),
        }

class PresentationFeedbackForm(forms.ModelForm):
    """Daire sunumu geri bildirim formu"""
    
    class Meta:
        model = PresentationFeedback
        fields = ['rating', 'comments']
        widgets = {
            'rating': forms.Select(attrs={"class": "form-control"}),
            'comments': forms.Textarea(attrs={"class": "form-control", "placeholder": "Yorumlar", "rows": 4}),
        } 