from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('portfolio', '0018_portal_notifications'),
    ]

    operations = [
        migrations.CreateModel(
            name='SahibindenSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('api_token', models.CharField(blank=True, max_length=500, verbose_name='API Token')),
                ('office_id', models.CharField(blank=True, max_length=100, verbose_name='Ofis ID')),
                ('feed_url_override', models.URLField(blank=True, verbose_name='XML Feed URL (otomatik üretilir)')),
                ('auto_sync_enabled', models.BooleanField(default=False, verbose_name='Otomatik Senkronizasyon')),
                ('last_import_at', models.DateTimeField(blank=True, null=True, verbose_name='Son İçe Aktarma')),
                ('last_export_at', models.DateTimeField(blank=True, null=True, verbose_name='Son Dışa Aktarma')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Sahibinden Ayarları',
                'verbose_name_plural': 'Sahibinden Ayarları',
            },
        ),
        migrations.CreateModel(
            name='SahibindenSyncLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sahibinden_listing_id', models.CharField(blank=True, max_length=100, verbose_name='Sahibinden İlan No')),
                ('sahibinden_url', models.URLField(blank=True, max_length=500, verbose_name='Sahibinden URL')),
                ('status', models.CharField(choices=[('pending', 'Bekliyor'), ('synced', 'Senkronize'), ('error', 'Hata'), ('deleted', 'Silindi')], default='pending', max_length=20, verbose_name='Durum')),
                ('direction', models.CharField(choices=[('export', 'Panel → Sahibinden'), ('import', 'Sahibinden → Panel')], default='export', max_length=10, verbose_name='Yön')),
                ('last_synced_at', models.DateTimeField(blank=True, null=True, verbose_name='Son Senkronizasyon')),
                ('error_message', models.TextField(blank=True, verbose_name='Hata Mesajı')),
                ('sync_count', models.PositiveIntegerField(default=0, verbose_name='Senkronizasyon Sayısı')),
                ('include_in_feed', models.BooleanField(default=True, verbose_name="XML Feed'e Dahil Et")),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('property', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='sahibinden_sync', to='portfolio.property', verbose_name='Gayrimenkul')),
            ],
            options={
                'verbose_name': 'Sahibinden Senkronizasyon',
                'verbose_name_plural': 'Sahibinden Senkronizasyonları',
                'ordering': ['-updated_at'],
            },
        ),
    ]
