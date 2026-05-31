from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('customers', '0021_neighborhood_consultant2'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AutoReplyTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.CharField(blank=True, choices=[('whatsapp', 'WhatsApp'), ('instagram', 'Instagram'), ('facebook', 'Facebook'), ('website', 'Web Sitesi')], max_length=20, verbose_name='Platform')),
                ('keyword', models.CharField(blank=True, help_text='Boş bırakılırsa tüm mesajlara uygulanır', max_length=100, verbose_name='Anahtar Kelime')),
                ('response', models.TextField(verbose_name='Yanıt Metni')),
                ('is_active', models.BooleanField(default=True, verbose_name='Aktif')),
                ('priority', models.IntegerField(default=0, verbose_name='Öncelik')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Otomatik Yanıt Şablonu',
                'verbose_name_plural': 'Otomatik Yanıt Şablonları',
                'ordering': ['-priority'],
            },
        ),
        migrations.CreateModel(
            name='IncomingMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.CharField(choices=[('whatsapp', 'WhatsApp'), ('instagram', 'Instagram'), ('facebook', 'Facebook'), ('website', 'Web Sitesi')], max_length=20, verbose_name='Platform')),
                ('sender_id', models.CharField(max_length=255, verbose_name='Gönderen ID')),
                ('sender_name', models.CharField(blank=True, max_length=255, verbose_name='Gönderen Adı')),
                ('sender_phone', models.CharField(blank=True, max_length=50, verbose_name='Telefon')),
                ('message_text', models.TextField(verbose_name='Mesaj')),
                ('ai_response', models.TextField(blank=True, verbose_name='AI Yanıtı')),
                ('is_ai_replied', models.BooleanField(default=False, verbose_name='AI Yanıtladı')),
                ('status', models.CharField(choices=[('new', 'Yeni'), ('replied', 'Yanıtlandı'), ('converted', 'Müşteriye Dönüştürüldü'), ('ignored', 'Yoksayıldı')], default='new', max_length=20, verbose_name='Durum')),
                ('raw_data', models.JSONField(blank=True, default=dict, verbose_name='Ham Veri')),
                ('meta_message_id', models.CharField(blank=True, max_length=255, null=True, unique=True, verbose_name='Meta Mesaj ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Alındı')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Güncellendi')),
                ('customer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='incoming_messages', to='customers.customer', verbose_name='Müşteri')),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_messages', to=settings.AUTH_USER_MODEL, verbose_name='Atanan Personel')),
            ],
            options={
                'verbose_name': 'Gelen Mesaj',
                'verbose_name_plural': 'Gelen Mesajlar',
                'ordering': ['-created_at'],
            },
        ),
    ]
