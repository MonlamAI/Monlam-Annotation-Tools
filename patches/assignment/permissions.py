"""
Assignment Permissions

Custom permission classes for controlling access to examples
based on assignment status and user role.

Role Hierarchy:
- Superusers: Full access to everything
- Project Admins: Full access within their projects
- Project Managers: Full access within their projects (can approve/reject)
- Annotation Approvers: Can approve/reject, see all submitted examples
- Annotators: Can only see examples assigned to them
"""

from rest_framework import permissions
from django.shortcuts import get_object_or_404
from .models_separate import Assignment


def get_user_role(user, project_id):
    """
    Get user's role in a project.
    
    Returns tuple: (role_name, is_privileged)
    - is_privileged: True if user can approve/reject and see all examples
    """
    if user.is_superuser:
        return ('superuser', True)
    
    try:
        from projects.models import Member
        member = Member.objects.filter(user=user, project_id=project_id).first()
        if not member or not member.role:
            return (None, False)
        
        role_name = member.role.name.lower() if member.role.name else ''
        
        # Check for privileged roles
        is_privileged = any(r in role_name for r in ['admin', 'manager', 'approver'])
        
        return (role_name, is_privileged)
    except Exception as e:
        print(f'[Monlam Permissions] Role check error: {e}')
        return (None, False)


class CanAccessExample(permissions.BasePermission):
    """
    Permission class to control which users can access which examples.
    
    Rules:
    1. Annotators can only see examples assigned to them
    2. Annotators cannot see submitted/approved examples (unless rejected)
    3. Annotation Approvers can see submitted/approved/rejected examples
    4. Project Managers can see all examples + approve/reject
    5. Project Admins can see all examples + full access
    6. Superusers can see all examples + full access
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
        
        # Get user's role
        role_name, is_privileged = get_user_role(user, project.id)
        
        # Privileged users (admins, managers, approvers) can see everything
        if is_privileged:
            return True
        
        # Annotators need specific checks
        is_annotator = role_name and 'annotator' in role_name
        
        # If not annotator and not privileged, deny
        if not is_annotator:
            return False
        
        # Annotator rules - check assignment
        try:
            assignment = Assignment.objects.get(
                project=project,
                example=obj,
                is_active=True
            )
        except Assignment.DoesNotExist:
            # No assignment - annotators cannot see unassigned examples
            return False
        
        # Must be assigned to this user
        if assignment.assigned_to != user:
            return False
        
        # Cannot see submitted or approved examples (unless rejected)
        if assignment.status in ['submitted', 'approved']:
            return False
        
        # Can see assigned, in_progress, rejected
        return assignment.status in ['assigned', 'in_progress', 'rejected']


class CanLockExample(permissions.BasePermission):
    """
    Permission to lock/unlock examples.
    
    An example can be locked when an annotator starts working on it.
    Other annotators cannot access locked examples.
    Privileged users (Admins, Managers, Approvers) can view locked examples.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user can lock/access this example."""
        user = request.user
        project = obj.project
        
        # Get user's role
        role_name, is_privileged = get_user_role(user, project.id)
        
        # Privileged users can always access (they're reviewing, not editing)
        if is_privileged:
            return True
        
        # Check assignment
        try:
            assignment = Assignment.objects.get(
                project=project,
                example=obj,
                is_active=True
            )
        except Assignment.DoesNotExist:
            return False
        
        # Check if locked by someone else
        if assignment.locked_by and assignment.locked_by != user:
            # Check if lock is expired (5 minutes default)
            from django.utils import timezone
            from datetime import timedelta
            
            if assignment.locked_at:
                lock_duration = timezone.now() - assignment.locked_at
                if lock_duration < timedelta(minutes=5):
                    # Still locked by someone else
                    return False
        
        # Either not locked, locked by this user, or lock expired
        return True



