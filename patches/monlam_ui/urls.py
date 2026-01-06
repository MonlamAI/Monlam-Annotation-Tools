"""
Monlam UI URL Configuration

URL patterns for the enhanced UI views.
These integrate with Doccano's existing URL structure.
"""

from django.urls import path
from . import views

app_name = 'monlam_ui'

urlpatterns = [
    # Project Landing Page (Main entry point)
    path(
        '<int:project_id>/',
        views.project_landing,
        name='project-landing'
    ),
    
    # Completion Dashboard (Project Manager view)
    path(
        '<int:project_id>/completion/',
        views.completion_dashboard,
        name='completion-dashboard'
    ),
    
    # Enhanced Dataset View with Assignment Status
    path(
        '<int:project_id>/dataset-enhanced/',
        views.enhanced_dataset,
        name='enhanced-dataset'
    ),
    
    # Annotation with Approval Interface
    path(
        '<int:project_id>/annotate/<int:example_id>/',
        views.annotation_with_approval,
        name='annotation-with-approval'
    ),
    
    # API Endpoints
    path(
        '<int:project_id>/api/dataset-assignments/',
        views.api_dataset_assignments,
        name='api-dataset-assignments'
    ),
    
    path(
        '<int:project_id>/api/completion-stats/',
        views.api_completion_stats,
        name='api-completion-stats'
    ),
]

