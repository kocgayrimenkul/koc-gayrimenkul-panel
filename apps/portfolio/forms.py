# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Portföy Yönetimi Formları
"""

from django import forms
from .models import Property, PropertyEnvironment, PropertyImage
from apps.customers.models import Neighborhood
from django.contrib.auth.models import User


class PropertyForm(forms.ModelForm):
    """Gayrimenkul kayıt formu"""
    
    class Meta:
        model = Property
        fields = [
            'title', 'description', 'property_type', 'status', 'price',
            'neighborhood', 'address', 'gross_area', 'net_area',
            'room_count', 'floor', 'building_age', 'heating', 'has_balcony',
            'dues', 'deed_status', 'is_suitable_for_credit', 'is_bargainable',
            'owner_name', 'owner_phone', 'owner_listing_number', 'branda_number',
            'key_holder', 'photo_status', 'listing_date', 'swot_analysis', 'target_audience',
            'floor_count', 'bathroom_count', 'usage_status', 'is_furnished',
            'is_in_site', 'is_exchangeable', 'category', 'listing_type',
            'listing_from', 'customer_tag', 'customer_source',
            'banner_status', 'poster_status', 'consultant'
        ]
        widgets = {
            'title': forms.TextInput(attrs={"class": "form-control", "placeholder": "İlan Başlığı"}),
            'description': forms.Textarea(attrs={"class": "form-control", "placeholder": "Açıklama", "rows": 4}),
            'property_type': forms.Select(attrs={"class": "form-control"}),
            'status': forms.Select(attrs={"class": "form-control"}),
            'price': forms.NumberInput(attrs={"class": "form-control", "placeholder": "Fiyat"}),
            'neighborhood': forms.Select(attrs={"class": "form-control"}),
            'address': forms.Textarea(attrs={"class": "form-control", "placeholder": "Açık Adres", "rows": 3}),
            'gross_area': forms.NumberInput(attrs={"class": "form-control", "placeholder": "Brüt m²"}),
            'net_area': forms.NumberInput(attrs={"class": "form-control", "placeholder": "Net m²"}),
            'room_count': forms.TextInput(attrs={"class": "form-control", "placeholder": "Oda Sayısı"}),
            'floor': forms.TextInput(attrs={"class": "form-control", "placeholder": "Bulunduğu Kat"}),
            'building_age': forms.NumberInput(attrs={"class": "form-control", "placeholder": "Bina Yaşı"}),
            'heating': forms.Select(attrs={"class": "form-control"}),
            'has_balcony': forms.CheckboxInput(attrs={"class": "custom-control-input"}),
            'dues': forms.NumberInput(attrs={"class": "form-control", "placeholder": "Aidat"}),
            'deed_status': forms.Select(attrs={"class": "form-control"}),
            'is_suitable_for_credit': forms.CheckboxInput(attrs={"class": "custom-control-input"}),
            'is_bargainable': forms.CheckboxInput(attrs={"class": "custom-control-input"}),
            'owner_name': forms.TextInput(attrs={"class": "form-control", "placeholder": "Mal Sahibi"}),
            'owner_phone': forms.TextInput(attrs={"class": "form-control", "placeholder": "Mal Sahibi Telefon"}),
            'owner_listing_number': forms.TextInput(attrs={"class": "form-control", "placeholder": "Sahibinden İlan No"}),
            'branda_number': forms.TextInput(attrs={"class": "form-control", "placeholder": "Branda No"}),
            'key_holder': forms.Select(attrs={"class": "form-control"}),
            'photo_status': forms.CheckboxInput(attrs={"class": "custom-control-input"}),
            'listing_date': forms.DateInput(attrs={"class": "form-control datepicker", "placeholder": "İlan Tarihi"}),
            'swot_analysis': forms.Textarea(attrs={"class": "form-control", "placeholder": "SWOT Analizi", "rows": 4}),
            'target_audience': forms.TextInput(attrs={"class": "form-control", "placeholder": "Hedef Kitle"}),
            'floor_count': forms.NumberInput(attrs={"class": "form-control", "placeholder": "Kat Sayısı"}),
            'bathroom_count': forms.NumberInput(attrs={"class": "form-control", "placeholder": "Banyo Sayısı"}),
            'usage_status': forms.Select(attrs={"class": "form-control"}),
            'is_furnished': forms.CheckboxInput(attrs={"class": "custom-control-input"}),
            'is_in_site': forms.CheckboxInput(attrs={"class": "custom-control-input"}),
            'is_exchangeable': forms.CheckboxInput(attrs={"class": "custom-control-input"}),
            'category': forms.Select(attrs={"class": "form-control"}),
            'listing_type': forms.Select(attrs={"class": "form-control"}),
            'listing_from': forms.Select(attrs={"class": "form-control"}),
            'customer_tag': forms.Select(attrs={"class": "form-control"}),
            'customer_source': forms.Select(attrs={"class": "form-control"}),
            'banner_status': forms.Select(attrs={"class": "form-control"}),
            'poster_status': forms.Select(attrs={"class": "form-control"}),
            'consultant': forms.Select(attrs={"class": "form-control"}),
        }


class PropertyEnvironmentForm(forms.ModelForm):
    """Gayrimenkul çevresi formu"""
    
    class Meta:
        model = PropertyEnvironment
        fields = ['place_name', 'distance']
        widgets = {
            'place_name': forms.TextInput(attrs={"class": "form-control", "placeholder": "Yer Adı"}),
            'distance': forms.TextInput(attrs={"class": "form-control", "placeholder": "Uzaklık"}),
        }


class PropertyImageForm(forms.ModelForm):
    """Gayrimenkul görseli formu"""
    
    class Meta:
        model = PropertyImage
        fields = ['image', 'title', 'order']
        widgets = {
            'image': forms.FileInput(attrs={"class": "form-control-file"}),
            'title': forms.TextInput(attrs={"class": "form-control", "placeholder": "Görsel Başlığı"}),
            'order': forms.NumberInput(attrs={"class": "form-control", "placeholder": "Sıralama"}),
        } 