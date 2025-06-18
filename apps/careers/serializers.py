# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Kariyer Serializers
"""

from rest_framework import serializers
from .models import JobApplication
from django.core.validators import FileExtensionValidator


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
    
    def validate_email(self, value):
        """E-posta tekrar kontrolü (aynı pozisyona aynı email ile başvuru engelleme)"""
        if self.instance is None:  # Yeni kayıt
            request = self.context.get('request')
            if request and request.data.get('position'):
                position = request.data.get('position')
                if JobApplication.objects.filter(email=value, position=position).exists():
                    raise serializers.ValidationError(
                        "Bu pozisyon için daha önce başvuru yapmışsınız."
                    )
        return value


class JobApplicationListSerializer(serializers.ModelSerializer):
    """İş Başvurusu Liste Serializer (admin için)"""
    full_name = serializers.CharField(read_only=True)
    position_display = serializers.CharField(source='get_position_display', read_only=True)
    experience_display = serializers.CharField(source='get_experience_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    cv_filename = serializers.CharField(read_only=True)
    
    class Meta:
        model = JobApplication
        fields = [
            'id', 'full_name', 'email', 'phone',
            'position_display', 'experience_display', 'status_display',
            'cv_filename', 'created_at'
        ] 