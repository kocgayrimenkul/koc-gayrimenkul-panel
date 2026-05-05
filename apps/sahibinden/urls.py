from django.urls import path
from . import views

urlpatterns = [
    # XML Feed — Sahibinden bu URL'yi çeker
    path('sahibinden/feed.xml',                     views.sahibinden_xml_feed,          name='sahibinden_feed'),

    # Dashboard
    path('sahibinden/',                             views.sahibinden_dashboard,         name='sahibinden_dashboard'),
    path('sahibinden/ayarlar/kaydet/',              views.sahibinden_settings_save,     name='sahibinden_settings_save'),

    # API aksiyonlar
    path('sahibinden/import/',                      views.sahibinden_import,            name='sahibinden_import'),
    path('sahibinden/push-all/',                    views.sahibinden_push_all,          name='sahibinden_push_all'),
    path('sahibinden/push/<int:property_id>/',      views.sahibinden_push_property,     name='sahibinden_push_property'),
    path('sahibinden/toggle/<int:property_id>/',    views.sahibinden_sync_toggle,       name='sahibinden_sync_toggle'),
]
