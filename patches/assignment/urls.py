"""
Assignment URL Configuration

These URLs should be included in the main Doccano urls.py:
    path('v1/projects/<int:project_id>/assignments/', include('assignment.urls')),
"""

from django.urls import path
from .views import AssignmentViewSet
from .completion_views import (
    CompletionMatrixViewSet,
    AnnotatorCompletionViewSet,
    ApproverCompletionViewSet
)
from .comprehensive_example_api import ComprehensiveExampleViewSet
from .example_filtering import ExampleLockingViewSet

urlpatterns = [
    # ===== Assignment URLs =====
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
    
    # ===== Completion Matrix URLs (Project Manager Dashboard) =====
    # Complete matrix (Project Managers only)
    path('completion-matrix/', 
         CompletionMatrixViewSet.as_view({'get': 'list'}), 
         name='completion-matrix-full'),
    
    # Annotator matrix
    path('completion-matrix/annotators/', 
         CompletionMatrixViewSet.as_view({'get': 'annotators'}), 
         name='completion-matrix-annotators'),
    
    # Approver matrix
    path('completion-matrix/approvers/', 
         CompletionMatrixViewSet.as_view({'get': 'approvers'}), 
         name='completion-matrix-approvers'),
    
    # My completion stats
    path('completion-matrix/my/', 
         CompletionMatrixViewSet.as_view({'get': 'my'}), 
         name='completion-matrix-my'),
    
    # Project summary
    path('completion-matrix/summary/', 
         CompletionMatrixViewSet.as_view({'get': 'summary'}), 
         name='completion-matrix-summary'),
    
    # Sync from assignments
    path('completion-matrix/sync/', 
         CompletionMatrixViewSet.as_view({'post': 'sync'}), 
         name='completion-matrix-sync'),
    
    # Export matrix
    path('completion-matrix/export/', 
         CompletionMatrixViewSet.as_view({'get': 'export'}), 
         name='completion-matrix-export'),
    
    # ===== Per-Example Completion Tracking =====
    # Annotator completion
    path('annotator-completion/<int:example_id>/', 
         AnnotatorCompletionViewSet.as_view({'get': 'retrieve'}), 
         name='annotator-completion-detail'),
    
    path('annotator-completion/<int:example_id>/complete/', 
         AnnotatorCompletionViewSet.as_view({'post': 'complete'}), 
         name='annotator-completion-complete'),
    
    path('annotator-completion/<int:example_id>/incomplete/', 
         AnnotatorCompletionViewSet.as_view({'post': 'incomplete'}), 
         name='annotator-completion-incomplete'),
    
    # Approver completion
    path('approver-completion/<int:example_id>/', 
         ApproverCompletionViewSet.as_view({'get': 'retrieve'}), 
         name='approver-completion-detail'),
    
    path('approver-completion/<int:example_id>/approve/', 
         ApproverCompletionViewSet.as_view({'post': 'approve'}), 
         name='approver-completion-approve'),
    
    path('approver-completion/<int:example_id>/reject/', 
         ApproverCompletionViewSet.as_view({'post': 'reject'}), 
         name='approver-completion-reject'),
    
    # ===== Comprehensive Example API (All data in one query) =====
    # Get examples with all completion metrics combined
    path('examples-comprehensive/', 
         ComprehensiveExampleViewSet.as_view({'get': 'list'}), 
         name='examples-comprehensive-list'),
    
    path('examples-comprehensive/<int:pk>/', 
         ComprehensiveExampleViewSet.as_view({'get': 'retrieve'}), 
         name='examples-comprehensive-detail'),
    
    path('examples-comprehensive/export-csv/', 
         ComprehensiveExampleViewSet.as_view({'get': 'export_csv'}), 
         name='examples-comprehensive-export'),
    
    # ===== Example Locking =====
    # Lock/unlock examples to prevent simultaneous editing
    path('examples/<int:example_id>/lock/', 
         ExampleLockingViewSet.as_view({'post': 'lock'}), 
         name='example-lock'),
    
    path('examples/<int:example_id>/unlock/', 
         ExampleLockingViewSet.as_view({'post': 'unlock'}), 
         name='example-unlock'),
    
    path('examples/<int:example_id>/lock-status/', 
         ExampleLockingViewSet.as_view({'get': 'lock_status'}), 
         name='example-lock-status'),
]

