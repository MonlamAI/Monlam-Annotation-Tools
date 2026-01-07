"""
Views for annotation tracking, approve/reject workflow, and metrics.
"""

from rest_framework import viewsets, status, generics
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.utils import timezone

from .models import AnnotationTracking, TrackingStatus, get_or_create_tracking
from .serializers import (
    TrackingSerializer, TrackingStatusSerializer,
    ApproveSerializer, RejectSerializer, LockSerializer,
    TrackingSummarySerializer, AnnotatorPerformanceSerializer,
    ReviewerPerformanceSerializer
)
from apps.projects.models import Project, Member, MemberRole
from apps.projects.permissions import IsProjectMember, IsReviewer, CanManageProject
from apps.examples.models import Example


class TrackingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing tracking records.
    Provides list and detail views for tracking data.
    """
    serializer_class = TrackingSerializer
    permission_classes = [IsAuthenticated, IsProjectMember]
    
    def get_project(self):
        return get_object_or_404(Project, id=self.kwargs['project_id'])
    
    def get_queryset(self):
        project = self.get_project()
        return AnnotationTracking.objects.filter(
            project=project
        ).select_related('annotated_by', 'reviewed_by', 'locked_by', 'example')
    
    @action(detail=False, methods=['get'])
    def summary(self, request, project_id=None):
        """
        Get summary statistics for the project.
        """
        project = self.get_project()
        
        # Total examples
        total_examples = Example.objects.filter(project=project).count()
        
        # Status counts
        status_counts = AnnotationTracking.objects.filter(
            project=project
        ).values('status').annotate(count=Count('id'))
        
        status_dict = {item['status']: item['count'] for item in status_counts}
        
        # Calculate pending (examples without tracking record)
        tracked_count = AnnotationTracking.objects.filter(project=project).count()
        pending_count = total_examples - tracked_count + status_dict.get('pending', 0)
        
        approved_count = status_dict.get('approved', 0)
        completion_rate = (approved_count / total_examples * 100) if total_examples > 0 else 0
        
        data = {
            'total': total_examples,
            'pending': pending_count,
            'in_progress': status_dict.get('in_progress', 0),
            'submitted': status_dict.get('submitted', 0),
            'approved': approved_count,
            'rejected': status_dict.get('rejected', 0),
            'completion_rate': round(completion_rate, 2)
        }
        
        serializer = TrackingSummarySerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, CanManageProject])
    def annotators(self, request, project_id=None):
        """
        Get annotator performance metrics.
        Only visible to PMs and Admins.
        """
        project = self.get_project()
        
        # Get all annotators who have annotated in this project
        annotator_stats = AnnotationTracking.objects.filter(
            project=project,
            annotated_by__isnull=False
        ).values('annotated_by', 'annotated_by__username').annotate(
            completed=Count('id'),
            approved=Count('id', filter=Q(status=TrackingStatus.APPROVED)),
            rejected=Count('id', filter=Q(status=TrackingStatus.REJECTED))
        )
        
        results = []
        for stat in annotator_stats:
            completed = stat['completed']
            approved = stat['approved']
            success_rate = (approved / completed * 100) if completed > 0 else 0
            
            results.append({
                'user_id': stat['annotated_by'],
                'username': stat['annotated_by__username'],
                'completed': completed,
                'approved': approved,
                'rejected': stat['rejected'],
                'success_rate': round(success_rate, 2)
            })
        
        serializer = AnnotatorPerformanceSerializer(results, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, CanManageProject])
    def approvers(self, request, project_id=None):
        """
        Get reviewer performance metrics.
        Only visible to PMs and Admins.
        """
        project = self.get_project()
        
        # Get all reviewers who have reviewed in this project
        reviewer_stats = AnnotationTracking.objects.filter(
            project=project,
            reviewed_by__isnull=False
        ).values('reviewed_by', 'reviewed_by__username').annotate(
            reviewed=Count('id'),
            approved=Count('id', filter=Q(status=TrackingStatus.APPROVED)),
            rejected=Count('id', filter=Q(status=TrackingStatus.REJECTED))
        )
        
        results = []
        for stat in reviewer_stats:
            reviewed = stat['reviewed']
            approved = stat['approved']
            approval_rate = (approved / reviewed * 100) if reviewed > 0 else 0
            
            results.append({
                'user_id': stat['reviewed_by'],
                'username': stat['reviewed_by__username'],
                'reviewed': reviewed,
                'approved': approved,
                'rejected': stat['rejected'],
                'approval_rate': round(approval_rate, 2)
            })
        
        serializer = ReviewerPerformanceSerializer(results, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, CanManageProject])
    def export(self, request, project_id=None):
        """
        Export tracking data as CSV.
        Only visible to PMs and Admins.
        """
        import csv
        from django.http import HttpResponse
        
        project = self.get_project()
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="tracking_report_{project_id}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Example ID', 'Text (truncated)', 'Status', 
            'Annotated By', 'Annotated At', 
            'Reviewed By', 'Reviewed At', 'Review Notes'
        ])
        
        tracking_records = AnnotationTracking.objects.filter(
            project=project
        ).select_related('annotated_by', 'reviewed_by', 'example').order_by('example_id')
        
        for tracking in tracking_records:
            text_preview = (tracking.example.text or '')[:100]
            if len(tracking.example.text or '') > 100:
                text_preview += '...'
            
            writer.writerow([
                tracking.example_id,
                text_preview,
                tracking.get_status_display(),
                tracking.annotated_by.username if tracking.annotated_by else '',
                tracking.annotated_at.isoformat() if tracking.annotated_at else '',
                tracking.reviewed_by.username if tracking.reviewed_by else '',
                tracking.reviewed_at.isoformat() if tracking.reviewed_at else '',
                tracking.review_notes or ''
            ])
        
        return response


class ExampleTrackingView(APIView):
    """
    Get or update tracking for a specific example.
    """
    permission_classes = [IsAuthenticated, IsProjectMember]
    
    def get_example(self):
        return get_object_or_404(
            Example,
            id=self.kwargs['example_id'],
            project_id=self.kwargs['project_id']
        )
    
    def get(self, request, project_id, example_id):
        """Get tracking status for an example."""
        example = self.get_example()
        project = example.project
        
        tracking = get_or_create_tracking(project, example)
        serializer = TrackingSerializer(tracking)
        return Response(serializer.data)


class ExampleStatusView(APIView):
    """
    Quick status check for an example.
    """
    permission_classes = [IsAuthenticated, IsProjectMember]
    
    def get(self, request, project_id, example_id):
        """Get just the status for an example."""
        example = get_object_or_404(
            Example,
            id=example_id,
            project_id=project_id
        )
        
        try:
            tracking = AnnotationTracking.objects.get(example=example)
            data = {
                'example_id': example.id,
                'status': tracking.status,
                'status_display': tracking.get_status_display(),
                'annotated_by': tracking.annotated_by.username if tracking.annotated_by else None,
                'reviewed_by': tracking.reviewed_by.username if tracking.reviewed_by else None,
                'is_locked': tracking.is_locked,
                'locked_by': tracking.locked_by.username if tracking.locked_by else None,
            }
        except AnnotationTracking.DoesNotExist:
            data = {
                'example_id': example.id,
                'status': 'pending',
                'status_display': 'Pending',
                'annotated_by': None,
                'reviewed_by': None,
                'is_locked': False,
                'locked_by': None,
            }
        
        serializer = TrackingStatusSerializer(data)
        return Response(serializer.data)


class ApproveView(APIView):
    """
    Approve an annotation.
    Only accessible to reviewers (Approvers, PMs, Admins).
    """
    permission_classes = [IsAuthenticated, IsReviewer]
    
    def post(self, request, project_id, example_id):
        """Approve the annotation on this example."""
        example = get_object_or_404(
            Example,
            id=example_id,
            project_id=project_id
        )
        project = example.project
        
        serializer = ApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        tracking = get_or_create_tracking(project, example)
        
        # Check if there's something to approve
        if tracking.status not in [TrackingStatus.SUBMITTED, TrackingStatus.REJECTED]:
            return Response(
                {'error': f'Cannot approve example with status "{tracking.status}". Only submitted or rejected examples can be approved.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tracking.approve(
            reviewer=request.user,
            notes=serializer.validated_data.get('notes', '')
        )
        
        return Response({
            'message': 'Example approved successfully!',
            'status': tracking.status,
            'reviewed_by': request.user.username,
            'reviewed_at': tracking.reviewed_at.isoformat()
        })


class RejectView(APIView):
    """
    Reject an annotation.
    Only accessible to reviewers (Approvers, PMs, Admins).
    Requires rejection reason.
    """
    permission_classes = [IsAuthenticated, IsReviewer]
    
    def post(self, request, project_id, example_id):
        """Reject the annotation on this example."""
        example = get_object_or_404(
            Example,
            id=example_id,
            project_id=project_id
        )
        project = example.project
        
        serializer = RejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        tracking = get_or_create_tracking(project, example)
        
        # Check if there's something to reject
        if tracking.status not in [TrackingStatus.SUBMITTED, TrackingStatus.APPROVED]:
            return Response(
                {'error': f'Cannot reject example with status "{tracking.status}". Only submitted or approved examples can be rejected.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tracking.reject(
            reviewer=request.user,
            notes=serializer.validated_data['notes']
        )
        
        return Response({
            'message': 'Example rejected. Annotator will see it again for revision.',
            'status': tracking.status,
            'reviewed_by': request.user.username,
            'reviewed_at': tracking.reviewed_at.isoformat(),
            'review_notes': tracking.review_notes
        })


class LockView(APIView):
    """
    Lock an example for editing.
    Prevents other users from editing simultaneously.
    """
    permission_classes = [IsAuthenticated, IsProjectMember]
    
    def post(self, request, project_id, example_id):
        """Acquire lock on an example."""
        example = get_object_or_404(
            Example,
            id=example_id,
            project_id=project_id
        )
        project = example.project
        
        tracking = get_or_create_tracking(project, example)
        
        if tracking.acquire_lock(request.user):
            return Response({
                'message': 'Lock acquired successfully.',
                'locked_by': request.user.username,
                'locked_at': tracking.locked_at.isoformat()
            })
        else:
            return Response(
                {
                    'error': f'Example is locked by {tracking.locked_by.username}.',
                    'locked_by': tracking.locked_by.username,
                    'locked_at': tracking.locked_at.isoformat() if tracking.locked_at else None
                },
                status=status.HTTP_409_CONFLICT
            )


class UnlockView(APIView):
    """
    Unlock an example.
    """
    permission_classes = [IsAuthenticated, IsProjectMember]
    
    def post(self, request, project_id, example_id):
        """Release lock on an example."""
        example = get_object_or_404(
            Example,
            id=example_id,
            project_id=project_id
        )
        project = example.project
        
        tracking = get_or_create_tracking(project, example)
        
        # Only allow unlock by the lock holder or admin
        if tracking.locked_by and tracking.locked_by != request.user:
            # Check if user is admin
            member = Member.objects.filter(
                project=project,
                user=request.user,
                role=MemberRole.PROJECT_ADMIN
            ).exists()
            
            if not member and not request.user.is_superuser:
                return Response(
                    {'error': 'Cannot unlock example locked by another user.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        tracking.release_lock()
        
        return Response({
            'message': 'Lock released successfully.'
        })


class MarkSubmittedView(APIView):
    """
    Manually mark an example as submitted.
    Used when auto-tracking doesn't catch the save.
    """
    permission_classes = [IsAuthenticated, IsProjectMember]
    
    def post(self, request, project_id, example_id):
        """Mark example as submitted."""
        example = get_object_or_404(
            Example,
            id=example_id,
            project_id=project_id
        )
        project = example.project
        
        tracking = get_or_create_tracking(project, example)
        tracking.mark_submitted(request.user)
        
        return Response({
            'message': 'Example marked as submitted.',
            'status': tracking.status,
            'annotated_by': request.user.username,
            'annotated_at': tracking.annotated_at.isoformat()
        })

