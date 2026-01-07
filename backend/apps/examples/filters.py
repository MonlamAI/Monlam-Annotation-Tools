"""
Example filters including the critical AnnotationVisibilityFilter.
"""

from rest_framework.filters import BaseFilterBackend
from django.db.models import Q

from apps.projects.permissions import get_member
from apps.projects.models import MemberRole


class AnnotationVisibilityFilter(BaseFilterBackend):
    """
    CRITICAL FILTER: Controls which examples annotators can see.
    
    Rules:
    - Superusers and Admins see everything
    - Approvers, PMs see everything
    - Annotators only see:
      1. Pending examples (not yet annotated by anyone)
      2. Rejected examples that THEY annotated (for re-work)
    
    This prevents annotators from:
    - Seeing examples annotated by others
    - Seeing submitted or approved examples
    - Re-working rejected examples from other annotators
    """
    
    def filter_queryset(self, request, queryset, view):
        user = request.user
        project_id = view.kwargs.get('project_id')
        
        if not project_id:
            return queryset
        
        # Superusers see everything
        if user.is_superuser:
            return queryset
        
        # Get user's membership
        member = get_member(user, project_id)
        
        if not member:
            return queryset.none()
        
        # Approvers, PMs, and Admins see all examples
        if member.can_see_all:
            return queryset
        
        # Annotators: filtered visibility
        if member.role == MemberRole.ANNOTATOR:
            from apps.monlam_tracking.models import AnnotationTracking
            
            # Get example IDs that are pending (no tracking record)
            tracked_example_ids = AnnotationTracking.objects.filter(
                project_id=project_id
            ).values_list('example_id', flat=True)
            
            # Get example IDs that are rejected and annotated by this user
            rejected_by_user_ids = AnnotationTracking.objects.filter(
                project_id=project_id,
                annotated_by=user,
                status='rejected'
            ).values_list('example_id', flat=True)
            
            # Filter: examples with no tracking OR rejected by this user
            return queryset.filter(
                Q(~Q(id__in=tracked_example_ids)) |  # Pending (no tracking)
                Q(id__in=rejected_by_user_ids)  # Rejected by this user
            )
        
        # Default: show nothing
        return queryset.none()


class StatusFilter(BaseFilterBackend):
    """
    Filter examples by tracking status.
    Query param: ?status=pending,submitted,approved,rejected
    """
    
    def filter_queryset(self, request, queryset, view):
        status_param = request.query_params.get('status')
        
        if not status_param:
            return queryset
        
        statuses = [s.strip() for s in status_param.split(',')]
        
        from apps.monlam_tracking.models import AnnotationTracking
        
        project_id = view.kwargs.get('project_id')
        if not project_id:
            return queryset
        
        if 'pending' in statuses:
            # Include examples without tracking record
            tracked_ids = AnnotationTracking.objects.filter(
                project_id=project_id
            ).values_list('example_id', flat=True)
            
            other_statuses = [s for s in statuses if s != 'pending']
            
            if other_statuses:
                filtered_ids = AnnotationTracking.objects.filter(
                    project_id=project_id,
                    status__in=other_statuses
                ).values_list('example_id', flat=True)
                
                return queryset.filter(
                    Q(~Q(id__in=tracked_ids)) |  # Pending
                    Q(id__in=filtered_ids)  # Other statuses
                )
            else:
                return queryset.filter(~Q(id__in=tracked_ids))
        else:
            filtered_ids = AnnotationTracking.objects.filter(
                project_id=project_id,
                status__in=statuses
            ).values_list('example_id', flat=True)
            
            return queryset.filter(id__in=filtered_ids)


class AnnotatedByFilter(BaseFilterBackend):
    """
    Filter examples by annotator.
    Query param: ?annotated_by=user_id
    """
    
    def filter_queryset(self, request, queryset, view):
        annotated_by = request.query_params.get('annotated_by')
        
        if not annotated_by:
            return queryset
        
        from apps.monlam_tracking.models import AnnotationTracking
        
        project_id = view.kwargs.get('project_id')
        if not project_id:
            return queryset
        
        annotated_ids = AnnotationTracking.objects.filter(
            project_id=project_id,
            annotated_by_id=annotated_by
        ).values_list('example_id', flat=True)
        
        return queryset.filter(id__in=annotated_ids)

