from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0020_propertypricehistory'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='sahibinden_url',
            field=models.URLField(blank=True, max_length=500, verbose_name='Sahibinden İlan Linki'),
        ),
        migrations.AddField(
            model_name='property',
            name='sahibinden_active',
            field=models.BooleanField(default=False, verbose_name="Sahibinden'de Yayında"),
        ),
    ]
