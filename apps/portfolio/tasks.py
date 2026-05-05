# -*- coding: utf-8 -*-
"""
apps/portfolio/tasks.py
Günlük çalışan Celery görevi: 30 günü geçen portal ilanlarını temizle
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(name='portfolio.expire_portal_listings')
def expire_portal_listings():
    """
    30 günü geçen portal ilan numaralarını temizle,
    ilgili danışmana bildirim oluştur.
    """
    from .models import Property, PortalNotification

    expiry_date = timezone.now() - timedelta(days=30)
    expired_count = 0

    # Her portal için kontrol
    portals = [
        ('owner_listing_number',     'owner_listing_updated_at',     'sahibinden'),
        ('emlakjet_listing_number',  'emlakjet_listing_updated_at',  'emlakjet'),
        ('hepsiemlak_listing_number','hepsiemlak_listing_updated_at','hepsiemlak'),
    ]

    for number_field, date_field, portal_key in portals:
        # 30 günden eski ve numarası dolu olan ilanlar
        expired_props = Property.objects.filter(
            is_active=True,
            **{
                f'{number_field}__gt': '',       # boş değil
                f'{date_field}__lt': expiry_date, # 30 günden eski
            }
        ).exclude(**{number_field: ''}).select_related('consultant')

        for prop in expired_props:
            # İlan numarasını temizle
            setattr(prop, number_field, '')
            setattr(prop, date_field, None)
            prop.save(update_fields=[number_field, date_field])

            # Danışmana bildirim oluştur (aynı bildirim yoksa)
            if prop.consultant:
                already_exists = PortalNotification.objects.filter(
                    property=prop,
                    portal=portal_key,
                    is_read=False,
                ).exists()

                if not already_exists:
                    PortalNotification.objects.create(
                        user=prop.consultant,
                        property=prop,
                        portal=portal_key,
                    )
                    logger.info(
                        f"[expire_portal_listings] {portal_key} - "
                        f"{prop.apartment_name} - {prop.consultant} bildirimi oluşturuldu."
                    )

            expired_count += 1

    logger.info(f"[expire_portal_listings] Toplam {expired_count} ilan temizlendi.")
    return f"{expired_count} ilan temizlendi."