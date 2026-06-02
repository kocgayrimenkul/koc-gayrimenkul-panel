from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='KaporaKayit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ofis', models.CharField(choices=[('beykent', 'Beykent'), ('fistiklik', 'Fıstıklık')], max_length=20, verbose_name='Ofis')),
                ('yer', models.CharField(max_length=255, verbose_name='Yer')),
                ('kapora', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Kapora (TL)')),
                ('ay', models.IntegerField(choices=[(1,'1. Ay'),(2,'2. Ay'),(3,'3. Ay'),(4,'4. Ay'),(5,'5. Ay'),(6,'6. Ay'),(7,'7. Ay'),(8,'8. Ay'),(9,'9. Ay'),(10,'10. Ay'),(11,'11. Ay'),(12,'12. Ay')], verbose_name='Ay')),
                ('yil', models.IntegerField(verbose_name='Yıl')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('satan', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='satan_kaporalar', to=settings.AUTH_USER_MODEL, verbose_name='Satan')),
                ('olusturan', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='olusturulan_kaporalar', to=settings.AUTH_USER_MODEL, verbose_name='Kaydeden')),
            ],
            options={'verbose_name': 'Kapora', 'verbose_name_plural': 'Kaporalar', 'ordering': ['-yil', '-ay', '-created_at']},
        ),
        migrations.CreateModel(
            name='GelirKayit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ofis', models.CharField(choices=[('beykent', 'Beykent'), ('fistiklik', 'Fıstıklık')], max_length=20, verbose_name='Ofis')),
                ('yer', models.CharField(max_length=255, verbose_name='Yer')),
                ('gelir', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Gelir (TL)')),
                ('kapora', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Kapora (TL)')),
                ('toplam', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Toplam (TL)')),
                ('ay', models.IntegerField(choices=[(1,'1. Ay'),(2,'2. Ay'),(3,'3. Ay'),(4,'4. Ay'),(5,'5. Ay'),(6,'6. Ay'),(7,'7. Ay'),(8,'8. Ay'),(9,'9. Ay'),(10,'10. Ay'),(11,'11. Ay'),(12,'12. Ay')], verbose_name='Ay')),
                ('yil', models.IntegerField(verbose_name='Yıl')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('bulan', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bulan_gelirler', to=settings.AUTH_USER_MODEL, verbose_name='Bulan')),
                ('satan', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='satan_gelirler', to=settings.AUTH_USER_MODEL, verbose_name='Satan')),
                ('olusturan', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='olusturulan_gelirler', to=settings.AUTH_USER_MODEL, verbose_name='Kaydeden')),
            ],
            options={'verbose_name': 'Gelir', 'verbose_name_plural': 'Gelirler', 'ordering': ['-yil', '-ay', '-created_at']},
        ),
        migrations.CreateModel(
            name='Gider',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tarih', models.DateField(verbose_name='Tarih')),
                ('tutar', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Tutar (TL)')),
                ('kategori', models.CharField(choices=[('kira','Kira'),('maas','Maaş / Prim'),('reklam','Reklam / Pazarlama'),('fatura','Fatura'),('arac','Araç / Yakıt'),('kirtasiye','Kırtasiye / Ofis'),('vergi','Vergi / SGK'),('diger','Diğer')], max_length=50, verbose_name='Kategori')),
                ('aciklama', models.TextField(blank=True, verbose_name='Açıklama')),
                ('odeme_yontemi', models.CharField(choices=[('nakit','Nakit'),('havale','Havale / EFT'),('kredi_karti','Kredi Kartı'),('cek','Çek'),('diger','Diğer')], default='nakit', max_length=20, verbose_name='Ödeme Yöntemi')),
                ('belge', models.FileField(blank=True, null=True, upload_to='muhasebe/gider/', verbose_name='Belge')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('personel', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='giderler', to=settings.AUTH_USER_MODEL, verbose_name='İlgili Personel')),
                ('olusturan', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='olusturulan_giderler', to=settings.AUTH_USER_MODEL, verbose_name='Kaydeden')),
            ],
            options={'verbose_name': 'Gider', 'verbose_name_plural': 'Giderler', 'ordering': ['-tarih', '-created_at']},
        ),
    ]
