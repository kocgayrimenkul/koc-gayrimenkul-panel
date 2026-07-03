# -*- coding: utf-8 -*-
"""
Geçmiş cevapsız çağrıları tarayarak geri dönüş eşleştirmesi yapar.

Kullanım:
    python manage.py check_call_returns
    python manage.py check_call_returns --days=60
    python manage.py check_call_returns --dry-run
"""

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Geçmiş cevapsız çağrılara geri dönüş yapılmış mı kontrol eder ve işaretler."

    def add_arguments(self, parser):
        parser.add_argument(
            '--days', type=int, default=30,
            help='Kaç günlük geçmişe bakılsın (varsayılan: 30)',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Değişiklik kaydetme, sadece raporla',
        )

    def handle(self, *args, **options):
        from apps.calls.models import CallLog

        days    = options['days']
        dry_run = options['dry_run']
        cutoff  = timezone.now() - timezone.timedelta(days=days)
        MISSED  = ('missed', 'busy', 'failed')

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN modu — kayıt yapılmıyor.\n"))

        # Son `days` gündeki çözümlenmemiş cevapsız gelen çağrılar
        missed_calls = CallLog.objects.filter(
            direction='inbound',
            status__in=MISSED,
            is_returned=False,
            start_time__gte=cutoff,
        ).order_by('start_time')

        total   = missed_calls.count()
        matched = 0

        self.stdout.write(
            f"Son {days} günde {total} adet çözümlenmemiş cevapsız çağrı taranıyor...\n"
        )

        for missed in missed_calls:
            caller_norm = CallLog.normalize_phone(missed.caller)
            if not caller_norm:
                continue

            tail = caller_norm[-9:]   # son 9 hane ile eşle

            # Bu cevapsız çağrıdan SONRA aynı numaraya giden çağrı var mı?
            outbound_match = CallLog.objects.filter(
                direction='outbound',
                start_time__gt=missed.start_time,
                called__icontains=tail,
            ).order_by('start_time').first()

            # Veya aynı numaradan gelen ve cevaplanmış çağrı var mı? (müşteri geri aramış)
            inbound_answered = CallLog.objects.filter(
                direction='inbound',
                status='answered',
                start_time__gt=missed.start_time,
                caller__icontains=tail,
            ).order_by('start_time').first()

            # En erken eşleşmeyi al
            candidates = [c for c in [outbound_match, inbound_answered] if c]
            if not candidates:
                continue

            match = min(candidates, key=lambda c: c.start_time)
            matched += 1

            self.stdout.write(
                f"  Eşleşme: #{missed.pk} ({missed.caller} @ {missed.start_time:%d.%m.%Y %H:%M})"
                f" → #{match.pk} ({match.direction} @ {match.start_time:%d.%m.%Y %H:%M})"
            )

            if not dry_run:
                missed.is_returned  = True
                missed.returned_at  = match.start_time
                missed.returned_by  = match.user
                missed.save(update_fields=['is_returned', 'returned_at', 'returned_by'])

        # Özet
        style = self.style.SUCCESS if matched else self.style.NOTICE
        verb  = "işaretlendi" if not dry_run else "işaretlenecekti"
        self.stdout.write(
            style(
                f"\nSonuç: {total} cevapsız çağrıdan {matched} tanesi '{verb}'. "
                f"{total - matched} adet hâlâ beklemede."
            )
        )
