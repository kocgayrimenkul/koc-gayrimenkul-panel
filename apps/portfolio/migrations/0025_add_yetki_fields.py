from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0024_property_archive_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='yetki_numarasi',
            field=models.CharField(blank=True, max_length=100, verbose_name='Yetki Numarası'),
        ),
        migrations.AddField(
            model_name='property',
            name='yetki_suresi',
            field=models.DateField(blank=True, null=True, verbose_name='Yetki Süresi'),
        ),
    ]
