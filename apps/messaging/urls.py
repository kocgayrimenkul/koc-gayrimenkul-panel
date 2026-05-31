from django.urls import path
from . import views

urlpatterns = [
    # Panel
    path('mesajlar/', views.message_list, name='message_list'),
    path('mesajlar/<int:msg_id>/musteriye-donustur/', views.convert_message_to_customer, name='convert_message_to_customer'),
    path('mesajlar/<int:msg_id>/yanıtla/', views.send_manual_reply, name='send_manual_reply'),

    # Webhook & API
    path('api/webhook/meta/', views.meta_webhook, name='meta_webhook'),
    path('api/chat/website/', views.website_chat, name='website_chat'),
    path('chat-widget.js', views.website_chat_widget, name='chat_widget_js'),
]
