"""
URL patterns for Monlam UI pages.
Note: Metrics → Completion redirect is handled by Vue router (frontend SPA).
"""

from django.urls import path
from .views import completion_dashboard, completion_dashboard_api

urlpatterns = [
    # Completion Dashboard (Django template fallback + API)
    path('<int:project_id>/completion/', completion_dashboard, name='completion_dashboard'),
    path('<int:project_id>/completion/api/', completion_dashboard_api, name='completion_dashboard_api'),
]

