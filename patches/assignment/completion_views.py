"""
Completion Matrix Views

API endpoints for accessing completion tracking and matrix views.
These views are accessible based on user roles:
- Project Managers: Full access to all matrices
- Approvers: Can see approval queue and their own stats
- Annotators: Can see their own completion status
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q

from .completion_tracking import (
    CompletionMatrix,
    CompletionMatrixUpdater,
    AnnotatorCompletionStatus,
    ApproverCompletionStatus
)
from .roles import (
    IsProjectManager,
    IsApproverOrHigher,
    CanViewCompletionMatrix,
    ProjectManagerMixin,
    ROLE_PROJECT_ADMIN,
    ROLE_ANNOTATION_APPROVER,
    ROLE_PROJECT_MANAGER
)


class CompletionMatrixViewSet(viewsets.ViewSet):
    """
    ViewSet for completion matrix and tracking.
    
    Endpoints:
    - GET /projects/{project_id}/completion-matrix/ - Get full matrix (PM only)
    - GET /projects/{project_id}/completion-matrix/annotators/ - Annotator matrix
    - GET /projects/{project_id}/completion-matrix/approvers/ - Approver matrix
    - GET /projects/{project_id}/completion-matrix/my/ - Current user's stats
    - GET /projects/{project_id}/completion-matrix/summary/ - Project summary
    - POST /projects/{project_id}/completion-matrix/sync/ - Sync from assignments
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_project(self, project_id):
        """Get project and check access."""
        from projects.models import Project
        return get_object_or_404(Project, pk=project_id)
    
    def list(self, request, project_id):
        """
        Get complete matrix with both annotators and approvers.
        Only accessible to Project Managers and Admins.
        """
        project = self.get_project(project_id)
        
        # Check permission
        if not ProjectManagerMixin.is_project_manager(request.user, project):
            return Response(
                {
                    'error': 'Only Project Managers and Admins can view the complete matrix',
                    'your_role': ProjectManagerMixin.get_user_role(request.user, project)
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        matrix = CompletionMatrix(project)
        data = matrix.get_complete_matrix()
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def annotators(self, request, project_id):
        """
        Get annotator completion matrix.
        Project Managers see all, others see filtered based on permissions.
        """
        project = self.get_project(project_id)
        
        try:
            # Get assignments grouped by annotator
            from .models_separate import Assignment
            from django.db.models import Count, Q
            
            # Get all unique annotators with their assignment counts
            annotator_data = Assignment.objects.filter(
                project=project,
                is_active=True
            ).values(
                'assigned_to__id',
                'assigned_to__username'
            ).annotate(
                assigned_count=Count('id'),
                completed_count=Count('id', filter=Q(status='completed')),
                submitted_count=Count('id', filter=Q(status='submitted'))
            )
            
            # Format the data
            data = []
            for item in annotator_data:
                if not item['assigned_to__id']:
                    continue
                assigned = item['assigned_count']
                completed = item['completed_count'] + item['submitted_count']
                data.append({
                    'user_id': item['assigned_to__id'],
                    'username': item['assigned_to__username'],
                    'assigned_count': assigned,
                    'completed_count': completed,
                    'completion_rate': round((completed / assigned * 100), 1) if assigned > 0 else 0
                })
            
            return Response(data)
            
        except Exception as e:
            # Fallback: return empty list on error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error fetching annotator matrix: {e}")
            return Response([])
    
    @action(detail=False, methods=['get'])
    def approvers(self, request, project_id):
        """
        Get approver completion matrix.
        Project Managers see all, Approvers see their own.
        """
        project = self.get_project(project_id)
        matrix = CompletionMatrix(project)
        
        # Check permissions
        is_manager = ProjectManagerMixin.is_project_manager(request.user, project)
        is_approver = ProjectManagerMixin.is_approver_or_higher(request.user, project)
        
        if is_manager:
            # Project Manager sees all approvers
            data = matrix.get_approver_matrix()
        elif is_approver:
            # Approvers see their own data
            data = [
                approver_data
                for approver_data in matrix.get_approver_matrix()
                if approver_data['approver_id'] == request.user.id
            ]
        else:
            return Response(
                {'error': 'You do not have permission to view approval data'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def my(self, request, project_id):
        """
        Get current user's completion stats (both as annotator and approver).
        """
        project = self.get_project(project_id)
        user = request.user
        
        # Get annotator stats
        annotator_completions = AnnotatorCompletionStatus.objects.filter(
            project=project,
            annotator=user
        )
        
        annotator_stats = {
            'total_assigned': annotator_completions.count(),
            'completed': annotator_completions.filter(is_completed=True).count(),
            'in_progress': annotator_completions.filter(is_completed=False).count(),
        }
        
        # Get approver stats
        approver_completions = ApproverCompletionStatus.objects.filter(
            project=project,
            approver=user
        )
        
        approver_stats = {
            'total_to_review': approver_completions.count(),
            'approved': approver_completions.filter(status='approved').count(),
            'rejected': approver_completions.filter(status='rejected').count(),
            'pending': approver_completions.filter(status='pending').count(),
        }
        
        return Response({
            'user_id': user.id,
            'username': user.username,
            'role': ProjectManagerMixin.get_user_role(user, project),
            'annotator_stats': annotator_stats,
            'approver_stats': approver_stats
        })
    
    @action(detail=False, methods=['get'])
    def summary(self, request, project_id):
        """
        Get project summary statistics.
        Available to all project members.
        """
        project = self.get_project(project_id)
        matrix = CompletionMatrix(project)
        
        summary = matrix._get_summary_stats()
        
        return Response(summary)
    
    @action(detail=False, methods=['post'])
    def sync(self, request, project_id):
        """
        Sync completion tracking from existing assignments.
        Only accessible to Project Admins.
        """
        project = self.get_project(project_id)
        
        # Check if user is project admin
        role = ProjectManagerMixin.get_user_role(request.user, project)
        if role != 'project_admin':
            return Response(
                {'error': 'Only Project Admins can sync data'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Perform sync
        CompletionMatrixUpdater.sync_from_assignments(project)
        
        return Response({
            'message': 'Successfully synced completion tracking from assignments'
        })
    
    @action(detail=False, methods=['get'])
    def export(self, request, project_id):
        """
        Export completion matrix as CSV.
        Only accessible to Project Managers and Admins.
        """
        project = self.get_project(project_id)
        
        # Check permission
        if not ProjectManagerMixin.is_project_manager(request.user, project):
            return Response(
                {'error': 'Only Project Managers and Admins can export data'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        matrix = CompletionMatrix(project)
        data = matrix.get_complete_matrix()
        
        # Format as CSV-friendly data
        csv_data = self._format_for_csv(data)
        
        return Response({
            'csv_data': csv_data,
            'filename': f'completion_matrix_{project.id}.csv'
        })
    
    def _format_for_csv(self, matrix_data):
        """
        Format matrix data for CSV export.
        """
        rows = []
        
        # Header
        rows.append([
            'Type', 'User ID', 'Username', 'Example ID',
            'Status', 'Completed/Reviewed At', 'Notes'
        ])
        
        # Annotator rows
        for annotator in matrix_data.get('annotators', []):
            for example in annotator.get('examples', []):
                rows.append([
                    'Annotator',
                    annotator['annotator_id'],
                    annotator['annotator_username'],
                    example['example_id'],
                    example['status'],
                    example.get('completed_at', ''),
                    ''
                ])
        
        # Approver rows
        for approver in matrix_data.get('approvers', []):
            for example in approver.get('examples', []):
                rows.append([
                    'Approver',
                    approver['approver_id'],
                    approver['approver_username'],
                    example['example_id'],
                    example['status'],
                    example.get('reviewed_at', ''),
                    example.get('review_notes', '')
                ])
        
        return rows


class AnnotatorCompletionViewSet(viewsets.ViewSet):
    """
    ViewSet for individual annotator completion tracking.
    
    Endpoints:
    - GET /projects/{project_id}/annotator-completion/{example_id}/ - Get status
    - POST /projects/{project_id}/annotator-completion/{example_id}/complete/ - Mark complete
    - POST /projects/{project_id}/annotator-completion/{example_id}/incomplete/ - Mark incomplete
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_project(self, project_id):
        """Get project and check access."""
        from projects.models import Project
        return get_object_or_404(Project, pk=project_id)
    
    def retrieve(self, request, project_id, example_id):
        """Get completion status for an example."""
        from examples.models import Example
        
        project = self.get_project(project_id)
        example = get_object_or_404(Example, pk=example_id, project=project)
        
        # Get completion status
        completion = AnnotatorCompletionStatus.objects.filter(
            example=example,
            annotator=request.user
        ).first()
        
        if not completion:
            return Response({
                'example_id': example_id,
                'is_completed': False,
                'completed_at': None
            })
        
        return Response({
            'example_id': example_id,
            'is_completed': completion.is_completed,
            'completed_at': completion.completed_at,
            'annotation_count': completion.annotation_count
        })
    
    @action(detail=True, methods=['post'])
    def complete(self, request, project_id, example_id):
        """Mark example as complete for current user."""
        from examples.models import Example
        
        project = self.get_project(project_id)
        example = get_object_or_404(Example, pk=example_id, project=project)
        
        # Update completion status
        completion = CompletionMatrixUpdater.update_annotator_status(
            example=example,
            annotator=request.user,
            is_completed=True
        )
        
        return Response({
            'message': 'Marked as complete',
            'example_id': example_id,
            'is_completed': completion.is_completed
        })
    
    @action(detail=True, methods=['post'])
    def incomplete(self, request, project_id, example_id):
        """Mark example as incomplete (revert completion)."""
        from examples.models import Example
        
        project = self.get_project(project_id)
        example = get_object_or_404(Example, pk=example_id, project=project)
        
        # Update completion status
        completion = CompletionMatrixUpdater.update_annotator_status(
            example=example,
            annotator=request.user,
            is_completed=False
        )
        
        return Response({
            'message': 'Marked as incomplete',
            'example_id': example_id,
            'is_completed': completion.is_completed
        })


class ApproverCompletionViewSet(viewsets.ViewSet):
    """
    ViewSet for approver completion tracking.
    
    Endpoints:
    - GET /projects/{project_id}/approver-completion/{example_id}/ - Get status (all authenticated users)
    - POST /projects/{project_id}/approver-completion/{example_id}/approve/ - Approve (approvers only)
    - POST /projects/{project_id}/approver-completion/{example_id}/reject/ - Reject (approvers only)
    
    Multi-level approval support:
    - Annotation approvers can approve/reject examples
    - Project admins can approve/reject examples even if annotation_approvers have already approved
    - Each approver maintains their own approval record
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_project(self, project_id):
        """Get project and check access."""
        from projects.models import Project
        return get_object_or_404(Project, pk=project_id)
    
    def _get_user_role(self, user, project):
        """Get user's role in the project."""
        from projects.models import Member
        try:
            member = Member.objects.filter(user=user, project=project).select_related('role').first()
            if member and member.role:
                return member.role.name.lower() if member.role.name else None
        except Exception:
            pass
        return None
    
    def retrieve(self, request, project_id, example_id):
        """
        Get approval status for an example.
        Accessible to all authenticated users (to view approval chain).
        """
        from examples.models import Example
        
        project = self.get_project(project_id)
        example = get_object_or_404(Example, pk=example_id, project=project)
        
        # Check if user has permission to approve (for can_review flag)
        can_review = ProjectManagerMixin.is_approver_or_higher(request.user, project)
        
        # Get current user's approval status
        approval = ApproverCompletionStatus.objects.filter(
            example=example,
            approver=request.user
        ).first()
        
        # Get all approver completions for this example (to show multi-level approval)
        all_approvals = ApproverCompletionStatus.objects.filter(
            example=example
        ).select_related('approver').order_by('-reviewed_at')
        
        # Build list of all approvals
        approvals_list = []
        for ap in all_approvals:
            approver_role = self._get_user_role(ap.approver, project)
            approvals_list.append({
                'approver_id': ap.approver.id,
                'approver_username': ap.approver.username,
                'approver_role': approver_role,
                'status': ap.status,
                'reviewed_at': ap.reviewed_at,
                'review_notes': ap.review_notes
            })
        
        # Check if any annotation_approver has approved
        annotation_approver_approved = any(
            ap['approver_role'] == ROLE_ANNOTATION_APPROVER and ap['status'] == 'approved'
            for ap in approvals_list
        )
        
        # Check if project_admin has approved
        project_admin_approved = any(
            ap['approver_role'] == ROLE_PROJECT_ADMIN and ap['status'] == 'approved'
            for ap in approvals_list
        )
        
        current_user_approval = {
            'example_id': example_id,
            'status': approval.status if approval else 'pending',
            'reviewed_at': approval.reviewed_at if approval else None,
            'review_notes': approval.review_notes if approval else ''
        }
        
        # Check if current user can review (with role-specific rules)
        user_role = self._get_user_role(request.user, project)
        can_review_now = False
        is_submitted = False
        
        # Check if example is submitted or confirmed
        from .simple_tracking import AnnotationTracking
        tracking = AnnotationTracking.objects.filter(
            project=project,
            example=example
        ).first()
        
        if tracking and tracking.status == 'submitted':
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
                state = ExampleState.objects.filter(example=example).first()
                if state and state.confirmed_by:
                    # Verify confirmed_by is still a project member
                    from projects.models import Member
                    is_member = Member.objects.filter(
                        user=state.confirmed_by,
                        project=project
                    ).exists()
                    if is_member or state.confirmed_by.is_superuser:
                        is_submitted = True
        
        if can_review:
            if user_role == ROLE_PROJECT_ADMIN:
                # Project admin can only review if annotation_approver has approved
                can_review_now = annotation_approver_approved
            elif user_role == ROLE_ANNOTATION_APPROVER:
                # Annotation approvers can only review if example is submitted
                can_review_now = is_submitted
            elif user_role == ROLE_PROJECT_MANAGER:
                # Project managers can always review
                can_review_now = True
            else:
                # Other roles (shouldn't reach here, but safe fallback)
                can_review_now = False
        
        return Response({
            **current_user_approval,
            'all_approvals': approvals_list,
            'annotation_approver_approved': annotation_approver_approved,
            'project_admin_approved': project_admin_approved,
            'can_review': can_review,  # User has permission to approve/reject (general)
            'can_review_now': can_review_now,  # User can review right now (role-specific rules)
            'is_submitted': is_submitted,  # Whether example has been submitted
            'user_role': user_role
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsApproverOrHigher])
    def approve(self, request, project_id, example_id):
        """
        Approve an example.
        
        Rules:
        - Annotation approvers can approve ONLY if example is submitted by annotator
        - Project admins can ONLY approve if an annotation_approver has already approved
        - Each approver maintains their own approval record.
        Requires approver or higher role.
        """
        from examples.models import Example
        
        project = self.get_project(project_id)
        example = get_object_or_404(Example, pk=example_id, project=project)
        
        # Get user's role
        user_role = self._get_user_role(request.user, project)
        
        # Check if example is submitted or confirmed (for annotation_approvers)
        if user_role == ROLE_ANNOTATION_APPROVER:
            # Check if example has been submitted or confirmed
            is_submitted = False
            
            # Check AnnotationTracking status
            from .simple_tracking import AnnotationTracking
            tracking = AnnotationTracking.objects.filter(
                project=project,
                example=example
            ).first()
            
            if tracking and tracking.status == 'submitted':
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
                    state = ExampleState.objects.filter(example=example).first()
                    if state and state.confirmed_by:
                        # Verify confirmed_by is still a project member
                        from projects.models import Member
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
        if user_role == ROLE_PROJECT_ADMIN:
            # Get all approvals for this example
            all_approvals = ApproverCompletionStatus.objects.filter(
                example=example
            ).select_related('approver')
            
            # Check if any annotation_approver has approved
            annotation_approver_approved = False
            for ap in all_approvals:
                approver_role = self._get_user_role(ap.approver, project)
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
        
        notes = request.data.get('notes', '') or request.data.get('review_notes', '')
        
        # Update approval status (creates or updates this user's approval record)
        approval = CompletionMatrixUpdater.update_approver_status(
            example=example,
            approver=request.user,
            status_choice='approved',
            notes=notes
        )
        
        return Response({
            'message': 'Example approved',
            'example_id': example_id,
            'status': approval.status,
            'approver_role': user_role,
            'reviewed_at': approval.reviewed_at
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsApproverOrHigher])
    def reject(self, request, project_id, example_id):
        """
        Reject an example.
        
        Rules:
        - Annotation approvers can reject ONLY if example is submitted by annotator
        - Project admins can ONLY reject if an annotation_approver has already approved
        - Each approver maintains their own approval record.
        Requires approver or higher role.
        """
        from examples.models import Example
        
        project = self.get_project(project_id)
        example = get_object_or_404(Example, pk=example_id, project=project)
        
        # Get user's role
        user_role = self._get_user_role(request.user, project)
        
        # Check if example is submitted or confirmed (for annotation_approvers)
        if user_role == ROLE_ANNOTATION_APPROVER:
            # Check if example has been submitted or confirmed
            is_submitted = False
            
            # Check AnnotationTracking status
            from .simple_tracking import AnnotationTracking
            tracking = AnnotationTracking.objects.filter(
                project=project,
                example=example
            ).first()
            
            if tracking and tracking.status == 'submitted':
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
                    state = ExampleState.objects.filter(example=example).first()
                    if state and state.confirmed_by:
                        # Verify confirmed_by is still a project member
                        from projects.models import Member
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
        if user_role == ROLE_PROJECT_ADMIN:
            # Get all approvals for this example
            all_approvals = ApproverCompletionStatus.objects.filter(
                example=example
            ).select_related('approver')
            
            # Check if any annotation_approver has approved
            annotation_approver_approved = False
            for ap in all_approvals:
                approver_role = self._get_user_role(ap.approver, project)
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
        
        notes = request.data.get('notes', '') or request.data.get('review_notes', '')
        
        # Update approval status (creates or updates this user's approval record)
        approval = CompletionMatrixUpdater.update_approver_status(
            example=example,
            approver=request.user,
            status_choice='rejected',
            notes=notes
        )
        
        return Response({
            'message': 'Example rejected',
            'example_id': example_id,
            'status': approval.status,
            'approver_role': user_role,
            'reviewed_at': approval.reviewed_at
        })

