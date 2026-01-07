"""
Serve Vue.js frontend for SPA routing.
"""

import os
from django.http import HttpResponse
from django.conf import settings
from django.views import View

from .static_serve import try_serve_static


class FrontendView(View):
    """
    Serve the Vue.js frontend.
    - First tries to serve as a static file (CSS, JS, images)
    - Otherwise serves index.html for SPA routing
    """
    
    def get(self, request, *args, **kwargs):
        # Try to serve as static file first
        static_response = try_serve_static(request)
        if static_response:
            return static_response
        
        # Serve index.html for SPA routes
        index_path = os.path.join(settings.BASE_DIR, 'static', 'dist', 'index.html')
        
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                return HttpResponse(f.read(), content_type='text/html')
        
        # Fallback if index.html not found
        return HttpResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>Monlam Annotation Tools</title>
    <meta charset="UTF-8">
    <style>
        body { 
            font-family: system-ui, sans-serif; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
            margin: 0; 
            background: #1a1a2e; 
            color: white; 
        }
        .container { text-align: center; }
        h1 { color: #B8963E; }
        a { 
            color: #B8963E; 
            text-decoration: none; 
            padding: 10px 20px; 
            border: 2px solid #B8963E; 
            border-radius: 8px; 
            display: inline-block; 
            margin: 10px; 
        }
        a:hover { background: #B8963E; color: #1a1a2e; }
    </style>
</head>
<body>
    <div class="container">
        <h1>སྨོན་ལམ་ཞུ་དག་ཁང་།</h1>
        <h2>Monlam Annotation Tools</h2>
        <p>Frontend assets not found. Please rebuild.</p>
        <a href="/admin/">Admin Panel</a>
        <a href="/health/">Health Check</a>
    </div>
</body>
</html>
        """, content_type='text/html')
