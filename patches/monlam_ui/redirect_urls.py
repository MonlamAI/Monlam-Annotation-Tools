"""
URL Redirects for Doccano Menu Items

These URLs intercept standard Doccano paths and redirect to Monlam enhanced views.
They must be included in the main urls.py BEFORE Doccano's URL patterns to take precedence.

Usage in config/urls.py:
    from monlam_ui.redirect_urls import redirect_patterns
    
    urlpatterns = [
        *redirect_patterns,  # Include redirects first
        # ... rest of Doccano URLs
    ]
"""

from django.urls import path
from .views import DatasetRedirectView, MetricsRedirectView

# These patterns intercept Doccano's default URLs
redirect_patterns = [
    # Redirect /projects/{id}/dataset → /monlam/{id}/dataset-enhanced/
    path(
        'projects/<int:project_id>/dataset',
        DatasetRedirectView.as_view(),
        name='monlam-dataset-redirect'
    ),
    
    # Redirect /projects/{id}/metrics → /monlam/{id}/completion/
    path(
        'projects/<int:project_id>/metrics',
        MetricsRedirectView.as_view(),
        name='monlam-metrics-redirect'
    ),
]

