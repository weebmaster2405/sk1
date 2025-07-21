"""
WSGI config for orgchart project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orgchart.settings')

application = get_wsgi_application()
