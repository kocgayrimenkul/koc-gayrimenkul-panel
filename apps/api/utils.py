# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - API Utilities
"""

from PIL import Image
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os
from io import BytesIO


def create_thumbnail(image_path, size=(300, 200), quality=80):
    """
    Görsel için thumbnail oluştur
    
    Args:
        image_path: Orijinal görselin yolu
        size: Thumbnail boyutu (genişlik, yükseklik)
        quality: JPEG kalitesi (1-100)
    
    Returns:
        Thumbnail URL'i veya None
    """
    try:
        # Thumbnail dosya adı oluştur
        path_parts = image_path.split('.')
        thumbnail_path = f"{'.'.join(path_parts[:-1])}_thumb_{size[0]}x{size[1]}.{path_parts[-1]}"
        
        # Eğer thumbnail zaten varsa URL'ini döndür
        if default_storage.exists(thumbnail_path):
            thumbnail_url = default_storage.url(thumbnail_path)
            # Tam URL'e çevir
            if thumbnail_url.startswith('http'):
                return thumbnail_url
            else:
                base_url = 'https://panelkocgayrimenkul.com'
                return base_url + thumbnail_url
        
        # Orijinal görseli aç
        if not default_storage.exists(image_path):
            return None
            
        with default_storage.open(image_path, 'rb') as f:
            image = Image.open(f)
            
            # RGBA modundaysa RGB'ye çevir (JPEG desteği için)
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # Thumbnail oluştur (aspect ratio'yu koru)
            image.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Buffer'a kaydet
            buffer = BytesIO()
            image.save(buffer, format='JPEG', quality=quality, optimize=True)
            buffer.seek(0)
            
            # Thumbnail'i kaydet
            default_storage.save(thumbnail_path, ContentFile(buffer.getvalue()))
            
            # Tam URL'e çevir
            thumbnail_url = default_storage.url(thumbnail_path)
            if thumbnail_url.startswith('http'):
                return thumbnail_url
            else:
                base_url = 'https://panelkocgayrimenkul.com'
                return base_url + thumbnail_url
            
    except Exception as e:
        print(f"Thumbnail oluşturma hatası: {e}")
        return None


def get_optimized_image_url(image_url, thumbnail_size=(300, 200)):
    """
    Optimize edilmiş görsel URL'i döndür
    
    Args:
        image_url: Orijinal görsel URL'i
        thumbnail_size: Thumbnail boyutu
    
    Returns:
        Optimize edilmiş görsel URL'i
    """
    if not image_url:
        return None
    
    try:
        # URL'den dosya yolunu çıkar
        if image_url.startswith('http'):
            # Full URL'den dosya yolunu çıkar
            image_path = image_url.split(settings.MEDIA_URL)[-1] if settings.MEDIA_URL in image_url else None
        else:
            # Relative path
            image_path = image_url.lstrip('/')
        
        if not image_path:
            return image_url
        
        # Thumbnail oluştur veya var olan thumbnail URL'ini al
        thumbnail_url = create_thumbnail(image_path, thumbnail_size)
        
        # Eğer thumbnail oluşturulamadıysa orijinal URL'i döndür
        if not thumbnail_url:
            return image_url
        
        # Thumbnail URL'i tam URL'e çevir
        if thumbnail_url.startswith('http'):
            return thumbnail_url
        else:
            # Production domain'i kullan
            base_url = 'https://panelkocgayrimenkul.com'
            return base_url + thumbnail_url
        
    except Exception as e:
        print(f"Görsel optimizasyon hatası: {e}")
        return image_url


def batch_create_thumbnails():
    """
    Mevcut tüm property image'ları için thumbnail oluştur
    (Management command ile çalıştırılabilir)
    """
    from apps.portfolio.models import PropertyImage
    
    images = PropertyImage.objects.filter(image__isnull=False)
    success_count = 0
    error_count = 0
    
    for img in images:
        try:
            if img.image:
                create_thumbnail(img.image.name)
                success_count += 1
        except Exception as e:
            print(f"Thumbnail oluşturma hatası - {img.id}: {e}")
            error_count += 1
    
    print(f"Thumbnail oluşturma tamamlandı. Başarılı: {success_count}, Hatalı: {error_count}") 