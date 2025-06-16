# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Kariyer URLs
"""

from django.urls import path
from . import views

app_name = 'careers'

urlpatterns = [
    # İş İlanları
    path('jobs/', views.JobPostingListAPIView.as_view(), name='job-list'),
    path('jobs/<int:id>/', views.JobPostingDetailAPIView.as_view(), name='job-detail'),
    
    # İş Başvuruları
    path('applications/', views.JobApplicationCreateAPIView.as_view(), name='application-create'),
    path('applications/choices/', views.job_application_choices, name='application-choices'),
    
    # Admin İş Başvuru Yönetimi
    path('admin/applications/', views.JobApplicationListAPIView.as_view(), name='admin-application-list'),
    path('admin/applications/<int:id>/', views.JobApplicationDetailAPIView.as_view(), name='admin-application-detail'),
    path('admin/applications/stats/', views.job_application_stats, name='admin-application-stats'),
] 