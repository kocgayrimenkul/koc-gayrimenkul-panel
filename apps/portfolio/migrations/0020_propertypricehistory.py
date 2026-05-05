from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0019_propertynote_is_completed_propertynote_is_reminder_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PropertyPriceHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('old_price', models.DecimalField(decimal_places=2, max_digits=14, verbose_name='Eski Fiyat')),
                ('new_price', models.DecimalField(decimal_places=2, max_digits=14, verbose_name='Yeni Fiyat')),
                ('note', models.CharField(blank=True, max_length=255, verbose_name='Not')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Tarih')),
                ('changed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                  to=settings.AUTH_USER_MODEL, verbose_name='Değiştiren')),
                ('property', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                               related_name='price_history', to='portfolio.property',
                                               verbose_name='Gayrimenkul')),
            ],
            options={
                'verbose_name': 'Fiyat Geçmişi',
                'verbose_name_plural': 'Fiyat Geçmişleri',
                'ordering': ['-created_at'],
            },
        ),
    ]
