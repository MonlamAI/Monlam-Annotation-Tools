"""
Patch for Doccano's Examples Views
Adds visibility filtering so annotators only see their own examples + unannotated ones
"""

from django.db.models import Q
from rest_framework import viewsets, status as http_status
from rest_framework.decorators import action
from rest_framework.response import Response


class ExampleVisibilityMixin:
    """
    Mixin to filter examples based on annotation tracking
    
    Rules (single annotator per project):
    1. Admins see everything
    2. Project Managers see everything
    3. Approvers/Reviewers see everything
    4. Annotators see everything (no filtering needed - single annotator per project)
    """
    
    def get_queryset(self):
        """
        Filter examples based on user role.
        For dataset table: All project members see all examples (no filtering for annotators).
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user.is_authenticated:
            return queryset.none()
        
        # Admins see everything
        if user.is_superuser:
            return queryset
        
        # Get project from URL
        project_id = self.kwargs.get('project_id')
        if not project_id:
            return queryset
        
        from projects.models import Project
        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return queryset.none()
        
        # Check if user is project member using Doccano's Member model
        from projects.models import Member
        try:
            member = Member.objects.filter(project=project, user=user).first()
            if not member:
                # User is not a project member
                return queryset.none()
        except Exception as e:
            import sys
            print(f'[ExampleVisibilityMixin] Error checking membership: {e}', file=sys.stderr, flush=True)
            # If we can't check membership, be safe and return empty
            return queryset.none()
        
        # All project members (including annotators) see all examples in the dataset table
        # Since there's only one annotator per project, no filtering is needed
        return queryset.filter(project_id=project_id)

