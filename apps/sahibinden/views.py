from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.utils import timezone
import json


# ─── XML FEED (Sahibinden bu URL'yi çeker) ─────────────────────────

def sahibinden_xml_feed(request):
    """
    Sahibinden'in çekeceği XML feed.
    URL: /sahibinden/feed.xml
    Bu URL'yi Sahibinden Pro Ofis > İlan Transferi > API ile Transfer Et'e girin.
    """
    from .services import generate_xml_feed
    xml_content = generate_xml_feed(request)
    return HttpResponse(xml_content, content_type='application/xml; charset=utf-8')


# ─── DASHBOARD ─────────────────────────────────────────────────────

@login_required
def sahibinden_dashboard(request):
    from .models import SahibindenSettings, SahibindenSyncLog
    from apps.portfolio.models import Property

    settings_obj = SahibindenSettings.get_settings()
    sync_logs = SahibindenSyncLog.objects.select_related('property').order_by('-updated_at')[:50]

    total_active = Property.objects.filter(is_active=True).count()
    synced_count = SahibindenSyncLog.objects.filter(status='synced').count()
    error_count = SahibindenSyncLog.objects.filter(status='error').count()
    pending_count = SahibindenSyncLog.objects.filter(status='pending').count()

    # Feed URL
    feed_url = request.build_absolute_uri('/sahibinden/feed.xml')

    context = {
        'segment': 'sahibinden',
        'settings_obj': settings_obj,
        'sync_logs': sync_logs,
        'total_active': total_active,
        'synced_count': synced_count,
        'error_count': error_count,
        'pending_count': pending_count,
        'feed_url': feed_url,
        'has_token': bool(settings_obj.api_token.strip() if settings_obj.api_token else ''),
    }
    return render(request, 'sahibinden/dashboard.html', context)


# ─── AYARLAR KAYDET ────────────────────────────────────────────────

@login_required
def sahibinden_settings_save(request):
    if request.method != 'POST':
        return redirect('sahibinden_dashboard')
    from .models import SahibindenSettings
    s = SahibindenSettings.get_settings()
    s.api_token = request.POST.get('api_token', '').strip()
    s.office_id = request.POST.get('office_id', '').strip()
    s.auto_sync_enabled = request.POST.get('auto_sync_enabled') == 'on'
    s.save()
    messages.success(request, 'Sahibinden API ayarları kaydedildi.')
    return redirect('sahibinden_dashboard')


# ─── AJAX: İÇE AKTAR ───────────────────────────────────────────────

@login_required
def sahibinden_import(request):
    """Sahibinden API'den ilanları çek"""
    from .services import fetch_listings_from_sahibinden
    result = fetch_listings_from_sahibinden()
    return JsonResponse(result)


# ─── AJAX: TEK İLAN GÖNDER ─────────────────────────────────────────

@login_required
def sahibinden_push_property(request, property_id):
    """Tek ilanı Sahibinden'e gönder"""
    from .services import push_property_to_sahibinden
    result = push_property_to_sahibinden(property_id)
    return JsonResponse(result)


# ─── AJAX: TOPLU GÖNDER ────────────────────────────────────────────

@login_required
def sahibinden_push_all(request):
    """Tüm aktif ilanları Sahibinden'e gönder"""
    from .services import push_property_to_sahibinden
    from apps.portfolio.models import Property

    properties = Property.objects.filter(is_active=True)
    total = properties.count()
    success = 0
    errors = []

    for prop in properties:
        result = push_property_to_sahibinden(prop.pk)
        if result['success']:
            success += 1
        else:
            errors.append({'id': prop.pk, 'name': prop.apartment_name, 'error': result['error']})

    return JsonResponse({
        'success': True,
        'total': total,
        'pushed': success,
        'errors': errors,
    })


# ─── AJAX: SYNC LOG DURUMU ─────────────────────────────────────────

@login_required
def sahibinden_sync_toggle(request, property_id):
    """İlanı feed'e dahil et / çıkar"""
    from .models import SahibindenSyncLog
    from apps.portfolio.models import Property
    prop = get_object_or_404(Property, pk=property_id)
    log, _ = SahibindenSyncLog.objects.get_or_create(property=prop)
    log.include_in_feed = not log.include_in_feed
    log.save(update_fields=['include_in_feed'])
    return JsonResponse({'success': True, 'include_in_feed': log.include_in_feed})
