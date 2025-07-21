"""
Production settings for PythonAnywhere deployment
"""
import os
from pathlib import Path
from .settings import *
import dj_database_url

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Update allowed hosts for your PythonAnywhere domain
ALLOWED_HOSTS = [
    'aniket3077.pythonanywhere.com',
    'www.aniket3077.pythonanywhere.com',
    'localhost',
    '127.0.0.1',
]

# Static files configuration for PythonAnywhere
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Database Configuration - Using Supabase PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
} if not os.environ.get('DATABASE_URL') else {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
        engine='django.db.backends.postgresql'
    )
}

# Security settings for production
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# CORS settings for production
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    'https://aniket3077.pythonanywhere.com',
    'https://www.aniket3077.pythonanywhere.com',
]

# CSRF settings
CSRF_TRUSTED_ORIGINS = [
    'https://aniket3077.pythonanywhere.com',
    'https://www.aniket3077.pythonanywhere.com',
]

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# Remove WhiteNoise middleware
MIDDLEWARE = [mw for mw in MIDDLEWARE if 'whitenoise' not in mw.lower()]