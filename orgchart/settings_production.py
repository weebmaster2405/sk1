"""
Production settings for PythonAnywhere deployment
"""
import os
from pathlib import Path
from .settings import *

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
STATIC_ROOT = '/home/aniket3077/insideorgs/staticfiles/'

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/aniket3077/insideorgs/media/'

# Database configuration for PythonAnywhere
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# CORS settings for production
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://aniket3077.pythonanywhere.com",
    "https://www.aniket3077.pythonanywhere.com",
]

# CSRF settings
CSRF_TRUSTED_ORIGINS = [
    'https://aniket3077.pythonanywhere.com',
    'https://www.aniket3077.pythonanywhere.com',
]

# Email configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'your-email@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'your-app-password')
EMAIL_SENDER_ID = os.environ.get('EMAIL_SENDER_ID', 'noreply@insideorgs.com')

# Remove WhiteNoise middleware for PythonAnywhere
MIDDLEWARE = [mw for mw in MIDDLEWARE if 'whitenoise' not in mw.lower()]