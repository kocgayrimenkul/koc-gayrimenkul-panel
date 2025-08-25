# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Çalışan Yönetimi Serializers
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import EmployeeProfile, Position, Permission

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Kullanıcı serializer"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id', 'username']

class PositionSerializer(serializers.ModelSerializer):
    """Pozisyon serializer"""
    class Meta:
        model = Position
        fields = ['id', 'name']

class EmployeeProfileSerializer(serializers.ModelSerializer):
    """Çalışan profil serializer"""
    user = UserSerializer(read_only=True)
    position = PositionSerializer(read_only=True)
    position_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = EmployeeProfile
        fields = [
            'id', 'user', 'phone', 'position', 'position_id', 
            'role', 'extension_number', 'is_active'
        ]
        read_only_fields = ['id', 'user']
    
    def validate_extension_number(self, value):
        """Extension numarası validasyonu"""
        if value:
            # Sadece rakam olmalı
            if not value.isdigit():
                raise serializers.ValidationError("Dahili numara sadece rakamlardan oluşmalıdır.")
            
            # 3-4 haneli olmalı (101-9999 arası)
            if len(value) < 3 or len(value) > 4:
                raise serializers.ValidationError("Dahili numara 3-4 haneli olmalıdır.")
            
            # Unique kontrolü (mevcut kayıt hariç)
            queryset = EmployeeProfile.objects.filter(extension_number=value)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise serializers.ValidationError("Bu dahili numara zaten kullanılıyor.")
        
        return value

class ExtensionUpdateSerializer(serializers.Serializer):
    """Extension güncelleme için özel serializer"""
    extension_number = serializers.CharField(
        max_length=10, 
        required=True,
        help_text="Netgsm santral dahili numarası (örn: 101, 102, 103, 104)"
    )
    
    def validate_extension_number(self, value):
        """Extension numarası validasyonu"""
        if not value:
            raise serializers.ValidationError("Dahili numara boş olamaz.")
        
        # Sadece rakam olmalı
        if not value.isdigit():
            raise serializers.ValidationError("Dahili numara sadece rakamlardan oluşmalıdır.")
        
        # 3-4 haneli olmalı (101-9999 arası)
        if len(value) < 3 or len(value) > 4:
            raise serializers.ValidationError("Dahili numara 3-4 haneli olmalıdır.")
        
        # Unique kontrolü
        if EmployeeProfile.objects.filter(extension_number=value).exists():
            raise serializers.ValidationError("Bu dahili numara zaten kullanılıyor.")
        
        return value