"""
WSGI config for KSGP Video project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ksgp_video.settings')

application = get_wsgi_application()
