from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0021_property_sahibinden'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='emlakjet_url',
            field=models.URLField(blank=True, max_length=500, verbose_name='Emlakjet İlan Linki'),
        ),
        migrations.AddField(
            model_name='property',
            name='emlakjet_active',
            field=models.BooleanField(default=False, verbose_name="Emlakjet'te Yayında"),
        ),
        migrations.AddField(
            model_name='property',
            name='hepsiemlak_url',
            field=models.URLField(blank=True, max_length=500, verbose_name='Hepsiemlak İlan Linki'),
        ),
        migrations.AddField(
            model_name='property',
            name='hepsiemlak_active',
            field=models.BooleanField(default=False, verbose_name="Hepsiemlak'ta Yayında"),
        ),
    ]
