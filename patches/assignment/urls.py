"""
Assignment URL Configuration

These URLs should be included in the main Doccano urls.py:
    path('v1/projects/<int:project_id>/assignments/', include('assignment.urls')),
"""

from django.urls import path
from .views import AssignmentViewSet

urlpatterns = [
    # List all assignments
    path('', AssignmentViewSet.as_view({'get': 'list'}), name='assignment-list'),
    
    # My assignments
    path('my/', AssignmentViewSet.as_view({'get': 'my'}), name='assignment-my'),
    
    # Bulk assign
    path('bulk/', AssignmentViewSet.as_view({'post': 'bulk'}), name='assignment-bulk'),
    
    # Statistics
    path('stats/', AssignmentViewSet.as_view({'get': 'stats'}), name='assignment-stats'),
    
    # Unassigned count
    path('unassigned/', AssignmentViewSet.as_view({'get': 'unassigned'}), name='assignment-unassigned'),
    
    # Actions on specific assignment
    path('<int:pk>/start/', AssignmentViewSet.as_view({'post': 'start'}), name='assignment-start'),
    path('<int:pk>/submit/', AssignmentViewSet.as_view({'post': 'submit'}), name='assignment-submit'),
    path('<int:pk>/approve/', AssignmentViewSet.as_view({'post': 'approve'}), name='assignment-approve'),
    path('<int:pk>/reject/', AssignmentViewSet.as_view({'post': 'reject'}), name='assignment-reject'),
]

