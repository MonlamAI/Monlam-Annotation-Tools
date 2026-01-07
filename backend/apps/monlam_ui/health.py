"""
Health check views for deployment monitoring.
"""

import os
import mimetypes
from pathlib import Path
from django.http import JsonResponse, FileResponse, Http404
from django.views import View
from django.db import connection
from django.conf import settings


class HealthCheckView(View):
    """
    Simple health check endpoint for container orchestration.
    """
    
    def get(self, request):
        # Check database connectivity
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
        
        return JsonResponse({
            "status": "healthy" if db_status == "healthy" else "unhealthy",
            "database": db_status,
            "app": "monlam-doccano"
        })


class DebugStaticView(View):
    """
    Debug endpoint to verify static files deployment.
    Access at /debug-static/
    """
    
    def get(self, request):
        whitenoise_root = getattr(settings, 'WHITENOISE_ROOT', None)
        
        result = {
            'version': '2.0',  # Increment to verify deployment
            'base_dir': str(settings.BASE_DIR),
            'whitenoise_root': whitenoise_root,
            'static_root': str(settings.STATIC_ROOT) if settings.STATIC_ROOT else None,
        }
        
        # Check directories
        static_dist = settings.BASE_DIR / 'static' / 'dist'
        result['static_dist_path'] = str(static_dist)
        result['static_dist_exists'] = os.path.exists(static_dist)
        
        # Check Vue dist contents
        if os.path.exists(static_dist):
            result['root_files'] = os.listdir(static_dist)[:20]
            
            assets_path = static_dist / 'assets'
            if os.path.exists(assets_path):
                result['assets_files'] = os.listdir(assets_path)[:10]
                # Check if specific JS file exists
                for f in os.listdir(assets_path):
                    if f.endswith('.js') and f.startswith('index'):
                        result['main_js_file'] = f
                        result['main_js_path'] = str(assets_path / f)
                        result['main_js_exists'] = os.path.exists(assets_path / f)
                        result['main_js_size'] = os.path.getsize(assets_path / f)
                        break
            
            fonts_path = static_dist / 'fonts'
            if os.path.exists(fonts_path):
                result['fonts_files'] = os.listdir(fonts_path)
        
        # Check URL patterns
        from django.urls import get_resolver
        resolver = get_resolver()
        result['url_pattern_count'] = len(resolver.url_patterns)
        result['first_patterns'] = [str(p.pattern) for p in resolver.url_patterns[:5]]
        
        return JsonResponse(result)


class TestServeView(View):
    """
    Test endpoint to directly serve the main JS file.
    Access at /test-serve-js/
    """
    
    def get(self, request):
        static_dist = Path(settings.BASE_DIR) / 'static' / 'dist'
        assets_path = static_dist / 'assets'
        
        # Find the main JS file
        js_file = None
        if assets_path.exists():
            for f in os.listdir(assets_path):
                if f.endswith('.js') and f.startswith('index'):
                    js_file = assets_path / f
                    break
        
        if not js_file or not js_file.exists():
            return JsonResponse({'error': 'JS file not found', 'checked': str(assets_path)}, status=404)
        
        # Serve it with explicit content type
        response = FileResponse(
            open(js_file, 'rb'),
            content_type='application/javascript'
        )
        response['Content-Length'] = js_file.stat().st_size
        response['X-Debug-File'] = str(js_file)
        return response

