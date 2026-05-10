from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0023_delete_propertypricehistory'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='is_archived',
            field=models.BooleanField(default=False, verbose_name='Arşivlendi'),
        ),
        migrations.AddField(
            model_name='property',
            name='archived_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Arşiv Tarihi'),
        ),
        migrations.AddField(
            model_name='property',
            name='archived_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='archived_properties',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Arşivleyen',
            ),
        ),
    ]
