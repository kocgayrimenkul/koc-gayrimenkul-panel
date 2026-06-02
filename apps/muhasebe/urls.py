from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('muhasebe/',                                 views.dashboard,           name='muhasebe_dashboard'),
    path('muhasebe/ozet/export/',                     views.dashboard_export,    name='muhasebe_dashboard_export'),

    # Personel kazanç (read-only)
    path('muhasebe/kazancim/',                        views.personel_kazanc,     name='personel_kazanc'),

    # Gelirler
    path('muhasebe/gelirler/',                        views.gelir_list,          name='gelir_list'),
    path('muhasebe/gelirler/export/',                 views.gelir_export,        name='gelir_export'),
    path('muhasebe/gelirler/<int:pk>/sil/',           views.gelir_sil,           name='gelir_sil'),

    # Kapora
    path('muhasebe/kapora/ekle/',                     views.kapora_ekle,         name='kapora_ekle'),
    path('muhasebe/kapora/<int:pk>/gerceklestir/',    views.kapora_gerceklestir, name='kapora_gerceklestir'),
    path('muhasebe/kapora/<int:pk>/sil/',             views.kapora_sil,          name='kapora_sil'),

    # Giderler
    path('muhasebe/giderler/',                        views.gider_list,          name='gider_list'),
    path('muhasebe/giderler/export/',                 views.gider_export,        name='gider_export'),
    path('muhasebe/giderler/ekle/',                   views.gider_ekle,          name='gider_ekle'),
    path('muhasebe/giderler/<int:pk>/duzenle/',       views.gider_duzenle,       name='gider_duzenle'),
    path('muhasebe/giderler/<int:pk>/sil/',           views.gider_sil,           name='gider_sil'),
]
