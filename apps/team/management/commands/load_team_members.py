# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Ekip Üyeleri Yükleme Komutu
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.team.models import TeamMember


class Command(BaseCommand):
    help = 'Koç Gayrimenkul ekip üyelerini sisteme yükler'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            dest='clear',
            help='Önce mevcut ekip üyelerini siler',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Koç Gayrimenkul ekip üyeleri yükleniyor...\n')
        )

        # Mevcut verileri temizle (opsiyonel)
        if options['clear']:
            self.stdout.write('Mevcut ekip üyeleri siliniyor...')
            TeamMember.objects.all().delete()
            self.stdout.write(
                self.style.WARNING('Mevcut ekip üyeleri silindi.\n')
            )

        # Ekip üyeleri verisi
        team_members_data = [
            # Üst Yönetim
            {
                'name': 'Osman Koç',
                'position': 'ceo',
                'custom_position': 'Kurucu',
                'display_order': 1,
                'is_active': True
            },
            {
                'name': 'Aytekin Kurtay',
                'position': 'manager',
                'custom_position': 'Genel Müdür',
                'display_order': 2,
                'is_active': True
            },
            {
                'name': 'Burhan Payaslı',
                'position': 'manager',
                'custom_position': 'Genel Müdür',
                'display_order': 3,
                'is_active': True
            },
            
            # Orta Kademe
            {
                'name': 'Öykü Demir',
                'position': 'coordinator',
                'custom_position': 'Ofis Yöneticisi',
                'display_order': 4,
                'is_active': True
            },
            {
                'name': 'Mervenur Çelik',
                'position': 'consultant',
                'custom_position': 'Müşteri Danışmanı',
                'display_order': 5,
                'is_active': True
            },
            
            # Emlak Danışmanları
            {
                'name': 'Ökkeş Kartal',
                'position': 'consultant',
                'custom_position': 'Emlak Danışmanı',
                'display_order': 6,
                'is_active': True
            },
            {
                'name': 'Eyüp Koç',
                'position': 'consultant',
                'custom_position': 'Emlak Danışmanı',
                'display_order': 7,
                'is_active': True
            },
            {
                'name': 'Samet Kanlıoğlu',
                'position': 'consultant',
                'custom_position': 'Emlak Danışmanı',
                'display_order': 8,
                'is_active': True
            },
            {
                'name': 'Abdullah Dündar',
                'position': 'consultant',
                'custom_position': 'Emlak Danışmanı',
                'display_order': 9,
                'is_active': True
            },
            {
                'name': 'Rojhat Aslan',
                'position': 'consultant',
                'custom_position': 'Emlak Danışmanı',
                'display_order': 10,
                'is_active': True
            },
            {
                'name': 'Selda Cüran',
                'position': 'consultant',
                'custom_position': 'Emlak Danışmanı',
                'display_order': 11,
                'is_active': True
            },
            {
                'name': 'Yavuz Selim Demir',
                'position': 'consultant',
                'custom_position': 'Emlak Danışmanı',
                'display_order': 12,
                'is_active': True
            },
            {
                'name': 'Mehmet Könez',
                'position': 'consultant',
                'custom_position': 'Emlak Danışmanı',
                'display_order': 13,
                'is_active': True
            },
        ]

        # Verileri yükle
        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for member_data in team_members_data:
                team_member, created = TeamMember.objects.get_or_create(
                    name=member_data['name'],
                    defaults=member_data
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        f"✅ {member_data['name']} - {member_data.get('custom_position', member_data['position'])} eklendi"
                    )
                else:
                    # Mevcut kayıt varsa güncelle
                    for key, value in member_data.items():
                        if key != 'name':  # İsmi güncelleme
                            setattr(team_member, key, value)
                    team_member.save()
                    updated_count += 1
                    self.stdout.write(
                        f"🔄 {member_data['name']} - {member_data.get('custom_position', member_data['position'])} güncellendi"
                    )

        # Sonuç özeti
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ İşlem tamamlandı!\n'
                f'📊 Eklenen üye sayısı: {created_count}\n'
                f'🔄 Güncellenen üye sayısı: {updated_count}\n'
                f'📈 Toplam ekip üyesi: {TeamMember.objects.count()}\n'
                f'🟢 Aktif üyeler: {TeamMember.objects.filter(is_active=True).count()}\n'
            )
        )
        
        # API test bilgisi
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.HTTP_INFO(
                '🌐 API Endpoint Testi:\n'
                'http://localhost:8000/team/api/ - Ekip listesi\n'
                'Admin Panel: http://localhost:8000/admin/team/teammember/\n'
                'Yönetim Paneli: http://localhost:8000/team/\n'
            )
        ) 