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


class ExampleLockingViewSet(viewsets.ViewSet):
    """
    ViewSet for locking/unlocking examples.
    
    Endpoints:
    - POST /lock/ - Lock an example
    - POST /unlock/ - Unlock an example
    - GET /status/ - Check lock status
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def lock(self, request, project_id, example_id):
        """
        Lock an example for editing.
        
        Prevents other annotators from accessing this example
        while the current user is working on it.
        """
        from examples.models import Example
        
        try:
            example = Example.objects.get(pk=example_id, project_id=project_id)
        except Example.DoesNotExist:
            return Response(
                {'error': 'Example not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get assignment
        try:
            assignment = Assignment.objects.get(
                project_id=project_id,
                example=example,
                is_active=True
            )
        except Assignment.DoesNotExist:
            return Response(
                {'error': 'No assignment found for this example'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user is assigned to this example
        if assignment.assigned_to != request.user:
            # Check if user is approver/PM
            from projects.models import Project
            project = Project.objects.get(pk=project_id)
            member_role = project.members.through.objects.filter(
                project=project,
                user=request.user
            ).first()
            
            role_name = getattr(member_role, 'role', None) if member_role else None
            is_approver_or_pm = role_name in ['approver', 'project_manager']
            
            if not is_approver_or_pm and not request.user.is_superuser:
                return Response(
                    {'error': 'You are not assigned to this example'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Check if already locked by someone else
        if assignment.locked_by and assignment.locked_by != request.user:
            # Check if lock is expired (5 minutes - matches tracking API)
            if assignment.locked_at:
                lock_duration = timezone.now() - assignment.locked_at
                if lock_duration < timedelta(minutes=5):
                    return Response(
                        {
                            'error': 'Example is locked by another user',
                            'locked_by': assignment.locked_by.username,
                            'locked_at': assignment.locked_at.isoformat(),
                        },
                        status=status.HTTP_423_LOCKED
                    )
        
        # Lock the example
        assignment.locked_by = request.user
        assignment.locked_at = timezone.now()
        assignment.save(update_fields=['locked_by', 'locked_at'])
        
        return Response({
            'message': 'Example locked successfully',
            'locked_by': request.user.username,
            'locked_at': assignment.locked_at.isoformat(),
        })
    
    @action(detail=True, methods=['post'])
    def unlock(self, request, project_id, example_id):
        """
        Unlock an example.
        
        Releases the lock so other users can access it.
        """
        from examples.models import Example
        
        try:
            example = Example.objects.get(pk=example_id, project_id=project_id)
        except Example.DoesNotExist:
            return Response(
                {'error': 'Example not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get assignment
        try:
            assignment = Assignment.objects.get(
                project_id=project_id,
                example=example,
                is_active=True
            )
        except Assignment.DoesNotExist:
            return Response(
                {'error': 'No assignment found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Only the user who locked it can unlock (or admin)
        if assignment.locked_by != request.user and not request.user.is_superuser:
            return Response(
                {'error': 'You did not lock this example'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Unlock
        assignment.locked_by = None
        assignment.locked_at = None
        assignment.save(update_fields=['locked_by', 'locked_at'])
        
        return Response({
            'message': 'Example unlocked successfully'
        })
    
    @action(detail=True, methods=['get'])
    def lock_status(self, request, project_id, example_id):
        """
        Check if an example is locked.
        
        Returns lock status and who locked it.
        """
        from examples.models import Example
        
        try:
            example = Example.objects.get(pk=example_id, project_id=project_id)
        except Example.DoesNotExist:
            return Response(
                {'error': 'Example not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get assignment
        try:
            assignment = Assignment.objects.get(
                project_id=project_id,
                example=example,
                is_active=True
            )
        except Assignment.DoesNotExist:
            return Response({
                'locked': False,
                'message': 'No assignment found'
            })
        
        if assignment.locked_by:
            # Check if lock is expired (5 minutes - matches tracking API)
            lock_duration = timezone.now() - assignment.locked_at
            if lock_duration >= timedelta(minutes=5):
                # Lock expired
                assignment.locked_by = None
                assignment.locked_at = None
                assignment.save(update_fields=['locked_by', 'locked_at'])
                
                return Response({
                    'locked': False,
                    'message': 'Lock expired'
                })
            
            return Response({
                'locked': True,
                'locked_by': assignment.locked_by.username,
                'locked_at': assignment.locked_at.isoformat(),
                'is_locked_by_me': (assignment.locked_by == request.user),
            })
        
        return Response({
            'locked': False
        })



