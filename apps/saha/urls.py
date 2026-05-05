from django.urls import path
from . import views

urlpatterns = [
    # Harita
    path('saha/',                                    views.saha_harita,                      name='saha_harita'),

    # Gorev Sistemi
    path('saha/gorevler/',                           views.gorev_plani_listesi,              name='gorev_plani_listesi'),
    path('saha/gorevler/olustur/',                   views.gorev_plani_olustur,              name='gorev_plani_olustur'),
    path('saha/gorevler/<int:plan_id>/',             views.gorev_plani_detay,                name='gorev_plani_detay'),
    path('saha/gorevim/',                            views.gunluk_gorevim,                   name='gunluk_gorevim'),
    path('saha/bildirimler/',                        views.broker_bildirimleri,              name='broker_bildirimleri'),

    # Parsel API
    path('api/saha/parseller/',                      views.api_parseller,                    name='api_parseller'),
    path('api/saha/parsel/ekle/',                    views.api_parsel_ekle,                  name='api_parsel_ekle'),
    path('api/saha/parsel/<int:parsel_id>/',         views.api_parsel_detay,                 name='api_parsel_detay'),
    path('api/saha/parsel/<int:parsel_id>/sil/',     views.api_parsel_sil,                   name='api_parsel_sil'),
    path('api/saha/parsel/<int:parsel_id>/gorusme/', views.api_gorusme_ekle,                 name='api_gorusme_ekle'),

    # Gorev API
    path('api/saha/gorev/parseller/',                views.api_gunluk_gorev_parselleri,      name='api_gunluk_gorev_parselleri'),
    path('api/saha/bildirim/sayisi/',                views.api_bildirim_sayisi,              name='api_bildirim_sayisi'),
    path('api/saha/gorev/<int:gorev_id>/bildir/',    views.api_gorev_bildir,                 name='api_gorev_bildir'),
    path('api/saha/plan/<int:plan_id>/sil/',         views.api_gorev_plani_sil,              name='api_gorev_plani_sil'),
    path('api/saha/mahalleler/',                     views.api_mahalleler,                   name='api_mahalleler'),

    # Panel API (sag panel)
    path('api/saha/gorev-planlari/',                 views.api_gorev_planlari_json,          name='api_gorev_planlari_json'),
    path('api/saha/bildirimler/',                    views.api_bildirimleri_json,            name='api_bildirimleri_json'),
    path('api/saha/plan/otomatik-olustur/',          views.api_planlari_otomatik_olustur,    name='api_planlari_otomatik_olustur'),
]
