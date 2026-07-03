# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Ayarlar
"""

import os
import environ
from unipath import Path

# Build paths
BASE_DIR = Path(__file__).parent
CORE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# django-environ kurulumu
env = environ.Env(
    DEBUG=(bool, True),
    SECRET_KEY=(str, 'S#perS3crEt_1122'),
    SERVER=(str, '127.0.0.1'),
    DB_NAME=(str, 'koc_gayrimenkul'),
    DB_USER=(str, 'root'),
    DB_PASSWORD=(str, ''),
    DB_HOST=(str, 'localhost'),
    DB_PORT=(str, '3306'),
    GOOGLE_MAPS_API_KEY=(str, ''),
    OPENAI_API_KEY=(str, ''),
    META_VERIFY_TOKEN=(str, 'koc_gayrimenkul_verify'),
    META_ACCESS_TOKEN=(str, ''),
    WHATSAPP_PHONE_NUMBER_ID=(str, ''),
    PANEL_URL=(str, 'https://panelkocgayrimenkul.com'),
)

# .env dosyasını oku
env_file = os.path.join(CORE_DIR, '.env')
environ.Env.read_env(env_file=env_file)

# ─────────────────────────────────────────────
# Güvenlik
# ─────────────────────────────────────────────
SECRET_KEY = env('SECRET_KEY')
OPENAI_API_KEY          = env('OPENAI_API_KEY')
# API key geçerli olduğunda True yapın
OPENAI_ENABLED          = False
META_VERIFY_TOKEN       = env('META_VERIFY_TOKEN')
META_ACCESS_TOKEN       = env('META_ACCESS_TOKEN')
WHATSAPP_PHONE_NUMBER_ID = env('WHATSAPP_PHONE_NUMBER_ID')
PANEL_URL               = env('PANEL_URL')
DEBUG = env('DEBUG')

raw_allowed = env('ALLOWED_HOSTS', default='localhost,127.0.0.1')
ALLOWED_HOSTS = [h.strip() for h in raw_allowed.split(',') if h.strip()]

# SERVER ekle
try:
    server_host = env('SERVER')
    if server_host and server_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(server_host)
except Exception:
    pass

# Ngrok/Cloudflare tünelleri için
for _p in ['.ngrok.io', '.ngrok-free.app', '.trycloudflare.com']:
    if _p not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_p)

# ─────────────────────────────────────────────
# Uygulamalar
# ─────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Third-party
    'rest_framework',
    'corsheaders',
    'django_filters',
    'django_celery_beat',
    'django_celery_results',

    # Local apps
    'apps.api',
    'apps.home',
    'apps.authentication',
    'apps.customers',
    'apps.portfolio',
    'apps.calendar',
    'apps.employees',
    'apps.presentation',
    'apps.fsbo',
    'apps.careers',
    'apps.contact',
    'apps.team',
    'apps.sales_process',
    'apps.calls',
    'apps.messaging',
    'apps.muhasebe',
    'apps.saha',
    'apps.sahibinden',
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'authentication.CustomUser'

AUTHENTICATION_BACKENDS = [
    'apps.authentication.backends.EmailOrUsernameBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# ─────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────
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
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "home"

# ─────────────────────────────────────────────
# Templates
# ─────────────────────────────────────────────
TEMPLATE_DIR = os.path.join(CORE_DIR, "apps/templates")

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
                'apps.customers.views.customer_reminders_processor',
                'apps.home.context_processors.settings_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# ─────────────────────────────────────────────
# Veritabanı
# ─────────────────────────────────────────────
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
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES', time_zone='+00:00';",
        },
    }
}

# ─────────────────────────────────────────────
# Şifre Doğrulama
# ─────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─────────────────────────────────────────────
# Dil & Zaman
# ─────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Istanbul'
USE_I18N = False
USE_L10N = True
USE_TZ = True

# ─────────────────────────────────────────────
# Static & Media
# ─────────────────────────────────────────────
STATIC_ROOT = os.path.join(CORE_DIR, 'staticfiles')
STATIC_URL = '/static/'
STATICFILES_DIRS = (os.path.join(CORE_DIR, 'apps/static'),)

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(CORE_DIR, 'media')

# ─────────────────────────────────────────────
# Messages
# ─────────────────────────────────────────────
from django.contrib.messages import constants as msg_constants
MESSAGE_TAGS = {
    msg_constants.DEBUG:   'alert-secondary',
    msg_constants.INFO:    'alert-info',
    msg_constants.SUCCESS: 'alert-success',
    msg_constants.WARNING: 'alert-warning',
    msg_constants.ERROR:   'alert-danger',
}

# ─────────────────────────────────────────────
# Özel Ayarlar
# ─────────────────────────────────────────────
SITE_TITLE = "Koç Gayrimenkul Panel"
GOOGLE_MAPS_API_KEY = env('GOOGLE_MAPS_API_KEY')

DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100 MB

# ─────────────────────────────────────────────
# CSRF & Cookie Güvenliği
# DEBUG=True ise güvensiz (local) modda çalış
# ─────────────────────────────────────────────
CSRF_TRUSTED_ORIGINS = [
    'https://panelkocgayrimenkul.com',
    'http://panelkocgayrimenkul.com',
    'https://www.panelkocgayrimenkul.com',
    'http://www.panelkocgayrimenkul.com',
]

if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
else:
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False

# ─────────────────────────────────────────────
# REST Framework
# ─────────────────────────────────────────────
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
    ],
}

# ─────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://panelkocgayrimenkul.com",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = DEBUG

CORS_ALLOW_HEADERS = [
    'accept', 'accept-encoding', 'authorization', 'content-type',
    'dnt', 'origin', 'user-agent', 'x-csrftoken', 'x-requested-with',
]

# ─────────────────────────────────────────────
# WhatsApp
# ─────────────────────────────────────────────
WHATSAPP_ACCESS_TOKEN = env('WHATSAPP_ACCESS_TOKEN', default='')
WHATSAPP_PHONE_NUMBER_ID = env('WHATSAPP_PHONE_NUMBER_ID', default='')
WHATSAPP_BUSINESS_ACCOUNT_ID = env('WHATSAPP_BUSINESS_ACCOUNT_ID', default='')
WHATSAPP_WEBHOOK_VERIFY_TOKEN = env('WHATSAPP_WEBHOOK_VERIFY_TOKEN', default='koc_gayrimenkul_webhook_token')
WHATSAPP_API_VERSION = env('WHATSAPP_API_VERSION', default='v18.0')
WHATSAPP_API_BASE_URL = f'https://graph.facebook.com/{WHATSAPP_API_VERSION}'
WHATSAPP_MOCK_MODE = env('WHATSAPP_MOCK_MODE', default=True)

# ─────────────────────────────────────────────
# NetGSM
# ─────────────────────────────────────────────
NETGSM_USERCODE = env('NETGSM_USERCODE', default='')
NETGSM_PASSWORD = env('NETGSM_PASSWORD', default='')

# ─────────────────────────────────────────────
# Celery
# ─────────────────────────────────────────────
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    'expire-portal-listings-daily': {
        'task': 'portfolio.expire_portal_listings',
        'schedule': crontab(hour=3, minute=0),
    },
}

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}
def customer_reminders_processor(request):
    """Context processor - her sayfada müşteri hatırlatmalarını sağlar"""
    if not request.user.is_authenticated:
        return {'customer_reminders': [], 'customer_reminders_count': 0}
    try:
        from .models import CustomerReminder
        reminders = CustomerReminder.objects.filter(
            customer__consultant=request.user,
            is_read=False,
        ).select_related('customer')[:10]
        return {
            'customer_reminders': reminders,
            'customer_reminders_count': reminders.count(),
        }
    except Exception:
        return {'customer_reminders': [], 'customer_reminders_count': 0}