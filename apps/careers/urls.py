# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Kariyer URLs
"""

from django.urls import path
from . import views

app_name = 'careers-views'

urlpatterns = [
    # API Endpoints (api/ prefix ana URLs'de zaten var)
    path('applications/', views.JobApplicationCreateAPIView.as_view(), name='api-application-create'),
    path('applications/choices/', views.job_application_choices, name='api-application-choices'),
    path('admin/applications/', views.JobApplicationListAPIView.as_view(), name='api-admin-application-list'),
    path('admin/applications/<int:id>/', views.JobApplicationDetailAPIView.as_view(), name='api-admin-application-detail'),
    path('admin/applications/stats/', views.job_application_stats, name='api-admin-application-stats'),
    
    # Template Views (admin paneli için) - careers/ prefix ile
    path('', views.application_list, name='application_list'),
    path('<int:pk>/', views.application_detail, name='application_detail'),
] 