# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - API Serializers
"""

from rest_framework import serializers
from django.conf import settings
from apps.portfolio.models import Property, PropertyImage, PropertyEnvironment
from apps.fsbo.models import FSBO
from apps.customers.models import Neighborhood
from apps.careers.models import JobApplication
from django.utils import timezone
from datetime import datetime


def get_full_image_url(image_url):
    """Image URL'ini tam URL'e çevirir"""
    if not image_url:
        return None
    
    if image_url.startswith('http'):
        return image_url
    
    # Production domain'i kullan
    base_url = 'https://panelkocgayrimenkul.com'
    return base_url + image_url


class NeighborhoodSerializer(serializers.ModelSerializer):
    """Mahalle serializer"""
    district_name = serializers.CharField(source='district.name', read_only=True)
    city_name = serializers.CharField(source='district.city.name', read_only=True)
    
    class Meta:
        model = Neighborhood
        fields = ['id', 'name', 'district_name', 'city_name']


class PropertyImageSerializer(serializers.ModelSerializer):
    """Gayrimenkul görseli serializer"""
    image_url = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()  # Frontend için 'image' alanı
    
    def get_image_url(self, obj):
        if obj.image:
            return get_full_image_url(obj.image.url)
        return None
    
    def get_image(self, obj):
        """Frontend 'image' alanını bekliyor, bu yüzden image_url ile aynı değeri döndürüyoruz"""
        return self.get_image_url(obj)
    
    class Meta:
        model = PropertyImage
        fields = ['id', 'title', 'image_url', 'image', 'order']


class PropertyEnvironmentSerializer(serializers.ModelSerializer):
    """Gayrimenkul çevresi serializer"""
    
    class Meta:
        model = PropertyEnvironment
        fields = ['id', 'place_name', 'distance']


class PropertyListSerializer(serializers.ModelSerializer):
    """Gayrimenkul liste serializer (özet bilgiler için)"""
    neighborhood = NeighborhoodSerializer(read_only=True)
    main_image = serializers.SerializerMethodField()
    consultant_name = serializers.CharField(source='consultant.get_full_name', read_only=True)
    bathrooms = serializers.IntegerField(source='bathroom_count', read_only=True)
    badges = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    date_display = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()  # Web title varsa onu, yoksa apartment_name'i döndür
    
    def get_title(self, obj):
        """Web title varsa onu döndür, yoksa apartment_name'i kullan"""
        return obj.web_title if obj.web_title else obj.apartment_name
    
    def get_main_image(self, obj):
        main_image = obj.images.order_by('order').first()
        if main_image and main_image.image:
            return get_full_image_url(main_image.image.url)
        return None
    
    def get_badges(self, obj):
        """Gayrimenkul için dinamik badges oluştur"""
        badges = []
        
        # Öne çıkan ilan
        if obj.is_featured:
            badges.append("Öne Çıkan")
        
        # İlan türü
        if obj.listing_type:
            listing_type_display = dict(obj.LISTING_TYPE_CHOICES).get(obj.listing_type, obj.listing_type)
            if listing_type_display and listing_type_display != 'Normal':
                badges.append(listing_type_display)
        
        # Krediye uygun
        if obj.is_suitable_for_credit:
            badges.append("Krediye Uygun")
        
        # Pazarlıklı
        if obj.is_bargainable:
            badges.append("Pazarlıklı")
        
        # Eşyalı
        if obj.is_furnished:
            badges.append("Eşyalı")
        
        # Site içerisinde
        if obj.is_in_site:
            badges.append("Site İçinde")
        
        # Takas
        if obj.is_exchangeable:
            badges.append("Takas")
        
        return badges
    
    def get_features(self, obj):
        """Gayrimenkul için özellik listesi oluştur"""
        features = []
        
        # Balkon
        if obj.has_balcony:
            features.append("Balkon")
        
        # Isıtma sistemi
        if obj.heating:
            heating_display = dict(obj.HEATING_CHOICES).get(obj.heating, obj.heating)
            if heating_display:
                features.append(f"Isıtma: {heating_display}")
        
        # Kat bilgisi
        if obj.floor:
            features.append(f"Kat: {obj.floor}")
        
        # Bina yaşı
        if obj.building_age:
            features.append(f"Bina Yaşı: {obj.building_age}")
        
        # Alan bilgisi
        if obj.gross_area:
            features.append(f"{obj.gross_area} m²")
        
        return features
    
    def get_date_display(self, obj):
        """Tarih gösterimi (kaç gün önce)"""
        now = timezone.now()
        created_date = obj.created_at
        
        # Gün farkını hesapla
        diff = now - created_date
        days = diff.days
        
        if days == 0:
            return "Bugün"
        elif days == 1:
            return "1 gün önce"
        elif days < 7:
            return f"{days} gün önce"
        elif days < 30:
            weeks = days // 7
            return f"{weeks} hafta önce"
        elif days < 365:
            months = days // 30
            return f"{months} ay önce"
        else:
            years = days // 365
            return f"{years} yıl önce"
    
    class Meta:
        model = Property
        fields = [
            'id', 'title', 'apartment_name', 'web_title', 'property_type', 'status', 'price',
            'neighborhood', 'gross_area', 'net_area', 'room_count', 
            'floor', 'building_age', 'bathrooms', 'main_image', 'consultant_name',
            'listing_date', 'created_at', 'category', 'listing_type', 'is_featured',
            'badges', 'features', 'date_display', 'description', 'address',
            'has_balcony', 'heating', 'dues', 'floor_count', 'deed_status'
        ]


class PropertyDetailSerializer(serializers.ModelSerializer):
    """Gayrimenkul detay serializer (tüm bilgiler için)"""
    neighborhood = NeighborhoodSerializer(read_only=True)
    images = PropertyImageSerializer(many=True, read_only=True)
    environments = PropertyEnvironmentSerializer(many=True, read_only=True)
    consultant_name = serializers.CharField(source='consultant.get_full_name', read_only=True)
    consultant_phone = serializers.SerializerMethodField()
    consultant_email = serializers.SerializerMethodField()
    consultant_photo = serializers.SerializerMethodField()
    
    # Frontend için ek alanlar
    main_image = serializers.SerializerMethodField()
    bathrooms = serializers.IntegerField(source='bathroom_count', read_only=True)
    badges = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    date_display = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    map_url = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()  # Web title varsa onu, yoksa apartment_name'i döndür
    
    def get_title(self, obj):
        """Web title varsa onu döndür, yoksa apartment_name'i kullan"""
        return obj.web_title if obj.web_title else obj.apartment_name
    
    def get_consultant_phone(self, obj):
        """Danışman telefonu - mevcut değilse owner_phone kullan"""
        if obj.consultant and hasattr(obj.consultant, 'phone') and obj.consultant.phone:
            return obj.consultant.phone
        return obj.owner_phone if obj.owner_phone else None
    
    def get_consultant_email(self, obj):
        """Danışman email - mevcut değilse None"""
        if obj.consultant and hasattr(obj.consultant, 'email'):
            return obj.consultant.email
        return None
    
    def get_consultant_photo(self, obj):
        """Danışman fotoğrafı - şimdilik None"""
        return None
    
    def get_main_image(self, obj):
        """Ana resim - ilk sıradaki resim"""
        main_image = obj.images.order_by('order').first()
        if main_image and main_image.image:
            return get_full_image_url(main_image.image.url)
        return None
    
    def get_badges(self, obj):
        """Gayrimenkul için dinamik badges oluştur"""
        badges = []
        
        # Öne çıkan ilan
        if obj.is_featured:
            badges.append("Öne Çıkan")
        
        # İlan türü
        if obj.listing_type:
            listing_type_display = dict(obj.LISTING_TYPE_CHOICES).get(obj.listing_type, obj.listing_type)
            if listing_type_display and listing_type_display != 'Normal':
                badges.append(listing_type_display)
        
        # Krediye uygun
        if obj.is_suitable_for_credit:
            badges.append("Krediye Uygun")
        
        # Pazarlıklı
        if obj.is_bargainable:
            badges.append("Pazarlıklı")
        
        # Eşyalı
        if obj.is_furnished:
            badges.append("Eşyalı")
        
        # Site içerisinde
        if obj.is_in_site:
            badges.append("Site İçinde")
        
        # Takas
        if obj.is_exchangeable:
            badges.append("Takas")
        
        return badges
    
    def get_features(self, obj):
        """Gayrimenkul için özellik listesi oluştur"""
        features = []
        
        # Balkon
        if obj.has_balcony:
            features.append("Balkon")
        
        # Isıtma sistemi
        if obj.heating:
            heating_display = dict(obj.HEATING_CHOICES).get(obj.heating, obj.heating)
            if heating_display:
                features.append(f"Isıtma: {heating_display}")
        
        # Kat bilgisi
        if obj.floor:
            features.append(f"Kat: {obj.floor}")
        
        # Bina yaşı
        if obj.building_age:
            features.append(f"Bina Yaşı: {obj.building_age}")
        
        # Alan bilgisi
        if obj.gross_area:
            features.append(f"{obj.gross_area} m²")
        
        # Banyo sayısı
        if obj.bathroom_count:
            features.append(f"{obj.bathroom_count} Banyo")
        
        # Eşyalı
        if obj.is_furnished:
            features.append("Eşyalı")
        
        # Site içinde
        if obj.is_in_site:
            features.append("Site İçinde")
        
        return features
    
    def get_date_display(self, obj):
        """Tarih gösterimi (kaç gün önce)"""
        now = timezone.now()
        created_date = obj.created_at
        
        # Gün farkını hesapla
        diff = now - created_date
        days = diff.days
        
        if days == 0:
            return "Bugün"
        elif days == 1:
            return "1 gün önce"
        elif days < 7:
            return f"{days} gün önce"
        elif days < 30:
            weeks = days // 7
            return f"{weeks} hafta önce"
        elif days < 365:
            months = days // 30
            return f"{months} ay önce"
        else:
            years = days // 365
            return f"{years} yıl önce"
    
    def get_video_url(self, obj):
        """Video URL - şimdilik None"""
        return None
    
    def get_map_url(self, obj):
        """Harita embed URL - map_coordinates varsa Google Maps embed URL'i oluştur"""
        if obj.map_coordinates:
            # map_coordinates formatı: "lat,lng" olduğunu varsayıyoruz
            return f"https://maps.google.com/maps?q={obj.map_coordinates}&output=embed"
        return None
    
    class Meta:
        model = Property
        fields = [
            'id', 'title', 'apartment_name', 'web_title', 'description', 'property_type', 'status', 'price',
            'neighborhood', 'address', 'map_coordinates',
            'gross_area', 'net_area', 'room_count', 'floor', 'floor_count',
            'building_age', 'heating', 'has_balcony', 'dues', 'bathroom_count', 'bathrooms',
            'usage_status', 'is_furnished', 'is_in_site', 'is_exchangeable',
            'category', 'listing_type', 'deed_status', 'is_suitable_for_credit',
            'is_bargainable', 'owner_name', 'owner_phone', 'key_holder',
            'photo_status', 'banner_status', 'listing_date', 'consultant_name',
            'consultant_phone', 'consultant_email', 'consultant_photo',
            'created_at', 'updated_at', 'is_active', 'is_featured',
            'images', 'environments', 'main_image', 'badges', 'features', 
            'date_display', 'video_url', 'map_url',
            # Modelde bulunan eksik alanlar
            'owner_listing_number', 'emlakjet_listing_number', 'hepsiemlak_listing_number',
            'website_listing_number', 'branda_number'
        ]


class FSBOSerializer(serializers.ModelSerializer):
    """FSBO serializer"""
    consultant_name = serializers.CharField(source='consultant.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = FSBO
        fields = [
            'id', 'full_name', 'phone', 'result', 'consultant', 'consultant_name',
            'created_by_name', 'link1', 'link2', 'reminder_status', 
            'reminder_date', 'reminder_time', 'notes', 'created_at'
        ]


# Careers Serializers
class JobApplicationSerializer(serializers.ModelSerializer):
    """İş Başvurusu Serializer"""
    cv_filename = serializers.CharField(read_only=True)
    position_display = serializers.CharField(source='get_position_display', read_only=True)
    experience_display = serializers.CharField(source='get_experience_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = JobApplication
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone',
            'position', 'position_display', 'experience', 'experience_display',
            'cover_letter', 'cv_file', 'cv_filename', 'status', 'status_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']
    
    def validate_cv_file(self, value):
        """CV dosya formatı kontrolü"""
        if value:
            valid_extensions = ['pdf', 'doc', 'docx']
            file_extension = value.name.split('.')[-1].lower()
            if file_extension not in valid_extensions:
                raise serializers.ValidationError(
                    "CV dosyası PDF, DOC veya DOCX formatında olmalıdır."
                )
            
            # Dosya boyutu kontrolü (max 5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError(
                    "CV dosyası 5MB'dan büyük olamaz."
                )
        
        return value 