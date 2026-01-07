"""
WSGI config for Monlam Doccano project.

Static files are served via Django URL routing (see urls.py).
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()

