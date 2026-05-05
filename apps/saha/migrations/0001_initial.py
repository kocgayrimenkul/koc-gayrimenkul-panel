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
            name='ParselKayit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lat', models.FloatField(verbose_name='Enlem')),
                ('lng', models.FloatField(verbose_name='Boylam')),
                ('adres', models.CharField(blank=True, max_length=500, verbose_name='Adres / Açıklama')),
                ('ada_no', models.CharField(blank=True, max_length=50, verbose_name='Ada No')),
                ('parsel_no', models.CharField(blank=True, max_length=50, verbose_name='Parsel No')),
                ('yonetici_ad', models.CharField(blank=True, max_length=150, verbose_name='Bina Yöneticisi Adı')),
                ('yonetici_tel', models.CharField(blank=True, max_length=30, verbose_name='Yönetici Telefonu')),
                ('kapici_ad', models.CharField(blank=True, max_length=150, verbose_name='Kapıcı Adı')),
                ('kapici_tel', models.CharField(blank=True, max_length=30, verbose_name='Kapıcı Telefonu')),
                ('diger_not', models.TextField(blank=True, verbose_name='Bina Hakkında Notlar')),
                ('olusturma_tarihi', models.DateTimeField(auto_now_add=True)),
                ('guncelleme_tarihi', models.DateTimeField(auto_now=True)),
                ('olusturan', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='parsel_kayitlar', to=settings.AUTH_USER_MODEL, verbose_name='Oluşturan')),
            ],
            options={
                'verbose_name': 'Parsel Kaydı',
                'verbose_name_plural': 'Parsel Kayıtları',
                'ordering': ['-olusturma_tarihi'],
            },
        ),
        migrations.CreateModel(
            name='SahaGorusme',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tarih', models.DateTimeField(auto_now_add=True, verbose_name='Görüşme Tarihi')),
                ('not_metni', models.TextField(verbose_name='Görüşme Notu')),
                ('parsel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gorusmeler', to='saha.parselkayit', verbose_name='Parsel')),
                ('personel', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='saha_gorusmeler', to=settings.AUTH_USER_MODEL, verbose_name='Personel')),
            ],
            options={
                'verbose_name': 'Saha Görüşmesi',
                'verbose_name_plural': 'Saha Görüşmeleri',
                'ordering': ['-tarih'],
            },
        ),
    ]
