from django.core.management.base import BaseCommand
from apps.customers.models import Neighborhood

class Command(BaseCommand):
    help = 'Tüm mahalleleri siler ve Şehitkamil ilçesine ait mahalleleri ekler'

    def handle(self, *args, **options):
        # Mevcut tüm mahalleleri sil
        neighborhood_count = Neighborhood.objects.count()
        Neighborhood.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Toplam {neighborhood_count} mahalle silindi'))

        # Şehitkamil ilçesine ait mahalleleri ekle
        neighborhoods_to_create = [
            'Beykent',
            'Alparslan', 
            'Göktürk',
            'Belkız',
            'Karacaahmet',
            'Fıstıklık',
            'Gazikent'
        ]

        # Mahalleleri oluştur
        for neighborhood_name in neighborhoods_to_create:
            Neighborhood.objects.create(
                name=neighborhood_name,
                district='Şehitkamil'
            )
            self.stdout.write(self.style.SUCCESS(f'Mahalle eklendi: {neighborhood_name}'))

        self.stdout.write(self.style.SUCCESS(f'Toplam {len(neighborhoods_to_create)} mahalle eklendi')) 