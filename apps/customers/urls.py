# -*- encoding: utf-8 -*-
"""Musteri URL rotalari"""

from django.urls import path
from django.shortcuts import redirect
from . import views


def customer_reminders_placeholder(request):
    return redirect('/admin/customers/customerreminder/')


urlpatterns = [
    # Musteri listesi (yeni) - kok route
    path('musteri/', views.customer_list, name='customer_list'),
    path('musteri/quick-create/', views.customer_quick_create, name='customer_quick_create'),
    path('musteri/is-akislari/kanban/', views.workflow_kanban, name='workflow_kanban'),
    path('musteri/<int:pk>/quick-update/', views.customer_quick_update, name='customer_quick_update'),

    # Musteri detay ve POST route'lari
    path('<int:pk>/', views.customer_detail, name='customer_detail'),
    path('<int:pk>/workflow/create/', views.customer_workflow_create, name='workflow_create'),
    path('<int:pk>/offer/create/', views.customer_offer_create, name='offer_create'),
    path('<int:pk>/note/create/', views.customer_note_create, name='note_create'),
    path('<int:pk>/presentation/create/', views.customer_presentation_create, name='presentation_create'),
    path('musteri/gayrimenkul-ara/', views.property_search_json, name='property_search_json'),

    # call_list URL'i apps/calls/urls.py'den geliyor (cagrilar/ -> calls.views.call_list)
    # Eski sidebar placeholder'lar (admin'e yonlendiren)
    path('hatirlatmalar/', views.customer_reminders_view, name='customer_reminders'),
    path('mahalleler/', views.neighborhood_list, name='neighborhood_list'),
    path('mahalleler/olustur/', views.neighborhood_create, name='neighborhood_create'),
    path('mahalleler/<int:pk>/guncelle/', views.neighborhood_update, name='neighborhood_update'),
    path('mahalleler/<int:pk>/sil/', views.neighborhood_delete, name='neighborhood_delete'),
]
