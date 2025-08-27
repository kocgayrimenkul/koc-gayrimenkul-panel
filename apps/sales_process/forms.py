# -*- encoding: utf-8 -*-
"""
Satış Süreç Yönetimi Formları
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import Lead, Task, Appointment, LeadNote, WhatsAppMessage


class LeadForm(forms.ModelForm):
    """
    Lead oluşturma ve düzenleme formu
    """
    
    class Meta:
        model = Lead
        fields = [
            'customer_name', 'customer_phone', 'source', 'contact_type',
            'interested_property', 'neighborhood', 'budget_min', 'budget_max',
            'priority', 'payment_type', 'meeting_result', 'meeting_status',
            'response_date', 'reminder_date', 'lead_notes'
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Adı Soyadı'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Telefon'}),

            'source': forms.Select(attrs={'class': 'form-control'}),
            'contact_type': forms.Select(attrs={'class': 'form-control'}),
            'interested_property': forms.Select(attrs={'class': 'form-control'}),
            'neighborhood': forms.Select(attrs={'class': 'form-control'}),
            'budget_min': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minimum Bütçe'}),
            'budget_max': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Maksimum Bütçe'}),
            'priority': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'payment_type': forms.Select(attrs={'class': 'form-control'}),
            'meeting_result': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Görüşme Sonucu', 'rows': 4}),
            'meeting_status': forms.Select(attrs={'class': 'form-control'}),
            'response_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'Geri Dönüş Tarihi'}),
            'reminder_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'Hatırlatma Tarihi'}),
            'lead_notes': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Notlar', 'rows': 4}),
        }


class TaskForm(forms.ModelForm):
    """
    Görev oluşturma ve düzenleme formu
    """
    
    class Meta:
        model = Task
        fields = [
            'task_type', 'title', 'description', 'assigned_to',
            'priority', 'due_date'
        ]
        widgets = {
            'task_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }


class AppointmentForm(forms.ModelForm):
    """
    Randevu oluşturma ve düzenleme formu
    """
    
    class Meta:
        model = Appointment
        fields = [
            'appointment_type', 'title', 'description', 'scheduled_date',
            'duration_minutes', 'location', 'assigned_staff', 'property'
        ]
        widgets = {
            'appointment_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'scheduled_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'assigned_staff': forms.Select(attrs={'class': 'form-control'}),
            'property': forms.Select(attrs={'class': 'form-control'}),
        }


class LeadNoteForm(forms.ModelForm):
    """
    Lead notu ekleme formu
    """
    
    class Meta:
        model = LeadNote
        fields = ['note_type', 'title', 'content', 'is_important']
        widgets = {
            'note_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_important': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class WhatsAppMessageForm(forms.Form):
    """
    WhatsApp mesajı gönderme formu
    """
    
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Metin Mesajı'),
        ('template', 'Şablon Mesajı'),
    ]
    
    TEMPLATE_CHOICES = [
        ('', 'Şablon Seçin'),
        ('welcome', 'Hoş Geldin Mesajı'),
        ('appointment_reminder', 'Randevu Hatırlatması'),
        ('offer_sent', 'Teklif Gönderildi'),
        ('contract_ready', 'Sözleşme Hazır'),
        ('satisfaction_survey', 'Memnuniyet Anketi'),
    ]
    
    message_type = forms.ChoiceField(
        choices=MESSAGE_TYPE_CHOICES,
        initial='text',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'message_type'})
    )
    
    message = forms.CharField(
        label='Mesaj',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Mesajınızı yazın...'
        }),
        required=False
    )
    
    template_name = forms.ChoiceField(
        choices=TEMPLATE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'template_name'})
    )
    
    template_params = forms.CharField(
        label='Şablon Parametreleri (virgülle ayırın)',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'param1, param2, param3'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        message_type = cleaned_data.get('message_type')
        message = cleaned_data.get('message')
        template_name = cleaned_data.get('template_name')
        
        if message_type == 'text' and not message:
            raise ValidationError('Metin mesajı için mesaj içeriği gereklidir.')
        
        if message_type == 'template' and not template_name:
            raise ValidationError('Şablon mesajı için şablon seçimi gereklidir.')
        
        return cleaned_data
    
    def get_template_params_list(self):
        """Template parametrelerini liste olarak döndürür"""
        params = self.cleaned_data.get('template_params', '')
        if params:
            return [param.strip() for param in params.split(',') if param.strip()]
        return []


class LeadFilterForm(forms.Form):
    """
    Lead filtreleme formu
    """
    
    STATUS_CHOICES = [('', 'Tüm Durumlar')] + Lead.STATUS_CHOICES
    SOURCE_CHOICES = [('', 'Tüm Kaynaklar')] + Lead.SOURCE_CHOICES
    
    search = forms.CharField(
        label='Arama',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Müşteri adı, telefon veya e-posta...'
        })
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    source = forms.ChoiceField(
        choices=SOURCE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    assigned_staff = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        empty_label='Tüm Personel',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    priority_min = forms.IntegerField(
        label='Min Öncelik',
        required=False,
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    priority_max = forms.IntegerField(
        label='Max Öncelik',
        required=False,
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    created_from = forms.DateField(
        label='Başlangıç Tarihi',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    created_to = forms.DateField(
        label='Bitiş Tarihi',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            # Sadece staff kullanıcıları göster
            self.fields['assigned_staff'].queryset = User.objects.filter(
                is_staff=True,
                is_active=True
            ).order_by('first_name', 'last_name')


class BulkActionForm(forms.Form):
    """
    Toplu işlem formu
    """
    
    ACTION_CHOICES = [
        ('', 'İşlem Seçin'),
        ('assign_staff', 'Personel Ata'),
        ('change_stage', 'Aşama Değiştir'),
        ('change_priority', 'Öncelik Değiştir'),
        ('send_whatsapp', 'WhatsApp Gönder'),
        ('create_task', 'Görev Oluştur'),
        ('export', 'Dışa Aktar'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Personel atama için
    assigned_staff = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Aşama değiştirme için
    new_stage = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Öncelik değiştirme için
    new_priority = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    # WhatsApp mesajı için
    whatsapp_message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'WhatsApp mesajı...'
        })
    )
    
    # Görev oluşturma için
    task_title = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    task_description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2
        })
    )
    
    task_due_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            from django.contrib.auth.models import User
            from .models import SalesStage
            
            # Staff kullanıcıları
            self.fields['assigned_staff'].queryset = User.objects.filter(
                is_staff=True,
                is_active=True
            ).order_by('first_name', 'last_name')
            
            # Aktif aşamalar
            self.fields['new_stage'].queryset = SalesStage.objects.filter(
                is_active=True
            ).order_by('stage_type', 'order')


class StageTransitionForm(forms.Form):
    """
    Aşama geçiş formu
    """
    
    reason = forms.CharField(
        label='Geçiş Nedeni',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Aşama geçiş nedenini açıklayın...'
        })
    )
    
    create_note = forms.BooleanField(
        label='Otomatik not oluştur',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )