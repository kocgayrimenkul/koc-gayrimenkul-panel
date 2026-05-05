# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('saha', '0002_gorev_sistemi'),
    ]

    operations = [
        migrations.AddField(
            model_name='parselkayit',
            name='durum',
            field=models.CharField(blank=True, default='', max_length=30,
                choices=[('yapim_asamasinda','Yapim Asamasinda'),
                         ('oturuma_hazir','Oturuma Hazir'),
                         ('dolu_bina','Dolu Bina')],
                verbose_name='Durum'),
        ),
        migrations.AddField(model_name='parselkayit', name='muteahit_ad',
            field=models.CharField(blank=True, max_length=150, verbose_name='Muteahit Adi')),
        migrations.AddField(model_name='parselkayit', name='muteahit_tel',
            field=models.CharField(blank=True, max_length=30, verbose_name='Muteahit Telefonu')),
        migrations.AddField(model_name='parselkayit', name='bekci_ad',
            field=models.CharField(blank=True, max_length=150, verbose_name='Bekci Adi')),
        migrations.AddField(model_name='parselkayit', name='bekci_tel',
            field=models.CharField(blank=True, max_length=30, verbose_name='Bekci Telefonu')),
        migrations.AddField(model_name='parselkayit', name='cavus_ad',
            field=models.CharField(blank=True, max_length=150, verbose_name='Cavus Adi')),
        migrations.AddField(model_name='parselkayit', name='cavus_tel',
            field=models.CharField(blank=True, max_length=30, verbose_name='Cavus Telefonu')),
        migrations.AddField(model_name='parselkayit', name='taseronlar',
            field=models.JSONField(blank=True, default=list, verbose_name='Taseronlar')),
        migrations.AddField(model_name='parselkayit', name='arsa_sahibi_ad',
            field=models.CharField(blank=True, max_length=150, verbose_name='Arsa Sahibi Adi')),
        migrations.AddField(model_name='parselkayit', name='arsa_sahibi_tel',
            field=models.CharField(blank=True, max_length=30, verbose_name='Arsa Sahibi Telefonu')),
    ]
