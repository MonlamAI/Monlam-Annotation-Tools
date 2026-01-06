"""
Assignment Permissions

Custom permission classes for controlling access to examples
based on assignment status and user role.
"""

from rest_framework import permissions
from django.shortcuts import get_object_or_404
from .models_separate import Assignment


class CanAccessExample(permissions.BasePermission):
    """
    Permission class to control which users can access which examples.
    
    Rules:
    1. Annotator can only see examples assigned to them
    2. Annotator cannot see submitted/approved examples (unless rejected)
    3. Approver can see submitted/approved/rejected examples
    4. Project Manager can see all examples
    5. Admin can see all examples
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to access examples."""
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user can access specific example.
        
        Args:
            obj: The Example object
        """
        user = request.user
        project = obj.project
        
        # Admins can see everything
        if user.is_superuser:
            return True
        
        # Check if user is project member
        if not project.members.filter(id=user.id).exists():
            return False
        
        # Get user's role in the project (using the existing role check)
        member_role = project.members.through.objects.filter(
            project=project,
            user=user
        ).first()
        
        # Determine role
        is_project_manager = False
        is_approver = False
        is_annotator = False
        
        if member_role:
            role_name = getattr(member_role, 'role', None)
            if role_name:
                is_project_manager = (role_name == 'project_manager')
                is_approver = (role_name == 'approver' or is_project_manager)
                is_annotator = (role_name == 'annotator')
        
        # Project Manager sees everything
        if is_project_manager:
            return True
        
        # Check if example has assignment
        try:
            assignment = Assignment.objects.get(
                project=project,
                example=obj,
                is_active=True
            )
        except Assignment.DoesNotExist:
            # No assignment - only PMs and admins can see
            return is_project_manager or user.is_superuser
        
        # Approver rules
        if is_approver:
            # Approvers can see submitted, approved, rejected examples
            return assignment.status in ['submitted', 'approved', 'rejected']
        
        # Annotator rules
        if is_annotator or (not is_approver and not is_project_manager):
            # Must be assigned to this user
            if assignment.assigned_to != user:
                return False
            
            # Cannot see submitted or approved examples
            if assignment.status in ['submitted', 'approved']:
                return False
            
            # Can see assigned, in_progress, rejected
            return assignment.status in ['assigned', 'in_progress', 'rejected']
        
        return False


class CanLockExample(permissions.BasePermission):
    """
    Permission to lock/unlock examples.
    
    An example can be locked when an annotator starts working on it.
    Other annotators cannot access locked examples.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user can lock/access this example."""
        user = request.user
        
        # Admins can always access
        if user.is_superuser:
            return True
        
        # Check assignment
        try:
            assignment = Assignment.objects.get(
                project=obj.project,
                example=obj,
                is_active=True
            )
        except Assignment.DoesNotExist:
            return False
        
        # Check if locked by someone else
        if assignment.locked_by and assignment.locked_by != user:
            # Check if lock is expired (10 minutes default)
            from django.utils import timezone
            from datetime import timedelta
            
            if assignment.locked_at:
                lock_duration = timezone.now() - assignment.locked_at
                if lock_duration < timedelta(minutes=10):
                    # Still locked by someone else
                    return False
        
        # Either not locked, locked by this user, or lock expired
        return True

