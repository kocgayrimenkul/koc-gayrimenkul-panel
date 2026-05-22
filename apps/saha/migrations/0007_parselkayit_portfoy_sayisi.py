from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('saha', '0006_sahagorusme_gorusulen_kisi'),
    ]

    operations = [
        migrations.AddField(
            model_name='parselkayit',
            name='portfoy_sayisi',
            field=models.PositiveIntegerField(default=0, verbose_name='Alinan Portfoy Sayisi'),
        ),
    ]
