"""
Health check views for deployment monitoring.
"""

import os
from django.http import JsonResponse
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
            'base_dir': str(settings.BASE_DIR),
            'whitenoise_root': whitenoise_root,
            'static_root': str(settings.STATIC_ROOT) if settings.STATIC_ROOT else None,
        }
        
        # Check directories
        static_dist = settings.BASE_DIR / 'static' / 'dist'
        result['static_dist_path'] = str(static_dist)
        result['static_dist_exists'] = os.path.exists(static_dist)
        
        if whitenoise_root:
            result['whitenoise_root_exists'] = os.path.exists(whitenoise_root)
            if os.path.exists(whitenoise_root):
                result['root_files'] = os.listdir(whitenoise_root)[:20]
                
                assets_path = os.path.join(whitenoise_root, 'assets')
                if os.path.exists(assets_path):
                    result['assets_files'] = os.listdir(assets_path)[:10]
                
                fonts_path = os.path.join(whitenoise_root, 'fonts')
                if os.path.exists(fonts_path):
                    result['fonts_files'] = os.listdir(fonts_path)
        
        return JsonResponse(result)

