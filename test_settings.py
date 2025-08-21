# -*- encoding: utf-8 -*-
"""
Test Settings - SQLite kullanarak testler için
"""

from core.settings import *

# Test için SQLite kullan
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Test için hızlandırma
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Test için cache devre dışı
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Test için email backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Test için debug kapalı
DEBUG = False

# Test için logging minimal
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}