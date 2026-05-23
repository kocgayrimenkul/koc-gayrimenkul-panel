from django.urls import path
from . import views

urlpatterns = [
    # Çağrı listesi sayfası
    path('cagrilar/', views.call_list, name='call_list'),

    # Çağrıyı müşteriye dönüştür
    path('cagrilar/<int:call_id>/musteriye-donustur/', views.convert_call_to_customer, name='convert_call_to_customer'),

    # NetGSM webhook
    path('webhook/netgsm/', views.netgsm_webhook, name='netgsm_webhook'),

    # AI çağrı özeti
    path('cagrilar/<int:call_id>/ai-ozet/', views.ai_summarize_call, name='ai_summarize_call'),

    # Ses kaydı proxy
    path('cagrilar/<int:call_id>/ses-kaydi/', views.proxy_recording, name='proxy_recording'),

    # API endpoints
    path('api/recent-calls/', views.recent_calls_api, name='recent_calls_api'),
    path('api/unmatched-calls/', views.unmatched_calls_api, name='unmatched_calls_api'),
    path('api/properties-by-neighborhood/', views.properties_by_neighborhood_api, name='properties_by_neighborhood_api'),
]
