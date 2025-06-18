# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Kariyer URLs
"""

from django.urls import path
from . import views

app_name = 'careers'

urlpatterns = [
    # API Endpoints
    path('api/applications/', views.JobApplicationCreateAPIView.as_view(), name='api-application-create'),
    path('api/applications/choices/', views.job_application_choices, name='api-application-choices'),
    path('api/admin/applications/', views.JobApplicationListAPIView.as_view(), name='api-admin-application-list'),
    path('api/admin/applications/<int:id>/', views.JobApplicationDetailAPIView.as_view(), name='api-admin-application-detail'),
    path('api/admin/applications/stats/', views.job_application_stats, name='api-admin-application-stats'),
    
    # Template Views (admin paneli için)
    path('', views.application_list, name='application_list'),
    path('<int:pk>/', views.application_detail, name='application_detail'),
] 