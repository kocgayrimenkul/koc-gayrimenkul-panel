"""
Sahibinden Pro Ofis API Entegrasyon Servisi
Belgeler: https://ofisim.sahibinden.com/ilanlar/ilan-transferi
"""
import requests
import logging
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)

SAHIBINDEN_API_BASE = "https://api.ofisim.sahibinden.com/v1"


def get_api_token():
    from .models import SahibindenSettings
    s = SahibindenSettings.get_settings()
    token = s.api_token.strip() if s.api_token else getattr(settings, 'SAHIBINDEN_API_TOKEN', '')
    return token


def api_headers():
    return {
        'Authorization': f'Bearer {get_api_token()}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }


# ─── PROPERTY → XML FEED DÖNÜŞÜMÜ ─────────────────────────────────

PROPERTY_TYPE_MAP = {
    'daire': 'Daire',
    'mustakil': 'Müstakil Ev',
    'dublex': 'Dubleks',
    'arsa': 'Arsa',
    'isyeri': 'İşyeri',
}

STATUS_MAP = {
    'satilik': 'SatılıkIsSaleTrue',
    'kiralik': 'KiralikIsRentTrue',
}

HEATING_MAP = {
    'dogalgaz': 'Doğalgaz (Kombi)',
    'merkezi': 'Merkezi Sistem',
    'klima': 'Klima',
    'soba': 'Soba',
    'yerden': 'Yerden Isıtma',
    'yok': 'Isıtma Yok',
}


def property_to_xml_dict(prop):
    """Property nesnesini XML feed sözlüğüne çevirir"""
    neighborhood = prop.neighborhood
    mahalle_adi = neighborhood.name if neighborhood else ''
    ilce = getattr(neighborhood, 'district', '') if neighborhood else ''
    il = getattr(neighborhood, 'city', '') if neighborhood else ''

    images = list(prop.images.filter().order_by('order').values_list('image', flat=True)[:20])

    return {
        'id': prop.pk,
        'title': prop.web_title or prop.apartment_name or f"İlan #{prop.pk}",
        'description': prop.description or '',
        'status': 'satilik' if prop.status == 'satilik' else 'kiralik',
        'price': str(int(prop.price)) if prop.price else '0',
        'property_type': PROPERTY_TYPE_MAP.get(prop.property_type, prop.property_type),
        'province': il,
        'district': ilce,
        'neighborhood': mahalle_adi,
        'address': prop.address or '',
        'net_area': str(int(prop.net_area)) if prop.net_area else '',
        'gross_area': str(int(prop.gross_area)) if prop.gross_area else '',
        'room_count': prop.room_count or '',
        'floor': prop.floor or '',
        'floor_count': prop.floor_count or '',
        'building_age': str(prop.building_age) if prop.building_age is not None else '',
        'heating': HEATING_MAP.get(prop.heating, ''),
        'has_balcony': 'true' if prop.has_balcony else 'false',
        'is_furnished': 'true' if prop.is_furnished else 'false',
        'is_in_site': 'true' if prop.is_in_site else 'false',
        'is_suitable_for_credit': 'true' if prop.is_suitable_for_credit else 'false',
        'is_bargainable': 'true' if prop.is_bargainable else 'false',
        'dues': str(int(prop.dues)) if prop.dues else '0',
        'images': images,
    }


# ─── XML FEED ÜRETİCİ ──────────────────────────────────────────────

def generate_xml_feed(request=None):
    """Tüm aktif ilanlar için Sahibinden XML feed'i üretir"""
    from apps.portfolio.models import Property
    from .models import SahibindenSyncLog
    import xml.etree.ElementTree as ET
    from xml.dom import minidom

    # Feed'e dahil edilecek ilanlar: aktif + sync kaydı olan veya hiç kaydı olmayan
    sync_excluded = SahibindenSyncLog.objects.filter(include_in_feed=False).values_list('property_id', flat=True)
    properties = Property.objects.filter(is_active=True).exclude(pk__in=sync_excluded).select_related('neighborhood').prefetch_related('images')

    root = ET.Element('Listings')
    root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')

    for prop in properties:
        d = property_to_xml_dict(prop)

        listing = ET.SubElement(root, 'Listing')

        def add(tag, text):
            el = ET.SubElement(listing, tag)
            el.text = str(text) if text is not None else ''

        add('ListingId', d['id'])
        add('Title', d['title'])

        desc_el = ET.SubElement(listing, 'Description')
        desc_el.text = d['description']

        add('ListingType', 'ForSale' if d['status'] == 'satilik' else 'ForRent')
        add('Price', d['price'])
        add('Currency', 'TRY')
        add('Category', 'Konut')
        add('PropertyType', d['property_type'])
        add('Province', d['province'])
        add('District', d['district'])
        add('Neighborhood', d['neighborhood'])
        add('Address', d['address'])
        add('NetArea', d['net_area'])
        add('GrossArea', d['gross_area'])
        add('RoomCount', d['room_count'])
        add('Floor', d['floor'])
        add('TotalFloors', d['floor_count'])
        add('BuildingAge', d['building_age'])
        add('HeatingType', d['heating'])
        add('HasBalcony', d['has_balcony'])
        add('IsFurnished', d['is_furnished'])
        add('IsInSite', d['is_in_site'])
        add('CreditEligible', d['is_suitable_for_credit'])
        add('IsBargainable', d['is_bargainable'])
        add('Dues', d['dues'])

        if d['images']:
            photos_el = ET.SubElement(listing, 'Photos')
            for i, img_path in enumerate(d['images'], 1):
                if request:
                    from django.conf import settings as django_settings
                    base = request.build_absolute_uri('/')[:-1]
                    img_url = f"{base}{django_settings.MEDIA_URL}{img_path}"
                else:
                    img_url = img_path
                photo_el = ET.SubElement(photos_el, 'Photo')
                photo_el.set('order', str(i))
                photo_el.text = img_url

    # Güzel formatla
    xml_str = ET.tostring(root, encoding='unicode', xml_declaration=False)
    dom = minidom.parseString(f'<?xml version="1.0" encoding="UTF-8"?>{xml_str}')
    return dom.toprettyxml(indent='  ', encoding=None).replace('<?xml version="1.0" ?>', '<?xml version="1.0" encoding="UTF-8"?>')


# ─── API İÇE AKTARMA (Sahibinden → Panel) ──────────────────────────

def fetch_listings_from_sahibinden():
    """Sahibinden'deki ilanları çekip panele aktarır"""
    token = get_api_token()
    if not token:
        return {'success': False, 'error': 'API token girilmemiş. Lütfen Sahibinden ayarlarından token ekleyin.'}

    try:
        resp = requests.get(
            f'{SAHIBINDEN_API_BASE}/listings',
            headers=api_headers(),
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        listings = data.get('listings', data.get('data', []))
        imported = 0
        updated = 0
        errors = []

        for listing in listings:
            try:
                result = _import_single_listing(listing)
                if result == 'created':
                    imported += 1
                elif result == 'updated':
                    updated += 1
            except Exception as e:
                errors.append(str(e))

        from .models import SahibindenSettings
        s = SahibindenSettings.get_settings()
        s.last_import_at = timezone.now()
        s.save(update_fields=['last_import_at'])

        return {
            'success': True,
            'imported': imported,
            'updated': updated,
            'errors': errors,
            'total': len(listings),
        }
    except requests.HTTPError as e:
        if e.response.status_code == 401:
            return {'success': False, 'error': 'API token geçersiz veya süresi dolmuş.'}
        return {'success': False, 'error': f'HTTP {e.response.status_code}: {e.response.text[:200]}'}
    except requests.RequestException as e:
        return {'success': False, 'error': f'Bağlantı hatası: {str(e)}'}


def _import_single_listing(listing_data):
    """Tek bir Sahibinden ilanını panele aktarır"""
    from apps.portfolio.models import Property
    from apps.customers.models import Neighborhood
    from .models import SahibindenSyncLog

    sahibinden_id = str(listing_data.get('id', '') or listing_data.get('listingId', ''))
    title = listing_data.get('title', '')
    price = listing_data.get('price', 0)
    description = listing_data.get('description', '')
    status = 'satilik' if listing_data.get('listingType', '').lower() in ['forsale', 'satilik'] else 'kiralik'
    neighborhood_name = listing_data.get('neighborhood', '')
    url = listing_data.get('url', '') or listing_data.get('listingUrl', '')

    # Mahalle bul veya oluştur
    neighborhood = None
    if neighborhood_name:
        neighborhood = Neighborhood.objects.filter(name__iexact=neighborhood_name).first()

    # Daha önce import edilmiş mi?
    existing_sync = SahibindenSyncLog.objects.filter(sahibinden_listing_id=sahibinden_id).first()
    if existing_sync:
        # Güncelle
        prop = existing_sync.property
        prop.price = price
        prop.description = description
        prop.save(update_fields=['price', 'description', 'updated_at'])
        existing_sync.last_synced_at = timezone.now()
        existing_sync.status = 'synced'
        existing_sync.sync_count += 1
        existing_sync.save()
        return 'updated'
    else:
        # Yeni ilan oluştur
        prop = Property.objects.create(
            apartment_name=title,
            description=description,
            price=price,
            status=status,
            property_type='daire',
            neighborhood=neighborhood or Neighborhood.objects.first(),
            sahibinden_active=True,
            owner_listing_number=sahibinden_id,
            sahibinden_url=url,
        )
        SahibindenSyncLog.objects.create(
            property=prop,
            sahibinden_listing_id=sahibinden_id,
            sahibinden_url=url,
            status='synced',
            direction='import',
            last_synced_at=timezone.now(),
        )
        return 'created'


# ─── API DIŞA AKTARMA (Panel → Sahibinden) ─────────────────────────

def push_property_to_sahibinden(property_id):
    """Tek bir ilanı Sahibinden API'ye gönderir"""
    from apps.portfolio.models import Property
    from .models import SahibindenSyncLog

    token = get_api_token()
    if not token:
        return {'success': False, 'error': 'API token girilmemiş.'}

    prop = Property.objects.select_related('neighborhood').prefetch_related('images').get(pk=property_id)
    d = property_to_xml_dict(prop)

    payload = {
        'title': d['title'],
        'description': d['description'],
        'listingType': 'ForSale' if d['status'] == 'satilik' else 'ForRent',
        'price': int(d['price']) if d['price'] else 0,
        'currency': 'TRY',
        'propertyType': d['property_type'],
        'province': d['province'],
        'district': d['district'],
        'neighborhood': d['neighborhood'],
        'netArea': int(d['net_area']) if d['net_area'] else None,
        'grossArea': int(d['gross_area']) if d['gross_area'] else None,
        'roomCount': d['room_count'],
        'floor': d['floor'],
        'buildingAge': int(d['building_age']) if d['building_age'] else None,
        'heatingType': d['heating'],
        'hasBalcony': d['has_balcony'] == 'true',
        'isFurnished': d['is_furnished'] == 'true',
        'creditEligible': d['is_suitable_for_credit'] == 'true',
    }
    payload = {k: v for k, v in payload.items() if v is not None and v != ''}

    sync_log, _ = SahibindenSyncLog.objects.get_or_create(property=prop)

    try:
        if sync_log.sahibinden_listing_id:
            # Güncelle
            resp = requests.put(
                f'{SAHIBINDEN_API_BASE}/listings/{sync_log.sahibinden_listing_id}',
                json=payload, headers=api_headers(), timeout=30,
            )
        else:
            # Yeni oluştur
            resp = requests.post(
                f'{SAHIBINDEN_API_BASE}/listings',
                json=payload, headers=api_headers(), timeout=30,
            )

        resp.raise_for_status()
        result = resp.json()

        listing_id = str(result.get('id', '') or result.get('listingId', ''))
        listing_url = result.get('url', '') or result.get('listingUrl', '')

        sync_log.sahibinden_listing_id = listing_id
        sync_log.sahibinden_url = listing_url
        sync_log.status = 'synced'
        sync_log.direction = 'export'
        sync_log.last_synced_at = timezone.now()
        sync_log.error_message = ''
        sync_log.sync_count += 1
        sync_log.save()

        # Portfolio modelini de güncelle
        prop.sahibinden_active = True
        prop.owner_listing_number = listing_id
        prop.sahibinden_url = listing_url
        prop.save(update_fields=['sahibinden_active', 'owner_listing_number', 'sahibinden_url'])

        from .models import SahibindenSettings
        s = SahibindenSettings.get_settings()
        s.last_export_at = timezone.now()
        s.save(update_fields=['last_export_at'])

        return {'success': True, 'listing_id': listing_id, 'url': listing_url}

    except requests.HTTPError as e:
        err = f'HTTP {e.response.status_code}: {e.response.text[:300]}'
        sync_log.status = 'error'
        sync_log.error_message = err
        sync_log.save()
        return {'success': False, 'error': err}
    except requests.RequestException as e:
        err = str(e)
        sync_log.status = 'error'
        sync_log.error_message = err
        sync_log.save()
        return {'success': False, 'error': err}
