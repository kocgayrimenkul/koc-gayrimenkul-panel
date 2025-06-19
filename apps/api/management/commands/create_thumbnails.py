# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Thumbnail Oluşturma Komutu
"""

from django.core.management.base import BaseCommand
from apps.api.utils import batch_create_thumbnails


class Command(BaseCommand):
    help = 'Mevcut property fotoğrafları için thumbnail oluşturur'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--size',
            type=str,
            default='300x200',
            help='Thumbnail boyutu (örn: 300x200)'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Property fotoğrafları için thumbnail oluşturuluyor...')
        )
        
        try:
            batch_create_thumbnails()
            self.stdout.write(
                self.style.SUCCESS('Thumbnail oluşturma işlemi başarıyla tamamlandı!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Hata oluştu: {e}')
            ) 