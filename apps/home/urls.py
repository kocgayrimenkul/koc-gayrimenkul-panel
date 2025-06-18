# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path
from apps.home import views

urlpatterns = [

    # Genel bakış sayfası (artık /genel-bakis/ altında)
    path('', views.index, name='dashboard'),
    
    # Harita sayfası
    path('map/', views.map_view, name='map'),

    # Matches any html file
    re_path(r'^.*\.*', views.pages, name='pages'),

]
