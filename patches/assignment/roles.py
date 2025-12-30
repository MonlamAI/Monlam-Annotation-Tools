"""
Project Manager Role and Permissions

This module defines a new "Project Manager" role that extends
the annotation approver role with additional permissions to view
the complete completion matrix for all annotators and approvers.
"""

from django.contrib.auth import get_user_model
from rest_framework import permissions

User = get_user_model()

# Role constants
ROLE_PROJECT_ADMIN = 'project_admin'
ROLE_ANNOTATOR = 'annotator'
ROLE_ANNOTATION_APPROVER = 'annotation_approver'
ROLE_PROJECT_MANAGER = 'project_manager'  # New role

# Role hierarchy (higher number = more permissions)
ROLE_HIERARCHY = {
    ROLE_ANNOTATOR: 1,
    ROLE_ANNOTATION_APPROVER: 2,
    ROLE_PROJECT_MANAGER: 3,
    ROLE_PROJECT_ADMIN: 4,
}


class ProjectManagerMixin:
    """
    Mixin to check if a user is a Project Manager or higher.
    """
    
    @staticmethod
    def is_project_manager(user, project):
        """
        Check if user has Project Manager role or higher in the project.
        
        Args:
            user: User instance
            project: Project instance
            
        Returns:
            bool: True if user is project manager or admin
        """
        try:
            # Check if user is in project members
            member = project.members.get(user=user)
            role = member.role
            
            # Project Manager or Project Admin can access
            return role in [ROLE_PROJECT_MANAGER, ROLE_PROJECT_ADMIN]
        except:
            return False
    
    @staticmethod
    def is_approver_or_higher(user, project):
        """
        Check if user has Approver role or higher.
        
        Args:
            user: User instance
            project: Project instance
            
        Returns:
            bool: True if user is approver, manager, or admin
        """
        try:
            member = project.members.get(user=user)
            role = member.role
            
            return role in [
                ROLE_ANNOTATION_APPROVER,
                ROLE_PROJECT_MANAGER,
                ROLE_PROJECT_ADMIN
            ]
        except:
            return False
    
    @staticmethod
    def get_user_role(user, project):
        """
        Get the user's role in the project.
        
        Args:
            user: User instance
            project: Project instance
            
        Returns:
            str: Role name or None
        """
        try:
            member = project.members.get(user=user)
            return member.role
        except:
            return None
    
    @staticmethod
    def has_role_permission(user_role, required_role):
        """
        Check if user_role has permission of required_role.
        
        Args:
            user_role: User's role string
            required_role: Required role string
            
        Returns:
            bool: True if user has sufficient permissions
        """
        user_level = ROLE_HIERARCHY.get(user_role, 0)
        required_level = ROLE_HIERARCHY.get(required_role, 0)
        
        return user_level >= required_level


class IsProjectManager(permissions.BasePermission):
    """
    Permission class to check if user is Project Manager or Admin.
    Use this for views that should only be accessible to managers.
    """
    
    message = 'You must be a Project Manager or Admin to access this.'
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user is project manager for this project."""
        # obj can be a Project, Assignment, or any model with a project FK
        project = obj if hasattr(obj, 'members') else obj.project
        return ProjectManagerMixin.is_project_manager(request.user, project)


class IsApproverOrHigher(permissions.BasePermission):
    """
    Permission class for approver, manager, or admin.
    """
    
    message = 'You must be an Approver, Manager, or Admin to access this.'
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user has approver role or higher."""
        project = obj if hasattr(obj, 'members') else obj.project
        return ProjectManagerMixin.is_approver_or_higher(request.user, project)


class CanViewCompletionMatrix(permissions.BasePermission):
    """
    Permission to view completion matrix.
    Only Project Managers and Admins can see the full matrix.
    Approvers can see their own approval stats.
    Annotators can see their own completion stats.
    """
    
    message = 'You do not have permission to view this completion data.'
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check viewing permissions based on scope."""
        project = obj if hasattr(obj, 'members') else obj.project
        user = request.user
        
        # Project Manager and Admin can see everything
        if ProjectManagerMixin.is_project_manager(user, project):
            return True
        
        # Approvers can see approval matrix
        if ProjectManagerMixin.is_approver_or_higher(user, project):
            # Check if requesting own data only
            requested_user_id = view.kwargs.get('user_id')
            if requested_user_id:
                return int(requested_user_id) == user.id
            return True
        
        # Annotators can only see their own completion
        requested_user_id = view.kwargs.get('user_id')
        return requested_user_id and int(requested_user_id) == user.id


def get_role_capabilities(role):
    """
    Get the capabilities/permissions for each role.
    
    Returns:
        dict: Capabilities for the role
    """
    capabilities = {
        ROLE_ANNOTATOR: {
            'can_annotate': True,
            'can_view_own_assignments': True,
            'can_view_own_completion': True,
            'can_view_full_matrix': False,
            'can_approve': False,
            'can_assign_tasks': False,
            'can_manage_project': False,
        },
        ROLE_ANNOTATION_APPROVER: {
            'can_annotate': True,
            'can_view_own_assignments': True,
            'can_view_own_completion': True,
            'can_view_full_matrix': False,
            'can_approve': True,
            'can_view_approval_queue': True,
            'can_assign_tasks': False,
            'can_manage_project': False,
        },
        ROLE_PROJECT_MANAGER: {
            'can_annotate': True,
            'can_view_own_assignments': True,
            'can_view_own_completion': True,
            'can_view_full_matrix': True,  # Key difference
            'can_approve': True,
            'can_view_approval_queue': True,
            'can_view_all_approvers': True,  # Can see all approvers' work
            'can_assign_tasks': False,
            'can_manage_project': False,
        },
        ROLE_PROJECT_ADMIN: {
            'can_annotate': True,
            'can_view_own_assignments': True,
            'can_view_own_completion': True,
            'can_view_full_matrix': True,
            'can_approve': True,
            'can_view_approval_queue': True,
            'can_view_all_approvers': True,
            'can_assign_tasks': True,
            'can_manage_project': True,
            'can_delete_project': True,
        },
    }
    
    return capabilities.get(role, {})


def get_user_capabilities(user, project):
    """
    Get capabilities for a specific user in a project.
    
    Args:
        user: User instance
        project: Project instance
        
    Returns:
        dict: User's capabilities in the project
    """
    role = ProjectManagerMixin.get_user_role(user, project)
    if not role:
        return {}
    
    return get_role_capabilities(role)

