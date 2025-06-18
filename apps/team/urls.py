from django.urls import path
from . import views

app_name = 'team'

urlpatterns = [
    # Panel URL'leri
    path('', views.team_list, name='team_list'),
    path('ekle/', views.team_create, name='team_create'),
    path('<int:pk>/', views.team_detail, name='team_detail'),
    path('<int:pk>/duzenle/', views.team_update, name='team_update'),
    path('<int:pk>/toggle-status/', views.team_toggle_status, name='team_toggle_status'),
    path('<int:pk>/update-order/', views.team_update_order, name='team_update_order'),
    path('<int:pk>/delete/', views.team_delete, name='team_delete'),
    
    # REST Framework API
    path('api/list/', views.TeamMemberListAPIView.as_view(), name='api_v1_team_list'),
] 