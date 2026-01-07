"""
Serve Vue.js frontend for SPA routing.
"""

import os
import logging
from django.http import HttpResponse, Http404
from django.conf import settings
from django.views import View

logger = logging.getLogger(__name__)


class FrontendView(View):
    """
    Serve the Vue.js frontend index.html for all non-API routes.
    This enables SPA routing (Vue Router handles client-side routes).
    """
    
    def get(self, request, *args, **kwargs):
        # Try to find index.html in static/dist
        index_paths = [
            os.path.join(settings.BASE_DIR, 'static', 'dist', 'index.html'),
            os.path.join(settings.STATIC_ROOT or '', 'dist', 'index.html'),
            os.path.join(settings.BASE_DIR, 'staticfiles', 'dist', 'index.html'),
        ]
        
        logger.info(f"FrontendView: Looking for index.html, BASE_DIR={settings.BASE_DIR}")
        
        for index_path in index_paths:
            logger.info(f"FrontendView: Checking {index_path}, exists={os.path.exists(index_path)}")
            if os.path.exists(index_path):
                with open(index_path, 'r', encoding='utf-8') as f:
                    return HttpResponse(f.read(), content_type='text/html')
        
        # Fallback: Return a simple HTML that redirects to /admin for now
        return HttpResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>Monlam Annotation Tools</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: system-ui, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #1a1a2e; color: white; }
        .container { text-align: center; }
        h1 { color: #B8963E; }
        a { color: #B8963E; text-decoration: none; padding: 10px 20px; border: 2px solid #B8963E; border-radius: 8px; display: inline-block; margin: 10px; }
        a:hover { background: #B8963E; color: #1a1a2e; }
    </style>
</head>
<body>
    <div class="container">
        <h1>མོན་ལམ་མཆན་འགོད་ལག་ཆ།</h1>
        <h2>Monlam Annotation Tools</h2>
        <p>API is running! Frontend assets not found.</p>
        <a href="/admin/">Admin Panel</a>
        <a href="/health/">Health Check</a>
        <a href="/v1/">API</a>
    </div>
</body>
</html>
        """, content_type='text/html')

