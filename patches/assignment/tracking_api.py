"""
API Endpoints for Annotation Tracking

Provides:
- Auto-tracking when annotations are submitted
- Approve/Reject endpoints for reviewers
- Status tracking

Permission Hierarchy:
- Annotators: Can only mark_submitted (submit their own annotations)
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
from .completion_tracking import ApproverCompletionStatus
from .roles import ROLE_PROJECT_ADMIN, ROLE_ANNOTATION_APPROVER, ROLE_PROJECT_MANAGER


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


def _get_user_role(user, project):
    """Get user's role in the project."""
    from projects.models import Member
    try:
        member = Member.objects.filter(user=user, project=project).select_related('role').first()
        if member and member.role:
            role_name = member.role.name.lower() if member.role.name else None
            # Normalize: replace spaces with underscores for consistency
            if role_name:
                role_name = role_name.replace(' ', '_')
            return role_name
    except Exception as e:
        print(f'[Monlam Tracking] Error getting user role: {e}')
    return None


def _is_annotator_only(user, project):
    """
    Check if user is ONLY an annotator (not approver/admin/manager).
    Only annotators can confirm/submit examples.
    
    Uses exact role name matching based on database role names.
    Role names in database are stored exactly as: 'annotator', 'annotation_approver', 
    'project_admin', 'project_manager'
    """
    if user.is_superuser:
        return False  # Superusers are not annotators
    
    role = _get_user_role(user, project)
    if not role:
        return False
    
    # Normalize role name (remove spaces, ensure lowercase)
    # _get_user_role already returns lowercase with spaces replaced by underscores
    role = role.lower().strip().replace(' ', '_')
    
    # Import role constant to ensure consistency
    from .roles import ROLE_ANNOTATOR
    
    # User is annotator ONLY if role exactly matches ROLE_ANNOTATOR constant
    # Any other role (approver, admin, manager) is NOT an annotator
    return role == ROLE_ANNOTATOR


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
            # Validate that user is a project member
            from projects.models import Member, Project
            project = Project.objects.get(pk=project_id)
            
            is_member = Member.objects.filter(
                user=request.user,
                project_id=project_id
            ).exists()
            
            if not is_member and not request.user.is_superuser:
                return Response(
                    {'error': 'You must be a project member to submit annotations'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # CRITICAL: Only annotators can confirm/submit examples
            # Reviewers, approvers, and project admins cannot submit
            if not _is_annotator_only(request.user, project):
                return Response(
                    {'error': 'Only annotators can confirm or submit examples. Reviewers and approvers should use the approve/reject buttons instead.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            with transaction.atomic():
                tracking, created = AnnotationTracking.objects.get_or_create(
                    project_id=project_id,
                    example_id=example_id,
                    defaults={
                        'annotated_by': request.user,  # Track who annotated (for metrics, not exposed in API)
                        'annotated_at': timezone.now(),
                        'status': 'submitted'  # Submitted for review
                    }
                )
                
                # Update status to submitted if it was pending
                needs_save = False
                if not tracking.annotated_by:
                    # Only set if user is still a project member
                    if is_member or request.user.is_superuser:
                        tracking.annotated_by = request.user
                        needs_save = True
                
                if tracking.status == 'pending':
                    tracking.annotated_at = timezone.now()
                    tracking.status = 'submitted'
                    needs_save = True
                
                # If rejected, update to submitted (resubmission)
                elif tracking.status == 'rejected':
                    tracking.annotated_at = timezone.now()
                    tracking.status = 'submitted'
                    needs_save = True
                
                # Calculate time spent if we have started_at
                if tracking.started_at and not tracking.time_spent_seconds:
                    time_diff = timezone.now() - tracking.started_at
                    tracking.time_spent_seconds = int(time_diff.total_seconds())
                    needs_save = True
                
                # Save if we made changes
                if needs_save:
                    tracking.save()
                
                # Also create ExampleState to mark as confirmed (for tick mark in UI)
                # This ensures the example shows as completed/confirmed in Doccano's native UI
                # Only create if user is still a project member
                if is_member or request.user.is_superuser:
                    try:
                        from examples.models import ExampleState
                        from examples.models import Example
                        example = Example.objects.get(pk=example_id)
                        # Use example as lookup, update confirmed_by and confirmed_at
                        ExampleState.objects.update_or_create(
                            example=example,
                            defaults={
                                'confirmed_by': request.user,  # Still need user for ExampleState
                                'confirmed_at': tracking.annotated_at or timezone.now()
                            }
                        )
                        print(f'[Monlam Tracking] ✅ Created/Updated ExampleState for example {example_id}')
                    except Exception as e:
                        print(f'[Monlam Tracking] ⚠️ Could not create ExampleState: {e}')
                        # Don't fail the whole request if ExampleState creation fails
                
                # Calculate time spent for new records too
                time_spent = None
                if tracking.started_at and tracking.annotated_at:
                    time_diff = tracking.annotated_at - tracking.started_at
                    time_spent = int(time_diff.total_seconds())
                
                return Response({
                    'success': True,
                    'status': tracking.status,
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
        
        Rules:
        - Annotation approvers can approve ONLY if example is submitted by annotator
        - Project admins can ONLY approve if an annotation_approver has already approved
        - Project managers can always approve
        Requires: project_admin, annotation_approver, or project_manager role
        """
        from examples.models import Example
        from projects.models import Project
        
        # Check permission
        if not has_approve_permission(request.user, project_id):
            return Response(
                {'error': 'You do not have permission to approve annotations. '
                         'Only Approvers, Project Managers, and Admins can approve.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get project and example
        try:
            project = Project.objects.get(pk=project_id)
            example = Example.objects.get(pk=pk, project=project)
        except (Project.DoesNotExist, Example.DoesNotExist):
            return Response(
                {'error': 'Project or example not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get user's role
        user_role = _get_user_role(request.user, project)
        
        # If role is None, deny access (shouldn't happen if has_approve_permission passed, but be safe)
        if not user_role:
            return Response(
                {'error': 'Unable to determine your role. Please contact an administrator.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Project managers can always approve (no restrictions)
        if user_role == ROLE_PROJECT_MANAGER:
            # Skip validation, allow approval
            pass
        # Check if example is submitted or confirmed (for annotation_approvers)
        elif user_role == ROLE_ANNOTATION_APPROVER:
            # Check if example has been submitted or confirmed
            is_submitted = False
            
            # Check AnnotationTracking status
            tracking_check = AnnotationTracking.objects.filter(
                project=project,
                example=example
            ).first()
            
            if tracking_check and tracking_check.status == 'submitted':
                is_submitted = True
            else:
                # Also check Assignment status as fallback
                from .models_separate import Assignment
                assignment = Assignment.objects.filter(
                    project=project,
                    example=example,
                    is_active=True
                ).first()
                
                if assignment and assignment.status == 'submitted':
                    is_submitted = True
                else:
                    # Also check ExampleState (confirmed via checkmark)
                    from examples.models import ExampleState
                    from projects.models import Member
                    state = ExampleState.objects.filter(example=example).first()
                    if state and state.confirmed_by:
                        # Verify confirmed_by is still a project member
                        is_member = Member.objects.filter(
                            user=state.confirmed_by,
                            project=project
                        ).exists()
                        if is_member or state.confirmed_by.is_superuser:
                            is_submitted = True
            
            if not is_submitted:
                return Response(
                    {
                        'error': 'Annotation approvers can only approve examples that have been submitted or confirmed by annotators.',
                        'requires_submission': True
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # If user is project_admin, check if annotation_approver has approved
        elif user_role == ROLE_PROJECT_ADMIN:
            # Get all approvals for this example
            all_approvals = ApproverCompletionStatus.objects.filter(
                example=example
            ).select_related('approver').defer('assignment')
            
            # Check if any annotation_approver has approved
            annotation_approver_approved = False
            for ap in all_approvals:
                approver_role = _get_user_role(ap.approver, project)
                if approver_role == ROLE_ANNOTATION_APPROVER and ap.status == 'approved':
                    annotation_approver_approved = True
                    break
            
            if not annotation_approver_approved:
                return Response(
                    {
                        'error': 'Project admins can only approve examples that have been approved by an annotation approver first.',
                        'requires_approver_approval': True
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
        
        try:
            with transaction.atomic():
                # Update AnnotationTracking (track reviewed_by in backend for comprehensive metrics)
                tracking, created = AnnotationTracking.objects.get_or_create(
                    project_id=project_id,
                    example_id=pk,
                    defaults={
                        'status': 'reviewed',  # Changed from 'approved' to 'reviewed'
                        'reviewed_by': request.user,  # Track who reviewed (for metrics, not exposed in API)
                        'reviewed_at': timezone.now(),
                        'review_notes': request.data.get('review_notes', '')
                    }
                )
                
                if not created:
                    tracking.status = 'reviewed'  # Changed from 'approved' to 'reviewed'
                    tracking.reviewed_by = request.user  # Track who reviewed (for metrics, not exposed in API)
                    tracking.reviewed_at = timezone.now()
                    tracking.review_notes = request.data.get('review_notes', '')
                    tracking.save()
                
                # Also update ApproverCompletionStatus for consistency
                from .completion_tracking import CompletionMatrixUpdater
                CompletionMatrixUpdater.update_approver_status(
                    example=example,
                    approver=request.user,
                    status_choice='approved',  # Keep 'approved' for ApproverCompletionStatus (different model)
                    notes=request.data.get('review_notes', '')
                )
                
                return Response({
                    'success': True,
                    'status': 'reviewed',  # Changed from 'approved' to 'reviewed'
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
        
        Rules:
        - Annotation approvers can reject ONLY if example is submitted by annotator
        - Project admins can ONLY reject if an annotation_approver has already approved
        - Project managers can always reject
        Requires: project_admin, annotation_approver, or project_manager role
        """
        from examples.models import Example
        from projects.models import Project
        
        # Check permission
        if not has_approve_permission(request.user, project_id):
            return Response(
                {'error': 'You do not have permission to reject annotations. '
                         'Only Approvers, Project Managers, and Admins can reject.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get project and example
        try:
            project = Project.objects.get(pk=project_id)
            example = Example.objects.get(pk=pk, project=project)
        except (Project.DoesNotExist, Example.DoesNotExist):
            return Response(
                {'error': 'Project or example not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get user's role
        user_role = _get_user_role(request.user, project)
        
        # If role is None, deny access (shouldn't happen if has_approve_permission passed, but be safe)
        if not user_role:
            return Response(
                {'error': 'Unable to determine your role. Please contact an administrator.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Project managers can always reject (no restrictions)
        if user_role == ROLE_PROJECT_MANAGER:
            # Skip validation, allow rejection
            pass
        # Check if example is submitted or confirmed (for annotation_approvers)
        elif user_role == ROLE_ANNOTATION_APPROVER:
            # Check if example has been submitted or confirmed
            is_submitted = False
            
            # Check AnnotationTracking status
            tracking_check = AnnotationTracking.objects.filter(
                project=project,
                example=example
            ).first()
            
            if tracking_check and tracking_check.status == 'submitted':
                is_submitted = True
            else:
                # Also check Assignment status as fallback
                from .models_separate import Assignment
                assignment = Assignment.objects.filter(
                    project=project,
                    example=example,
                    is_active=True
                ).first()
                
                if assignment and assignment.status == 'submitted':
                    is_submitted = True
                else:
                    # Also check ExampleState (confirmed via checkmark)
                    from examples.models import ExampleState
                    from projects.models import Member
                    state = ExampleState.objects.filter(example=example).first()
                    if state and state.confirmed_by:
                        # Verify confirmed_by is still a project member
                        is_member = Member.objects.filter(
                            user=state.confirmed_by,
                            project=project
                        ).exists()
                        if is_member or state.confirmed_by.is_superuser:
                            is_submitted = True
            
            if not is_submitted:
                return Response(
                    {
                        'error': 'Annotation approvers can only reject examples that have been submitted or confirmed by annotators.',
                        'requires_submission': True
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # If user is project_admin, check if annotation_approver has approved
        elif user_role == ROLE_PROJECT_ADMIN:
            # Get all approvals for this example
            all_approvals = ApproverCompletionStatus.objects.filter(
                example=example
            ).select_related('approver').defer('assignment')
            
            # Check if any annotation_approver has approved
            annotation_approver_approved = False
            for ap in all_approvals:
                approver_role = _get_user_role(ap.approver, project)
                if approver_role == ROLE_ANNOTATION_APPROVER and ap.status == 'approved':
                    annotation_approver_approved = True
                    break
            
            if not annotation_approver_approved:
                return Response(
                    {
                        'error': 'Project admins can only reject examples that have been approved by an annotation approver first.',
                        'requires_approver_approval': True
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
        
        review_notes = request.data.get('review_notes', '')
        # Notes are now optional for rejection
        
        try:
            with transaction.atomic():
                # Update AnnotationTracking (track reviewed_by in backend for comprehensive metrics)
                tracking, created = AnnotationTracking.objects.get_or_create(
                    project_id=project_id,
                    example_id=pk,
                    defaults={
                        'status': 'rejected',
                        'reviewed_by': request.user,  # Track who reviewed (for metrics, not exposed in API)
                        'reviewed_at': timezone.now(),
                        'review_notes': review_notes
                    }
                )
                
                if not created:
                    tracking.status = 'rejected'
                    tracking.reviewed_by = request.user  # Track who reviewed (for metrics, not exposed in API)
                    tracking.reviewed_at = timezone.now()
                    tracking.review_notes = review_notes
                    tracking.save()
                
                # Also update ApproverCompletionStatus for consistency
                from .completion_tracking import CompletionMatrixUpdater
                CompletionMatrixUpdater.update_approver_status(
                    example=example,
                    approver=request.user,
                    status_choice='rejected',
                    notes=review_notes
                )
                
                return Response({
                    'success': True,
                    'status': 'rejected',
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
            # Check Doccano's native ExampleState (confirmation via checkmark)
            is_confirmed = False
            confirmed_by = None
            try:
                from examples.models import ExampleState
                from projects.models import Member
                
                state = ExampleState.objects.filter(example_id=pk).select_related('confirmed_by').first()
                if state and state.confirmed_by:
                    # Only show confirmed_by if they're still a project member
                    is_member = Member.objects.filter(
                        user=state.confirmed_by,
                        project_id=project_id
                    ).exists()
                    
                    if is_member or state.confirmed_by.is_superuser:
                        is_confirmed = True
                        confirmed_by = state.confirmed_by.username
                    else:
                        # User is no longer a project member - don't show their name
                        is_confirmed = True  # Still confirmed, but don't show who
                        confirmed_by = None
            except Exception:
                pass  # ExampleState may not exist
            
            # Get our custom tracking record
            tracking = AnnotationTracking.objects.filter(
                project_id=project_id,
                example_id=pk
            ).select_related('annotated_by', 'reviewed_by').first()
            
            if not tracking:
                return Response({
                    'status': 'submitted' if is_confirmed else 'pending',  # If confirmed but no tracking, treat as submitted
                    'is_confirmed': is_confirmed,
                    'confirmed_by': confirmed_by,  # From ExampleState
                    'annotated_by': confirmed_by,  # Use confirmed_by as fallback
                    'reviewed_by': None,
                    'annotated_at': None,
                    'reviewed_at': None,
                    'review_notes': ''
                })
            
            # Override status if confirmed but tracking says pending
            effective_status = tracking.status
            if is_confirmed and tracking.status == 'pending':
                effective_status = 'submitted'
            
            # Get annotated_by username (who submitted/confirmed)
            annotated_by_username = None
            if tracking.annotated_by:
                from projects.models import Member
                is_member = Member.objects.filter(
                    user=tracking.annotated_by,
                    project_id=project_id
                ).exists()
                if is_member or tracking.annotated_by.is_superuser:
                    annotated_by_username = tracking.annotated_by.username
            
            # Get reviewed_by username (who approved/rejected)
            reviewed_by_username = None
            if tracking.reviewed_by:
                from projects.models import Member
                is_member = Member.objects.filter(
                    user=tracking.reviewed_by,
                    project_id=project_id
                ).exists()
                if is_member or tracking.reviewed_by.is_superuser:
                    reviewed_by_username = tracking.reviewed_by.username
            
            return Response({
                'status': effective_status,
                'is_confirmed': is_confirmed,
                'confirmed_by': confirmed_by,  # From ExampleState
                'annotated_by': annotated_by_username,  # Who submitted/annotated
                'reviewed_by': reviewed_by_username,  # Who approved/rejected
                'annotated_at': tracking.annotated_at,
                'reviewed_at': tracking.reviewed_at,
                'review_notes': tracking.review_notes
            })
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # ========================================
    # NOTE: Locking endpoints removed - single annotator per project, no race conditions
    # ========================================

