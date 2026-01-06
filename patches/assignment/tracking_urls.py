"""
URL Configuration for Annotation Tracking API
"""

from django.urls import path
from rest_framework.routers import DefaultRouter
from .tracking_api import AnnotationTrackingViewSet

app_name = 'tracking'

# Create router for viewset
router = DefaultRouter()
router.register(r'', AnnotationTrackingViewSet, basename='tracking')

urlpatterns = router.urls

