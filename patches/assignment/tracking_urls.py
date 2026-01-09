"""
Tracking API URL Configuration

URLs for the annotation tracking API (approve/reject/status/lock)
Registered at: /v1/projects/<project_id>/tracking/
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
    
    # Lock an example
    path('<int:pk>/lock/', 
         AnnotationTrackingViewSet.as_view({'post': 'lock'}), 
         name='tracking-lock'),
    
    # Unlock an example
    path('<int:pk>/unlock/', 
         AnnotationTrackingViewSet.as_view({'post': 'unlock'}), 
         name='tracking-unlock'),
    
    # Check lock status
    path('<int:pk>/lock-status/', 
         AnnotationTrackingViewSet.as_view({'get': 'lock_status'}), 
         name='tracking-lock-status'),
]
