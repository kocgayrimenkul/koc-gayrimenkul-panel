# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Ana URL Yapılandırması
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),                      # Django admin
    path("", include("apps.authentication.urls")),        # Auth - giriş / kayıt
    path("", include("apps.customers.urls")),             # Müşteri yönetimi
    path("", include("apps.portfolio.urls")),             # Portföy yönetimi
    path("", include("apps.calendar.urls")),              # Takvim/ajanda
    path("", include("apps.employees.urls")),             # Çalışan yönetimi
    path("", include("apps.home.urls"))                   # Ana sayfa ve diğer UI Kits
]

# Eğer debug modu açıksa, medya dosyaları için URL yapılandırması
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
