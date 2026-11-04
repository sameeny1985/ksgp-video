"""
ASGI config for KSGP Video project.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ksgp_video.settings')

application = get_asgi_application()
