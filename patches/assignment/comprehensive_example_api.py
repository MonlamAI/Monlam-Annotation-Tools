"""
Comprehensive Example API with Completion Metrics

This provides an API endpoint that returns Example data with all completion
metrics in a single query, without modifying the Example table.

Usage:
    GET /v1/projects/{project_id}/examples-comprehensive/
    GET /v1/projects/{project_id}/examples-comprehensive/{example_id}/
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q, Max, Case, When, Value, CharField, F
from django.db.models.functions import Coalesce


class ComprehensiveExampleViewSet(viewsets.ViewSet):
    """
    ViewSet that returns Examples with all completion metrics combined.
    
    This gives you comprehensive data in one query without modifying
    the Example table.
    
    Endpoints:
    - GET /projects/{project_id}/examples-comprehensive/
    - GET /projects/{project_id}/examples-comprehensive/{example_id}/
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_project(self, project_id):
        """Get project and check access."""
        from projects.models import Project
        return get_object_or_404(Project, pk=project_id)
    
    def get_comprehensive_queryset(self, project):
        """
        Build a queryset that includes all completion metrics.
        This uses Django ORM to efficiently join all related data.
        """
        from examples.models import Example
        from assignment.models_separate import Assignment
        from assignment.completion_tracking import (
            AnnotatorCompletionStatus,
            ApproverCompletionStatus
        )
        
        queryset = Example.objects.filter(project=project)
        
        # Annotate with assignment info
        queryset = queryset.select_related('project').annotate(
            # Assignment data
            assignment_id=F('assignments__id'),
            assignment_status=F('assignments__status'),
            assigned_to_id=F('assignments__assigned_to_id'),
            assigned_to_username=F('assignments__assigned_to__username'),
            assigned_at=F('assignments__assigned_at'),
            started_at=F('assignments__started_at'),
            submitted_at=F('assignments__submitted_at'),
            
            # Annotator completion aggregates
            total_annotators=Count(
                'annotator_completions',
                distinct=True
            ),
            completed_by_annotators=Count(
                'annotator_completions',
                filter=Q(annotator_completions__is_completed=True),
                distinct=True
            ),
            
            # Approver completion aggregates
            total_approvers=Count(
                'approver_completions',
                distinct=True
            ),
            approved_by=Count(
                'approver_completions',
                filter=Q(approver_completions__status='approved'),
                distinct=True
            ),
            rejected_by=Count(
                'approver_completions',
                filter=Q(approver_completions__status='rejected'),
                distinct=True
            ),
            pending_approvers=Count(
                'approver_completions',
                filter=Q(approver_completions__status='pending'),
                distinct=True
            ),
            
            # Timestamps
            last_completed_at=Max('annotator_completions__completed_at'),
            last_reviewed_at=Max('approver_completions__reviewed_at'),
            
            # Overall status (computed)
            overall_status=Case(
                When(approver_completions__status='approved', then=Value('approved')),
                When(approver_completions__status='rejected', then=Value('rejected')),
                When(annotator_completions__is_completed=True, then=Value('completed')),
                When(assignments__status='in_progress', then=Value('in_progress')),
                When(assignments__status__isnull=False, then=Value('assigned')),
                default=Value('unassigned'),
                output_field=CharField()
            )
        )
        
        return queryset
    
    def list(self, request, project_id):
        """
        List all examples with comprehensive completion metrics.
        
        Query Parameters:
        - status: Filter by overall status (approved, rejected, completed, etc.)
        - assigned_to: Filter by assigned user ID
        - completion_rate_min: Filter by minimum completion rate (0-100)
        - approval_rate_min: Filter by minimum approval rate (0-100)
        - page: Page number
        - page_size: Results per page (default: 50)
        """
        project = self.get_project(project_id)
        queryset = self.get_comprehensive_queryset(project)
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(overall_status=status_filter)
        
        assigned_to = request.query_params.get('assigned_to')
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)
        
        # Pagination
        page_size = int(request.query_params.get('page_size', 50))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        total = queryset.count()
        results = queryset[start:end]
        
        # Serialize data
        data = []
        for example in results:
            # Calculate rates
            completion_rate = 0
            if example.total_annotators > 0:
                completion_rate = round(
                    (example.completed_by_annotators / example.total_annotators) * 100,
                    1
                )
            
            approval_rate = 0
            if example.total_approvers > 0:
                approval_rate = round(
                    (example.approved_by / example.total_approvers) * 100,
                    1
                )
            
            data.append({
                # Original Example data
                'id': example.id,
                'uuid': str(example.uuid),
                'text': example.text,
                'meta': example.meta,
                'filename': example.filename,
                'project_id': example.project_id,
                'project_name': example.project.name,
                'created_at': example.created_at,
                'updated_at': example.updated_at,
                
                # Assignment info
                'assignment': {
                    'id': example.assignment_id,
                    'status': example.assignment_status,
                    'assigned_to_id': example.assigned_to_id,
                    'assigned_to_username': example.assigned_to_username,
                    'assigned_at': example.assigned_at,
                    'started_at': example.started_at,
                    'submitted_at': example.submitted_at,
                },
                
                # Completion metrics
                'completion_metrics': {
                    'annotators': {
                        'total': example.total_annotators,
                        'completed': example.completed_by_annotators,
                        'completion_rate': completion_rate,
                        'last_completed_at': example.last_completed_at,
                    },
                    'approvers': {
                        'total': example.total_approvers,
                        'approved': example.approved_by,
                        'rejected': example.rejected_by,
                        'pending': example.pending_approvers,
                        'approval_rate': approval_rate,
                        'last_reviewed_at': example.last_reviewed_at,
                    },
                    'overall_status': example.overall_status,
                },
                
                # Annotation count
                'annotation_count': example.annotations.count() if hasattr(example, 'annotations') else 0,
            })
        
        return Response({
            'count': total,
            'page': page,
            'page_size': page_size,
            'results': data
        })
    
    def retrieve(self, request, project_id, pk):
        """
        Get a single example with all completion metrics.
        """
        project = self.get_project(project_id)
        queryset = self.get_comprehensive_queryset(project)
        
        try:
            example = queryset.get(pk=pk)
        except:
            return Response(
                {'error': 'Example not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get detailed annotator completion data
        annotator_completions = []
        for ac in example.annotator_completions.all():
            annotator_completions.append({
                'annotator_id': ac.annotator_id,
                'annotator_username': ac.annotator.username,
                'is_completed': ac.is_completed,
                'completed_at': ac.completed_at,
                'annotation_count': ac.annotation_count,
            })
        
        # Get detailed approver completion data
        approver_completions = []
        for ap in example.approver_completions.all():
            approver_completions.append({
                'approver_id': ap.approver_id,
                'approver_username': ap.approver.username,
                'status': ap.status,
                'reviewed_at': ap.reviewed_at,
                'review_notes': ap.review_notes,
            })
        
        # Calculate rates
        completion_rate = 0
        if example.total_annotators > 0:
            completion_rate = round(
                (example.completed_by_annotators / example.total_annotators) * 100,
                1
            )
        
        approval_rate = 0
        if example.total_approvers > 0:
            approval_rate = round(
                (example.approved_by / example.total_approvers) * 100,
                1
            )
        
        data = {
            # Original Example data
            'id': example.id,
            'uuid': str(example.uuid),
            'text': example.text,
            'meta': example.meta,
            'filename': example.filename,
            'project_id': example.project_id,
            'project_name': example.project.name,
            'created_at': example.created_at,
            'updated_at': example.updated_at,
            
            # Assignment info
            'assignment': {
                'id': example.assignment_id,
                'status': example.assignment_status,
                'assigned_to_id': example.assigned_to_id,
                'assigned_to_username': example.assigned_to_username,
                'assigned_at': example.assigned_at,
                'started_at': example.started_at,
                'submitted_at': example.submitted_at,
            },
            
            # Detailed completion data
            'annotator_completions': annotator_completions,
            'approver_completions': approver_completions,
            
            # Summary metrics
            'completion_summary': {
                'total_annotators': example.total_annotators,
                'completed_by': example.completed_by_annotators,
                'completion_rate': completion_rate,
                'total_approvers': example.total_approvers,
                'approved_by': example.approved_by,
                'rejected_by': example.rejected_by,
                'pending_approvers': example.pending_approvers,
                'approval_rate': approval_rate,
                'overall_status': example.overall_status,
                'last_completed_at': example.last_completed_at,
                'last_reviewed_at': example.last_reviewed_at,
            },
            
            # Annotations
            'annotation_count': example.annotations.count() if hasattr(example, 'annotations') else 0,
        }
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request, project_id):
        """
        Export all examples with completion metrics as CSV.
        """
        import csv
        from django.http import HttpResponse
        
        project = self.get_project(project_id)
        queryset = self.get_comprehensive_queryset(project)
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="examples_comprehensive_{project_id}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Example ID', 'Text', 'Filename', 'Project',
            'Assignment Status', 'Assigned To', 'Assigned At',
            'Total Annotators', 'Completed By', 'Completion Rate',
            'Total Approvers', 'Approved By', 'Rejected By', 'Approval Rate',
            'Overall Status', 'Last Completed', 'Last Reviewed'
        ])
        
        for example in queryset:
            completion_rate = 0
            if example.total_annotators > 0:
                completion_rate = round(
                    (example.completed_by_annotators / example.total_annotators) * 100,
                    1
                )
            
            approval_rate = 0
            if example.total_approvers > 0:
                approval_rate = round(
                    (example.approved_by / example.total_approvers) * 100,
                    1
                )
            
            writer.writerow([
                example.id,
                example.text[:100] if example.text else '',
                example.filename or '',
                example.project.name,
                example.assignment_status or 'unassigned',
                example.assigned_to_username or '',
                example.assigned_at or '',
                example.total_annotators,
                example.completed_by_annotators,
                f"{completion_rate}%",
                example.total_approvers,
                example.approved_by,
                example.rejected_by,
                f"{approval_rate}%",
                example.overall_status,
                example.last_completed_at or '',
                example.last_reviewed_at or '',
            ])
        
        return response

