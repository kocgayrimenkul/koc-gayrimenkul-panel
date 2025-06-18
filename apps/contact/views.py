# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - İletişim Views
"""

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.throttling import AnonRateThrottle
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from .models import ContactMessage
from .serializers import ContactMessageSerializer, ContactMessageListSerializer


class ContactMessageCreateView(generics.CreateAPIView):
    """İletişim mesajı oluşturma view (herkese açık)"""
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]
    
    def perform_create(self, serializer):
        """Mesaj kaydedilirken çalışır"""
        message = serializer.save()
        
        # E-posta bildirimi gönder (opsiyonel)
        try:
            self.send_notification_email(message)
        except Exception as e:
            print(f"E-posta gönderimi başarısız: {e}")
    
    def send_notification_email(self, message):
        """Yeni mesaj bildirimi gönder"""
        subject = f"Yeni İletişim Mesajı - {message.name}"
        email_message = f"""
        Yeni bir iletişim mesajı alındı:
        
        Ad: {message.name}
        E-posta: {message.email}
        Telefon: {message.phone or 'Belirtilmemiş'}
        Gayrimenkul Tercihi: {message.get_property_type_display() or 'Belirtilmemiş'}
        
        Mesaj:
        {message.message}
        
        Tarih: {message.created_at.strftime('%d.%m.%Y %H:%M')}
        """
        
        # Admin e-posta adresi varsa gönder
        if hasattr(settings, 'ADMIN_EMAIL'):
            send_mail(
                subject,
                email_message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],
                fail_silently=True,
            )


class ContactMessageListView(generics.ListAPIView):
    """İletişim mesajları listeleme view (admin için)"""
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageListSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtreleme parametreleri
        status_filter = self.request.query_params.get('status')
        property_type = self.request.query_params.get('property_type')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if property_type:
            queryset = queryset.filter(property_type=property_type)
        
        return queryset.order_by('-created_at')


class ContactMessageDetailView(generics.RetrieveUpdateAPIView):
    """İletişim mesajı detay ve güncelleme view (admin için)"""
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageListSerializer
    permission_classes = [IsAdminUser]
    
    def update(self, request, *args, **kwargs):
        """Mesaj güncellenirken sadece durum güncellenebilir"""
        instance = self.get_object()
        
        # Sadece durum güncellenebilir
        if 'status' in request.data:
            instance.status = request.data['status']
            instance.save()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


# Template-based Views (sadece listeleme ve detay)
@login_required
def contact_list(request):
    """İletişim listesi view"""
    # Filtreleme parametreleri
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    property_type_filter = request.GET.get('property_type', '')
    date_range = request.GET.get('date_range', '')
    
    # Base queryset
    contacts = ContactMessage.objects.all()
    
    # Arama filtresi
    if search:
        contacts = contacts.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search) |
            Q(message__icontains=search)
        )
    
    # Durum filtresi
    if status_filter:
        contacts = contacts.filter(status=status_filter)
    
    # Gayrimenkul türü filtresi
    if property_type_filter:
        contacts = contacts.filter(property_type=property_type_filter)
    
    # Tarih aralığı filtresi
    if date_range:
        today = timezone.now().date()
        if date_range == 'today':
            contacts = contacts.filter(created_at__date=today)
        elif date_range == 'week':
            week_ago = today - timedelta(days=7)
            contacts = contacts.filter(created_at__date__gte=week_ago)
        elif date_range == 'month':
            month_ago = today - timedelta(days=30)
            contacts = contacts.filter(created_at__date__gte=month_ago)
    
    # Sıralama
    contacts = contacts.order_by('-created_at')
    
    # Sayfalama
    paginator = Paginator(contacts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # İstatistikler
    total_contacts = ContactMessage.objects.count()
    new_contacts = ContactMessage.objects.filter(status='yeni').count()
    pending_contacts = ContactMessage.objects.filter(status='okundu').count()
    this_month_contacts = ContactMessage.objects.filter(
        created_at__date__gte=timezone.now().date() - timedelta(days=30)
    ).count()
    
    context = {
        'contacts': page_obj,
        'total_contacts': total_contacts,
        'active_contacts': new_contacts,
        'pending_contacts': pending_contacts,
        'this_month_contacts': this_month_contacts,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    }
    
    return render(request, 'contacts/contact_list.html', context)


@login_required
def contact_detail(request, pk):
    """İletişim detay view (sadece görüntüleme)"""
    contact = get_object_or_404(ContactMessage, pk=pk)
    
    context = {
        'contact': contact,
    }
    
    return render(request, 'contacts/contact_detail.html', context)
