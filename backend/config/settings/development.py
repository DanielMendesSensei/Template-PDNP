# backend/config/settings/development.py
from .base import *

DEBUG = True

# REMOVER completamente arquivos estáticos para API
STATICFILES_DIRS = []
STATIC_ROOT = None
STATIC_URL = None

# Remover WhiteNoise do middleware
MIDDLEWARE = [item for item in MIDDLEWARE if 'whitenoise' not in item.lower()]

# Remover staticfiles do INSTALLED_APPS
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'django.contrib.staticfiles']

# API-only: sem admin interface
# INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'django.contrib.admin']

# CORS para Next.js
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]
CORS_ALLOW_ALL_ORIGINS = True  # Apenas para desenvolvimento
CORS_ALLOW_CREDENTIALS = True

# ===== CACHE (usar Redis) =====
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Session usando Redis
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'