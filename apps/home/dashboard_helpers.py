# -*- coding: utf-8 -*-
"""
Koc Gayrimenkul Panel - Dashboard Helpers
==========================================
Anasayfa icin yardimci context hesaplamalari.
Phase 2: Cagri istatistikleri + 4 sekmeli performans grafigi.
"""
import json
from datetime import timedelta
from django.db.models import Q


def get_phase2_dashboard_context(user, today, date_from):
    """
    Anasayfa icin Faz 2 context degiskenlerini hesaplar.

    Args:
        user: request.user
        today: timezone.now().date()
        date_from: Tarih filtresine gore baslangic tarihi

    Returns:
        dict: context'e merge edilecek yeni anahtarlar
    """
    # Lazy imports - app henuz yuklenmemis olabilir
    from apps.calls.models import CallLog
    from apps.employees.models import EmployeeProfile, UserNote, UserTask
    from apps.customers.models import CustomerOffer

    ctx = {}

    # ====================================================================
    # 1) BUGUNKU CAGRI ISTATISTIKLERI (uc kutu)
    # ====================================================================
    today_incoming = CallLog.objects.filter(
        start_time__date=today,
        direction='inbound',
    )
    total_inbound = today_incoming.count()
    returned = today_incoming.filter(is_returned=True).count()
    not_returned = total_inbound - returned

    ctx['today_calls_total'] = total_inbound
    ctx['today_calls_returned'] = returned
    ctx['today_calls_not_returned'] = not_returned
    ctx['call_return_rate'] = (
        round((returned / total_inbound) * 100) if total_inbound > 0 else 0
    )

    # ====================================================================
    # 2) AKTIF DANISMANLAR (grafik etiketleri icin)
    # ====================================================================
    consultants = list(
        EmployeeProfile.objects.filter(
            role='consultant',
            is_active=True,
        ).select_related('user')
    )

    # ====================================================================
    # 3) SEKME 1: Personel bazinda tamamlanan gorev sayisi
    # ====================================================================
    chart_tasks_labels = []
    chart_tasks_data = []
    for cp in consultants:
        chart_tasks_labels.append(cp.user.get_full_name() or cp.user.username)
        chart_tasks_data.append(
            UserTask.objects.filter(
                user=cp.user,
                status='completed',
                completed_at__gte=date_from,
            ).count()
        )

    ctx['chart_tasks_labels'] = json.dumps(chart_tasks_labels)
    ctx['chart_tasks_data'] = json.dumps(chart_tasks_data)

    # ====================================================================
    # 4) SEKME 2: Personel bazinda cagri donus orani
    # ====================================================================
    chart_call_labels = []
    chart_call_data = []
    for cp in consultants:
        user_calls = CallLog.objects.filter(
            start_time__gte=date_from,
            direction='inbound',
        ).filter(Q(user=cp.user) | Q(returned_by=cp.user))
        total = user_calls.count()
        ret = user_calls.filter(is_returned=True).count()
        rate = round((ret / total) * 100) if total > 0 else 0
        chart_call_labels.append(cp.user.get_full_name() or cp.user.username)
        chart_call_data.append(rate)

    ctx['chart_call_labels'] = json.dumps(chart_call_labels)
    ctx['chart_call_data'] = json.dumps(chart_call_data)

    # ====================================================================
    # 5) SEKME 3: Personel bazinda teklif sayisi
    # ====================================================================
    chart_offer_labels = []
    chart_offer_data = []
    for cp in consultants:
        chart_offer_labels.append(cp.user.get_full_name() or cp.user.username)
        chart_offer_data.append(
            CustomerOffer.objects.filter(
                created_by=cp.user,
                created_at__gte=date_from,
            ).count()
        )

    ctx['chart_offer_labels'] = json.dumps(chart_offer_labels)
    ctx['chart_offer_data'] = json.dumps(chart_offer_data)

    # ====================================================================
    # 6) SEKME 4: Genel sistem - gunluk cagri trendi (son 30 gun)
    # ====================================================================
    daily_labels = []
    daily_inbound = []
    daily_returned = []
    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        day_qs = CallLog.objects.filter(
            start_time__date=day,
            direction='inbound',
        )
        daily_labels.append(day.strftime('%d.%m'))
        daily_inbound.append(day_qs.count())
        daily_returned.append(day_qs.filter(is_returned=True).count())

    ctx['chart_daily_labels'] = json.dumps(daily_labels)
    ctx['chart_daily_inbound'] = json.dumps(daily_inbound)
    ctx['chart_daily_returned'] = json.dumps(daily_returned)

    # ====================================================================
    # 7) KULLANICININ KENDI GOREV/NOT SAYILARI (sag panel ozetler icin)
    # ====================================================================
    ctx['my_tasks_pending'] = UserTask.objects.filter(
        user=user,
        status__in=['pending', 'in_progress'],
    ).count()

    ctx['my_tasks_overdue'] = UserTask.objects.filter(
        user=user,
        status='overdue',
    ).count()

    ctx['my_notes_active'] = UserNote.objects.filter(
        user=user,
        is_completed=False,
    ).count()

    return ctx
