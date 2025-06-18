# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Team Serializers
"""

from rest_framework import serializers
from .models import TeamMember


def get_full_image_url(image_url):
    """Image URL'ini tam URL'e çevirir"""
    if not image_url:
        return None
    
    if image_url.startswith('http'):
        return image_url
    
    # Production domain'i kullan
    base_url = 'https://panelkocgayrimenkul.com'
    return base_url + image_url


class TeamMemberListSerializer(serializers.ModelSerializer):
    """Ekip üyesi liste serializer"""
    position_display = serializers.CharField(source='get_position_display_custom', read_only=True)
    image_url = serializers.SerializerMethodField()
    
    def get_image_url(self, obj):
        """Fotoğraf URL'sini döndürür"""
        image_url = obj.get_image_url()
        return get_full_image_url(image_url)
    
    class Meta:
        model = TeamMember
        fields = [
            'id',
            'name',
            'position_display',
            'image_url'
        ] 