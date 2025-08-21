from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model

User = get_user_model()
from .models import Lead, LeadAssignment, SalesStage, Task
from .assignment_service import AssignmentService
from .forms import LeadFilterForm
import json


@login_required
def assignment_dashboard(request):
    """Atama yönetimi ana sayfası"""
    
    # İstatistikler
    total_leads = Lead.objects.filter(status='active').count()
    assigned_leads = Lead.objects.filter(status='active', assigned_staff__isnull=False).count()
    unassigned_leads = total_leads - assigned_leads
    
    # Sticky assignment istatistikleri
    sticky_assignments = LeadAssignment.objects.filter(
        is_sticky=True, 
        status='active'
    ).count()
    
    # Son 7 günün atama istatistikleri
    week_ago = timezone.now() - timedelta(days=7)
    recent_assignments = LeadAssignment.objects.filter(
        assigned_at__gte=week_ago
    ).values('assignment_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Personel iş yükü dağılımı
    staff_workload = User.objects.filter(
        is_active=True,
        groups__name='Sales Staff'
    ).annotate(
        active_leads=Count('assigned_leads', filter=Q(assigned_leads__status='active')),
        total_assignments=Count('lead_assignments', filter=Q(lead_assignments__status='active'))
    ).order_by('-active_leads')
    
    # Gecikmiş görevler
    overdue_tasks = Task.objects.filter(
        status__in=['pending', 'in_progress'],
        due_date__lt=timezone.now()
    ).count()
    
    context = {
        'total_leads': total_leads,
        'assigned_leads': assigned_leads,
        'unassigned_leads': unassigned_leads,
        'sticky_assignments': sticky_assignments,
        'recent_assignments': recent_assignments,
        'staff_workload': staff_workload,
        'overdue_tasks': overdue_tasks,
    }
    
    return render(request, 'sales_process/assignment_dashboard.html', context)


@login_required
def lead_assignment_list(request):
    """Lead atama geçmişi listesi"""
    
    assignments = LeadAssignment.objects.select_related(
        'lead', 'assigned_to', 'assigned_by'
    ).all()
    
    # Filtreleme
    assignment_type = request.GET.get('assignment_type')
    status = request.GET.get('status')
    assigned_to = request.GET.get('assigned_to')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if assignment_type:
        assignments = assignments.filter(assignment_type=assignment_type)
    if status:
        assignments = assignments.filter(status=status)
    if assigned_to:
        assignments = assignments.filter(assigned_to_id=assigned_to)
    if date_from:
        assignments = assignments.filter(assigned_at__date__gte=date_from)
    if date_to:
        assignments = assignments.filter(assigned_at__date__lte=date_to)
    
    # Sayfalama
    paginator = Paginator(assignments, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Personel listesi (filtre için)
    staff_list = User.objects.filter(
        is_active=True,
        groups__name='Sales Staff'
    ).order_by('first_name', 'last_name')
    
    context = {
        'page_obj': page_obj,
        'staff_list': staff_list,
        'assignment_types': LeadAssignment.ASSIGNMENT_TYPE_CHOICES,
        'status_choices': LeadAssignment.STATUS_CHOICES,
        'filters': {
            'assignment_type': assignment_type,
            'status': status,
            'assigned_to': assigned_to,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    
    return render(request, 'sales_process/lead_assignment_list.html', context)


@login_required
@require_http_methods(["POST"])
def auto_assign_leads(request):
    """Atanmamış lead'leri otomatik ata"""
    
    try:
        # Atanmamış lead'leri al
        unassigned_leads = Lead.objects.filter(
            status='active',
            assigned_staff__isnull=True
        )
        
        assigned_count = 0
        for lead in unassigned_leads:
            assigned_staff = AssignmentService.auto_assign_lead(lead)
            if assigned_staff:
                assigned_count += 1
        
        messages.success(
            request, 
            f'{assigned_count} lead başarıyla otomatik olarak atandı.'
        )
        
        return JsonResponse({
            'success': True,
            'assigned_count': assigned_count,
            'message': f'{assigned_count} lead başarıyla atandı.'
        })
        
    except Exception as e:
        messages.error(request, f'Otomatik atama sırasında hata: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def assign_lead_to_staff(request, lead_id):
    """Belirli bir lead'i personele ata"""
    
    lead = get_object_or_404(Lead, id=lead_id)
    staff_id = request.POST.get('staff_id')
    assignment_reason = request.POST.get('assignment_reason', '')
    
    if not staff_id:
        return JsonResponse({
            'success': False,
            'error': 'Personel seçimi gerekli.'
        })
    
    try:
        staff = User.objects.get(id=staff_id, is_active=True)
        
        # Lead'i ata
        success = AssignmentService.assign_lead_to_user(
            lead=lead,
            user=staff,
            assigned_by=request.user,
            assignment_type='manual',
            reason=assignment_reason
        )
        
        if success:
            messages.success(
                request, 
                f'{lead.customer_name} başarıyla {staff.get_full_name()} kişisine atandı.'
            )
            return JsonResponse({
                'success': True,
                'message': f'Lead başarıyla {staff.get_full_name()} kişisine atandı.'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Lead atama işlemi başarısız.'
            })
            
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Seçilen personel bulunamadı.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def reassign_overdue_leads(request):
    """Gecikmiş lead'leri yeniden ata"""
    
    try:
        reassigned_count = AssignmentService.reassign_overdue_leads()
        
        messages.success(
            request, 
            f'{reassigned_count} gecikmiş lead yeniden atandı.'
        )
        
        return JsonResponse({
            'success': True,
            'reassigned_count': reassigned_count,
            'message': f'{reassigned_count} gecikmiş lead yeniden atandı.'
        })
        
    except Exception as e:
        messages.error(request, f'Yeniden atama sırasında hata: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def balance_workload(request):
    """Personel iş yükünü dengele"""
    
    try:
        balanced_count = AssignmentService.balance_staff_workload()
        
        messages.success(
            request, 
            f'{balanced_count} lead iş yükü dengeleme için yeniden atandı.'
        )
        
        return JsonResponse({
            'success': True,
            'balanced_count': balanced_count,
            'message': f'{balanced_count} lead yeniden atandı.'
        })
        
    except Exception as e:
        messages.error(request, f'İş yükü dengeleme sırasında hata: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def assignment_statistics(request):
    """Atama istatistikleri"""
    
    # Tarih aralığı
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if not date_from:
        date_from = (timezone.now() - timedelta(days=30)).date()
    else:
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
    
    if not date_to:
        date_to = timezone.now().date()
    else:
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
    
    # Atama istatistikleri
    stats = AssignmentService.get_assignment_statistics(
        date_from=date_from,
        date_to=date_to
    )
    
    # Günlük atama trendi
    daily_assignments = LeadAssignment.objects.filter(
        assigned_at__date__range=[date_from, date_to]
    ).extra(
        select={'day': 'date(assigned_at)'}
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    # Atama tipi dağılımı
    assignment_type_distribution = LeadAssignment.objects.filter(
        assigned_at__date__range=[date_from, date_to]
    ).values('assignment_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # En aktif personeller
    top_staff = User.objects.filter(
        lead_assignments__assigned_at__date__range=[date_from, date_to]
    ).annotate(
        assignment_count=Count('lead_assignments')
    ).order_by('-assignment_count')[:10]
    
    context = {
        'stats': stats,
        'daily_assignments': daily_assignments,
        'assignment_type_distribution': assignment_type_distribution,
        'top_staff': top_staff,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'sales_process/assignment_statistics.html', context)


@login_required
def sticky_assignments(request):
    """Sticky assignment yönetimi"""
    
    sticky_assignments = LeadAssignment.objects.filter(
        is_sticky=True,
        status='active'
    ).select_related('lead', 'assigned_to').order_by('-assigned_at')
    
    # Sayfalama
    paginator = Paginator(sticky_assignments, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'sales_process/sticky_assignments.html', context)


@login_required
@require_http_methods(["POST"])
def toggle_sticky_assignment(request, assignment_id):
    """Sticky assignment durumunu değiştir"""
    
    assignment = get_object_or_404(LeadAssignment, id=assignment_id)
    
    try:
        assignment.is_sticky = not assignment.is_sticky
        if assignment.is_sticky:
            assignment.sticky_reason = request.POST.get('sticky_reason', 'Manuel olarak sticky yapıldı')
        else:
            assignment.sticky_reason = ''
        assignment.save()
        
        status = 'aktif' if assignment.is_sticky else 'pasif'
        messages.success(
            request, 
            f'{assignment.lead.customer_name} için sticky assignment {status} hale getirildi.'
        )
        
        return JsonResponse({
            'success': True,
            'is_sticky': assignment.is_sticky,
            'message': f'Sticky assignment {status} hale getirildi.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })