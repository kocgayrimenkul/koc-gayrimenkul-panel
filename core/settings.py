# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel 
"""

import os
import environ
from unipath import Path

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = Path(__file__).parent
CORE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# django-environ kurulumu
env = environ.Env(
    # varsayılan değerler
    DEBUG=(bool, True),
    SECRET_KEY=(str, 'S#perS3crEt_1122'),
    SERVER=(str, '127.0.0.1'),
    DB_NAME=(str, 'koc_gayrimenkul'),
    DB_USER=(str, 'root'),
    DB_PASSWORD=(str, ''),
    DB_HOST=(str, 'localhost'),
    DB_PORT=(str, '3306'),
    GOOGLE_MAPS_API_KEY=(str, ''),
)

# .env dosyasının yolu
env_file = os.path.join(CORE_DIR, '.env')

# .env dosyasını oku (varsa)
environ.Env.read_env(env_file=env_file)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

# load production server from .env
# Prefer ALLOWED_HOSTS from environment (comma separated). Keep localhost and SERVER by default.
raw_allowed = env('ALLOWED_HOSTS', default='localhost,127.0.0.1')
ALLOWED_HOSTS = [h.strip() for h in raw_allowed.split(',') if h.strip()]

# Ensure SERVER is present
try:
    server_host = env('SERVER')
except Exception:
    server_host = None
if server_host and server_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(server_host)

# Allow common ngrok domains (use leading dot to permit any subdomain)
for _p in ['.ngrok.io', '.ngrok-free.app', '.trycloudflare.com']:
    if _p not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_p)

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',  # Fiyat formatlaması için humanize filter'ları
    
    # Django REST Framework
    'rest_framework',
    'corsheaders',
    'django_filters',
    
    'apps.api',              # REST API uygulaması
    'apps.home',             # Ana sayfa
    'apps.authentication',   # Kimlik doğrulama
    'apps.customers',        # Müşteri yönetimi
    'apps.portfolio',        # Portföy yönetimi
    'apps.calendar',         # Takvim/ajanda
    'apps.employees',        # Çalışan yönetimi
    'apps.presentation',     # Daire sunumu
    'apps.fsbo',             # FSBO yönetimi
    'apps.careers',          # Kariyer yönetimi
    'apps.contact',          # İletişim yönetimi
    'apps.team',             # Ekip yönetimi
    'apps.sales_process',    # Satış Süreç Yönetimi
]

# Django 3.2+ için modellerdeki otomatik primary key tipi ayarı
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Özel kullanıcı modeli
AUTH_USER_MODEL = 'authentication.CustomUser'

# Kimlik doğrulama backend'leri
AUTHENTICATION_BACKENDS = [
    'apps.authentication.backends.EmailOrUsernameBackend',
    'django.contrib.auth.backends.ModelBackend',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'
LOGIN_REDIRECT_URL = "calendar"  # Route defined in calendar/urls.py
LOGOUT_REDIRECT_URL = "home"  # Route defined in home/urls.py
TEMPLATE_DIR = os.path.join(CORE_DIR, "apps/templates")  # ROOT dir for templates

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.customers.views.customer_reminders_processor',  # Müşteri hatırlatmaları
                'apps.home.context_processors.settings_context',  # Settings değişkenlerine erişim
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DB_NAME', default='koc_gayrimenkul'),
        'USER': env('DB_USER', default='root'),
        'PASSWORD': env('DB_PASSWORD', default=''),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        }
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'tr-tr'

TIME_ZONE = 'Europe/Istanbul'

USE_I18N = True

USE_L10N = True

USE_TZ = True

#############################################################
# SRC: https://devcenter.heroku.com/articles/django-assets

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/
STATIC_ROOT = os.path.join(CORE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Extra places for collectstatic to find static files.
STATICFILES_DIRS = (
    os.path.join(CORE_DIR, 'apps/static'),
)

# Media dosyaları için yapılandırma
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(CORE_DIR, 'media')

# Mesaj çerçevesi
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-secondary',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

# Koç Gayrimenkul Özel Ayarlar
SITE_TITLE = "Koç Gayrimenkul Panel"

# Google Maps API Anahtarı
GOOGLE_MAPS_API_KEY = env('GOOGLE_MAPS_API_KEY')

# Dosya Yükleme Limitleri
DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100 MB

# CSRF Ayarları ve Güvenli Cookie
CSRF_TRUSTED_ORIGINS = ['https://panelkocgayrimenkul.com', 'http://panelkocgayrimenkul.com']
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

#############################################################
#############################################################

# Django REST Framework Ayarları
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ]
}

# CORS Ayarları (Next.js için)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Next.js development server
    "http://127.0.0.1:3000",
    "https://yourdomain.com",  # Production Next.js domain
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_ALL_ORIGINS = DEBUG  # Sadece development'ta tüm origin'lere izin ver

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# WhatsApp Business Cloud API Settings
WHATSAPP_ACCESS_TOKEN = env('WHATSAPP_ACCESS_TOKEN', default='')
WHATSAPP_PHONE_NUMBER_ID = env('WHATSAPP_PHONE_NUMBER_ID', default='')
WHATSAPP_BUSINESS_ACCOUNT_ID = env('WHATSAPP_BUSINESS_ACCOUNT_ID', default='')
WHATSAPP_WEBHOOK_VERIFY_TOKEN = env('WHATSAPP_WEBHOOK_VERIFY_TOKEN', default='koc_gayrimenkul_webhook_token')
WHATSAPP_API_VERSION = env('WHATSAPP_API_VERSION', default='v18.0')
WHATSAPP_API_BASE_URL = f'https://graph.facebook.com/{WHATSAPP_API_VERSION}'

# WhatsApp Mock Mode - Gerçek entegrasyon aktif olmadığında simülasyon için
WHATSAPP_MOCK_MODE =True

# Celery Configuration (for async tasks)
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Netgsm API Settings (for call center integration)
NETGSM_ENABLED = False  # NetGSM entegrasyonunu aktif/pasif yapmak için
NETGSM_USERNAME = env('NETGSM_USERNAME', default='8508850860')  # Santral numarası
NETGSM_PASSWORD = '72B5*C8'
NETGSM_API_KEY = env('NETGSM_API_KEY', default='')
NETGSM_WEBHOOK_SECRET = env('NETGSM_WEBHOOK_SECRET', default='netgsm_webhook_secret')
NETGSM_PBX_NUMBER = env('NETGSM_PBX_NUMBER', default='8508850860')  # Santral numarası
NETGSM_CRM_BASE_URL = env('NETGSM_CRM_BASE_URL', default='http://crmsntrl.netgsm.com.tr:9111')  # CRM API Base URL
NETGSM_API_BASE_URL = env('NETGSM_API_BASE_URL', default='https://api.netgsm.com.tr')  # Main API Base URL

#############################################################
#############################################################
