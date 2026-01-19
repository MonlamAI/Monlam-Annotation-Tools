"""
Tracking API URL Configuration

URLs for the annotation tracking API (approve/reject/status)
Registered at: /v1/projects/<project_id>/tracking/
NOTE: Locking endpoints removed - single annotator per project, no race conditions
"""

from django.urls import path
from .tracking_api import AnnotationTrackingViewSet

urlpatterns = [
    # Mark example as submitted
    path('mark-submitted/', 
         AnnotationTrackingViewSet.as_view({'post': 'mark_submitted'}), 
         name='tracking-mark-submitted'),
    
    # Get status of specific example
    path('<int:pk>/status/', 
         AnnotationTrackingViewSet.as_view({'get': 'get_status'}), 
         name='tracking-status'),
    
    # Approve an example
    path('<int:pk>/approve/', 
         AnnotationTrackingViewSet.as_view({'post': 'approve'}), 
         name='tracking-approve'),
    
    # Reject an example
    path('<int:pk>/reject/', 
         AnnotationTrackingViewSet.as_view({'post': 'reject'}), 
         name='tracking-reject'),
    
    # NOTE: Locking URLs removed - single annotator per project, no race conditions
]
