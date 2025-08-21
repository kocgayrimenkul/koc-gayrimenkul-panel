# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Satış Süreç Yönetimi URL Yapılandırması
"""

from django.urls import path
from . import views
from . import whatsapp_views
from . import netgsm_views
from . import assignment_views
from . import manager_views

app_name = 'sales_process'

urlpatterns = [
    # Ana kanban panelleri
    path('', views.sales_dashboard, name='dashboard'),
    path('personel/', views.staff_kanban, name='staff_kanban'),
    path('personel/fullscreen/', views.staff_kanban_fullscreen, name='staff_kanban_fullscreen'),
    path('mudur/', views.manager_kanban, name='manager_kanban'),
    path('mudur/fullscreen/', views.manager_kanban_fullscreen, name='manager_kanban_fullscreen'),
    
    # Lead yönetimi
    path('lead/create/', views.lead_create, name='lead_create'),
    path('lead/<uuid:lead_id>/', views.lead_detail, name='lead_detail'),
    path('lead/<int:lead_id>/update/', views.lead_update, name='lead_update'),
    
    # Process Flow Actions
    path('lead/<int:lead_id>/add-note/', views.add_note, name='add_note'),
    path('lead/<int:lead_id>/schedule-appointment/', views.schedule_appointment, name='schedule_appointment'),
    
    # WhatsApp Integration
    path('whatsapp/webhook/', whatsapp_views.whatsapp_webhook, name='whatsapp_webhook'),
    path('whatsapp/send/<int:lead_id>/', whatsapp_views.send_whatsapp_message, name='send_whatsapp_message'),
    path('whatsapp/history/<int:lead_id>/', whatsapp_views.whatsapp_message_history, name='whatsapp_message_history'),
    path('whatsapp/template/<int:lead_id>/', whatsapp_views.send_template_message, name='send_template_message'),
    path('whatsapp/bulk-send/', whatsapp_views.bulk_whatsapp_send, name='bulk_whatsapp_send'),
    path('whatsapp/statistics/', whatsapp_views.whatsapp_statistics, name='whatsapp_statistics'),
    
    # Netgsm Call Center Integration
    path('netgsm/webhook/', netgsm_views.netgsm_webhook, name='netgsm_webhook'),
    path('call-logs/', netgsm_views.call_logs, name='call_logs'),
    path('call-statistics/', netgsm_views.call_statistics, name='call_statistics'),
    path('make-call/<int:lead_id>/', netgsm_views.make_call, name='make_call'),
    path('call-detail/<int:call_id>/', netgsm_views.call_detail, name='call_detail'),
    path('agent-dashboard/', netgsm_views.agent_dashboard, name='agent_dashboard'),
    path('update-call-notes/<int:call_id>/', netgsm_views.update_call_notes, name='update_call_notes'),
    path('export-call-logs/', netgsm_views.export_call_logs, name='export_call_logs'),
    
    # NetGSM Santral API Endpoints
    path('netgsm/hangup-call/', netgsm_views.hangup_call, name='hangup_call'),
    path('netgsm/mute-call/', netgsm_views.mute_call, name='mute_call'),
    path('netgsm/link-calls/', netgsm_views.link_calls, name='link_calls'),
    path('netgsm/queue-stats/', netgsm_views.queue_stats, name='queue_stats'),
    path('netgsm/agent-login/', netgsm_views.agent_login, name='agent_login'),
    path('netgsm/agent-logout/', netgsm_views.agent_logout, name='agent_logout'),
    path('netgsm/agent-pause/', netgsm_views.agent_pause, name='agent_pause'),
    path('netgsm/add-external-number/', netgsm_views.add_external_number_to_queue, name='add_external_number_to_queue'),
    path('netgsm/dynamic-redirect/', netgsm_views.dynamic_redirect, name='dynamic_redirect'),
    path('netgsm/management/', netgsm_views.netgsm_management, name='netgsm_management'),
    
    # Assignment Management
    path('assignment/', assignment_views.assignment_dashboard, name='assignment_dashboard'),
    path('assignment/list/', assignment_views.lead_assignment_list, name='lead_assignment_list'),
    path('assignment/auto-assign/', assignment_views.auto_assign_leads, name='auto_assign_leads'),
    path('assignment/assign/<int:lead_id>/', assignment_views.assign_lead_to_staff, name='assign_lead_to_staff'),
    path('assignment/reassign-overdue/', assignment_views.reassign_overdue_leads, name='reassign_overdue_leads'),
    path('assignment/balance-workload/', assignment_views.balance_workload, name='balance_workload'),
    path('assignment/statistics/', assignment_views.assignment_statistics, name='assignment_statistics'),
    path('assignment/sticky/', assignment_views.sticky_assignments, name='sticky_assignments'),
    path('assignment/toggle-sticky/<int:assignment_id>/', assignment_views.toggle_sticky_assignment, name='toggle_sticky_assignment'),
    
    # Manager Operations
    path('manager/analytics/', manager_views.manager_analytics, name='manager_analytics'),
    path('manager/bulk-assign/', manager_views.bulk_assign_leads, name='bulk_assign_leads'),
    path('manager/team-performance/', manager_views.team_performance_report, name='team_performance_report'),
    path('manager/lead-distribution/', manager_views.lead_distribution_report, name='lead_distribution_report'),
    path('manager/reassign-overdue/', manager_views.reassign_overdue_leads, name='manager_reassign_overdue_leads'),
    path('manager/dashboard-stats/', manager_views.manager_dashboard_stats, name='manager_dashboard_stats'),
    path('manager/export-reports/', manager_views.export_manager_reports, name='export_manager_reports'),
    
    # AJAX endpoints
    path('ajax/get-leads/', views.get_leads_ajax, name='get_leads_ajax'),
    path('ajax/get-manager-leads/', manager_views.get_manager_leads_ajax, name='get_manager_leads_ajax'),
    path('ajax/update-stage/', views.update_stage_ajax, name='update_stage_ajax'),
    path('ajax/move-stage/', views.move_stage_ajax, name='move_stage_ajax'),
    path('ajax/lead-detail/<uuid:lead_id>/', views.lead_detail_ajax, name='lead_detail_ajax'),
    
    # Reports
    path('reports/', views.sales_reports, name='sales_reports'),
    path('reports/export/', views.export_reports, name='export_reports'),
]