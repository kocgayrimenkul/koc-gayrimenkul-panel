from django.contrib import admin
from .models import GelirKayit, KaporaKayit, Gider

@admin.register(GelirKayit)
class GelirAdmin(admin.ModelAdmin):
    list_display = ['yil', 'ay', 'ofis', 'bulan', 'satan', 'yer', 'toplam']
    list_filter  = ['ofis', 'ay', 'yil']
    search_fields = ['yer']

@admin.register(KaporaKayit)
class KaporaAdmin(admin.ModelAdmin):
    list_display = ['yil', 'ay', 'ofis', 'satan', 'yer', 'kapora']
    list_filter  = ['ofis', 'ay', 'yil']
    search_fields = ['yer']

@admin.register(Gider)
class GiderAdmin(admin.ModelAdmin):
    list_display = ['tarih', 'kategori', 'tutar', 'personel', 'odeme_yontemi']
    list_filter  = ['kategori', 'odeme_yontemi']
    search_fields = ['aciklama']
