"""
URL patterns for annotation tracking.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    TrackingViewSet, ExampleTrackingView, ExampleStatusView,
    ApproveView, RejectView, LockView, UnlockView, MarkSubmittedView
)

router = DefaultRouter()
router.register('tracking', TrackingViewSet, basename='tracking')

urlpatterns = [
    # Tracking ViewSet (list, detail, summary, annotators, approvers)
    path('projects/<int:project_id>/', include(router.urls)),
    
    # Example-specific tracking endpoints
    path('projects/<int:project_id>/tracking/<int:example_id>/', 
         ExampleTrackingView.as_view(), name='example_tracking'),
    path('projects/<int:project_id>/tracking/<int:example_id>/status/', 
         ExampleStatusView.as_view(), name='example_status'),
    
    # Approve/Reject workflow
    path('projects/<int:project_id>/tracking/<int:example_id>/approve/', 
         ApproveView.as_view(), name='approve'),
    path('projects/<int:project_id>/tracking/<int:example_id>/reject/', 
         RejectView.as_view(), name='reject'),
    
    # Lock/Unlock
    path('projects/<int:project_id>/tracking/<int:example_id>/lock/', 
         LockView.as_view(), name='lock'),
    path('projects/<int:project_id>/tracking/<int:example_id>/unlock/', 
         UnlockView.as_view(), name='unlock'),
    
    # Manual submit
    path('projects/<int:project_id>/tracking/<int:example_id>/submit/', 
         MarkSubmittedView.as_view(), name='mark_submitted'),
]

