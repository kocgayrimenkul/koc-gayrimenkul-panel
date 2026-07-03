# -*- coding: utf-8 -*-
"""
Gayrimenkul tanıtım videosu üretici — saf FFmpeg pipeline.

SAHNELER
  1. AÇILIŞ  (2 sn)   : koyu arka plan + logo + SATILIK/KİRALIK badge + ilan başlığı
  2. FOTOĞRAF (3 sn×N) : fill-crop + Ken Burns zoompan + alt bilgi şeridi + sağ üst badge
  3. KAPANIŞ  (3 sn)   : koyu arka plan + logo + iletişim bilgisi

GEÇİŞLER  : xfade=fade 0.5 sn
ÇIKTI     : H.264 MP4, 24 fps, ses yok → media/videos/

KRİTİK NOT (Windows):
  • Font path: C\\:/Windows/Fonts/arialbd.ttf  (4-backslash Python → C\\: FFmpeg)
  • Geçici dosyalar: C:\\koc_vid_tmp\\  (ASCII-only, Unicode path FFmpeg'i bozar)
  • Fotoğraf giriş: -loop 1  (statik JPEG'i 3 sn boyunca döngüle, aksi hâlde 1 frame)
  • Türkçe metin: textfile= ile (filter-string escaping sorunundan kaçınır)
  • zoompan z expr: 'zoom+step' (n değişkeni FFmpeg 8.x'te tanımsız; min() virgülü split eder)
"""

import os
import re
import json
import shutil
import logging
import tempfile
import threading
import subprocess
from decimal import Decimal

from django.conf import settings

log = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Sabitler
# ──────────────────────────────────────────────────────────────────────────────
FPS       = 24
INTRO_DUR = 2
PHOTO_DUR = 3
OUTRO_DUR = 3
XFADE_DUR = 0.5

BG_COLOR   = "#1a1a2e"
ACCENT_HEX = "FF7800"    # turuncu badge
WHITE_HEX  = "ffffff"

# FFmpeg filter-string için font yolu  (Python 4-backslash → string C\\:/ → FFmpeg C:/)
FONT_BOLD = "C\\\\:/Windows/Fonts/arialbd.ttf"
FONT_REG  = "C\\\\:/Windows/Fonts/arial.ttf"

LOGO_SRC  = os.path.join(
    settings.BASE_DIR, "apps", "static", "assets", "img", "logo.png"
)
VIDEOS_DIR = os.path.join(settings.MEDIA_ROOT, "videos")

# Tüm FFmpeg işlemleri bu ASCII-only klasörde yapılır
TMP_BASE = r"C:\koc_vid_tmp"

PHONE_LINE   = "0(342) XXX XX XX"          # Gerçek numarayı buraya yazın
WEBSITE_LINE = "panelkocgayrimenkul.com"


# ──────────────────────────────────────────────────────────────────────────────
# Yardımcılar
# ──────────────────────────────────────────────────────────────────────────────

def _ffmpeg_exe() -> str:
    """Sistem PATH'indeki ffmpeg'i bul; bulamazsa imageio-ffmpeg."""
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    raise RuntimeError("FFmpeg bulunamadı. 'winget install Gyan.FFmpeg' ile kurun.")


def _run(cmd: list, label: str = ""):
    """FFmpeg komutunu çalıştır; hata varsa RuntimeError fırlat."""
    r = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"FFmpeg [{label}]:\n{(r.stderr or '')[-1000:]}")


def _safe_tmp() -> str:
    """ASCII-only geçici klasör oluştur."""
    os.makedirs(TMP_BASE, exist_ok=True)
    return tempfile.mkdtemp(dir=TMP_BASE)


def _ffmpeg_path(win_path: str) -> str:
    """
    Windows mutlak yolunu FFmpeg filter-string formatına çevir.
    C:\\foo\\bar.txt  →  C\\\\:/foo/bar.txt  (Python string)
    (Subprocess yoluyla FFmpeg'e C\\:/foo/bar.txt ulaşır ve çalışır.)
    """
    p = win_path.replace("\\", "/")              # C:/foo/bar.txt
    p = re.sub(r"^([A-Za-z]):/", r"\1\\\\:/", p) # C\\:/foo/bar.txt
    return p


def _write_tf(tmp_dir: str, name: str, text: str) -> str:
    """
    Türkçe metni UTF-8 dosyaya yaz; FFmpeg textfile= için yolu döndür.
    Böylece Türkçe karakter filter-string'e girmez.
    """
    fpath = os.path.join(tmp_dir, name)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(text)
    return _ffmpeg_path(fpath)


def _dim(resolution: str, aspect: str) -> tuple[int, int]:
    """
    (W, H) döndür.
    9:16 dikey : 480p→480×854, 720p→720×1280, 1080p→1080×1920
    16:9 yatay : 480p→854×480, 720p→1280×720, 1080p→1920×1080
    """
    base = {"480p": 480, "720p": 720, "1080p": 1080}.get(resolution, 720)
    if aspect == "9:16":
        h = base * 16 // 9
        return (base, h + h % 2)
    w = base * 16 // 9
    return (w + w % 2, base)


def _fmt_price(price) -> str:
    try:
        v = int(Decimal(str(price)))
        return f"{v:,}".replace(",", ".") + " TL"
    except Exception:
        return str(price)


def _probe_duration(ffmpeg: str, path: str) -> float:
    probe = ffmpeg.replace("ffmpeg", "ffprobe").replace("ffmpeg.EXE", "ffprobe.EXE")
    if not os.path.isfile(probe):
        probe = shutil.which("ffprobe") or ffmpeg
    r = subprocess.run(
        [probe, "-v", "quiet", "-print_format", "json",
         "-show_streams", "-select_streams", "v:0", path],
        capture_output=True, encoding="utf-8", errors="replace",
    )
    try:
        return float(json.loads(r.stdout)["streams"][0].get("duration", PHOTO_DUR))
    except Exception:
        return float(PHOTO_DUR)


def _prepare_logo(tmp_dir: str, logo_h: int) -> str | None:
    """Logo'yu ölçekle, ASCII tmp_dir'e kaydet; None → logo yoksa."""
    if not os.path.exists(LOGO_SRC):
        return None
    try:
        from PIL import Image
        img = Image.open(LOGO_SRC).convert("RGBA")
        ratio = logo_h / img.height
        img = img.resize((int(img.width * ratio), logo_h), Image.LANCZOS)
        out = os.path.join(tmp_dir, "logo.png")
        img.save(out)
        return out
    except Exception as exc:
        log.warning("Logo hazırlanamadı: %s", exc)
        return None


def _overlay_logo(ffmpeg: str, base_mp4: str, logo_png: str, logo_y: int, out: str):
    """base_mp4 üzerine logo_png overlay et → out."""
    cmd = [
        ffmpeg, "-y",
        "-i", base_mp4,
        "-i", logo_png,
        "-filter_complex", f"[0:v][1:v]overlay=(W-w)/2:{logo_y}[v]",
        "-map", "[v]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "22",
        out,
    ]
    _run(cmd, "overlay-logo")


# ──────────────────────────────────────────────────────────────────────────────
# 1. AÇILIŞ
# ──────────────────────────────────────────────────────────────────────────────

def _make_intro(ffmpeg: str, W: int, H: int,
                title_tf: str, status_tf: str,
                logo_png: str | None, tmp_dir: str, out: str):
    """
    Açılış (INTRO_DUR sn):
      Koyu arka plan → logo (veya marka adı) → SATILIK/KİRALIK badge → ilan başlığı
    """
    fs_brand = max(24, H // 18)
    fs_badge = max(16, H // 30)
    fs_title = max(18, H // 24)

    logo_y  = int(H * 0.18)
    badge_y = int(H * 0.46)
    title_y = badge_y + fs_badge + 30

    # SATILIK badge (beyaz yazı turuncu kutu, ortalı)
    badge_vf = (
        f"drawtext=fontfile={FONT_BOLD}"
        f":textfile={status_tf}"
        f":fontsize={fs_badge}:fontcolor={WHITE_HEX}"
        f":box=1:boxcolor={ACCENT_HEX}@1.0:boxborderw=12"
        f":x=(w-text_w)/2:y={badge_y}"
        f":shadowx=1:shadowy=1:shadowcolor=black@0.7"
    )
    # İlan başlığı (beyaz, ortalı)
    title_vf = (
        f"drawtext=fontfile={FONT_BOLD}"
        f":textfile={title_tf}"
        f":fontsize={fs_title}:fontcolor={WHITE_HEX}"
        f":x=(w-text_w)/2:y={title_y}"
        f":shadowx=2:shadowy=2:shadowcolor=black@0.8"
    )

    if logo_png:
        # Geçiş 1: renk arka plan + metin
        base = out + ".base.mp4"
        _run([
            ffmpeg, "-y", "-f", "lavfi",
            "-i", f"color=c={BG_COLOR}:s={W}x{H}:r={FPS}:d={INTRO_DUR}",
            "-vf", f"{badge_vf},{title_vf}",
            "-t", str(INTRO_DUR),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "22",
            base,
        ], "intro-base")
        # Geçiş 2: logo overlay
        _overlay_logo(ffmpeg, base, logo_png, logo_y, out)
        os.remove(base)
    else:
        brand_tf = _write_tf(tmp_dir, "brand.txt", "KOC GAYRIMENKUL")
        brand_vf = (
            f"drawtext=fontfile={FONT_BOLD}"
            f":textfile={brand_tf}"
            f":fontsize={fs_brand}:fontcolor={WHITE_HEX}"
            f":x=(w-text_w)/2:y={logo_y}"
            f":shadowx=2:shadowy=2:shadowcolor=black@0.8"
        )
        _run([
            ffmpeg, "-y", "-f", "lavfi",
            "-i", f"color=c={BG_COLOR}:s={W}x{H}:r={FPS}:d={INTRO_DUR}",
            "-vf", f"{brand_vf},{badge_vf},{title_vf}",
            "-t", str(INTRO_DUR),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "22",
            out,
        ], "intro")


# ──────────────────────────────────────────────────────────────────────────────
# 2. FOTOĞRAF SAHNESİ
# ──────────────────────────────────────────────────────────────────────────────

def _make_photo(ffmpeg: str, W: int, H: int,
                img_path: str,
                info_tf: str,    # textfile path (FFmpeg-safe)
                status_tf: str,  # textfile path
                pan_dir: int,    # +1 sağa, -1 sola
                out: str):
    """
    Fotoğraf sahnesi (PHOTO_DUR sn):
      -loop 1 → scale+crop (fill) → zoompan Ken Burns → drawbox şerit → drawtext × 2

    KRİTİK: '-loop 1' olmadan JPEG 1 frame → video neredeyse boş çıkar.
    """
    total_frames = PHOTO_DUR * FPS   # 72 @ 24fps
    fs_info  = max(14, H // 36)
    fs_badge = max(12, H // 42)

    # Ken Burns: zoom artımlı (zoom değişkeni, n yok)
    # 72 frame sonunda zoom ≈ 1.0 + 72 * (0.05/72) = 1.05
    zoom_step  = round(0.05 / total_frames, 6)       # ≈ 0.000694
    pan_px     = int(W * 0.03) * pan_dir             # ±%3 yatay kayma
    pan_factor = pan_px * 20                          # (zoom-1)/0.05 * pan_px
    zoompan = (
        f"zoompan=z='zoom+{zoom_step}'"
        f":x='iw/2-(iw/zoom/2)+(zoom-1.0)*{pan_factor}'"
        f":y='ih/2-(ih/zoom/2)'"
        f":d={total_frames}"
        f":s={W}x{H}"
    )

    # Alt bilgi şeridi (~%15 yükseklik, %70 saydam siyah)
    band_h  = int(H * 0.15)
    band_y  = H - band_h
    info_y  = band_y + max(8, int(band_h * 0.18))
    dbox    = f"drawbox=x=0:y={band_y}:w=iw:h={band_h}:color=black@0.72:t=fill"
    info_dt = (
        f"drawtext=fontfile={FONT_BOLD}"
        f":textfile={info_tf}"
        f":fontsize={fs_info}:fontcolor={WHITE_HEX}"
        f":x=w*0.04:y={info_y}"
        f":shadowx=1:shadowy=1:shadowcolor=black@0.9"
    )

    # Sağ üst badge
    badge_y2 = int(H * 0.03)
    badge_dt = (
        f"drawtext=fontfile={FONT_BOLD}"
        f":textfile={status_tf}"
        f":fontsize={fs_badge}:fontcolor={WHITE_HEX}"
        f":box=1:boxcolor={ACCENT_HEX}@1.0:boxborderw=8"
        f":x=w-text_w-w*0.03:y={badge_y2}"
        f":shadowx=1:shadowy=1:shadowcolor=black@0.6"
    )

    vf = (
        f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={W}:{H},"
        f"{zoompan},"
        f"{dbox},"
        f"{info_dt},"
        f"{badge_dt}"
    )

    # -loop 1: JPEG'i bitene kadar döngüle; -t PHOTO_DUR ile durdur
    cmd = [
        ffmpeg, "-y",
        "-loop", "1",               # ← ZORUNLU: statik görüntüyü döngüle
        "-framerate", str(FPS),     # giriş frame hızı
        "-i", img_path,
        "-vf", vf,
        "-t", str(PHOTO_DUR),
        "-r", str(FPS),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "fast", "-crf", "22",
        out,
    ]
    _run(cmd, f"photo:{os.path.basename(img_path)}")


# ──────────────────────────────────────────────────────────────────────────────
# 3. KAPANIŞ
# ──────────────────────────────────────────────────────────────────────────────

def _make_outro(ffmpeg: str, W: int, H: int,
                phone_tf: str, web_tf: str,
                logo_png: str | None, tmp_dir: str, out: str):
    """
    Kapanış (OUTRO_DUR sn):
      Koyu arka plan → logo (veya marka adı) → telefon + website
    """
    fs_brand   = max(24, H // 18)
    fs_contact = max(14, H // 35)
    fs_web     = max(12, H // 42)

    logo_y    = int(H * 0.28)
    phone_y   = int(H * 0.60)
    web_y     = phone_y + fs_contact + 14

    phone_vf = (
        f"drawtext=fontfile={FONT_BOLD}"
        f":textfile={phone_tf}"
        f":fontsize={fs_contact}:fontcolor={WHITE_HEX}"
        f":x=(w-text_w)/2:y={phone_y}"
        f":shadowx=2:shadowy=2:shadowcolor=black@0.8"
    )
    web_vf = (
        f"drawtext=fontfile={FONT_REG}"
        f":textfile={web_tf}"
        f":fontsize={fs_web}:fontcolor=b0c4de"     # açık mavi-beyaz
        f":x=(w-text_w)/2:y={web_y}"
        f":shadowx=1:shadowy=1:shadowcolor=black@0.7"
    )

    if logo_png:
        base = out + ".base.mp4"
        _run([
            ffmpeg, "-y", "-f", "lavfi",
            "-i", f"color=c={BG_COLOR}:s={W}x{H}:r={FPS}:d={OUTRO_DUR}",
            "-vf", f"{phone_vf},{web_vf}",
            "-t", str(OUTRO_DUR),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "22",
            base,
        ], "outro-base")
        _overlay_logo(ffmpeg, base, logo_png, logo_y, out)
        os.remove(base)
    else:
        brand_tf = _write_tf(tmp_dir, "brand_outro.txt", "KOC GAYRIMENKUL")
        brand_vf = (
            f"drawtext=fontfile={FONT_BOLD}"
            f":textfile={brand_tf}"
            f":fontsize={fs_brand}:fontcolor={WHITE_HEX}"
            f":x=(w-text_w)/2:y={logo_y}"
            f":shadowx=2:shadowy=2:shadowcolor=black@0.8"
        )
        _run([
            ffmpeg, "-y", "-f", "lavfi",
            "-i", f"color=c={BG_COLOR}:s={W}x{H}:r={FPS}:d={OUTRO_DUR}",
            "-vf", f"{brand_vf},{phone_vf},{web_vf}",
            "-t", str(OUTRO_DUR),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "22",
            out,
        ], "outro")


# ──────────────────────────────────────────────────────────────────────────────
# 4. XFADE BİRLEŞTİRME
# ──────────────────────────────────────────────────────────────────────────────

def _concat_xfade(ffmpeg: str, segments: list[str], out: str):
    """Tüm segment'leri xfade=fade geçişleriyle birleştir."""
    if len(segments) == 1:
        shutil.copy(segments[0], out)
        return

    durations = [_probe_duration(ffmpeg, s) for s in segments]
    inputs = []
    for s in segments:
        inputs += ["-i", s]

    parts = []
    cumul = 0.0
    prev  = "[0:v]"
    for i in range(len(segments) - 1):
        cumul += durations[i] - XFADE_DUR
        nxt   = f"[{i+1}:v]"
        lbl   = f"[vx{i+1}]"
        parts.append(
            f"{prev}{nxt}xfade=transition=fade"
            f":duration={XFADE_DUR}"
            f":offset={round(cumul, 3)}{lbl}"
        )
        prev = lbl

    _run(
        [ffmpeg, "-y"] + inputs + [
            "-filter_complex", ";".join(parts),
            "-map", prev,
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "fast", "-crf", "22",
            out,
        ],
        "concat-xfade",
    )


# ──────────────────────────────────────────────────────────────────────────────
# 5. ANA ÜRETİCİ (arka plan thread)
# ──────────────────────────────────────────────────────────────────────────────

def _build_video(job_id: int):
    from apps.portfolio.models import VideoJob

    job = VideoJob.objects.get(pk=job_id)
    job.status = "processing"
    job.save(update_fields=["status", "updated_at"])

    tmp = None
    try:
        ffmpeg = _ffmpeg_exe()
        prop   = job.property
        photos = job.get_ordered_photos()
        W, H   = _dim(job.resolution, job.aspect_ratio)

        # Statü etiketi (Türkçe, textfile ile render edilir)
        status_label = "SATILIK" if prop.status == "satilik" else "KIRALIK"
        title_text   = (prop.web_title or prop.apartment_name or "Gayrimenkul Ilani")

        # Alt bilgi satırı
        parts = []
        if prop.net_area:
            parts.append(f"{int(prop.net_area)} m2")
        if prop.room_count:
            parts.append(str(prop.room_count))
        if prop.price:
            parts.append(_fmt_price(prop.price))
        if prop.neighborhood:
            parts.append(str(prop.neighborhood.name))
        info_line = "  |  ".join(parts) if parts else title_text

        # Çıktı yolları
        os.makedirs(VIDEOS_DIR, exist_ok=True)
        out_filename = f"property_{prop.id}_job_{job.id}.mp4"
        final_path   = os.path.join(VIDEOS_DIR, out_filename)

        tmp     = _safe_tmp()
        tmp_out = os.path.join(tmp, "output.mp4")

        # Metin dosyaları (Türkçe karakter filter-string'e girmez)
        status_tf = _write_tf(tmp, "status.txt",   status_label)
        title_tf  = _write_tf(tmp, "title.txt",    title_text[:55])
        info_tf   = _write_tf(tmp, "info.txt",     info_line[:70])
        phone_tf  = _write_tf(tmp, "phone.txt",    PHONE_LINE)
        web_tf    = _write_tf(tmp, "website.txt",  WEBSITE_LINE)

        # Logo hazırla (ASCII yolda)
        logo_h   = H // 6
        logo_png = _prepare_logo(tmp, logo_h)

        segments: list[str] = []

        # ── Açılış ──
        intro_p = os.path.join(tmp, "seg_00_intro.mp4")
        _make_intro(ffmpeg, W, H, title_tf, status_tf, logo_png, tmp, intro_p)
        segments.append(intro_p)

        # ── Fotoğraflar ──
        pan_cycle = [1, -1, 1, -1, 1, -1, 1, -1]
        for i, photo_obj in enumerate(photos):
            img_path = os.path.join(settings.MEDIA_ROOT, str(photo_obj.image))
            if not os.path.isfile(img_path):
                log.warning("Fotoğraf bulunamadı, atlanıyor: %s", img_path)
                continue
            seg_p = os.path.join(tmp, f"seg_{i+1:02d}_photo.mp4")
            _make_photo(
                ffmpeg, W, H,
                img_path, info_tf, status_tf,
                pan_dir=pan_cycle[i % len(pan_cycle)],
                out=seg_p,
            )
            segments.append(seg_p)

        # ── Kapanış ──
        outro_p = os.path.join(tmp, f"seg_{len(segments):02d}_outro.mp4")
        _make_outro(ffmpeg, W, H, phone_tf, web_tf, logo_png, tmp, outro_p)
        segments.append(outro_p)

        # ── Birleştir ──
        _concat_xfade(ffmpeg, segments, tmp_out)

        # TMP → MEDIA_ROOT (Unicode yola Python kopyalar, sorun yok)
        shutil.copy2(tmp_out, final_path)

        job.output_url    = f"{settings.MEDIA_URL}videos/{out_filename}"
        job.status        = "completed"
        job.error_message = ""
        job.save(update_fields=["status", "output_url", "error_message", "updated_at"])
        log.info("VideoJob #%s tamamlandı → %s", job.id, final_path)

    except Exception as exc:
        log.exception("VideoJob #%s hata", job_id)
        try:
            job.status        = "error"
            job.error_message = str(exc)[:500]
            job.save(update_fields=["status", "error_message", "updated_at"])
        except Exception:
            pass
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def create_video_job(property_obj, user, photo_ids: list,
                     resolution: str = "720p", aspect_ratio: str = "9:16"):
    from apps.portfolio.models import VideoJob

    if not (3 <= len(photo_ids) <= 8):
        raise ValueError(
            f"Fotoğraf sayısı 3-8 arasında olmalıdır (gönderilen: {len(photo_ids)})."
        )
    valid_res    = [r[0] for r in VideoJob.RESOLUTION_CHOICES]
    valid_aspect = [r[0] for r in VideoJob.ASPECT_CHOICES]
    if resolution    not in valid_res:    resolution    = "720p"
    if aspect_ratio  not in valid_aspect: aspect_ratio  = "9:16"

    job = VideoJob.objects.create(
        property     = property_obj,
        created_by   = user,
        status       = "queued",
        resolution   = resolution,
        aspect_ratio = aspect_ratio,
        photo_order  = list(photo_ids),
    )
    threading.Thread(target=_build_video, args=(job.id,), daemon=True).start()
    return job


def cancel_video_job(job) -> bool:
    if job.status == "queued":
        job.status        = "error"
        job.error_message = "Kullanıcı tarafından iptal edildi."
        job.save(update_fields=["status", "error_message", "updated_at"])
        return True
    return False
