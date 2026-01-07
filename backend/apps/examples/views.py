"""
Example views for API.
"""

from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404

from .models import Example, Comment
from .serializers import (
    ExampleSerializer, EnhancedExampleSerializer,
    ExampleCreateSerializer, ExampleBulkCreateSerializer,
    CommentSerializer
)
from .filters import AnnotationVisibilityFilter, StatusFilter, AnnotatedByFilter
from apps.projects.models import Project
from apps.projects.permissions import IsProjectMember, IsProjectAdmin


class ExampleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing examples within a project.
    Includes visibility filtering based on user role.
    """
    permission_classes = [IsAuthenticated, IsProjectMember]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [
        AnnotationVisibilityFilter,
        StatusFilter,
        AnnotatedByFilter,
    ]
    
    def get_project(self):
        project_id = self.kwargs.get('project_id')
        return get_object_or_404(Project, id=project_id)
    
    def get_queryset(self):
        project = self.get_project()
        return Example.objects.filter(project=project).order_by('id')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ExampleCreateSerializer
        # Use enhanced serializer with tracking data
        return EnhancedExampleSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['project'] = self.get_project()
        return context
    
    def perform_create(self, serializer):
        project = self.get_project()
        serializer.save(project=project)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsProjectAdmin])
    def bulk_create(self, request, project_id=None):
        """Bulk create examples."""
        project = self.get_project()
        serializer = ExampleBulkCreateSerializer(
            data=request.data,
            context={'project': project, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        examples = serializer.save()
        
        return Response({
            'created': len(examples),
            'message': f'Created {len(examples)} examples.'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['delete'], permission_classes=[IsAuthenticated, IsProjectAdmin])
    def bulk_delete(self, request, project_id=None):
        """Bulk delete examples."""
        project = self.get_project()
        example_ids = request.data.get('ids', [])
        
        if not example_ids:
            return Response(
                {'error': 'No example IDs provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deleted_count, _ = Example.objects.filter(
            project=project,
            id__in=example_ids
        ).delete()
        
        return Response({
            'deleted': deleted_count,
            'message': f'Deleted {deleted_count} examples.'
        })
    
    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, project_id=None, pk=None):
        """Get or add comments for an example."""
        example = self.get_object()
        
        if request.method == 'GET':
            comments = example.comments.all()
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            serializer = CommentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(example=example, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request, project_id=None):
        """Get example statistics for the project."""
        project = self.get_project()
        
        from apps.monlam_tracking.models import AnnotationTracking
        from django.db.models import Count
        
        total_examples = Example.objects.filter(project=project).count()
        
        # Status counts
        status_counts = AnnotationTracking.objects.filter(
            project=project
        ).values('status').annotate(count=Count('id'))
        
        status_dict = {item['status']: item['count'] for item in status_counts}
        
        # Calculate pending (examples without tracking)
        tracked_count = AnnotationTracking.objects.filter(project=project).count()
        pending_count = total_examples - tracked_count
        
        return Response({
            'total': total_examples,
            'pending': pending_count,
            'in_progress': status_dict.get('in_progress', 0),
            'submitted': status_dict.get('submitted', 0),
            'approved': status_dict.get('approved', 0),
            'rejected': status_dict.get('rejected', 0),
        })

