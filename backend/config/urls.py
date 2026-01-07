"""
URL configuration for Monlam Doccano project.
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from apps.monlam_ui.health import HealthCheckView
from apps.monlam_ui.frontend import FrontendView
from apps.monlam_ui.static_serve import serve_assets, serve_fonts, serve_root_file

urlpatterns = [
    # Serve Vue.js static assets FIRST (before any other patterns)
    path('_app/<path:path>', serve_assets, name='serve_assets'),
    path('_fonts/<path:path>', serve_fonts, name='serve_fonts'),
    re_path(r'^(?P<path>favicon\.(ico|png|svg))$', serve_root_file, name='serve_favicon'),
    re_path(r'^(?P<path>logo\.(png|svg))$', serve_root_file, name='serve_logo'),
    
    # Health check
    path('health/', HealthCheckView.as_view(), name='health'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # Authentication
    path('v1/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('v1/auth/', include('apps.users.urls')),
    
    # Core API endpoints
    path('v1/', include('apps.projects.urls')),
    path('v1/', include('apps.examples.urls')),
    path('v1/', include('apps.labels.urls')),
    
    # Monlam tracking endpoints
    path('v1/', include('apps.monlam_tracking.urls')),
    
    # Monlam UI (completion dashboard API)
    path('monlam/', include('apps.monlam_ui.urls')),
]

# Static files for Django admin in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Catch-all: Serve Vue.js frontend for SPA routing
# This must be LAST so API routes and static files take precedence
urlpatterns += [
    re_path(r'^.*$', FrontendView.as_view(), name='frontend'),
]
