"""
Example URL patterns.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ExampleViewSet
from .upload_views import ExampleUploadView, ExampleUploadPreviewView

router = DefaultRouter()
router.register('examples', ExampleViewSet, basename='example')

urlpatterns = [
    path('projects/<int:project_id>/', include(router.urls)),
    # Upload endpoints
    path('projects/<int:project_id>/examples/upload', 
         ExampleUploadView.as_view(), name='example-upload'),
    path('projects/<int:project_id>/examples/upload/preview', 
         ExampleUploadPreviewView.as_view(), name='example-upload-preview'),
]

