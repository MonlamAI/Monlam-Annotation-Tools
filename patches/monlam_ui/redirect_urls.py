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

# SERVER-SIDE REDIRECTS DISABLED
# Reason: Server-side redirects can't "pass through" to Doccano's original views
#         This breaks Project Admins who need the original dataset page
#
# Solution: Client-side redirects ONLY (in index.html)
#          Client-side can check user roles and decide whether to redirect
#
redirect_patterns = [
    # Empty list - no server-side redirects
    # All redirects handled by JavaScript in patches/frontend/index.html
]

