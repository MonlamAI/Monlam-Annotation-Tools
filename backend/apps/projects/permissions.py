"""
Custom permissions for project access control.
"""

from rest_framework import permissions
from .models import Member, MemberRole


def get_user_role(user, project_id):
    """
    Get the user's role in a project.
    Returns the role string or None if not a member.
    """
    if user.is_superuser:
        return MemberRole.PROJECT_ADMIN
    
    try:
        member = Member.objects.get(project_id=project_id, user=user)
        return member.role
    except Member.DoesNotExist:
        return None


def get_member(user, project_id):
    """
    Get the Member object for a user in a project.
    Returns None if not a member.
    """
    if user.is_superuser:
        # Create a virtual member object for superusers
        from .models import Project
        try:
            project = Project.objects.get(id=project_id)
            return type('VirtualMember', (), {
                'role': MemberRole.PROJECT_ADMIN,
                'can_annotate': True,
                'can_review': True,
                'can_see_all': True,
                'can_manage': True,
                'is_admin': True,
                'project': project,
                'user': user,
            })()
        except Project.DoesNotExist:
            return None
    
    try:
        return Member.objects.get(project_id=project_id, user=user)
    except Member.DoesNotExist:
        return None


class IsProjectMember(permissions.BasePermission):
    """
    Allows access only to project members.
    """
    
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        
        project_id = view.kwargs.get('project_id')
        if not project_id:
            return True  # Let view handle project-level access
        
        return Member.objects.filter(
            project_id=project_id,
            user=request.user
        ).exists()


class IsProjectAdmin(permissions.BasePermission):
    """
    Allows access only to project admins.
    """
    
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        
        project_id = view.kwargs.get('project_id')
        if not project_id:
            return False
        
        return Member.objects.filter(
            project_id=project_id,
            user=request.user,
            role=MemberRole.PROJECT_ADMIN
        ).exists()


class IsReviewer(permissions.BasePermission):
    """
    Allows access only to reviewers (Approver, PM, or Admin).
    """
    
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        
        project_id = view.kwargs.get('project_id')
        if not project_id:
            return False
        
        return Member.objects.filter(
            project_id=project_id,
            user=request.user,
            role__in=[
                MemberRole.APPROVER,
                MemberRole.PROJECT_MANAGER,
                MemberRole.PROJECT_ADMIN
            ]
        ).exists()


class CanManageProject(permissions.BasePermission):
    """
    Allows access to PMs and Admins for project management.
    """
    
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        
        project_id = view.kwargs.get('project_id')
        if not project_id:
            return False
        
        return Member.objects.filter(
            project_id=project_id,
            user=request.user,
            role__in=[
                MemberRole.PROJECT_MANAGER,
                MemberRole.PROJECT_ADMIN
            ]
        ).exists()

