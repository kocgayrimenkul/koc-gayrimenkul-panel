# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Team Serializers
"""

from rest_framework import serializers
from .models import TeamMember


class TeamMemberListSerializer(serializers.ModelSerializer):
    """Ekip üyesi liste serializer"""
    position_display = serializers.CharField(source='get_position_display_custom', read_only=True)
    image_url = serializers.SerializerMethodField()
    
    def get_image_url(self, obj):
        """Fotoğraf URL'sini döndürür"""
        image_url = obj.get_image_url()
        if image_url:
            request = self.context.get('request')
            if request and not image_url.startswith('http'):
                return request.build_absolute_uri(image_url)
            return image_url
        return None
    
    class Meta:
        model = TeamMember
        fields = [
            'id',
            'name',
            'position_display',
            'image_url'
        ] 