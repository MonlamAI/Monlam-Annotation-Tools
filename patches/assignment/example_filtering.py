"""
Example Filtering

Filters examples based on user role and assignment status.
This ensures annotators only see their own assigned examples,
and completed examples are hidden from annotators.
"""

from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta

from .models_separate import Assignment


class ExampleFilterMixin:
    """
    Mixin to filter examples based on user role and assignment.
    
    Apply this to Doccano's example viewsets to enforce
    assignment-based visibility.
    """
    
    def get_queryset(self):
        """
        Filter examples based on user role.
        
        Rules:
        - Admins: See all examples
        - Project Managers: See all examples in their projects
        - Approvers: See submitted/approved/rejected examples
        - Annotators: See only their assigned examples (not submitted/approved)
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user.is_authenticated:
            return queryset.none()
        
        # Admins see everything
        if user.is_superuser:
            return queryset
        
        # Get project from URL kwargs
        project_id = self.kwargs.get('project_id')
        if not project_id:
            return queryset
        
        from projects.models import Project
        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return queryset.none()
        
        # Check if user is project member
        if not project.members.filter(id=user.id).exists():
            return queryset.none()
        
        # Determine user's role
        member_role = project.members.through.objects.filter(
            project=project,
            user=user
        ).first()
        
        role_name = getattr(member_role, 'role', None) if member_role else None
        
        is_project_manager = (role_name == 'project_manager')
        is_approver = (role_name == 'approver' or is_project_manager)
        is_annotator = (role_name == 'annotator')
        
        # Project Manager sees everything
        if is_project_manager:
            return queryset
        
        # Get all assignments for this project
        assignments = Assignment.objects.filter(
            project=project,
            is_active=True
        )
        
        # Approver sees submitted, approved, rejected examples
        if is_approver:
            approver_assignments = assignments.filter(
                status__in=['submitted', 'approved', 'rejected']
            )
            example_ids = list(approver_assignments.values_list('example_id', flat=True))
            return queryset.filter(id__in=example_ids)
        
        # Annotator sees only their assignments (not submitted/approved)
        annotator_assignments = assignments.filter(
            assigned_to=user,
            status__in=['assigned', 'in_progress', 'rejected']
        )
        example_ids = list(annotator_assignments.values_list('example_id', flat=True))
        return queryset.filter(id__in=example_ids)


# NOTE: ExampleLockingViewSet removed - single annotator per project, no race conditions



