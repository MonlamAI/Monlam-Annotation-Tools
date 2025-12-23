"""
Assignment URL patterns.

Add these to /doccano/backend/examples/urls.py
"""

from django.urls import path

from .views_assignment import (
    AutoAssignView,
    BulkAssignmentView,
    AssignmentStatsView,
    ReviewQueueView,
    ReviewActionView,
    SubmitForReviewView,
)

# Add these patterns to urlpatterns in examples/urls.py:
assignment_urlpatterns = [
    # Assignment endpoints
    path(
        "projects/<int:project_id>/assignment/bulk/",
        BulkAssignmentView.as_view(),
        name="bulk-assignment"
    ),
    path(
        "projects/<int:project_id>/assignment/auto/",
        AutoAssignView.as_view(),
        name="auto-assignment"
    ),
    path(
        "projects/<int:project_id>/assignment/stats/",
        AssignmentStatsView.as_view(),
        name="assignment-stats"
    ),
    
    # Review endpoints
    path(
        "projects/<int:project_id>/review/queue/",
        ReviewQueueView.as_view(),
        name="review-queue"
    ),
    path(
        "projects/<int:project_id>/review/<int:example_id>/",
        ReviewActionView.as_view(),
        name="review-action"
    ),
    
    # Annotator submit
    path(
        "projects/<int:project_id>/examples/<int:example_id>/submit/",
        SubmitForReviewView.as_view(),
        name="submit-for-review"
    ),
]

