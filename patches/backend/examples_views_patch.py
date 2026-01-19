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
    4. Annotators see:
       - All examples that are NOT completed (pending, rejected, or no tracking)
       - Hide completed examples (submitted/approved/reviewed)
    """
    
    def get_queryset(self):
        """
        Filter examples based on user role and tracking status.
        Simplified for single annotator per project - no need to check who annotated.
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
            
            # Check if user is project creator or has admin role (they see everything)
            role_name = member.role.name.lower() if member.role and member.role.name else ''
            is_project_admin = (
                project.created_by == user or
                'admin' in role_name or
                'manager' in role_name
            )
            
            if is_project_admin:
                return queryset
            
            # Check if user is approver (they also see everything for reviewing)
            is_approver = 'approver' in role_name
            if is_approver:
                return queryset
        except Exception as e:
            import sys
            print(f'[ExampleVisibilityMixin] Error checking membership: {e}', file=sys.stderr, flush=True)
            # If we can't check membership, be safe and return empty
            return queryset.none()
        
        # For annotators: Simple filtering - hide completed examples only
        # Since there's only one annotator per project, we don't need to check who annotated
        try:
            from assignment.simple_tracking import AnnotationTracking
            
            # Get all completed example IDs (submitted/approved/reviewed)
            completed_example_ids = set(
                AnnotationTracking.objects.filter(
                    project_id=project_id,
                    status__in=['submitted', 'approved', 'reviewed']
                ).values_list('example_id', flat=True)
            )
            
            # Return all examples in project EXCEPT completed ones
            return queryset.filter(project_id=project_id).exclude(id__in=completed_example_ids)
            
        except ImportError:
            # If tracking not available, return full queryset
            return queryset.filter(project_id=project_id)

