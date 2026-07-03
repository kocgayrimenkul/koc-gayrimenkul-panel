# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Müşteri Yönetimi Formları
"""

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Customer, Neighborhood
import re

User = get_user_model()  # CustomUser'ı otomatik alır


class CustomerForm(forms.ModelForm):
    """Müşteri kayıt formu"""

    class Meta:
        model = Customer
        fields = [
            'full_name', 'phone', 'neighborhood', 'source',
            'contact_type', 'meeting_result', 'notes', 'reminder_date',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Adı Soyadı",
                "autocomplete": "off",
            }),
            'phone': forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "05XX XXX XX XX",
                "autocomplete": "off",
            }),
            'neighborhood': forms.Select(attrs={"class": "form-control select2"}),
            'source': forms.Select(attrs={"class": "form-control"}),
            'contact_type': forms.Select(attrs={"class": "form-control"}),
            'meeting_result': forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Görüşme Sonucu",
                "rows": 4,
            }),
            'notes': forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Müşteri ile ilgili notlar",
                "rows": 4,
            }),
            'reminder_date': forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)
        if not re.match(r'^\+?[\d]{10,15}$', cleaned):
            raise forms.ValidationError(
                'Geçerli bir telefon numarası giriniz. (Örn: 05XX XXX XX XX)'
            )
        return phone

    def clean_full_name(self):
        name = self.cleaned_data.get('full_name', '').strip()
        if len(name) < 3:
            raise forms.ValidationError('Ad soyad en az 3 karakter olmalıdır.')
        return name

    def clean_reminder_date(self):
        from django.utils import timezone
        reminder_date = self.cleaned_data.get('reminder_date')
        if reminder_date and reminder_date < timezone.now().date():
            raise forms.ValidationError('Hatırlatma tarihi geçmişte olamaz.')
        return reminder_date


class CustomerEditForm(forms.ModelForm):
    """Müşteri düzenleme formu - Tüm alanları içerir"""

    class Meta:
        model = Customer
        fields = [
            'full_name', 'phone', 'neighborhood', 'source', 'contact_type',
            'meeting_status', 'meeting_result', 'response_date', 'reminder_date', 'notes',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Adı Soyadı",
            }),
            'phone': forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "05XX XXX XX XX",
            }),
            'neighborhood': forms.Select(attrs={"class": "form-control select2"}),
            'source': forms.Select(attrs={"class": "form-control"}),
            'contact_type': forms.Select(attrs={"class": "form-control"}),
            'meeting_status': forms.Select(attrs={"class": "form-control"}),
            'meeting_result': forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Görüşme Sonucu",
                "rows": 4,
            }),
            'response_date': forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            'reminder_date': forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            'notes': forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Müşteri ile ilgili notlar",
                "rows": 4,
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)
        if not re.match(r'^\+?[\d]{10,15}$', cleaned):
            raise forms.ValidationError(
                'Geçerli bir telefon numarası giriniz. (Örn: 05XX XXX XX XX)'
            )
        return phone

    def clean_full_name(self):
        name = self.cleaned_data.get('full_name', '').strip()
        if len(name) < 3:
            raise forms.ValidationError('Ad soyad en az 3 karakter olmalıdır.')
        return name

    def clean(self):
        cleaned_data = super().clean()
        from django.utils import timezone
        today = timezone.now().date()
        reminder_date = cleaned_data.get('reminder_date')
        response_date = cleaned_data.get('response_date')
        if reminder_date and reminder_date < today:
            self.add_error('reminder_date', 'Hatırlatma tarihi geçmişte olamaz.')
        if response_date and response_date > today:
            self.add_error('response_date', 'Geri dönüş tarihi gelecekte olamaz.')
        return cleaned_data


class NeighborhoodForm(forms.ModelForm):
    """Mahalle ekleme/düzenleme formu"""

    consultant = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=True) | User.objects.filter(
            employee_profile__role='consultant'
        ),
        required=False,
        widget=forms.Select(attrs={"class": "form-control select2"}),
        label="Bağlı Danışman",
        empty_label="-- Danışman Seçin --",
    )

    consultant2 = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=True) | User.objects.filter(
            employee_profile__role='consultant'
        ),
        required=False,
        widget=forms.Select(attrs={"class": "form-control select2"}),
        label="2. Danışman",
        empty_label="-- 2. Danışman Seçin --",
    )

    class Meta:
        model = Neighborhood
        fields = ['name', 'district', 'consultant', 'consultant2']
        widgets = {
            'name': forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Mahalle Adı",
            }),
            'district': forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "İlçe",
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError('Mahalle adı en az 2 karakter olmalıdır.')
        qs = Neighborhood.objects.filter(name__iexact=name)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Bu isimde bir mahalle zaten mevcut.')
        return name