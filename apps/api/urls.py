# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - API URLs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    PropertyListAPIView,
    PropertyDetailAPIView,
    FeaturedPropertyListAPIView,
    NeighborhoodListAPIView,
    FSBOListAPIView,
    property_stats_api,
    property_search_api
)

app_name = 'api'

urlpatterns = [
    # Gayrimenkul API'leri
    path('properties/', PropertyListAPIView.as_view(), name='property-list'),
    path('properties/featured/', FeaturedPropertyListAPIView.as_view(), name='featured-properties'),
    path('properties/<int:id>/', PropertyDetailAPIView.as_view(), name='property-detail'),
    path('properties/search/', property_search_api, name='property-search'),
    path('properties/stats/', property_stats_api, name='property-stats'),
    
    # Mahalle API'leri
    path('neighborhoods/', NeighborhoodListAPIView.as_view(), name='neighborhood-list'),
    
    # FSBO API'leri
    path('fsbo/', FSBOListAPIView.as_view(), name='fsbo-list'),
    
    # DRF Auth API'leri
    path('auth/', include('rest_framework.urls')),
] 