# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('saha', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ParselKayit'e mahalle alanı ekle
        migrations.AddField(
            model_name='parselkayit',
            name='mahalle',
            field=models.CharField(
                blank=True, max_length=200, verbose_name='Mahalle',
                help_text='Bölge uzmanına görev atanabilmesi için mahalleyi girin'
            ),
        ),

        # SahaGorevPlani
        migrations.CreateModel(
            name='SahaGorevPlani',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mahalle_adi', models.CharField(
                    max_length=200, verbose_name='Mahalle Adı',
                    help_text='ParselKayit.mahalle alanıyla eşleşmeli'
                )),
                ('yil', models.PositiveSmallIntegerField(verbose_name='Yıl')),
                ('ay', models.PositiveSmallIntegerField(verbose_name='Ay', choices=[
                    (1,'Ocak'),(2,'Şubat'),(3,'Mart'),(4,'Nisan'),
                    (5,'Mayıs'),(6,'Haziran'),(7,'Temmuz'),(8,'Ağustos'),
                    (9,'Eylül'),(10,'Ekim'),(11,'Kasım'),(12,'Aralık'),
                ])),
                ('toplam_bina', models.PositiveIntegerField(verbose_name='Toplam Bina Sayısı')),
                ('calisma_gunu', models.PositiveSmallIntegerField(verbose_name='Çalışma Günü')),
                ('gunluk_hedef', models.PositiveSmallIntegerField(verbose_name='Günlük Hedef (Bina)')),
                ('aktif', models.BooleanField(default=True, verbose_name='Aktif')),
                ('olusturma_tarihi', models.DateTimeField(auto_now_add=True)),
                ('bolge_uzmani', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='gorev_planlari',
                    to=settings.AUTH_USER_MODEL, verbose_name='Bölge Uzmanı'
                )),
                ('atayan_broker', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='atadigi_planlar',
                    to=settings.AUTH_USER_MODEL, verbose_name='Atayan Broker'
                )),
            ],
            options={
                'verbose_name': 'Saha Görev Planı',
                'verbose_name_plural': 'Saha Görev Planları',
                'ordering': ['-olusturma_tarihi'],
            },
        ),
        migrations.AddConstraint(
            model_name='sahagorevplani',
            constraint=models.UniqueConstraint(
                fields=['mahalle_adi', 'bolge_uzmani', 'yil', 'ay'],
                name='unique_plan_per_mahalle_uzman_ay'
            ),
        ),

        # GunlukGorev
        migrations.CreateModel(
            name='GunlukGorev',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tarih', models.DateField(verbose_name='Görev Tarihi')),
                ('tamamlandi', models.BooleanField(default=False, verbose_name='Tamamlandı')),
                ('broker_bildirildi', models.BooleanField(default=False, verbose_name='Broker Bildirildi')),
                ('plan', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='gunluk_gorevler',
                    to='saha.sahagorevplani', verbose_name='Plan'
                )),
                ('atanan_parseller', models.ManyToManyField(
                    blank=True, related_name='gunluk_gorevler',
                    to='saha.parselkayit', verbose_name='Atanan Binalar'
                )),
            ],
            options={
                'verbose_name': 'Günlük Görev',
                'verbose_name_plural': 'Günlük Görevler',
                'ordering': ['tarih'],
            },
        ),
        migrations.AddConstraint(
            model_name='gunlukgorev',
            constraint=models.UniqueConstraint(
                fields=['plan', 'tarih'],
                name='unique_gorev_per_plan_tarih'
            ),
        ),

        # BrokerBildirim
        migrations.CreateModel(
            name='BrokerBildirim',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mesaj', models.TextField(verbose_name='Bildirim Mesajı')),
                ('goruldu', models.BooleanField(default=False, verbose_name='Görüldü')),
                ('tarih', models.DateTimeField(auto_now_add=True, verbose_name='Bildirim Tarihi')),
                ('alici', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='broker_bildirimleri',
                    to=settings.AUTH_USER_MODEL, verbose_name='Alıcı (Broker)'
                )),
                ('gorev', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='bildirimler',
                    to='saha.gunlukgorev', verbose_name='İlgili Görev'
                )),
            ],
            options={
                'verbose_name': 'Broker Bildirimi',
                'verbose_name_plural': 'Broker Bildirimleri',
                'ordering': ['-tarih'],
            },
        ),
    ]
