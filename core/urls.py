# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Ana URL Yapılandırması
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.calendar import views as calendar_views

urlpatterns = [
    path('admin/', admin.site.urls),                      # Django admin
    path('api/', include('apps.api.urls')),               # REST API
    path('api/careers/', include('apps.careers.urls')),   # Kariyer API
    path('api/contact/', include(('apps.contact.urls', 'contact'), namespace='contact-api')),   # İletişim API
    
    # Ana sayfa olarak ajenda
    path('', calendar_views.calendar_view, name='home'),   # Ana sayfa artık ajenda
    
    # App URL'leri
    path("", include("apps.authentication.urls")),        # Auth - giriş / kayıt
    path("", include("apps.customers.urls")),             # Müşteri yönetimi
    path("", include("apps.portfolio.urls")),             # Portföy yönetimi
    path("", include("apps.employees.urls")),             # Çalışan yönetimi
    path("", include("apps.presentation.urls")),          # Daire sunumu
    path("fsbo/", include("apps.fsbo.urls")),             # FSBO yönetimi
    path("", include("apps.calendar.urls")),              # Takvim/ajenda (ajenda/ alt path'leri için)
    path("genel-bakis/", include("apps.home.urls")),      # Genel bakış sayfası
    path("contact/", include(('apps.contact.urls', 'contact'), namespace='contact-views')),       # İletişim yönetimi (template views)
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
