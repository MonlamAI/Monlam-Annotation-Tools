"""
Assignment Views

REST API views for the Assignment system.
These extend Doccano's functionality without replacing core views.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

from .serializers import (
    AssignmentSerializer,
    BulkAssignmentSerializer,
    AssignmentStatsSerializer
)


class AssignmentViewSet(viewsets.ViewSet):
    """
    ViewSet for managing task assignments.
    
    Endpoints:
    - GET /projects/{project_id}/assignments/ - List all assignments
    - GET /projects/{project_id}/assignments/my/ - Get my assignments
    - POST /projects/{project_id}/assignments/bulk/ - Bulk assign
    - POST /projects/{project_id}/assignments/{id}/start/ - Start working
    - POST /projects/{project_id}/assignments/{id}/submit/ - Submit for review
    - POST /projects/{project_id}/assignments/{id}/approve/ - Approve
    - POST /projects/{project_id}/assignments/{id}/reject/ - Reject
    - GET /projects/{project_id}/assignments/stats/ - Get statistics
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_project(self, project_id):
        """Get project and check access."""
        from projects.models import Project
        return get_object_or_404(Project, pk=project_id)
    
    def list(self, request, project_id):
        """List all assignments in a project."""
        from .models_separate import Assignment
        
        project = self.get_project(project_id)
        assignments = Assignment.objects.filter(project=project, is_active=True)
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            assignments = assignments.filter(status=status_filter)
        
        # Filter by user if provided
        user_id = request.query_params.get('user_id')
        if user_id:
            assignments = assignments.filter(assigned_to_id=user_id)
        
        serializer = AssignmentSerializer(assignments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my(self, request, project_id):
        """Get current user's assignments."""
        from .models_separate import Assignment
        
        project = self.get_project(project_id)
        assignments = Assignment.objects.filter(
            project=project,
            assigned_to=request.user,
            is_active=True
        )
        
        serializer = AssignmentSerializer(assignments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk(self, request, project_id):
        """Bulk assign examples to a user."""
        from .models_separate import Assignment
        from examples.models import Example
        from django.contrib.auth import get_user_model
        
        project = self.get_project(project_id)
        User = get_user_model()
        
        serializer = BulkAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        example_ids = serializer.validated_data['example_ids']
        assigned_to_id = serializer.validated_data['assigned_to_id']
        
        # Get examples and user
        examples = Example.objects.filter(id__in=example_ids, project=project)
        user = get_object_or_404(User, pk=assigned_to_id)
        
        # Bulk assign
        assignments = Assignment.bulk_assign(
            examples=examples,
            user=user,
            assigned_by=request.user,
            project=project
        )
        
        return Response({
            'message': f'Assigned {len(assignments)} examples to {user.username}',
            'count': len(assignments)
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def start(self, request, project_id, pk):
        """Mark assignment as in progress."""
        from .models_separate import Assignment
        
        assignment = get_object_or_404(Assignment, pk=pk, project_id=project_id)
        
        # Verify user is the assignee
        if assignment.assigned_to != request.user:
            return Response(
                {'error': 'You are not assigned to this task'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        assignment.start()
        return Response({'status': 'in_progress'})
    
    @action(detail=True, methods=['post'])
    def submit(self, request, project_id, pk):
        """Submit assignment for review."""
        from .models_separate import Assignment
        
        assignment = get_object_or_404(Assignment, pk=pk, project_id=project_id)
        
        # Verify user is the assignee
        if assignment.assigned_to != request.user:
            return Response(
                {'error': 'You are not assigned to this task'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        assignment.submit()
        return Response({'status': 'submitted'})
    
    @action(detail=True, methods=['post'])
    def approve(self, request, project_id, pk):
        """Approve an assignment (reviewer only)."""
        from .models_separate import Assignment
        
        assignment = get_object_or_404(Assignment, pk=pk, project_id=project_id)
        notes = request.data.get('notes', '')
        
        assignment.approve(reviewer=request.user, notes=notes)
        return Response({'status': 'approved'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, project_id, pk):
        """Reject an assignment (reviewer only)."""
        from .models_separate import Assignment
        
        assignment = get_object_or_404(Assignment, pk=pk, project_id=project_id)
        notes = request.data.get('notes', '')
        
        assignment.reject(reviewer=request.user, notes=notes)
        return Response({'status': 'rejected'})
    
    @action(detail=False, methods=['get'])
    def stats(self, request, project_id):
        """Get assignment statistics by user."""
        from .models_separate import Assignment
        from django.contrib.auth import get_user_model
        
        project = self.get_project(project_id)
        User = get_user_model()
        
        # Get stats per user
        stats = Assignment.objects.filter(
            project=project,
            is_active=True
        ).values('assigned_to__id', 'assigned_to__username').annotate(
            total_assigned=Count('id'),
            in_progress=Count('id', filter=Q(status='in_progress')),
            submitted=Count('id', filter=Q(status='submitted')),
            approved=Count('id', filter=Q(status='approved')),
            rejected=Count('id', filter=Q(status='rejected'))
        )
        
        # Add completion rate
        result = []
        for s in stats:
            if s['assigned_to__id']:
                total = s['total_assigned']
                completed = s['submitted'] + s['approved']
                result.append({
                    'user_id': s['assigned_to__id'],
                    'username': s['assigned_to__username'],
                    'total_assigned': total,
                    'in_progress': s['in_progress'],
                    'submitted': s['submitted'],
                    'approved': s['approved'],
                    'rejected': s['rejected'],
                    'completion_rate': round(completed / total * 100, 1) if total > 0 else 0
                })
        
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def unassigned(self, request, project_id):
        """Get unassigned examples in a project."""
        from .models_separate import Assignment
        from examples.models import Example
        
        project = self.get_project(project_id)
        
        # Get example IDs that have active assignments
        assigned_example_ids = Assignment.objects.filter(
            project=project,
            is_active=True
        ).values_list('example_id', flat=True)
        
        # Get unassigned examples
        unassigned = Example.objects.filter(
            project=project
        ).exclude(
            id__in=assigned_example_ids
        ).count()
        
        return Response({
            'unassigned_count': unassigned,
            'total_count': Example.objects.filter(project=project).count()
        })

