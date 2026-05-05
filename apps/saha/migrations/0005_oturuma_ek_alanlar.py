from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('saha', '0004_alter_gunlukgorev_options_alter_parselkayit_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='parselkayit',
            name='oturuma_yonetici_ad',
            field=models.CharField(blank=True, max_length=150, verbose_name='Oturuma Yonetici Adi'),
        ),
        migrations.AddField(
            model_name='parselkayit',
            name='oturuma_yonetici_tel',
            field=models.CharField(blank=True, max_length=30, verbose_name='Oturuma Yonetici Telefonu'),
        ),
        migrations.AddField(
            model_name='parselkayit',
            name='oturuma_bekci_ad',
            field=models.CharField(blank=True, max_length=150, verbose_name='Oturuma Bekci Adi'),
        ),
        migrations.AddField(
            model_name='parselkayit',
            name='oturuma_bekci_tel',
            field=models.CharField(blank=True, max_length=30, verbose_name='Oturuma Bekci Telefonu'),
        ),
        migrations.AddField(
            model_name='parselkayit',
            name='oturuma_ek_kisiler',
            field=models.JSONField(blank=True, default=list, verbose_name='Oturuma Ek Kisiler'),
        ),
        migrations.AddField(
            model_name='parselkayit',
            name='dolu_ek_kisiler',
            field=models.JSONField(blank=True, default=list, verbose_name='Dolu Bina Ek Kisiler'),
        ),
    ]
