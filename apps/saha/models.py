# -*- coding: utf-8 -*-
import calendar
from django.db import models
from django.conf import settings


DURUM_SECENEKLER = [
    ('yapim_asamasinda', 'Yapim Asamasinda'),
    ('oturuma_hazir', 'Oturuma Hazir'),
    ('dolu_bina', 'Dolu Bina'),
]


class ParselKayit(models.Model):
    lat = models.FloatField(verbose_name='Enlem')
    lng = models.FloatField(verbose_name='Boylam')
    adres = models.CharField(max_length=500, verbose_name='Adres', blank=True)
    ada_no = models.CharField(max_length=50, verbose_name='Ada No', blank=True)
    parsel_no = models.CharField(max_length=50, verbose_name='Parsel No', blank=True)
    mahalle = models.CharField(max_length=200, verbose_name='Mahalle', blank=True)

    # Durum
    durum = models.CharField(
        max_length=30, choices=DURUM_SECENEKLER,
        verbose_name='Durum', blank=True, default=''
    )

    # Yapim Asamasinda
    muteahit_ad = models.CharField(max_length=150, blank=True, verbose_name='Muteahit Adi')
    muteahit_tel = models.CharField(max_length=30, blank=True, verbose_name='Muteahit Telefonu')
    bekci_ad = models.CharField(max_length=150, blank=True, verbose_name='Bekci Adi')
    bekci_tel = models.CharField(max_length=30, blank=True, verbose_name='Bekci Telefonu')
    cavus_ad = models.CharField(max_length=150, blank=True, verbose_name='Cavus Adi')
    cavus_tel = models.CharField(max_length=30, blank=True, verbose_name='Cavus Telefonu')
    taseronlar = models.JSONField(default=list, blank=True, verbose_name='Taseronlar')

    # Oturuma Hazir
    arsa_sahibi_ad = models.CharField(max_length=150, blank=True, verbose_name='Arsa Sahibi Adi')
    arsa_sahibi_tel = models.CharField(max_length=30, blank=True, verbose_name='Arsa Sahibi Telefonu')
    oturuma_yonetici_ad = models.CharField(max_length=150, blank=True, verbose_name='Oturuma Yonetici Adi')
    oturuma_yonetici_tel = models.CharField(max_length=30, blank=True, verbose_name='Oturuma Yonetici Telefonu')
    oturuma_bekci_ad = models.CharField(max_length=150, blank=True, verbose_name='Oturuma Bekci Adi')
    oturuma_bekci_tel = models.CharField(max_length=30, blank=True, verbose_name='Oturuma Bekci Telefonu')
    oturuma_ek_kisiler = models.JSONField(default=list, blank=True, verbose_name='Oturuma Ek Kisiler')

    # Dolu Bina
    yonetici_ad = models.CharField(max_length=150, blank=True, verbose_name='Bina Yoneticisi Adi')
    yonetici_tel = models.CharField(max_length=30, blank=True, verbose_name='Yonetici Telefonu')
    kapici_ad = models.CharField(max_length=150, blank=True, verbose_name='Kapici Adi')
    kapici_tel = models.CharField(max_length=30, blank=True, verbose_name='Kapici Telefonu')
    dolu_ek_kisiler = models.JSONField(default=list, blank=True, verbose_name='Dolu Bina Ek Kisiler')

    portfoy_sayisi = models.PositiveIntegerField(default=0, verbose_name='Alinan Portfoy Sayisi')
    diger_not = models.TextField(blank=True, verbose_name='Bina Hakkinda Notlar')
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='parsel_kayitlar',
        verbose_name='Olusturan'
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Parsel Kaydi'
        verbose_name_plural = 'Parsel Kayitlari'
        ordering = ['-olusturma_tarihi']

    def __str__(self):
        return self.adres or 'Parsel (%.5f, %.5f)' % (self.lat, self.lng)


class SahaGorusme(models.Model):
    parsel = models.ForeignKey(
        ParselKayit, on_delete=models.CASCADE,
        related_name='gorusmeler', verbose_name='Parsel'
    )
    personel = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='saha_gorusmeler',
        verbose_name='Personel'
    )
    tarih = models.DateTimeField(auto_now_add=True, verbose_name='Gorusme Tarihi')
    not_metni = models.TextField(verbose_name='Gorusme Notu')
    gorusulen_kisi = models.CharField(max_length=150, blank=True, verbose_name='Gorusulen Kisi')

    class Meta:
        verbose_name = 'Saha Gorusmesi'
        verbose_name_plural = 'Saha Gorusmeleri'
        ordering = ['-tarih']

    def __str__(self):
        return '%s -- %s' % (self.personel, self.parsel)


# ---------------------------------------------------------------------------
# GOREV SISTEMI
# ---------------------------------------------------------------------------

def _calisma_gunleri(yil, ay):
    _, toplam_gun = calendar.monthrange(yil, ay)
    from datetime import date
    return toplam_gun - sum(
        1 for g in range(1, toplam_gun + 1)
        if date(yil, ay, g).weekday() == 6
    )


def _calisma_gun_listesi(yil, ay):
    from datetime import date
    _, toplam_gun = calendar.monthrange(yil, ay)
    return [
        date(yil, ay, g)
        for g in range(1, toplam_gun + 1)
        if date(yil, ay, g).weekday() != 6
    ]


AY_SECENEKLER = [
    (1, 'Ocak'), (2, 'Subat'), (3, 'Mart'), (4, 'Nisan'),
    (5, 'Mayis'), (6, 'Haziran'), (7, 'Temmuz'), (8, 'Agustos'),
    (9, 'Eylul'), (10, 'Ekim'), (11, 'Kasim'), (12, 'Aralik'),
]


class SahaGorevPlani(models.Model):
    mahalle_adi = models.CharField(max_length=200)
    bolge_uzmani = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='gorev_planlari'
    )
    atayan_broker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='atadigi_planlar'
    )
    yil = models.PositiveSmallIntegerField()
    ay = models.PositiveSmallIntegerField(choices=AY_SECENEKLER)
    toplam_bina = models.PositiveIntegerField()
    calisma_gunu = models.PositiveSmallIntegerField()
    gunluk_hedef = models.PositiveSmallIntegerField()
    aktif = models.BooleanField(default=True)
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Saha Gorev Plani'
        verbose_name_plural = 'Saha Gorev Planlari'
        ordering = ['-olusturma_tarihi']
        unique_together = [['mahalle_adi', 'bolge_uzmani', 'yil', 'ay']]

    def __str__(self):
        return '%s -- %s (%s %d)' % (
            self.mahalle_adi,
            self.bolge_uzmani.get_full_name(),
            dict(AY_SECENEKLER).get(self.ay, str(self.ay)),
            self.yil,
        )

    def get_ay_display(self):
        return dict(AY_SECENEKLER).get(self.ay, str(self.ay))

    def gorevler_olustur(self):
        import math
        self.gunluk_gorevler.all().delete()
        parseller = list(
            ParselKayit.objects.filter(mahalle__iexact=self.mahalle_adi).order_by('id')
        )
        if not parseller:
            return
        gun_listesi = _calisma_gun_listesi(self.yil, self.ay)
        hedef = self.gunluk_hedef or 1
        idx = 0
        for gun in gun_listesi:
            gorev = GunlukGorev.objects.create(plan=self, tarih=gun)
            gorev.atanan_parseller.set(parseller[idx: idx + hedef])
            idx += hedef
            if idx >= len(parseller):
                idx = 0


class GunlukGorev(models.Model):
    plan = models.ForeignKey(
        SahaGorevPlani, on_delete=models.CASCADE, related_name='gunluk_gorevler'
    )
    tarih = models.DateField()
    atanan_parseller = models.ManyToManyField(
        ParselKayit, blank=True, related_name='gunluk_gorevler'
    )
    tamamlandi = models.BooleanField(default=False)
    broker_bildirildi = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Gunluk Gorev'
        verbose_name_plural = 'Gunluk Gorevler'
        ordering = ['tarih']
        unique_together = [['plan', 'tarih']]

    def __str__(self):
        return '%s / %s -- %s' % (
            self.plan.mahalle_adi,
            self.plan.bolge_uzmani.get_full_name(),
            self.tarih.strftime('%d.%m.%Y'),
        )

    def ziyaret_edildi_mi(self, parsel):
        return SahaGorusme.objects.filter(
            parsel=parsel, tarih__date=self.tarih
        ).exists()

    def tamamlanma_orani(self):
        toplam = self.atanan_parseller.count()
        if toplam == 0:
            return 0, 0
        tamamlanan = sum(
            1 for p in self.atanan_parseller.all()
            if self.ziyaret_edildi_mi(p)
        )
        return tamamlanan, toplam

    def kontrol_et_ve_tamamla(self):
        tamamlanan, toplam = self.tamamlanma_orani()
        if toplam > 0 and tamamlanan >= toplam:
            self.tamamlandi = True
            self.save(update_fields=['tamamlandi'])
            return True
        return False


class BrokerBildirim(models.Model):
    alici = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='broker_bildirimleri'
    )
    gorev = models.ForeignKey(
        GunlukGorev, on_delete=models.CASCADE, related_name='bildirimler'
    )
    mesaj = models.TextField()
    goruldu = models.BooleanField(default=False)
    tarih = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Broker Bildirimi'
        verbose_name_plural = 'Broker Bildirimleri'
        ordering = ['-tarih']

    def __str__(self):
        return '%s <- %s' % (self.alici, self.gorev)
