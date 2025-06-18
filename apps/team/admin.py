from django.contrib import admin
from django.utils.html import format_html
from .models import TeamMember


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'get_position_display_custom', 
        'image_preview',
        'is_active', 
        'display_order',
        'created_at'
    ]
    
    list_filter = [
        'is_active',
        'position',
        'created_at'
    ]
    
    search_fields = [
        'name', 
        'position',
        'custom_position'
    ]
    
    list_editable = [
        'is_active',
        'display_order'
    ]
    
    ordering = ['display_order', 'name']
    
    fieldsets = (
        ('Genel Bilgiler', {
            'fields': (
                'name',
                ('position', 'custom_position')
            )
        }),
        ('Fotoğraf', {
            'fields': (
                'image',
                'image_url'
            ),
            'description': 'Fotoğraf yükleyebilir veya harici URL kullanabilirsiniz.'
        }),
        ('Görünüm Ayarları', {
            'fields': (
                'is_active',
                'display_order'
            )
        })
    )
    
    def image_preview(self, obj):
        """Admin panelinde küçük fotoğraf önizlemesi gösterir"""
        image_url = obj.get_image_url()
        if image_url:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 50%;" />',
                image_url
            )
        return "Fotoğraf Yok"
    
    image_preview.short_description = "Fotoğraf"
    
    def get_position_display_custom(self, obj):
        """Özel pozisyon varsa onu gösterir"""
        return obj.get_position_display_custom()
    
    get_position_display_custom.short_description = "Pozisyon"
