"""
URL configuration for Monlam Doccano project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from apps.monlam_ui.health import HealthCheckView

urlpatterns = [
    # Health check
    path('health/', HealthCheckView.as_view(), name='health'),
    
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
    
    # Note: Metrics → Completion redirect is handled by Vue router (frontend)
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

