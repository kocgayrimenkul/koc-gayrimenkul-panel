from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calls', '0005_alter_calllog_extension'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calllog',
            name='recording_url',
            field=models.TextField(blank=True, default='', null=True, verbose_name='Kayıt'),
        ),
    ]
