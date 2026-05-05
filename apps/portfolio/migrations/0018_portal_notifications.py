from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0017_auto_20260222_2327'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='owner_listing_updated_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Sahibinden Güncelleme Tarihi'),
        ),
        migrations.AddField(
            model_name='property',
            name='emlakjet_listing_updated_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Emlakjet Güncelleme Tarihi'),
        ),
        migrations.AddField(
            model_name='property',
            name='hepsiemlak_listing_updated_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Hepsiemlak Güncelleme Tarihi'),
        ),
        migrations.CreateModel(
            name='PortalNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('portal', models.CharField(choices=[('sahibinden', 'Sahibinden'), ('emlakjet', 'Emlakjet'), ('hepsiemlak', 'Hepsiemlak')], max_length=20, verbose_name='Portal')),
                ('is_read', models.BooleanField(default=False, verbose_name='Okundu')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Tarih')),
                ('property', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='portal_notifications', to='portfolio.property', verbose_name='Gayrimenkul')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='portal_notifications', to=settings.AUTH_USER_MODEL, verbose_name='Danışman')),
            ],
            options={
                'verbose_name': 'Portal Bildirimi',
                'verbose_name_plural': 'Portal Bildirimleri',
                'ordering': ['-created_at'],
            },
        ),
    ]