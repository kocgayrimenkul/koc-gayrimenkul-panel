# -*- coding: utf-8 -*-
import json
import math
from datetime import date as date_cls

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST, require_http_methods
from django.utils import timezone
from django.contrib import messages

from .models import (
    ParselKayit, SahaGorusme,
    SahaGorevPlani, GunlukGorev, BrokerBildirim,
    _calisma_gunleri, _calisma_gun_listesi, AY_SECENEKLER,
)

User = get_user_model()

# Tum parsel alanlari (yeni + eski)
PARSEL_STR_FIELDS = [
    'adres', 'ada_no', 'parsel_no', 'mahalle', 'durum',
    'muteahit_ad', 'muteahit_tel',
    'bekci_ad', 'bekci_tel',
    'cavus_ad', 'cavus_tel',
    'arsa_sahibi_ad', 'arsa_sahibi_tel',
    'oturuma_yonetici_ad', 'oturuma_yonetici_tel',
    'oturuma_bekci_ad', 'oturuma_bekci_tel',
    'yonetici_ad', 'yonetici_tel',
    'kapici_ad', 'kapici_tel',
    'diger_not',
]


def _parsel_to_dict(k):
    return {
        'id': k.id, 'lat': k.lat, 'lng': k.lng,
        'adres': k.adres, 'ada_no': k.ada_no, 'parsel_no': k.parsel_no,
        'mahalle': k.mahalle,
        'durum': k.durum,
        'muteahit_ad': k.muteahit_ad, 'muteahit_tel': k.muteahit_tel,
        'bekci_ad': k.bekci_ad, 'bekci_tel': k.bekci_tel,
        'cavus_ad': k.cavus_ad, 'cavus_tel': k.cavus_tel,
        'taseronlar': k.taseronlar or [],
        'arsa_sahibi_ad': k.arsa_sahibi_ad, 'arsa_sahibi_tel': k.arsa_sahibi_tel,
        'oturuma_yonetici_ad': k.oturuma_yonetici_ad, 'oturuma_yonetici_tel': k.oturuma_yonetici_tel,
        'oturuma_bekci_ad': k.oturuma_bekci_ad, 'oturuma_bekci_tel': k.oturuma_bekci_tel,
        'oturuma_ek_kisiler': k.oturuma_ek_kisiler or [],
        'dolu_ek_kisiler': k.dolu_ek_kisiler or [],
        'yonetici_ad': k.yonetici_ad, 'yonetici_tel': k.yonetici_tel,
        'kapici_ad': k.kapici_ad, 'kapici_tel': k.kapici_tel,
        'diger_not': k.diger_not,
        'portfoy_sayisi': k.portfoy_sayisi,
        'gorusme_sayisi': k.gorusmeler.count(),
        'son_gorusme': (
            k.gorusmeler.first().tarih.strftime('%d.%m.%Y %H:%M')
            if k.gorusmeler.exists() else None
        ),
        'son_gorusme_gun': (
            (timezone.now() - k.gorusmeler.first().tarih).days
            if k.gorusmeler.exists() else None
        ),
    }


@login_required(login_url='/login/')
def saha_harita(request):
    from apps.customers.models import Neighborhood
    user = request.user
    is_broker = user.is_superuser or user.has_role('Mudur') or user.has_role('Yonetici')

    baslangic_lat = 37.0662
    baslangic_lng = 37.3833
    baslangic_zoom = 12
    mahalle_adi = ''

    if not is_broker:
        # Kullanicinin atandigi mahalleler
        mahalleler = list(Neighborhood.objects.filter(consultant=user).values_list('name', flat=True))
        if mahalleler:
            mahalle_adi = mahalleler[0]
            # O mahalledeki parsellerden merkez hesapla
            parseller = ParselKayit.objects.filter(mahalle__iexact=mahalle_adi)
            if parseller.exists():
                lats = [p.lat for p in parseller]
                lngs = [p.lng for p in parseller]
                baslangic_lat = sum(lats) / len(lats)
                baslangic_lng = sum(lngs) / len(lngs)
                baslangic_zoom = 15

    return render(request, 'saha/harita.html', {
        'segment': 'saha',
        'baslangic_lat': baslangic_lat,
        'baslangic_lng': baslangic_lng,
        'baslangic_zoom': baslangic_zoom,
        'mahalle_adi': mahalle_adi,
    })


@login_required(login_url='/login/')
def parsel_detay(request, parsel_id):
    parsel = get_object_or_404(ParselKayit, pk=parsel_id)
    gorusmeler = parsel.gorusmeler.select_related('personel').order_by('-tarih')

    # Aktivite listesi oluştur
    aktiviteler = []
    for g in gorusmeler:
        aktiviteler.append({
            'tur': 'gorusme',
            'tarih': g.tarih,
            'metin': g.not_metni,
            'personel': g.personel.get_full_name() if g.personel else '—',
            'gorusulen_kisi': g.gorusulen_kisi,
        })

    return render(request, 'saha/parsel_detay.html', {
        'segment': 'saha',
        'parsel': parsel,
        'aktiviteler': aktiviteler,
        'gorusme_sayisi': gorusmeler.count(),
        'portfoy_sayisi': parsel.portfoy_sayisi,
    })


@login_required(login_url='/login/')
def api_parseller(request):
    kayitlar = ParselKayit.objects.prefetch_related('gorusmeler__personel').all()
    return JsonResponse({'parseller': [_parsel_to_dict(k) for k in kayitlar]})


@login_required(login_url='/login/')
@require_POST
def api_parsel_ekle(request):
    try:
        body = json.loads(request.body)
        kayit = ParselKayit.objects.create(
            lat=float(body['lat']),
            lng=float(body['lng']),
            adres=body.get('adres', ''),
            ada_no=body.get('ada_no', ''),
            parsel_no=body.get('parsel_no', ''),
            mahalle=body.get('mahalle', ''),
            durum=body.get('durum', ''),
            muteahit_ad=body.get('muteahit_ad', ''),
            muteahit_tel=body.get('muteahit_tel', ''),
            bekci_ad=body.get('bekci_ad', ''),
            bekci_tel=body.get('bekci_tel', ''),
            cavus_ad=body.get('cavus_ad', ''),
            cavus_tel=body.get('cavus_tel', ''),
            taseronlar=body.get('taseronlar', []),
            arsa_sahibi_ad=body.get('arsa_sahibi_ad', ''),
            arsa_sahibi_tel=body.get('arsa_sahibi_tel', ''),
            oturuma_yonetici_ad=body.get('oturuma_yonetici_ad', ''),
            oturuma_yonetici_tel=body.get('oturuma_yonetici_tel', ''),
            oturuma_bekci_ad=body.get('oturuma_bekci_ad', ''),
            oturuma_bekci_tel=body.get('oturuma_bekci_tel', ''),
            oturuma_ek_kisiler=body.get('oturuma_ek_kisiler', []),
            dolu_ek_kisiler=body.get('dolu_ek_kisiler', []),
            yonetici_ad=body.get('yonetici_ad', ''),
            yonetici_tel=body.get('yonetici_tel', ''),
            kapici_ad=body.get('kapici_ad', ''),
            kapici_tel=body.get('kapici_tel', ''),
            diger_not=body.get('diger_not', ''),
            olusturan=request.user,
        )
        return JsonResponse({'success': True, 'id': kayit.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def api_parsel_detay(request, parsel_id):
    try:
        kayit = ParselKayit.objects.prefetch_related('gorusmeler__personel').get(pk=parsel_id)
    except ParselKayit.DoesNotExist:
        return JsonResponse({'error': 'Parsel bulunamadi'}, status=404)

    if request.method == 'POST':
        body = json.loads(request.body)
        for f in PARSEL_STR_FIELDS:
            if f in body:
                setattr(kayit, f, body[f])
        if 'taseronlar' in body:
            kayit.taseronlar = body['taseronlar']
        if 'oturuma_ek_kisiler' in body:
            kayit.oturuma_ek_kisiler = body['oturuma_ek_kisiler']
        if 'dolu_ek_kisiler' in body:
            kayit.dolu_ek_kisiler = body['dolu_ek_kisiler']
        kayit.save()
        return JsonResponse({'success': True})

    gorusmeler = [
        {'id': g.id,
         'personel': g.personel.get_full_name() if g.personel else 'Bilinmiyor',
         'tarih': g.tarih.strftime('%d.%m.%Y %H:%M'),
         'not_metni': g.not_metni}
        for g in kayit.gorusmeler.all()
    ]
    d = _parsel_to_dict(kayit)
    d['gorusmeler'] = gorusmeler
    return JsonResponse(d)


@login_required(login_url='/login/')
@require_POST
def api_parsel_sil(request, parsel_id):
    try:
        ParselKayit.objects.get(pk=parsel_id).delete()
        return JsonResponse({'success': True})
    except ParselKayit.DoesNotExist:
        return JsonResponse({'error': 'Bulunamadi'}, status=404)


@login_required(login_url='/login/')
@require_POST
def api_gorusme_ekle(request, parsel_id):
    try:
        kayit = ParselKayit.objects.get(pk=parsel_id)
        body = json.loads(request.body)
        not_metni = body.get('not_metni', '').strip()
        gorusulen_kisi = body.get('gorusulen_kisi', '').strip()
        if not not_metni:
            return JsonResponse({'error': 'Not bos olamaz'}, status=400)
        gorusme = SahaGorusme.objects.create(
            parsel=kayit, personel=request.user, not_metni=not_metni,
            gorusulen_kisi=gorusulen_kisi,
        )
        return JsonResponse({
            'success': True,
            'gorusme': {
                'id': gorusme.id,
                'personel': request.user.get_full_name(),
                'gorusulen_kisi': gorusme.gorusulen_kisi,
                'tarih': gorusme.tarih.strftime('%d.%m.%Y %H:%M'),
                'not_metni': gorusme.not_metni,
            }
        })
    except ParselKayit.DoesNotExist:
        return JsonResponse({'error': 'Parsel bulunamadi'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required(login_url='/login/')
@require_POST
def api_portfoy_guncelle(request, parsel_id):
    """Portföy alındı/alınmadı güncelle"""
    try:
        kayit = ParselKayit.objects.get(pk=parsel_id)
        body = json.loads(request.body)
        eylem = body.get('eylem')  # 'alindi' veya 'alinmadi'
        if eylem == 'alindi':
            kayit.portfoy_sayisi = kayit.portfoy_sayisi + 1
            kayit.save(update_fields=['portfoy_sayisi'])
            return JsonResponse({'success': True, 'portfoy_sayisi': kayit.portfoy_sayisi})
        elif eylem == 'alinmadi':
            # Bilgi kaydı - sayıyı değiştirme
            return JsonResponse({'success': True, 'portfoy_sayisi': kayit.portfoy_sayisi})
        else:
            return JsonResponse({'error': 'Geçersiz eylem'}, status=400)
    except ParselKayit.DoesNotExist:
        return JsonResponse({'error': 'Parsel bulunamadı'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ---- GOREV SISTEMI ----------------------------------------------------------

@login_required(login_url='/login/')
def gorev_plani_listesi(request):
    user = request.user
    if user.is_superuser or user.has_role('Muteahit') or user.has_role('Yonetici') or user.has_role('Broker') or user.has_role('Manager'):
        planlar = SahaGorevPlani.objects.select_related('bolge_uzmani', 'atayan_broker').all()
        is_broker = True
    elif user.has_role('Muteahit') or user.has_role('Mudur') or user.has_role('Yonetici'):
        planlar = SahaGorevPlani.objects.select_related('bolge_uzmani', 'atayan_broker').all()
        is_broker = True
    else:
        planlar = SahaGorevPlani.objects.select_related(
            'bolge_uzmani', 'atayan_broker').filter(bolge_uzmani=user)
        is_broker = False

    bolge_uzmanlari = User.objects.filter(
        groups__name__in=['Danishman', 'Calisanlar']
    ).distinct().order_by('first_name', 'last_name')

    bugun = date_cls.today()
    return render(request, 'saha/gorev_plani.html', {
        'segment': 'saha',
        'planlar': planlar,
        'is_broker': is_broker,
        'bolge_uzmanlari': bolge_uzmanlari,
        'ay_secenekler': AY_SECENEKLER,
        'bugun_yil': bugun.year,
        'bugun_ay': bugun.month,
    })


@login_required(login_url='/login/')
@require_POST
def gorev_plani_olustur(request):
    try:
        mahalle_adi = request.POST.get('mahalle_adi', '').strip()
        bolge_uzmani_id = request.POST.get('bolge_uzmani_id')
        yil = int(request.POST.get('yil'))
        ay = int(request.POST.get('ay'))

        if not mahalle_adi or not bolge_uzmani_id:
            messages.error(request, 'Mahalle adi ve bolge uzmani zorunludur.')
            return redirect('gorev_plani_listesi')

        bolge_uzmani = get_object_or_404(User, pk=bolge_uzmani_id)
        toplam_bina = ParselKayit.objects.filter(mahalle__iexact=mahalle_adi).count()

        if toplam_bina == 0:
            messages.warning(request,
                '"%s" mahallesinde kayitli bina bulunamadi. '
                'Once binalari haritaya ekleyin.' % mahalle_adi)
            return redirect('gorev_plani_listesi')

        calisma_gunu = _calisma_gunleri(yil, ay)
        gunluk_hedef = max(1, math.ceil(toplam_bina / calisma_gunu))

        plan, created = SahaGorevPlani.objects.get_or_create(
            mahalle_adi=mahalle_adi, bolge_uzmani=bolge_uzmani, yil=yil, ay=ay,
            defaults={
                'atayan_broker': request.user,
                'toplam_bina': toplam_bina,
                'calisma_gunu': calisma_gunu,
                'gunluk_hedef': gunluk_hedef,
                'aktif': True,
            }
        )
        if not created:
            plan.toplam_bina = toplam_bina
            plan.calisma_gunu = calisma_gunu
            plan.gunluk_hedef = gunluk_hedef
            plan.atayan_broker = request.user
            plan.aktif = True
            plan.save()

        plan.gorevler_olustur()
        ay_adi = dict(AY_SECENEKLER).get(ay, str(ay))
        messages.success(request,
            '"%s" icin %s %d plani olusturuldu. %d bina / %d gun = gunluk %d bina.' % (
                mahalle_adi, ay_adi, yil, toplam_bina, calisma_gunu, gunluk_hedef))
    except Exception as e:
        messages.error(request, 'Hata: %s' % str(e))

    return redirect('gorev_plani_listesi')


@login_required(login_url='/login/')
def gorev_plani_detay(request, plan_id):
    plan = get_object_or_404(SahaGorevPlani, pk=plan_id)
    user = request.user
    is_broker = user.is_superuser or user.has_role('Mudur') or user.has_role('Yonetici')
    if not is_broker and plan.bolge_uzmani != user:
        messages.error(request, 'Bu plana erisim yetkiniz yok.')
        return redirect('gorev_plani_listesi')

    gorevler = plan.gunluk_gorevler.prefetch_related('atanan_parseller').all()
    bugun = date_cls.today()
    gorev_listesi = []
    for g in gorevler:
        tamamlanan, toplam = g.tamamlanma_orani()
        gorev_listesi.append({
            'gorev': g,
            'tamamlanan': tamamlanan,
            'toplam': toplam,
            'yuzde': int(tamamlanan / toplam * 100) if toplam else 0,
            'bugun': g.tarih == bugun,
            'gecmis': g.tarih < bugun,
        })

    return render(request, 'saha/gorev_plani_detay.html', {
        'segment': 'saha',
        'plan': plan,
        'gorev_listesi': gorev_listesi,
        'is_broker': is_broker,
        'bugun': bugun,
    })


@login_required(login_url='/login/')
def gunluk_gorevim(request):
    user = request.user
    bugun = date_cls.today()

    # Bugünkü görev
    gorev = GunlukGorev.objects.filter(
        plan__bolge_uzmani=user, plan__aktif=True, tarih=bugun,
    ).select_related('plan__bolge_uzmani', 'plan__atayan_broker').first()

    parseller_bilgi = []
    if gorev:
        for p in gorev.atanan_parseller.all():
            ziyaret = gorev.ziyaret_edildi_mi(p)
            bugun_gorusmeler = SahaGorusme.objects.filter(
                parsel=p, tarih__date=bugun).order_by('-tarih')
            parseller_bilgi.append({
                'parsel': p,
                'ziyaret_edildi': ziyaret,
                'bugun_gorusmeler': list(bugun_gorusmeler),
            })
        gorev.kontrol_et_ve_tamamla()

    # ── Geçmiş günlerden devredilen (notu yazılmamış) parseller ──────────────
    # Önceki günlere ait aktif görevleri al, en yeni tarihten eskiye doğru
    gecmis_gorevler = GunlukGorev.objects.filter(
        plan__bolge_uzmani=user,
        plan__aktif=True,
        tarih__lt=bugun,
    ).prefetch_related('atanan_parseller').order_by('-tarih')

    # Bugünkü görevdeki parsel ID'leri → devre dışı bırakmak için
    bugun_parsel_ids = {item['parsel'].id for item in parseller_bilgi}
    gorulmus_ids = set(bugun_parsel_ids)  # tekrar eklemeyi önle

    devreden_parseller = []
    for gecmis_gorev in gecmis_gorevler:
        for p in gecmis_gorev.atanan_parseller.all():
            # O günün notu yazılmışsa atla
            if gecmis_gorev.ziyaret_edildi_mi(p):
                continue
            # Aynı parsel birden fazla geçmiş günde varsa sadece bir kez ekle
            if p.id in gorulmus_ids:
                continue
            gorulmus_ids.add(p.id)

            # Bugün bu parsele not yazıldı mı?
            bugun_gorusmeler = SahaGorusme.objects.filter(
                parsel=p, tarih__date=bugun).order_by('-tarih')
            geciken_gun = (bugun - gecmis_gorev.tarih).days

            devreden_parseller.append({
                'parsel': p,
                'orijinal_tarih': gecmis_gorev.tarih,
                'geciken_gun': geciken_gun,
                'ziyaret_edildi': bugun_gorusmeler.exists(),
                'bugun_gorusmeler': list(bugun_gorusmeler),
            })

    # Bugün tamamlananlar öne, gecikmeli olanlar arkaya
    devreden_parseller.sort(key=lambda x: (x['ziyaret_edildi'], -x['geciken_gun']))

    tamamlanan_sayi = sum(1 for p in parseller_bilgi if p['ziyaret_edildi'])
    devreden_tamamlanan = sum(1 for p in devreden_parseller if p['ziyaret_edildi'])

    return render(request, 'saha/gunluk_gorev.html', {
        'segment': 'saha',
        'gorev': gorev,
        'parseller_bilgi': parseller_bilgi,
        'devreden_parseller': devreden_parseller,
        'bugun': bugun,
        'tamamlanan_sayi': tamamlanan_sayi,
        'toplam_sayi': len(parseller_bilgi),
        'devreden_tamamlanan': devreden_tamamlanan,
        'devreden_toplam': len(devreden_parseller),
    })


@login_required(login_url='/login/')
def broker_bildirimleri(request):
    user = request.user
    if not (user.is_superuser or user.has_role('Mudur') or user.has_role('Yonetici')):
        messages.error(request, 'Bu sayfaya erisim yetkiniz yok.')
        return redirect('gorev_plani_listesi')

    bildirimler = BrokerBildirim.objects.filter(
        alici=user
    ).select_related('gorev__plan__bolge_uzmani').order_by('-tarih')
    bildirimler.filter(goruldu=False).update(goruldu=True)

    return render(request, 'saha/broker_bildirimleri.html', {
        'segment': 'saha',
        'bildirimler': bildirimler,
    })


# ---- GOREV APILERI ----------------------------------------------------------

@login_required(login_url='/login/')
def api_gunluk_gorev_parselleri(request):
    bugun = date_cls.today()
    gorev = GunlukGorev.objects.filter(
        plan__bolge_uzmani=request.user, plan__aktif=True, tarih=bugun,
    ).first()

    if not gorev:
        return JsonResponse({'gorev_id': None, 'parsel_ids': [],
                             'tamamlandi': False, 'tamamlanan': 0, 'toplam': 0,
                             'devreden_parsel_ids': []})

    parsel_ids = list(gorev.atanan_parseller.values_list('id', flat=True))
    tamamlanan, toplam = gorev.tamamlanma_orani()

    # Devredilen (geçmiş günlerden notu yazılmamış) parselleri de haritaya gönder
    gecmis_gorevler = GunlukGorev.objects.filter(
        plan__bolge_uzmani=request.user,
        plan__aktif=True,
        tarih__lt=bugun,
    ).prefetch_related('atanan_parseller')

    gorulmus = set(parsel_ids)
    devreden_ids = []
    for gg in gecmis_gorevler:
        for p in gg.atanan_parseller.all():
            if not gg.ziyaret_edildi_mi(p) and p.id not in gorulmus:
                gorulmus.add(p.id)
                devreden_ids.append(p.id)

    return JsonResponse({
        'gorev_id': gorev.id,
        'parsel_ids': parsel_ids,
        'tamamlandi': gorev.tamamlandi,
        'tamamlanan': tamamlanan,
        'toplam': toplam,
        'devreden_parsel_ids': devreden_ids,
    })


@login_required(login_url='/login/')
def api_bildirim_sayisi(request):
    sayi = BrokerBildirim.objects.filter(
        alici=request.user, goruldu=False).count()
    return JsonResponse({'okunmamis': sayi})


@login_required(login_url='/login/')
@require_POST
def api_gorev_bildir(request, gorev_id):
    gorev = get_object_or_404(GunlukGorev, pk=gorev_id)
    user = request.user
    is_broker = user.is_superuser or user.has_role('Mudur') or user.has_role('Yonetici')
    if not is_broker and gorev.plan.bolge_uzmani != user:
        return JsonResponse({'error': 'Yetki yok'}, status=403)

    tamamlanan, toplam = gorev.tamamlanma_orani()
    if toplam == 0 or tamamlanan >= toplam:
        return JsonResponse({'success': False, 'mesaj': 'Gorev zaten tamamlandi.'})
    if gorev.broker_bildirildi:
        return JsonResponse({'success': False, 'mesaj': 'Broker zaten bilgilendirildi.'})

    broker = gorev.plan.atayan_broker
    if not broker:
        return JsonResponse({'success': False, 'mesaj': 'Atayan broker bulunamadi.'})

    mesaj = (
        '%s  --  %s tarihli gorevini tamamlamadi. '
        '(%d/%d bina ziyaret edildi)  Mahalle: %s' % (
            gorev.plan.bolge_uzmani.get_full_name(),
            gorev.tarih.strftime('%d.%m.%Y'),
            tamamlanan, toplam,
            gorev.plan.mahalle_adi,
        )
    )
    BrokerBildirim.objects.create(alici=broker, gorev=gorev, mesaj=mesaj)
    gorev.broker_bildirildi = True
    gorev.save(update_fields=['broker_bildirildi'])
    return JsonResponse({'success': True, 'mesaj': 'Broker bilgilendirildi.'})


@login_required(login_url='/login/')
@require_POST
def api_gorev_plani_sil(request, plan_id):
    user = request.user
    if not (user.is_superuser or user.has_role('Mudur') or user.has_role('Yonetici')):
        return JsonResponse({'error': 'Yetki yok'}, status=403)
    plan = get_object_or_404(SahaGorevPlani, pk=plan_id)
    plan.delete()
    return JsonResponse({'success': True})


@login_required(login_url='/login/')
def api_mahalleler(request):
    from apps.customers.models import Neighborhood
    mahalleler = list(
        Neighborhood.objects.values('id', 'name', 'district').order_by('name')
    )
    return JsonResponse({'mahalleler': mahalleler})


# ---- PANEL API'LERI (saha haritası sağ panel) --------------------------------

@login_required(login_url='/login/')
def api_gorev_planlari_json(request):
    user = request.user
    is_broker = user.is_superuser or user.has_role('Mudur') or user.has_role('Yonetici')
    if is_broker:
        planlar = SahaGorevPlani.objects.select_related('bolge_uzmani', 'atayan_broker').order_by('-olusturma_tarihi')
    else:
        planlar = SahaGorevPlani.objects.select_related('bolge_uzmani', 'atayan_broker').filter(bolge_uzmani=user).order_by('-olusturma_tarihi')

    result = []
    for p in planlar:
        gorevler = p.gunluk_gorevler.all()
        toplam_gorev = gorevler.count()
        tamamlanan_gorev = gorevler.filter(tamamlandi=True).count()
        result.append({
            'id': p.id,
            'mahalle': p.mahalle_adi,
            'uzman': p.bolge_uzmani.get_full_name(),
            'ay': p.get_ay_display(),
            'yil': p.yil,
            'aktif': p.aktif,
            'toplam_bina': p.toplam_bina,
            'calisma_gunu': p.calisma_gunu,
            'gunluk_hedef': p.gunluk_hedef,
            'toplam_gorev': toplam_gorev,
            'tamamlanan_gorev': tamamlanan_gorev,
            'yuzde': int(tamamlanan_gorev * 100 / toplam_gorev) if toplam_gorev else 0,
        })

    bolge_uzmanlari = list(
        User.objects.filter(groups__name__in=['Danishman', 'Calisanlar']).distinct()
        .values('id', 'first_name', 'last_name').order_by('first_name')
    )

    return JsonResponse({'planlar': result, 'is_broker': is_broker, 'bolge_uzmanlari': bolge_uzmanlari})


@login_required(login_url='/login/')
def api_bildirimleri_json(request):
    user = request.user
    if not (user.is_superuser or user.has_role('Mudur') or user.has_role('Yonetici')):
        return JsonResponse({'bildirimler': [], 'okunmamis': 0})

    bildirimler_qs = BrokerBildirim.objects.filter(alici=user).select_related('gorev__plan__bolge_uzmani').order_by('-tarih')
    okunmamis = bildirimler_qs.filter(goruldu=False).count()

    # Okundu olarak işaretle
    bildirimler_qs.filter(goruldu=False).update(goruldu=True)

    result = []
    for b in bildirimler_qs[:50]:
        result.append({
            'id': b.id,
            'mesaj': b.mesaj,
            'tarih': b.tarih.strftime('%d.%m.%Y %H:%M'),
            'goruldu': b.goruldu,
            'uzman': b.gorev.plan.bolge_uzmani.get_full_name() if b.gorev and b.gorev.plan else '',
        })

    return JsonResponse({'bildirimler': result, 'okunmamis': okunmamis})


@login_required(login_url='/login/')
@require_POST
def api_gorev_plani_olustur_json(request):
    import json as json_mod
    user = request.user
    if not (user.is_superuser or user.has_role('Mudur') or user.has_role('Yonetici')):
        return JsonResponse({'error': 'Yetki yok'}, status=403)

    try:
        data = json_mod.loads(request.body)
        mahalle_adi = data.get('mahalle_adi', '').strip()
        bolge_uzmani_id = int(data.get('bolge_uzmani_id', 0))
        yil = int(data.get('yil', 0))
        ay = int(data.get('ay', 0))
        toplam_bina = int(data.get('toplam_bina', 0))
        calisma_gunu = int(data.get('calisma_gunu', 1))
    except Exception:
        return JsonResponse({'error': 'Gecersiz veri'}, status=400)

    if not mahalle_adi or not bolge_uzmani_id or not yil or not ay or not toplam_bina:
        return JsonResponse({'error': 'Eksik alan'}, status=400)

    bolge_uzmani = get_object_or_404(User, pk=bolge_uzmani_id)
    gunluk_hedef = max(1, toplam_bina // max(calisma_gunu, 1))

    plan, created = SahaGorevPlani.objects.get_or_create(
        mahalle_adi=mahalle_adi, bolge_uzmani=bolge_uzmani, yil=yil, ay=ay,
        defaults={
            'toplam_bina': toplam_bina,
            'calisma_gunu': calisma_gunu,
            'gunluk_hedef': gunluk_hedef,
            'atayan_broker': user,
            'aktif': True,
        }
    )
    if not created:
        plan.toplam_bina = toplam_bina
        plan.calisma_gunu = calisma_gunu
        plan.gunluk_hedef = gunluk_hedef
        plan.atayan_broker = user
        plan.aktif = True
        plan.save()

    plan.gorevler_olustur()
    return JsonResponse({'success': True, 'plan_id': plan.id})


@login_required(login_url='/login/')
@require_POST
def api_planlari_otomatik_olustur(request):
    from datetime import date as date_cls2
    import json as json_mod2
    user = request.user
    if not (user.is_superuser or user.has_role('Mudur') or user.has_role('Yonetici')):
        return JsonResponse({'error': 'Yetki yok'}, status=403)

    from apps.customers.models import Neighborhood
    bugun = date_cls2.today()
    yil, ay = bugun.year, bugun.month

    try:
        data = json_mod2.loads(request.body or '{}')
        yil = int(data.get('yil', yil))
        ay = int(data.get('ay', ay))
        calisma_gunu = int(data.get('calisma_gunu', 20))
    except Exception:
        calisma_gunu = 20

    mahalleler = Neighborhood.objects.select_related('consultant').filter(consultant__isnull=False)
    olusturulan = 0
    guncellenen = 0

    atlanan = 0
    for m in mahalleler:
        consultant = m.consultant
        toplam_bina = ParselKayit.objects.filter(mahalle__iexact=m.name).count()

        # Mahallede hiç parsel yoksa plan oluşturma — görev de atanamaz
        if toplam_bina == 0:
            atlanan += 1
            continue

        gunluk_hedef = max(1, toplam_bina // max(calisma_gunu, 1))

        plan, created = SahaGorevPlani.objects.get_or_create(
            mahalle_adi=m.name,
            bolge_uzmani=consultant,
            yil=yil,
            ay=ay,
            defaults={
                'toplam_bina': toplam_bina,
                'calisma_gunu': calisma_gunu,
                'gunluk_hedef': gunluk_hedef,
                'atayan_broker': user,
                'aktif': True,
            }
        )
        if not created:
            plan.toplam_bina = toplam_bina
            plan.calisma_gunu = calisma_gunu
            plan.gunluk_hedef = gunluk_hedef
            plan.atayan_broker = user
            plan.aktif = True
            plan.save()
            guncellenen += 1
        else:
            olusturulan += 1

        plan.gorevler_olustur()

    return JsonResponse({
        'success': True,
        'olusturulan': olusturulan,
        'guncellenen': guncellenen,
        'atlanan': atlanan,
        'toplam': olusturulan + guncellenen,
    })
