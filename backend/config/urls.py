"""
URL configuration for Monlam Doccano project.
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from apps.monlam_ui.health import HealthCheckView, DebugStaticView
from apps.monlam_ui.frontend import FrontendView

# Vue dist directory for serving assets (as string for Django's serve view)
VUE_DIST_DIR = str(settings.BASE_DIR / 'static' / 'dist')
VUE_ASSETS_DIR = str(settings.BASE_DIR / 'static' / 'dist' / 'assets')
VUE_FONTS_DIR = str(settings.BASE_DIR / 'static' / 'dist' / 'fonts')

urlpatterns = [
    # Health check and debug
    path('health/', HealthCheckView.as_view(), name='health'),
    path('debug-static/', DebugStaticView.as_view(), name='debug_static'),
    
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
    
    # Serve Vue.js static assets directly (bypassing Whitenoise issues)
    re_path(r'^assets/(?P<path>.*)$', serve, {'document_root': VUE_ASSETS_DIR}),
    re_path(r'^fonts/(?P<path>.*)$', serve, {'document_root': VUE_FONTS_DIR}),
    re_path(r'^(?P<path>favicon\.(ico|png|svg))$', serve, {'document_root': VUE_DIST_DIR}),
    re_path(r'^(?P<path>logo\.(png|svg))$', serve, {'document_root': VUE_DIST_DIR}),
]

# Static files for Django admin etc
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Catch-all: Serve Vue.js frontend for SPA routing
# This must be LAST so API routes and static files take precedence
urlpatterns += [
    re_path(r'^.*$', FrontendView.as_view(), name='frontend'),
]

