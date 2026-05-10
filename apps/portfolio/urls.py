# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Portföy URL Yapılandırması
"""

from django.urls import path, re_path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Gayrimenkul listeleme
    path('gayrimenkul/', views.property_list, name='property_list'),
    
    # Gruplu görünüm
    path('liste-gruplu/', views.property_list_grouped, name='property_list_grouped'),
    path('gayrimenkul/liste-gruplu/', views.property_list_grouped, name='property_list_grouped_alt'),
    
    # Gayrimenkul detay
    path('gayrimenkul/<int:property_id>/', views.property_detail, name='property_detail'),
    
    # Gayrimenkul ekleme
    path('gayrimenkul/ekle/', views.property_create, name='property_create'),
    
    # Gayrimenkul güncelleme
    path('gayrimenkul/duzenle/<int:property_id>/', views.property_update, name='property_update'),
    
    # Gayrimenkul silme
    path('gayrimenkul/sil/<int:property_id>/', views.property_delete, name='property_delete'),
    
    # Gayrimenkul görsel işlemleri
    path('property-image-upload/', views.property_image_upload, name='property_image_upload'),
    path('property-image-delete/', views.property_image_delete, name='property_image_delete'),
    path('image-delete/', views.property_image_delete, name='image-delete'),
    path('image-update-main/', views.image_update_main, name='image-update-main'),
    path('image-update-order/', views.image_update_order, name='image-update-order'),
    
    # AJAX işlemleri
    path('property-update-field/', views.property_update_field, name='property_update_field'),
    path('update-portal-link/', views.update_portal_link, name='update_portal_link'),
    path('update-photo-status/', views.update_photo_status, name='update_photo_status'),
    path('update-banner-status/', views.update_banner_status, name='update_banner_status'),
    path('move-to-group/', views.move_property_to_group, name='move_property_to_group'),
    
    # Harita görünümü
    path('gayrimenkul/harita/', views.property_map, name='property_map'),

    # API URL'leri
    path('api/properties/', views.api_properties, name='api_properties'),

    # Not sistemi
    path('gayrimenkul/<int:property_id>/notlar/',   views.property_notes,       name='property_notes'),
    path('gayrimenkul/<int:property_id>/not-ekle/', views.property_note_add,    name='property_note_add'),
    path('gayrimenkul/not-sil/<int:note_id>/',      views.property_note_delete, name='property_note_delete'),
    # AJAX API not sistemi
    path('api/gayrimenkul/<int:property_id>/notlar/',  views.property_notes_api,         name='property_notes_api'),
    path('api/gayrimenkul/<int:property_id>/not-ekle/', views.property_note_add_api,      name='property_note_add_api'),
    path('api/not/<int:note_id>/toggle/',              views.property_note_toggle_complete, name='property_note_toggle_complete'),
    path('api/not/<int:note_id>/sil/',                 views.property_note_delete_api,    name='property_note_delete_api'),

    # Portal bildirimleri
    path('portal-bildirimleri/',                        views.portal_notifications,          name='portal_notifications'),
    path('portal-bildirim-oku/<int:notification_id>/',  views.portal_notification_read,      name='portal_notification_read'),
    path('portal-bildirimleri-hepsini-oku/',             views.portal_notifications_read_all, name='portal_notifications_read_all'),

    # Fiyat geçmişi
    path('api/gayrimenkul/<int:property_id>/fiyat-gecmisi/', views.price_history_api, name='price_history_api'),

    # Sunum yapılan müşteriler
    path('api/gayrimenkul/<int:property_id>/sunum-musteriler/', views.property_sunum_musteriler_api, name='property_sunum_musteriler_api'),

    # Sosyal medya şablonları
    path('gayrimenkul/<int:property_id>/sosyal-medya/', views.social_media_page, name='social_media_page'),

    # Arşivden geri al
    path('gayrimenkul/<int:property_id>/geri-al/', views.property_restore, name='property_restore'),

    # Sahibinden entegrasyonu
    path('sahibinden/', views.sahibinden_export, name='sahibinden_export'),
    path('sahibinden/xml/', views.sahibinden_xml_feed, name='sahibinden_xml_feed'),
    path('sahibinden/toggle/<int:property_id>/', views.sahibinden_toggle, name='sahibinden_toggle'),

    # Emlakjet entegrasyonu
    path('emlakjet/', views.emlakjet_export, name='emlakjet_export'),
    path('emlakjet/toggle/<int:property_id>/', views.emlakjet_toggle, name='emlakjet_toggle'),

    # Hepsiemlak entegrasyonu
    path('hepsiemlak/', views.hepsiemlak_export, name='hepsiemlak_export'),
    path('hepsiemlak/toggle/<int:property_id>/', views.hepsiemlak_toggle, name='hepsiemlak_toggle'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)