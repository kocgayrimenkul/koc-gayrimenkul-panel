from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('saha', '0005_oturuma_ek_alanlar'),
    ]

    operations = [
        migrations.AddField(
            model_name='sahagorusme',
            name='gorusulen_kisi',
            field=models.CharField(blank=True, max_length=150, verbose_name='Gorusulen Kisi'),
        ),
    ]
