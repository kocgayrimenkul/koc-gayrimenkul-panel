# Generated migration

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0018_customer_address_customer_city_and_more'),
        ('portfolio', '0014_propertyimage_is_main_photo'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomerPresentation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meeting_notes', models.TextField(blank=True, verbose_name='Görüşme Sonucu')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_presentations', to=settings.AUTH_USER_MODEL, verbose_name='Danışman')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='presentations', to='customers.customer', verbose_name='Müşteri')),
                ('property', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='customer_presentations', to='portfolio.property', verbose_name='Sunulan Daire')),
            ],
            options={
                'verbose_name': 'Daire Sunumu',
                'verbose_name_plural': 'Daire Sunumları',
                'ordering': ['-created_at'],
            },
        ),
    ]
