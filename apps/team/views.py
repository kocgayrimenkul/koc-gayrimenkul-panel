from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

# REST Framework imports
from rest_framework import generics, filters
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend

from .models import TeamMember
from .serializers import TeamMemberListSerializer


@login_required
def team_list(request):
    """Ekip üyeleri listesi"""
    search_query = request.GET.get('search', '')
    position_filter = request.GET.get('position', '')
    status_filter = request.GET.get('status', '')
    
    # Ana sorgu
    team_members = TeamMember.objects.all()
    
    # Filtreleme
    if search_query:
        team_members = team_members.filter(
            Q(name__icontains=search_query) |
            Q(custom_position__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    if position_filter:
        team_members = team_members.filter(position=position_filter)
    
    if status_filter == 'active':
        team_members = team_members.filter(is_active=True)
    elif status_filter == 'inactive':
        team_members = team_members.filter(is_active=False)
    
    # Sıralama
    team_members = team_members.order_by('display_order', 'name')
    
    # Sayfalama
    paginator = Paginator(team_members, 20)
    page = request.GET.get('page')
    
    try:
        team_members = paginator.page(page)
    except PageNotAnInteger:
        team_members = paginator.page(1)
    except EmptyPage:
        team_members = paginator.page(paginator.num_pages)
    
    # İstatistikler
    stats = {
        'total': TeamMember.objects.count(),
        'active': TeamMember.objects.filter(is_active=True).count(),
        'inactive': TeamMember.objects.filter(is_active=False).count(),
    }
    
    context = {
        'team_members': team_members,
        'search_query': search_query,
        'position_filter': position_filter,
        'status_filter': status_filter,
        'stats': stats,
        'position_choices': TeamMember.POSITION_CHOICES,
    }
    
    return render(request, 'team/team_list.html', context)


@login_required
def team_detail(request, pk):
    """Ekip üyesi detayı"""
    team_member = get_object_or_404(TeamMember, pk=pk)
    
    context = {
        'team_member': team_member,
    }
    
    return render(request, 'team/team_detail.html', context)


@login_required
def team_create(request):
    """Yeni ekip üyesi ekleme"""
    if request.method == 'POST':
        # Form verilerini al
        name = request.POST.get('name', '').strip()
        position = request.POST.get('position', '')
        custom_position = request.POST.get('custom_position', '').strip()
        image_url = request.POST.get('image_url', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        display_order = request.POST.get('display_order', '0')
        
        # Validasyon
        if not name:
            messages.error(request, 'Ad Soyad alanı zorunludur.')
            return render(request, 'team/team_create.html', {
                'position_choices': TeamMember.POSITION_CHOICES,
                'form_data': request.POST
            })
        
        if not position:
            messages.error(request, 'Pozisyon seçimi zorunludur.')
            return render(request, 'team/team_create.html', {
                'position_choices': TeamMember.POSITION_CHOICES,
                'form_data': request.POST
            })
        
        try:
            # Yeni ekip üyesini oluştur
            team_member = TeamMember.objects.create(
                name=name,
                position=position,
                custom_position=custom_position if custom_position else None,
                image_url=image_url if image_url else None,
                is_active=is_active,
                display_order=int(display_order) if display_order else 0
            )
            
            # Dosya yükleme
            if 'image' in request.FILES:
                team_member.image = request.FILES['image']
                team_member.save()
            
            messages.success(request, f'{name} başarıyla ekip üyesi olarak eklendi.')
            return redirect('team:team_detail', pk=team_member.pk)
            
        except ValueError as e:
            messages.error(request, f'Geçersiz veri girişi: {str(e)}')
        except Exception as e:
            messages.error(request, f'Ekip üyesi eklenirken bir hata oluştu: {str(e)}')
    
    context = {
        'position_choices': TeamMember.POSITION_CHOICES,
        'form_data': {}
    }
    
    return render(request, 'team/team_create.html', context)


@login_required
def team_update(request, pk):
    """Ekip üyesi güncelleme"""
    team_member = get_object_or_404(TeamMember, pk=pk)
    
    if request.method == 'POST':
        # Form verilerini al
        name = request.POST.get('name', '').strip()
        position = request.POST.get('position', '')
        custom_position = request.POST.get('custom_position', '').strip()
        image_url = request.POST.get('image_url', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        display_order = request.POST.get('display_order', '0')
        
        # Validasyon
        if not name:
            messages.error(request, 'Ad Soyad alanı zorunludur.')
            return render(request, 'team/team_update.html', {
                'team_member': team_member,
                'position_choices': TeamMember.POSITION_CHOICES,
                'form_data': request.POST
            })
        
        if not position:
            messages.error(request, 'Pozisyon seçimi zorunludur.')
            return render(request, 'team/team_update.html', {
                'team_member': team_member,
                'position_choices': TeamMember.POSITION_CHOICES,
                'form_data': request.POST
            })
        
        try:
            # Ekip üyesini güncelle
            team_member.name = name
            team_member.position = position
            team_member.custom_position = custom_position if custom_position else None
            team_member.image_url = image_url if image_url else None
            team_member.is_active = is_active
            team_member.display_order = int(display_order) if display_order else 0
            
            # Dosya yükleme
            if 'image' in request.FILES:
                team_member.image = request.FILES['image']
            
            team_member.save()
            
            messages.success(request, f'{name} başarıyla güncellendi.')
            return redirect('team:team_detail', pk=team_member.pk)
            
        except ValueError as e:
            messages.error(request, f'Geçersiz veri girişi: {str(e)}')
        except Exception as e:
            messages.error(request, f'Ekip üyesi güncellenirken bir hata oluştu: {str(e)}')
    
    context = {
        'team_member': team_member,
        'position_choices': TeamMember.POSITION_CHOICES,
        'form_data': {}
    }
    
    return render(request, 'team/team_update.html', context)


@login_required
@require_http_methods(["POST"])
def team_toggle_status(request, pk):
    """Ekip üyesinin aktiflik durumunu değiştirir"""
    team_member = get_object_or_404(TeamMember, pk=pk)
    
    field = request.POST.get('field')
    
    if field == 'is_active':
        team_member.is_active = not team_member.is_active
        team_member.save()
        
        status = "aktif" if team_member.is_active else "pasif"
        return JsonResponse({
            'success': True,
            'message': f'{team_member.name} {status} yapıldı.',
            'new_status': team_member.is_active
        })
    
    elif field == 'is_featured':
        team_member.is_featured = not team_member.is_featured
        team_member.save()
        
        status = "öne çıkarıldı" if team_member.is_featured else "öne çıkarma kaldırıldı"
        return JsonResponse({
            'success': True,
            'message': f'{team_member.name} {status}.',
            'new_status': team_member.is_featured
        })
    
    return JsonResponse({'success': False, 'message': 'Geçersiz işlem.'})


@login_required
@require_http_methods(["POST"])
def team_update_order(request, pk):
    """Ekip üyesinin sıralama numarasını günceller"""
    team_member = get_object_or_404(TeamMember, pk=pk)
    
    new_order = request.POST.get('order')
    
    try:
        new_order = int(new_order)
        team_member.display_order = new_order
        team_member.save()
        
        return JsonResponse({
            'success': True,
            'message': f'{team_member.name} sıralaması güncellendi.'
        })
    except (ValueError, TypeError):
        return JsonResponse({
            'success': False,
            'message': 'Geçersiz sıralama numarası.'
        })


@login_required
@require_http_methods(["POST"])
def team_delete(request, pk):
    """Ekip üyesini siler"""
    team_member = get_object_or_404(TeamMember, pk=pk)
    name = team_member.name
    
    try:
        # Silme işlemini gerçekleştir
        team_member.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'{name} başarıyla silindi.'
        })
        
    except Exception as e:
        # Hata logunu kaydet
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Team member deletion failed for {name}: {str(e)}')
        
        return JsonResponse({
            'success': False,
            'message': f'Silme işlemi başarısız: {str(e)}'
        })


# REST Framework API Views
class TeamMemberListAPIView(generics.ListAPIView):
    """Ekip üyeleri listesi REST API"""
    queryset = TeamMember.objects.filter(is_active=True).order_by('display_order', 'name')
    serializer_class = TeamMemberListSerializer
    permission_classes = [AllowAny]
    pagination_class = None  # Pagination'ı kapat
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filtreleme alanları
    filterset_fields = {
        'position': ['exact'],
        'is_active': ['exact'],
    }
    
    # Arama alanları
    search_fields = ['name', 'custom_position']
    
    # Sıralama alanları
    ordering_fields = ['display_order', 'name', 'created_at']
    ordering = ['display_order', 'name']
