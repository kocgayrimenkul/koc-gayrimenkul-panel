from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.db.models import Q, Count, Avg, Sum, F
from django.utils import timezone
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
import json

from .models import Lead, SalesStage, Task, LeadNote, StageTransition, LeadAssignment, Appointment, ActionLog
from .assignment_service import AssignmentService
from django.contrib.auth import get_user_model

User = get_user_model()


def is_manager(user):
    """Check if user is a manager"""
    return user.is_staff or user.groups.filter(name='Managers').exists()


@login_required
@user_passes_test(is_manager)
def manager_kanban(request):
    """
    Manager kanban dashboard with analytics and team overview
    """
    try:
        # Get specific stages for manager workflow
        sozlesme_yapildi_stage = SalesStage.objects.get(name='sozlesme_yapildi')
        kredi_islemleri_stage = SalesStage.objects.get(name='kredi_islemleri')
        tapu_islemi_stage = SalesStage.objects.get(name='tapu_islemi')
        hizmet_tamamlandi_stage = SalesStage.objects.get(name='hizmet_tamamlandi')
        memnuniyet_anketi_stage = SalesStage.objects.get(name='memnuniyet_anketi')
        dosya_kapandi_stage = SalesStage.objects.get(name='dosya_kapandi')
        
        # Get leads for each stage
        contract_leads = Lead.objects.filter(current_stage=sozlesme_yapildi_stage).select_related('assigned_staff')
        credit_leads = Lead.objects.filter(current_stage=kredi_islemleri_stage).select_related('assigned_staff')
        deed_leads = Lead.objects.filter(current_stage=tapu_islemi_stage).select_related('assigned_staff')
        service_completed_leads = Lead.objects.filter(current_stage=hizmet_tamamlandi_stage).select_related('assigned_staff')
        satisfaction_survey_leads = Lead.objects.filter(current_stage=memnuniyet_anketi_stage).select_related('assigned_staff')
        closed_leads = Lead.objects.filter(current_stage=dosya_kapandi_stage).select_related('assigned_staff')
        
        # Get all agents (staff users)
        agents = User.objects.filter(
            is_active=True,
            groups__name='Sales_Staff'
        ).annotate(
            active_leads_count=Count('assigned_leads', filter=Q(assigned_leads__status='active'))
        )
        
        context = {
            'sozlesme_yapildi_stage': sozlesme_yapildi_stage,
            'kredi_islemleri_stage': kredi_islemleri_stage,
            'tapu_islemi_stage': tapu_islemi_stage,
            'hizmet_tamamlandi_stage': hizmet_tamamlandi_stage,
            'memnuniyet_anketi_stage': memnuniyet_anketi_stage,
            'dosya_kapandi_stage': dosya_kapandi_stage,
            'contract_leads': contract_leads,
            'credit_leads': credit_leads,
            'deed_leads': deed_leads,
            'service_completed_leads': service_completed_leads,
            'satisfaction_survey_leads': satisfaction_survey_leads,
            'closed_leads': closed_leads,
            'agents': agents,
            'today': timezone.now().date(),
            'page_title': 'Müdür Satış Sonrası Akışı',
        }
        
        return render(request, 'sales_process/manager_kanban.html', context)
        
    except SalesStage.DoesNotExist:
        messages.error(request, 'Satış aşamaları henüz oluşturulmamış. Lütfen sistem yöneticinizle iletişime geçin.')
        return redirect('sales_process:dashboard')


@login_required
@user_passes_test(is_manager)
def get_manager_leads_ajax(request):
    """
    Get leads data for manager kanban view with filters
    """
    # Get filter parameters
    agent_id = request.GET.get('agent')
    priority = request.GET.get('priority')
    source = request.GET.get('source')
    date_filter = request.GET.get('date')
    search = request.GET.get('search')
    
    # Base queryset
    leads = Lead.objects.filter(status='active').select_related(
        'assigned_to', 'current_stage'
    )
    
    # Apply filters
    if agent_id:
        leads = leads.filter(assigned_to_id=agent_id)
    
    if priority:
        leads = leads.filter(priority=priority)
    
    if source:
        leads = leads.filter(source=source)
    
    if date_filter:
        filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
        leads = leads.filter(created_at__date=filter_date)
    
    if search:
        leads = leads.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search)
        )
    
    # Prepare leads data
    leads_data = []
    for lead in leads:
        leads_data.append({
            'id': lead.id,
            'first_name': lead.first_name,
            'last_name': lead.last_name,
            'phone': lead.phone,
            'email': lead.email,
            'priority': lead.priority,
            'priority_display': lead.get_priority_display(),
            'source': lead.source,
            'current_stage_id': lead.current_stage.id if lead.current_stage else None,
            'current_stage_slug': lead.current_stage.slug if lead.current_stage else 'new',
            'assigned_to_name': lead.assigned_to.get_full_name() if lead.assigned_to else None,
            'created_at_display': lead.created_at.strftime('%d.%m.%Y') if lead.created_at else 'Tarih Yok',
            'last_activity': lead.updated_at.strftime('%d.%m.%Y %H:%M') if lead.updated_at else 'Tarih Yok',
        })
    
    # Calculate statistics
    total_leads = leads.count()
    conversion_rate = 0
    avg_response_time = 0
    
    if total_leads > 0:
        closed_won = leads.filter(current_stage__slug='closed-won').count()
        conversion_rate = round((closed_won / total_leads) * 100, 1)
        
        # Calculate average response time (simplified)
        avg_response_time = 2.5  # This would be calculated from actual response data
    
    return JsonResponse({
        'success': True,
        'leads': leads_data,
        'statistics': {
            'total_leads': total_leads,
            'conversion_rate': conversion_rate,
            'avg_response_time': avg_response_time,
        }
    })


@login_required
@user_passes_test(is_manager)
def manager_analytics(request):
    """
    Get analytics data for manager dashboard
    """
    # Date range for analytics
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Team performance
    team_performance = []
    agents = User.objects.filter(
        is_active=True,
        groups__name='Sales_Staff'
    ).annotate(
        active_leads=Count('assigned_leads', filter=Q(assigned_leads__status='active')),
        closed_leads=Count('assigned_leads', filter=Q(
            assigned_leads__current_stage__slug='closed-won',
            assigned_leads__updated_at__date__gte=start_date
        )),
        total_leads=Count('assigned_leads', filter=Q(
            assigned_leads__created_at__date__gte=start_date
        ))
    )
    
    for agent in agents:
        conversion_rate = 0
        if agent.total_leads > 0:
            conversion_rate = round((agent.closed_leads / agent.total_leads) * 100, 1)
        
        team_performance.append({
            'name': agent.get_full_name(),
            'active_leads': agent.active_leads,
            'conversion_rate': conversion_rate,
            'total_leads': agent.total_leads,
        })
    
    # Stage distribution
    stages = SalesStage.objects.filter(is_active=True)
    stage_distribution = {
        'labels': [],
        'data': []
    }
    
    for stage in stages:
        count = Lead.objects.filter(
            current_stage=stage,
            is_active=True
        ).count()
        stage_distribution['labels'].append(stage.name)
        stage_distribution['data'].append(count)
    
    # Priority distribution
    priority_counts = Lead.objects.filter(
        is_active=True
    ).values('priority').annotate(
        count=Count('id')
    ).order_by('priority')
    
    priority_distribution = [0, 0, 0]  # high, medium, low
    for item in priority_counts:
        if item['priority'] == 'high':
            priority_distribution[0] = item['count']
        elif item['priority'] == 'medium':
            priority_distribution[1] = item['count']
        elif item['priority'] == 'low':
            priority_distribution[2] = item['count']
    
    # Recent activities
    recent_activities = []
    recent_transitions = StageTransition.objects.select_related(
        'lead', 'changed_by', 'from_stage', 'to_stage'
    ).order_by('-created_at')[:10]
    
    for transition in recent_transitions:
        recent_activities.append({
            'user': transition.changed_by.get_full_name() if transition.changed_by else 'Sistem',
            'action': f"{transition.lead.first_name} {transition.lead.last_name} - {transition.from_stage.name if transition.from_stage else 'Yeni'} → {transition.to_stage.name}",
            'timestamp': transition.created_at.strftime('%d.%m.%Y %H:%M'),
        })
    
    return JsonResponse({
        'success': True,
        'team_performance': team_performance,
        'stage_distribution': stage_distribution,
        'priority_distribution': priority_distribution,
        'recent_activities': recent_activities,
    })


@login_required
@user_passes_test(is_manager)
@require_http_methods(["POST"])
def bulk_assign_leads(request):
    """
    Bulk assign multiple leads to agents
    """
    try:
        data = json.loads(request.body)
        lead_ids = data.get('lead_ids', [])
        agent_id = data.get('agent_id')
        assignment_type = data.get('assignment_type', 'manual')
        
        if not lead_ids or not agent_id:
            return JsonResponse({
                'success': False,
                'message': 'Lead IDs ve agent ID gerekli'
            })
        
        agent = get_object_or_404(User, id=agent_id)
        assignment_service = AssignmentService()
        
        assigned_count = 0
        for lead_id in lead_ids:
            try:
                lead = Lead.objects.get(id=lead_id, status='active')
                success = assignment_service.assign_lead_to_user(
                    lead=lead,
                    user=agent,
                    assignment_type=assignment_type,
                    assigned_by=request.user,
                    reason=f"Bulk assignment by {request.user.get_full_name()}"
                )
                if success:
                    assigned_count += 1
            except Lead.DoesNotExist:
                continue
        
        return JsonResponse({
            'success': True,
            'assigned_count': assigned_count,
            'message': f'{assigned_count} lead başarıyla atandı'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Hata: {str(e)}'
        })


@login_required
@user_passes_test(is_manager)
def team_performance_report(request):
    """
    Detailed team performance report
    """
    # Date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = (timezone.now().date() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().date().strftime('%Y-%m-%d')
    
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get team performance data
    agents = User.objects.filter(
        is_active=True,
        groups__name='Sales_Staff'
    ).annotate(
        total_assigned=Count('assigned_leads', filter=Q(
            assigned_leads__created_at__date__gte=start_date,
            assigned_leads__created_at__date__lte=end_date
        )),
        closed_won=Count('assigned_leads', filter=Q(
            assigned_leads__current_stage__slug='closed-won',
            assigned_leads__updated_at__date__gte=start_date,
            assigned_leads__updated_at__date__lte=end_date
        )),
        closed_lost=Count('assigned_leads', filter=Q(
            assigned_leads__current_stage__slug='closed-lost',
            assigned_leads__updated_at__date__gte=start_date,
            assigned_leads__updated_at__date__lte=end_date
        )),
        active_leads=Count('assigned_leads', filter=Q(
            assigned_leads__status='active'
        ))
    )
    
    performance_data = []
    for agent in agents:
        conversion_rate = 0
        if agent.total_assigned > 0:
            conversion_rate = round((agent.closed_won / agent.total_assigned) * 100, 1)
        
        performance_data.append({
            'agent': agent,
            'total_assigned': agent.total_assigned,
            'closed_won': agent.closed_won,
            'closed_lost': agent.closed_lost,
            'active_leads': agent.active_leads,
            'conversion_rate': conversion_rate,
        })
    
    context = {
        'performance_data': performance_data,
        'start_date': start_date,
        'end_date': end_date,
        'page_title': 'Takım Performans Raporu',
    }
    
    return render(request, 'sales_process/team_performance_report.html', context)


@login_required
@user_passes_test(is_manager)
def lead_distribution_report(request):
    """
    Lead distribution and pipeline analysis
    """
    # Stage distribution
    stages = SalesStage.objects.filter(is_active=True).annotate(
        lead_count=Count('leads', filter=Q(leads__is_active=True)),
        avg_time_in_stage=Avg('stage_transitions_to__time_in_stage')
    ).order_by('order')
    
    # Source distribution
    source_distribution = Lead.objects.filter(
        is_active=True
    ).values('source').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Priority distribution
    priority_distribution = Lead.objects.filter(
        is_active=True
    ).values('priority').annotate(
        count=Count('id')
    ).order_by('priority')
    
    # Monthly trend
    monthly_data = []
    for i in range(6):
        month_start = (timezone.now().date().replace(day=1) - timedelta(days=i*30))
        month_end = month_start + timedelta(days=30)
        
        count = Lead.objects.filter(
            created_at__date__gte=month_start,
            created_at__date__lt=month_end
        ).count()
        
        monthly_data.append({
            'month': month_start.strftime('%B %Y'),
            'count': count
        })
    
    monthly_data.reverse()
    
    context = {
        'stages': stages,
        'source_distribution': source_distribution,
        'priority_distribution': priority_distribution,
        'monthly_data': monthly_data,
        'page_title': 'Lead Dağılım Raporu',
    }
    
    return render(request, 'sales_process/lead_distribution_report.html', context)


@login_required
@user_passes_test(is_manager)
@require_http_methods(["POST"])
def reassign_overdue_leads(request):
    """
    Reassign leads that have been inactive for too long
    """
    try:
        days_threshold = int(request.POST.get('days_threshold', 7))
        new_agent_id = request.POST.get('new_agent_id')
        
        if new_agent_id:
            new_agent = get_object_or_404(User, id=new_agent_id)
        else:
            new_agent = None
        
        assignment_service = AssignmentService()
        result = assignment_service.reassign_overdue_leads(
            days_threshold=days_threshold,
            new_agent=new_agent
        )
        
        return JsonResponse({
            'success': True,
            'reassigned_count': result['reassigned_count'],
            'message': f"{result['reassigned_count']} lead yeniden atandı"
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Hata: {str(e)}'
        })


@login_required
@user_passes_test(is_manager)
def export_manager_reports(request):
    """
    Export manager reports in various formats
    """
    report_type = request.GET.get('type', 'team_performance')
    format_type = request.GET.get('format', 'excel')
    
    # This would implement actual export functionality
    # For now, return a simple response
    
    return JsonResponse({
        'success': True,
        'message': f'{report_type} raporu {format_type} formatında hazırlanıyor...',
        'download_url': f'/sales-process/reports/{report_type}.{format_type}'
    })


@login_required
@user_passes_test(is_manager)
def manager_dashboard_stats(request):
    """
    Get real-time dashboard statistics
    """
    today = timezone.now().date()
    
    # Today's statistics
    today_leads = Lead.objects.filter(created_at__date=today).count()
    today_assignments = LeadAssignment.objects.filter(created_at__date=today).count()
    today_conversions = Lead.objects.filter(
        current_stage__slug='closed-won',
        updated_at__date=today
    ).count()
    
    # Active statistics
    active_leads = Lead.objects.filter(status='active').count()
    unassigned_leads = Lead.objects.filter(status='active', assigned_to__isnull=True).count()
    
    # Team workload
    team_workload = User.objects.filter(
        is_active=True,
        groups__name='Sales_Staff'
    ).annotate(
        active_leads=Count('assigned_leads', filter=Q(assigned_leads__status='active'))
    ).values('id', 'first_name', 'last_name', 'active_leads')
    
    return JsonResponse({
        'success': True,
        'today_stats': {
            'new_leads': today_leads,
            'assignments': today_assignments,
            'conversions': today_conversions,
        },
        'active_stats': {
            'total_leads': active_leads,
            'unassigned_leads': unassigned_leads,
            'assignment_rate': round(((active_leads - unassigned_leads) / active_leads * 100), 1) if active_leads > 0 else 0,
        },
        'team_workload': list(team_workload)
    })


@login_required
@user_passes_test(is_manager)
def manager_lead_detail(request, lead_id):
    """Manager-specific lead detail page with post-sales workflow focus"""
    lead = get_object_or_404(Lead, lead_id=lead_id)
    
    # Get related data
    notes = LeadNote.objects.filter(lead=lead).order_by('-created_at')
    tasks = Task.objects.filter(lead=lead).order_by('-created_at')
    appointments = Appointment.objects.filter(lead=lead).order_by('-scheduled_date')
    action_logs = ActionLog.objects.filter(lead=lead).order_by('-created_at')
    
    # Get stage transitions for this lead
    stage_transitions = StageTransition.objects.filter(lead=lead).order_by('-created_at')
    
    # Manager-specific context
    context = {
        'title': f'{lead.customer_name} - Müdür Detayı',
        'lead': lead,
        'notes': notes,
        'tasks': tasks,
        'appointments': appointments,
        'action_logs': action_logs,
        'stage_transitions': stage_transitions,
        'is_manager_view': True,
        'today': timezone.now().date(),
    }
    
    return render(request, 'sales_process/manager_lead_detail.html', context)