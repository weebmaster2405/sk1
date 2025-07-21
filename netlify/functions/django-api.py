import os
from django.core.wsgi import get_wsgi_application

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orgchart.settings_production')
application = get_wsgi_application()

def handler(event, context):
    """Serverless function handler for Django application."""
    return application(event, context)
