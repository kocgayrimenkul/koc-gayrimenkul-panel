# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - İletişim Serializers
"""

from rest_framework import serializers
from .models import ContactMessage


class ContactMessageSerializer(serializers.ModelSerializer):
    """İletişim mesajı serializer"""
    
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'property_type', 'message']
    
    def validate_email(self, value):
        """E-posta doğrulama"""
        if not value:
            raise serializers.ValidationError("E-posta adresi gereklidir.")
        return value.lower()
    
    def validate_name(self, value):
        """İsim doğrulama"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Ad en az 2 karakter olmalıdır.")
        return value.title()
    
    def validate_message(self, value):
        """Mesaj doğrulama"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Mesaj en az 10 karakter olmalıdır.")
        return value


class ContactMessageListSerializer(serializers.ModelSerializer):
    """İletişim mesajı listeleme serializer (admin için)"""
    
    property_type_display = serializers.CharField(source='get_property_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ContactMessage
        fields = [
            'id', 'name', 'email', 'phone', 'property_type', 'property_type_display',
            'message', 'status', 'status_display', 'created_at'
        ]
        read_only_fields = ['id', 'created_at'] 