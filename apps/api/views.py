# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - API Views
"""

from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from apps.portfolio.models import Property, PropertyImage
from apps.fsbo.models import FSBO
from apps.customers.models import Neighborhood

from .serializers import (
    PropertyListSerializer, 
    PropertyDetailSerializer,
    NeighborhoodSerializer,
    FSBOSerializer
)


class PropertyListAPIView(generics.ListAPIView):
    """Gayrimenkul listesi API"""
    queryset = Property.objects.filter(is_active=True).select_related('neighborhood', 'consultant').prefetch_related('images')
    serializer_class = PropertyListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filtreleme alanları
    filterset_fields = {
        'property_type': ['exact'],
        'status': ['exact'],
        'price': ['gte', 'lte'],
        'room_count': ['exact'],
        'neighborhood': ['exact'],
        'gross_area': ['gte', 'lte'],
        'net_area': ['gte', 'lte'],
        'building_age': ['gte', 'lte'],
        'heating': ['exact'],
        'has_balcony': ['exact'],
        'is_furnished': ['exact'],
        'is_in_site': ['exact'],
        'category': ['exact'],
        'listing_type': ['exact'],
        'is_suitable_for_credit': ['exact'],
        'is_featured': ['exact'],
    }
    
    # Arama alanları
    search_fields = ['apartment_name', 'description', 'address', 'neighborhood__name']
    
    # Sıralama alanları
    ordering_fields = ['price', 'created_at', 'listing_date', 'gross_area', 'net_area']
    ordering = ['-created_at']


class FeaturedPropertyListAPIView(generics.ListAPIView):
    """Öne çıkan gayrimenkul listesi API"""
    queryset = Property.objects.filter(is_active=True, is_featured=True).select_related('neighborhood', 'consultant').prefetch_related('images')
    serializer_class = PropertyListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filtreleme alanları
    filterset_fields = {
        'property_type': ['exact'],
        'status': ['exact'],
        'price': ['gte', 'lte'],
        'room_count': ['exact'],
        'neighborhood': ['exact'],
        'gross_area': ['gte', 'lte'],
        'net_area': ['gte', 'lte'],
        'building_age': ['gte', 'lte'],
        'heating': ['exact'],
        'has_balcony': ['exact'],
        'is_furnished': ['exact'],
        'is_in_site': ['exact'],
        'category': ['exact'],
        'listing_type': ['exact'],
        'is_suitable_for_credit': ['exact'],
        'is_featured': ['exact'],
    }
    
    # Arama alanları
    search_fields = ['apartment_name', 'description', 'address', 'neighborhood__name']
    
    # Sıralama alanları
    ordering_fields = ['price', 'created_at', 'listing_date', 'gross_area', 'net_area']
    ordering = ['-created_at']


class PropertyDetailAPIView(generics.RetrieveAPIView):
    """Gayrimenkul detay API"""
    queryset = Property.objects.filter(is_active=True).select_related('neighborhood', 'consultant').prefetch_related('images', 'environments')
    serializer_class = PropertyDetailSerializer
    lookup_field = 'id'


class NeighborhoodListAPIView(generics.ListAPIView):
    """Mahalle listesi API"""
    queryset = Neighborhood.objects.all()
    serializer_class = NeighborhoodSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['district']
    search_fields = ['name', 'district']


class FSBOListAPIView(generics.ListAPIView):
    """FSBO listesi API"""
    queryset = FSBO.objects.select_related('consultant', 'created_by').all()
    serializer_class = FSBOSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['result', 'consultant', 'reminder_status']
    search_fields = ['full_name', 'phone', 'notes']
    ordering_fields = ['created_at']
    ordering = ['-created_at']


@api_view(['GET'])
def property_stats_api(request):
    """Gayrimenkul istatistikleri API"""
    total_properties = Property.objects.filter(is_active=True).count()
    for_sale = Property.objects.filter(is_active=True, status='satilik').count()
    for_rent = Property.objects.filter(is_active=True, status='kiralik').count()
    
    property_types = Property.objects.filter(is_active=True).values('property_type').distinct()
    type_counts = {}
    for prop_type in property_types:
        type_name = prop_type['property_type']
        count = Property.objects.filter(is_active=True, property_type=type_name).count()
        type_counts[type_name] = count
    
    data = {
        'total_properties': total_properties,
        'for_sale': for_sale,
        'for_rent': for_rent,
        'property_types': type_counts
    }
    
    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
def property_search_api(request):
    """Gelişmiş gayrimenkul arama API"""
    queryset = Property.objects.filter(is_active=True).select_related('neighborhood', 'consultant').prefetch_related('images')
    
    # Fiyat aralığı
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        queryset = queryset.filter(price__gte=min_price)
    if max_price:
        queryset = queryset.filter(price__lte=max_price)
    
    # Alan aralığı
    min_area = request.GET.get('min_area')
    max_area = request.GET.get('max_area')
    if min_area:
        queryset = queryset.filter(gross_area__gte=min_area)
    if max_area:
        queryset = queryset.filter(gross_area__lte=max_area)
    
    # Şehir ve ilçe
    city = request.GET.get('city')
    district = request.GET.get('district')
    if district:
        queryset = queryset.filter(neighborhood__district__icontains=district)
    
    # Oda sayısı (örn: "2+1,3+1" formatında)
    room_counts = request.GET.get('room_counts')
    if room_counts:
        room_list = room_counts.split(',')
        queryset = queryset.filter(room_count__in=room_list)
    
    # Emlak tipi
    property_types = request.GET.get('property_types')
    if property_types:
        type_list = property_types.split(',')
        queryset = queryset.filter(property_type__in=type_list)
    
    # Metin arama
    search = request.GET.get('search')
    if search:
        queryset = queryset.filter(
            Q(apartment_name__icontains=search) |
            Q(description__icontains=search) |
            Q(address__icontains=search) |
            Q(neighborhood__name__icontains=search)
        )
    
    # Sıralama
    ordering = request.GET.get('ordering', '-created_at')
    queryset = queryset.order_by(ordering)
    
    # Sayfalama
    page_size = int(request.GET.get('page_size', 20))
    page = int(request.GET.get('page', 1))
    start = (page - 1) * page_size
    end = start + page_size
    
    total_count = queryset.count()
    results = queryset[start:end]
    
    serializer = PropertyListSerializer(results, many=True, context={'request': request})
    
    data = {
        'count': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': (total_count + page_size - 1) // page_size,
        'results': serializer.data
    }
    
    return Response(data, status=status.HTTP_200_OK) 