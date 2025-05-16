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
ALLOWED_HOSTS = ['localhost', '127.0.0.1', env('SERVER')]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.home',             # Ana sayfa
    'apps.authentication',   # Kimlik doğrulama
    'apps.customers',        # Müşteri yönetimi
    'apps.portfolio',        # Portföy yönetimi
    'apps.calendar',         # Takvim/ajanda
    'apps.employees',        # Çalışan yönetimi
    'apps.presentation',     # Daire sunumu
    'apps.fsbo',             # FSBO yönetimi
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
LOGIN_REDIRECT_URL = "home"  # Route defined in home/urls.py
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
