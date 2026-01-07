"""
WSGI config for Monlam Doccano project.

Whitenoise is configured here to serve Vue.js static files from WHITENOISE_ROOT.
"""

import os
from pathlib import Path

from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create the Django WSGI application
django_application = get_wsgi_application()

# Wrap with WhiteNoise for static file serving
application = WhiteNoise(django_application)

# Add Vue.js dist files at root URL (so /assets/... serves from static/dist/assets/...)
BASE_DIR = Path(__file__).resolve().parent.parent
vue_dist_path = BASE_DIR / 'static' / 'dist'
if vue_dist_path.exists():
    application.add_files(str(vue_dist_path), prefix='')

