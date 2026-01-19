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
        
        # Annotator rules - check AnnotationTracking first (primary source of truth)
        try:
            from .simple_tracking import AnnotationTracking
            tracking = AnnotationTracking.objects.filter(
                project=project,
                example=obj
            ).first()
            
            if tracking:
                # CRITICAL: If annotated_by is set and it's NOT the current user, DENY access
                if tracking.annotated_by and tracking.annotated_by != user:
                    return False
                
                # If annotated_by IS the current user, check status
                if tracking.annotated_by == user:
                    # Can access if rejected (needs fixing)
                    if tracking.status == 'rejected':
                        return True
                    # Cannot access if submitted or approved (already done)
                    if tracking.status in ['submitted', 'approved']:
                        return False
                    # Can access if pending (still working on it)
                    if tracking.status == 'pending':
                        return True
            
            # No tracking record = unannotated = can access
            # Also check assignment as fallback
            try:
                assignment = Assignment.objects.get(
                    project=project,
                    example=obj,
                    is_active=True
                )
                # Must be assigned to this user
                if assignment.assigned_to != user:
                    return False
                # Cannot see submitted or approved examples
                if assignment.status in ['submitted', 'approved']:
                    return False
                # Can see assigned, in_progress, rejected
                return assignment.status in ['assigned', 'in_progress', 'rejected']
            except Assignment.DoesNotExist:
                # No assignment and no tracking = unannotated = can access
                return True
                
        except Exception as e:
            print(f'[Monlam Permissions] Error checking access permission: {e}')
            # On error, be safe and deny
            return False


class CanEditExample(permissions.BasePermission):
    """
    Permission to edit/annotate examples.
    
    Rules:
    1. Privileged users (admins, managers, approvers) can always edit
    2. Annotators can ONLY edit examples they annotated themselves
    3. Annotators CANNOT edit examples annotated/submitted by other annotators
    4. Annotators CAN edit their own rejected examples (to fix them)
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user can edit this example."""
        user = request.user
        project = obj.project
        
        # Get user's role
        role_name, is_privileged = get_user_role(user, project.id)
        
        # Privileged users can always edit (they're reviewing/approving)
        if is_privileged:
            return True
        
        # Check AnnotationTracking to see who annotated this example
        try:
            from .simple_tracking import AnnotationTracking
            tracking = AnnotationTracking.objects.filter(
                project=project,
                example=obj
            ).first()
            
            if tracking:
                # If annotated_by is set and it's NOT the current user, deny edit
                if tracking.annotated_by and tracking.annotated_by != user:
                    return False
                
                # If annotated_by IS the current user, check status
                if tracking.annotated_by == user:
                    # Can edit if rejected (needs fixing)
                    if tracking.status == 'rejected':
                        return True
                    # Cannot edit if submitted or approved (already done)
                    if tracking.status in ['submitted', 'approved']:
                        return False
                    # Can edit if pending (still working on it)
                    if tracking.status == 'pending':
                        return True
            
            # No tracking record = unannotated = can edit
            return True
            
        except Exception as e:
            print(f'[Monlam Permissions] Error checking edit permission: {e}')
            # On error, be safe and deny
            return False


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
        
        # Check AnnotationTracking for locking
        try:
            from .simple_tracking import AnnotationTracking
            tracking = AnnotationTracking.objects.filter(
                project=project,
                example=obj
            ).first()
            
            if tracking:
                # Check if locked by someone else
                if tracking.locked_by and tracking.locked_by != user:
                    # Check if lock is expired (5 minutes default)
                    from django.utils import timezone
                    from datetime import timedelta
                    
                    if tracking.locked_at:
                        lock_expiry = tracking.locked_at + timedelta(minutes=5)
                        if timezone.now() < lock_expiry:
                            # Still locked by someone else
                            return False
                        else:
                            # Lock expired, clear it
                            tracking.locked_by = None
                            tracking.locked_at = None
                            tracking.save(update_fields=['locked_by', 'locked_at'])
            
            # Either not locked, locked by this user, or lock expired
            return True
            
        except Exception as e:
            print(f'[Monlam Permissions] Error checking lock permission: {e}')
            # On error, be safe and deny
            return False



