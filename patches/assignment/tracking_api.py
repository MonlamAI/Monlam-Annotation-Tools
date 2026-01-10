"""
API Endpoints for Annotation Tracking

Provides:
- Auto-tracking when annotations are submitted
- Approve/Reject endpoints for reviewers
- Status tracking

Permission Hierarchy:
- Annotators: Can only mark_submitted and lock/unlock their own examples
- Annotation Approvers: Can approve/reject annotations
- Project Managers: Can approve/reject annotations + view analytics
- Project Admins: Full access
- Superusers: Full access
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
from .simple_tracking import AnnotationTracking


def has_approve_permission(user, project_id):
    """
    Check if user has permission to approve/reject annotations.
    
    Allowed roles:
    - Superusers (always)
    - Project Admins
    - Annotation Approvers
    - Project Managers
    """
    if user.is_superuser:
        return True
    
    try:
        from projects.models import Member
        member = Member.objects.filter(user=user, project_id=project_id).first()
        if not member or not member.role:
            return False
        
        role_name = member.role.name.lower() if member.role.name else ''
        
        # These roles can approve/reject
        if any(r in role_name for r in ['admin', 'approver', 'manager']):
            return True
        
        return False
    except Exception as e:
        print(f'[Monlam] Permission check error: {e}')
        return False


class AnnotationTrackingViewSet(viewsets.ViewSet):
    """
    API for annotation tracking
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'], url_path='mark-submitted')
    def mark_submitted(self, request, project_id=None):
        """
        Mark an example as submitted (auto-called when annotation is saved)
        
        POST /v1/projects/{project_id}/tracking/mark-submitted/
        {
            "example_id": 123
        }
        """
        example_id = request.data.get('example_id')
        if not example_id:
            return Response(
                {'error': 'example_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                tracking, created = AnnotationTracking.objects.get_or_create(
                    project_id=project_id,
                    example_id=example_id,
                    defaults={
                        'annotated_by': request.user,
                        'annotated_at': timezone.now(),
                        'status': 'submitted'
                    }
                )
                
                # If already exists and not annotated yet, update it
                if not created and not tracking.annotated_by:
                    tracking.annotated_by = request.user
                    tracking.annotated_at = timezone.now()
                    tracking.status = 'submitted'
                    
                    # Calculate time spent if we have started_at
                    if tracking.started_at:
                        time_diff = timezone.now() - tracking.started_at
                        tracking.time_spent_seconds = int(time_diff.total_seconds())
                    
                    tracking.save()
                
                # Calculate time spent for new records too
                time_spent = None
                if tracking.started_at and tracking.annotated_at:
                    time_diff = tracking.annotated_at - tracking.started_at
                    time_spent = int(time_diff.total_seconds())
                
                return Response({
                    'success': True,
                    'status': tracking.status,
                    'annotated_by': tracking.annotated_by.username if tracking.annotated_by else None,
                    'annotated_at': tracking.annotated_at,
                    'time_spent_seconds': time_spent
                })
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, project_id=None, pk=None):
        """
        Approve an example
        
        POST /v1/projects/{project_id}/tracking/{example_id}/approve/
        {
            "review_notes": "Looks good!"
        }
        
        Requires: project_admin, annotation_approver, or project_manager role
        """
        # Check permission
        if not has_approve_permission(request.user, project_id):
            return Response(
                {'error': 'You do not have permission to approve annotations. '
                         'Only Approvers, Project Managers, and Admins can approve.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            with transaction.atomic():
                tracking, created = AnnotationTracking.objects.get_or_create(
                    project_id=project_id,
                    example_id=pk,
                    defaults={
                        'status': 'approved',
                        'reviewed_by': request.user,
                        'reviewed_at': timezone.now(),
                        'review_notes': request.data.get('review_notes', '')
                    }
                )
                
                if not created:
                    tracking.status = 'approved'
                    tracking.reviewed_by = request.user
                    tracking.reviewed_at = timezone.now()
                    tracking.review_notes = request.data.get('review_notes', '')
                    tracking.save()
                
                return Response({
                    'success': True,
                    'status': 'approved',
                    'reviewed_by': tracking.reviewed_by.username,
                    'reviewed_at': tracking.reviewed_at
                })
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, project_id=None, pk=None):
        """
        Reject an example
        
        POST /v1/projects/{project_id}/tracking/{example_id}/reject/
        {
            "review_notes": "Needs correction (optional)"
        }
        
        Requires: project_admin, annotation_approver, or project_manager role
        """
        # Check permission
        if not has_approve_permission(request.user, project_id):
            return Response(
                {'error': 'You do not have permission to reject annotations. '
                         'Only Approvers, Project Managers, and Admins can reject.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        review_notes = request.data.get('review_notes', '')
        # Notes are now optional for rejection
        
        try:
            with transaction.atomic():
                tracking, created = AnnotationTracking.objects.get_or_create(
                    project_id=project_id,
                    example_id=pk,
                    defaults={
                        'status': 'rejected',
                        'reviewed_by': request.user,
                        'reviewed_at': timezone.now(),
                        'review_notes': review_notes
                    }
                )
                
                if not created:
                    tracking.status = 'rejected'
                    tracking.reviewed_by = request.user
                    tracking.reviewed_at = timezone.now()
                    tracking.review_notes = review_notes
                    tracking.save()
                
                return Response({
                    'success': True,
                    'status': 'rejected',
                    'reviewed_by': tracking.reviewed_by.username,
                    'reviewed_at': tracking.reviewed_at,
                    'review_notes': review_notes
                })
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='status')
    def get_status(self, request, project_id=None, pk=None):
        """
        Get tracking status for an example
        Also checks ExampleState for Doccano's native confirmation
        
        GET /v1/projects/{project_id}/tracking/{example_id}/status/
        
        Returns:
        - is_confirmed: True if marked complete via Doccano checkmark
        - confirmed_by: Username who confirmed (if any)
        - status: 'pending', 'submitted', 'approved', 'rejected' (from our tracking)
        - All other tracking fields
        """
        try:
            from datetime import timedelta
            
            # Check Doccano's native ExampleState (confirmation via checkmark)
            is_confirmed = False
            confirmed_by = None
            try:
                from examples.models import ExampleState
                state = ExampleState.objects.filter(example_id=pk).select_related('confirmed_by').first()
                if state and state.confirmed_by:
                    is_confirmed = True
                    confirmed_by = state.confirmed_by.username
            except Exception:
                pass  # ExampleState may not exist
            
            # Get our custom tracking record
            tracking = AnnotationTracking.objects.filter(
                project_id=project_id,
                example_id=pk
            ).select_related('annotated_by', 'reviewed_by', 'locked_by').first()
            
            if not tracking:
                return Response({
                    'status': 'submitted' if is_confirmed else 'pending',  # If confirmed but no tracking, treat as submitted
                    'is_confirmed': is_confirmed,
                    'confirmed_by': confirmed_by,
                    'annotated_by': confirmed_by,  # Use confirmed_by as annotator if no tracking
                    'reviewed_by': None,
                    'locked_by': None,
                    'is_locked': False
                })
            
            # Check if lock is still valid (5 minute expiry)
            is_locked = False
            locked_by_username = None
            if tracking.locked_by and tracking.locked_at:
                lock_expiry = tracking.locked_at + timedelta(minutes=5)
                if timezone.now() < lock_expiry:
                    is_locked = True
                    locked_by_username = tracking.locked_by.username
                else:
                    # Lock expired, clear it
                    tracking.locked_by = None
                    tracking.locked_at = None
                    tracking.save(update_fields=['locked_by', 'locked_at'])
            
            # Override status if confirmed but tracking says pending
            effective_status = tracking.status
            if is_confirmed and tracking.status == 'pending':
                effective_status = 'submitted'
            
            return Response({
                'status': effective_status,
                'is_confirmed': is_confirmed,
                'confirmed_by': confirmed_by,
                'annotated_by': tracking.annotated_by.username if tracking.annotated_by else confirmed_by,
                'annotated_at': tracking.annotated_at,
                'reviewed_by': tracking.reviewed_by.username if tracking.reviewed_by else None,
                'reviewed_at': tracking.reviewed_at,
                'review_notes': tracking.review_notes,
                'locked_by': locked_by_username,
                'is_locked': is_locked,
                'locked_at': tracking.locked_at if is_locked else None
            })
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # ========================================
    # LOCKING ENDPOINTS
    # ========================================
    
    @action(detail=True, methods=['post'], url_path='lock')
    def lock(self, request, project_id=None, pk=None):
        """
        Lock an example for annotation.
        
        POST /v1/projects/{project_id}/tracking/{example_id}/lock/
        
        Locks expire after 5 minutes.
        Returns error if already locked by another user.
        """
        from datetime import timedelta
        
        try:
            with transaction.atomic():
                tracking, created = AnnotationTracking.objects.select_for_update().get_or_create(
                    project_id=project_id,
                    example_id=pk,
                    defaults={
                        'locked_by': request.user,
                        'locked_at': timezone.now(),
                        'started_at': timezone.now(),  # Track when annotation started
                        'status': 'pending'
                    }
                )
                
                if not created:
                    # Check if already locked by someone else
                    if tracking.locked_by and tracking.locked_by != request.user:
                        # Check if lock is still valid
                        lock_expiry = tracking.locked_at + timedelta(minutes=5) if tracking.locked_at else timezone.now()
                        if timezone.now() < lock_expiry:
                            return Response({
                                'success': False,
                                'error': 'locked_by_other',
                                'message': f'This example is locked by {tracking.locked_by.username}',
                                'locked_by': tracking.locked_by.username,
                                'locked_at': tracking.locked_at,
                                'expires_in_minutes': int((lock_expiry - timezone.now()).total_seconds() / 60)
                            }, status=status.HTTP_409_CONFLICT)
                    
                    # Lock it for this user (or renew existing lock)
                    tracking.locked_by = request.user
                    tracking.locked_at = timezone.now()
                    tracking.save(update_fields=['locked_by', 'locked_at'])
                
                print(f'[Monlam Lock] Example {pk} locked by {request.user.username}')
                
                # Calculate expiry time dynamically
                lock_expiry = tracking.locked_at + timedelta(minutes=5)
                
                return Response({
                    'success': True,
                    'locked_by': request.user.username,
                    'locked_at': tracking.locked_at,
                    'expires_in_minutes': int((lock_expiry - timezone.now()).total_seconds() / 60)
                })
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='unlock')
    def unlock(self, request, project_id=None, pk=None):
        """
        Unlock an example.
        
        POST /v1/projects/{project_id}/tracking/{example_id}/unlock/
        
        Only the user who locked it (or an admin) can unlock.
        """
        try:
            tracking = AnnotationTracking.objects.filter(
                project_id=project_id,
                example_id=pk
            ).first()
            
            if not tracking:
                return Response({
                    'success': True,
                    'message': 'No tracking record exists'
                })
            
            # Check if user can unlock
            if tracking.locked_by and tracking.locked_by != request.user:
                # Only privileged users can unlock others' locks
                if not has_approve_permission(request.user, project_id):
                    return Response({
                        'success': False,
                        'error': 'not_authorized',
                        'message': 'Only the lock owner, Approvers, Project Managers, or Admins can unlock'
                    }, status=status.HTTP_403_FORBIDDEN)
            
            # Unlock
            tracking.locked_by = None
            tracking.locked_at = None
            tracking.save(update_fields=['locked_by', 'locked_at'])
            
            print(f'[Monlam Lock] Example {pk} unlocked by {request.user.username}')
            
            return Response({
                'success': True,
                'message': 'Example unlocked'
            })
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='lock-status')
    def lock_status(self, request, project_id=None, pk=None):
        """
        Check lock status of an example.
        
        GET /v1/projects/{project_id}/tracking/{example_id}/lock-status/
        """
        from datetime import timedelta
        
        try:
            tracking = AnnotationTracking.objects.filter(
                project_id=project_id,
                example_id=pk
            ).select_related('locked_by').first()
            
            if not tracking or not tracking.locked_by:
                return Response({
                    'is_locked': False,
                    'locked_by': None,
                    'can_edit': True
                })
            
            # Check if lock is still valid
            lock_expiry = tracking.locked_at + timedelta(minutes=5) if tracking.locked_at else timezone.now()
            if timezone.now() >= lock_expiry:
                # Lock expired
                return Response({
                    'is_locked': False,
                    'locked_by': None,
                    'can_edit': True,
                    'message': 'Lock expired'
                })
            
            # Lock is valid
            is_own_lock = tracking.locked_by == request.user
            return Response({
                'is_locked': True,
                'locked_by': tracking.locked_by.username,
                'locked_at': tracking.locked_at,
                'expires_at': lock_expiry,
                'expires_in_minutes': int((lock_expiry - timezone.now()).total_seconds() / 60),
                'is_own_lock': is_own_lock,
                'can_edit': is_own_lock
            })
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

