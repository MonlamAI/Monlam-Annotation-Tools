"""
Simple Example Filtering & Locking

Rules:
1. Unannotated examples: Visible to all annotators (first-come-first-serve)
2. Once annotated by someone: Hidden from other annotators
3. Submitted/Approved: Hidden from all annotators
4. Rejected: Visible only to original annotator (to fix)
5. Reviewers & Project Managers: See everything
6. Locking: Example locked when being edited
"""

from django.db.models import Q
from django.utils import timezone
from datetime import timedelta


class SimpleExampleFilterMixin:
    """
    Simple filtering based on annotation tracking
    No complex assignments - just first-come-first-serve
    """
    
    def get_queryset(self):
        """
        Filter examples based on tracking and user role
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
        
        # Check if user is project member
        if not project.members.filter(id=user.id).exists():
            return queryset.none()
        
        # Determine user's role (simplified - check if user can manage project)
        is_project_manager = (project.created_by == user or 
                            project.admins.filter(id=user.id).exists())
        
        # Check if user has approver/reviewer permissions
        # (In Doccano, check project role)
        from django.contrib.contenttypes.models import ContentType
        is_approver = is_project_manager  # Simplified - can be enhanced
        
        # Project Managers and Approvers see everything
        if is_project_manager or is_approver:
            return queryset
        
        # For annotators: Apply filtering
        from .simple_tracking import AnnotationTracking
        
        # Get all tracking records for this project
        tracking_records = AnnotationTracking.objects.filter(
            project=project
        ).select_related('annotated_by')
        
        # Build list of example IDs to show/hide
        show_ids = []
        hide_ids = []
        
        for tracking in tracking_records:
            if tracking.status in ['pending']:
                # Unannotated - show to everyone
                show_ids.append(tracking.example_id)
            
            elif tracking.status == 'rejected' and tracking.annotated_by == user:
                # Rejected by this user - show so they can fix it
                show_ids.append(tracking.example_id)
            
            elif tracking.annotated_by == user and tracking.status in ['submitted', 'approved']:
                # Annotated by this user but already submitted/approved - hide
                hide_ids.append(tracking.example_id)
            
            elif tracking.annotated_by != user:
                # Annotated by someone else - hide
                hide_ids.append(tracking.example_id)
        
        # Get all example IDs in this project
        all_example_ids = set(queryset.filter(project=project).values_list('id', flat=True))
        
        # Examples with no tracking record yet = unannotated = show to everyone
        tracked_ids = set(tracking_records.values_list('example_id', flat=True))
        untracked_ids = all_example_ids - tracked_ids
        
        # Final list: show untracked + explicitly shown - explicitly hidden
        final_ids = (set(show_ids) | untracked_ids) - set(hide_ids)
        
        return queryset.filter(id__in=final_ids)


class ExampleLockingViewSet:
    """
    Example locking functionality
    """
    
    @action(detail=True, methods=['post'])
    def lock(self, request, pk=None, project_id=None):
        """
        Lock an example for editing
        
        POST /v1/projects/{project_id}/examples/{example_id}/lock/
        """
        from .simple_tracking import AnnotationTracking
        
        try:
            tracking, created = AnnotationTracking.objects.get_or_create(
                project_id=project_id,
                example_id=pk,
                defaults={
                    'status': 'pending'
                }
            )
            
            # Check if already locked by someone else
            if hasattr(tracking, 'locked_by') and tracking.locked_by and tracking.locked_by != request.user:
                # Check if lock is expired (5 minutes)
                if hasattr(tracking, 'locked_at') and tracking.locked_at:
                    if timezone.now() - tracking.locked_at < timedelta(minutes=5):
                        return Response({
                            'locked': True,
                            'locked_by': tracking.locked_by.username,
                            'message': 'Example is being edited by another user'
                        }, status=400)
            
            # Lock it
            if hasattr(tracking, 'locked_by'):
                tracking.locked_by = request.user
                tracking.locked_at = timezone.now()
                tracking.save()
            
            return Response({
                'success': True,
                'locked_by': request.user.username
            })
        
        except Exception as e:
            return Response({'error': str(e)}, status=500)
    
    @action(detail=True, methods=['post'])
    def unlock(self, request, pk=None, project_id=None):
        """
        Unlock an example
        
        POST /v1/projects/{project_id}/examples/{example_id}/unlock/
        """
        from .simple_tracking import AnnotationTracking
        
        try:
            tracking = AnnotationTracking.objects.filter(
                project_id=project_id,
                example_id=pk
            ).first()
            
            if tracking and hasattr(tracking, 'locked_by'):
                # Only allow unlock if locked by this user or lock expired
                if tracking.locked_by == request.user or \
                   (tracking.locked_at and timezone.now() - tracking.locked_at > timedelta(minutes=5)):
                    tracking.locked_by = None
                    tracking.locked_at = None
                    tracking.save()
                    
                    return Response({'success': True})
            
            return Response({'success': True})  # Already unlocked
        
        except Exception as e:
            return Response({'error': str(e)}, status=500)

