"""
API Endpoints for Annotation Tracking

Provides:
- Auto-tracking when annotations are submitted
- Approve/Reject endpoints for reviewers
- Status tracking
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
from .simple_tracking import AnnotationTracking


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
                    tracking.save()
                
                return Response({
                    'success': True,
                    'status': tracking.status,
                    'annotated_by': tracking.annotated_by.username if tracking.annotated_by else None,
                    'annotated_at': tracking.annotated_at
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
        """
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
            "review_notes": "Needs correction"
        }
        """
        review_notes = request.data.get('review_notes', '')
        if not review_notes:
            return Response(
                {'error': 'review_notes is required for rejection'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
        
        GET /v1/projects/{project_id}/tracking/{example_id}/status/
        """
        try:
            tracking = AnnotationTracking.objects.filter(
                project_id=project_id,
                example_id=pk
            ).select_related('annotated_by', 'reviewed_by').first()
            
            if not tracking:
                return Response({
                    'status': 'pending',
                    'annotated_by': None,
                    'reviewed_by': None
                })
            
            return Response({
                'status': tracking.status,
                'annotated_by': tracking.annotated_by.username if tracking.annotated_by else None,
                'annotated_at': tracking.annotated_at,
                'reviewed_by': tracking.reviewed_by.username if tracking.reviewed_by else None,
                'reviewed_at': tracking.reviewed_at,
                'review_notes': tracking.review_notes
            })
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

