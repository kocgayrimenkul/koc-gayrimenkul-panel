# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Kariyer Views
"""

from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.core.mail import send_mail
from django.conf import settings

from .models import JobApplication, JobPosting
from .serializers import (
    JobApplicationSerializer, 
    JobApplicationListSerializer,
    JobPostingSerializer,
    JobPostingListSerializer
)


class JobPostingListAPIView(generics.ListAPIView):
    """Aktif İş İlanları Listesi (Herkese Açık)"""
    queryset = JobPosting.objects.filter(is_active=True)
    serializer_class = JobPostingListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['department', 'employment_type', 'location']
    search_fields = ['title', 'description', 'requirements']
    ordering_fields = ['created_at', 'deadline']
    ordering = ['-created_at']


class JobPostingDetailAPIView(generics.RetrieveAPIView):
    """İş İlanı Detayı (Herkese Açık)"""
    queryset = JobPosting.objects.filter(is_active=True)
    serializer_class = JobPostingSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'


class JobApplicationCreateAPIView(generics.CreateAPIView):
    """İş Başvurusu Oluşturma (Herkese Açık)"""
    queryset = JobApplication.objects.all()
    serializer_class = JobApplicationSerializer
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    
    def perform_create(self, serializer):
        # Başvuruyu kaydet
        application = serializer.save()
        
        # E-posta bildirimi gönder (İsteğe bağlı)
        try:
            self.send_application_notification(application)
        except Exception as e:
            # E-posta gönderilmezse hata verme, sadece log'la
            print(f"E-posta gönderilemedi: {e}")
    
    def send_application_notification(self, application):
        """Başvuru bildirimi e-postası gönder"""
        subject = f"Yeni İş Başvurusu: {application.get_position_display()}"
        message = f"""
        Yeni bir iş başvurusu alındı:
        
        Ad Soyad: {application.full_name}
        E-posta: {application.email}
        Telefon: {application.phone}
        Pozisyon: {application.get_position_display()}
        Deneyim: {application.get_experience_display()}
        
        Başvuru Tarihi: {application.created_at.strftime('%d.%m.%Y %H:%M')}
        
        Admin panelinden detayları görüntüleyebilirsiniz.
        """
        
        # E-posta ayarları varsa gönder
        if hasattr(settings, 'EMAIL_HOST') and settings.EMAIL_HOST:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['hr@kocgayrimenkul.com'],  # İK e-posta adresi
                fail_silently=True
            )


class JobApplicationListAPIView(generics.ListAPIView):
    """İş Başvuruları Listesi (Admin)"""
    queryset = JobApplication.objects.all()
    serializer_class = JobApplicationListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['position', 'experience', 'status']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


class JobApplicationDetailAPIView(generics.RetrieveUpdateAPIView):
    """İş Başvurusu Detayı ve Güncelleme (Admin)"""
    queryset = JobApplication.objects.all()
    serializer_class = JobApplicationSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'


@api_view(['GET'])
@permission_classes([AllowAny])
def job_application_choices(request):
    """İş başvuru formu için seçenekler"""
    data = {
        'positions': [
            {'value': choice[0], 'label': choice[1]} 
            for choice in JobApplication.POSITION_CHOICES
        ],
        'experience_levels': [
            {'value': choice[0], 'label': choice[1]} 
            for choice in JobApplication.EXPERIENCE_CHOICES
        ]
    }
    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def job_application_stats(request):
    """İş başvuru istatistikleri (Admin)"""
    total_applications = JobApplication.objects.count()
    new_applications = JobApplication.objects.filter(status='yeni').count()
    in_review = JobApplication.objects.filter(status='inceleniyor').count()
    interviews = JobApplication.objects.filter(status='mulakat').count()
    approved = JobApplication.objects.filter(status='onaylandi').count()
    rejected = JobApplication.objects.filter(status='reddedildi').count()
    
    # Pozisyona göre başvuru sayıları
    position_stats = {}
    for position_code, position_name in JobApplication.POSITION_CHOICES:
        count = JobApplication.objects.filter(position=position_code).count()
        position_stats[position_name] = count
    
    data = {
        'total_applications': total_applications,
        'status_breakdown': {
            'new': new_applications,
            'in_review': in_review,
            'interviews': interviews,
            'approved': approved,
            'rejected': rejected
        },
        'position_stats': position_stats
    }
    
    return Response(data, status=status.HTTP_200_OK)
