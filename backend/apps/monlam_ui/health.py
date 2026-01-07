"""
Health check views for deployment monitoring.
"""

from django.http import JsonResponse
from django.views import View
from django.db import connection


class HealthCheckView(View):
    """
    Health check endpoint for container orchestration (Render, K8s, etc.).
    Returns 200 if healthy, 503 if database connection fails.
    """
    
    def get(self, request):
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
