# apps/home/urls.py
from django.urls import path, re_path
from apps.home import views

urlpatterns = [
    # Dashboard
    path('', views.index, name='dashboard'),
    
    # Harita ve Analizler
    path('map/', views.map_view, name='map'),
    path('consultant-performance/', views.consultant_performance, name='consultant_performance'),
    path('neighborhood-analytics/', views.neighborhood_analytics, name='neighborhood_analytics'),
    path('dashboard-stats/', views.dashboard_stats_api, name='dashboard_stats'),
    
    # Müşteri İşlemleri - KALDIRILDI (apps.customers'ta var)
    # path('customer/create/', views.customer_create, name='customer_create'),
    # path('customer/list/', views.customer_list, name='customer_list'),
    # path('customer/<int:pk>/', views.customer_detail, name='customer_detail'),
    # path('customer/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    # path('customer/<int:pk>/delete/', views.customer_delete, name='customer_delete'),
    
    # Emlak İşlemleri - KALDIRILDI (apps.portfolio'da var)
    # path('property/create/', views.property_create, name='property_create'),
    # path('property/list/', views.property_list, name='property_list'),
    # path('property/<int:pk>/', views.property_detail, name='property_detail'),
    # path('property/<int:pk>/edit/', views.property_edit, name='property_edit'),
    # path('property/<int:pk>/delete/', views.property_delete, name='property_delete'),
    
    # Sunum İşlemleri - KALDIRILDI (apps.presentation'da var)
    # path('presentation/create/', views.presentation_create, name='presentation_create'),
    # path('presentation/list/', views.presentation_list, name='presentation_list'),
    # path('presentation/<int:pk>/edit/', views.presentation_edit, name='presentation_edit'),
    # path('presentation/<int:pk>/delete/', views.presentation_delete, name='presentation_delete'),
    
    # Wildcard - GEÇİCİ KAPALI (500 hatalarına neden oluyor)
    # re_path(r'^.*\.*', views.pages, name='pages'),
]