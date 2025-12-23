"""
Assignment System - Views Patches for Doccano

This replaces/patches the example list view to filter by assignment.
Annotators ONLY see their assigned items.
Admins/Approvers see all items.
"""

from django.db.models import Q
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from examples.models import Example
from projects.permissions import IsProjectMember


class AssignmentFilterMixin:
    """
    Mixin to filter examples by assignment.
    
    - Project Admin: sees all
    - Annotation Approver: sees all
    - Annotator: sees only assigned items
    """
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        project = self.get_project()
        
        # Check user's role in project
        member = project.members.filter(user=user).first()
        
        if not member:
            return queryset.none()
        
        role_name = member.role.name.lower()
        
        # Admins and Approvers see everything
        if role_name in ['project_admin', 'annotation_approver', 'admin']:
            return queryset
        
        # Annotators only see their assignments
        if role_name == 'annotator':
            return queryset.filter(
                Q(assigned_to=user) | Q(assigned_to__isnull=True, assignment_status='unassigned')
            )
        
        # Default: only assigned items
        return queryset.filter(assigned_to=user)


class BulkAssignmentView(APIView):
    """
    API endpoint for bulk task assignment.
    Only Project Admins can assign tasks.
    
    POST /projects/{project_id}/examples/assign/
    {
        "example_ids": [1, 2, 3, 4, 5],
        "user_id": 10
    }
    """
    permission_classes = [IsAuthenticated, IsProjectMember]
    
    def post(self, request, project_id):
        example_ids = request.data.get('example_ids', [])
        user_id = request.data.get('user_id')
        
        if not example_ids:
            return Response(
                {'error': 'No examples provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update examples
        updated = Example.objects.filter(
            id__in=example_ids,
            project_id=project_id
        ).update(
            assigned_to_id=user_id,
            assignment_status='assigned' if user_id else 'unassigned'
        )
        
        return Response({
            'assigned': updated,
            'user_id': user_id
        })


class AutoAssignView(APIView):
    """
    Auto-assign unassigned examples evenly among annotators.
    
    POST /projects/{project_id}/examples/auto-assign/
    {
        "user_ids": [1, 2, 3, 4, 5]  // Annotators to assign to
    }
    """
    permission_classes = [IsAuthenticated, IsProjectMember]
    
    def post(self, request, project_id):
        user_ids = request.data.get('user_ids', [])
        
        if not user_ids:
            return Response(
                {'error': 'No users provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get unassigned examples
        unassigned = list(Example.objects.filter(
            project_id=project_id,
            assigned_to__isnull=True
        ).values_list('id', flat=True))
        
        if not unassigned:
            return Response({'message': 'No unassigned examples', 'assigned': 0})
        
        # Distribute evenly
        assignments = {}
        for i, example_id in enumerate(unassigned):
            user_id = user_ids[i % len(user_ids)]
            if user_id not in assignments:
                assignments[user_id] = []
            assignments[user_id].append(example_id)
        
        # Bulk update
        total_assigned = 0
        for user_id, example_ids in assignments.items():
            count = Example.objects.filter(id__in=example_ids).update(
                assigned_to_id=user_id,
                assignment_status='assigned'
            )
            total_assigned += count
        
        return Response({
            'assigned': total_assigned,
            'distribution': {uid: len(eids) for uid, eids in assignments.items()}
        })


class ReviewQueueView(APIView):
    """
    Get items pending review (submitted but not approved).
    
    GET /projects/{project_id}/examples/review-queue/
    """
    permission_classes = [IsAuthenticated, IsProjectMember]
    
    def get(self, request, project_id):
        items = Example.objects.filter(
            project_id=project_id,
            assignment_status='submitted'
        ).select_related('assigned_to')
        
        data = [{
            'id': item.id,
            'filename': str(item.filename),
            'text': item.text,
            'assigned_to': item.assigned_to.username if item.assigned_to else None,
            'assignment_status': item.assignment_status,
        } for item in items]
        
        return Response(data)


class ReviewActionView(APIView):
    """
    Approve or reject an example.
    
    POST /projects/{project_id}/examples/{example_id}/review/
    {
        "action": "approve" | "reject",
        "notes": "Optional review notes"
    }
    """
    permission_classes = [IsAuthenticated, IsProjectMember]
    
    def post(self, request, project_id, example_id):
        from django.utils import timezone
        
        action = request.data.get('action')
        notes = request.data.get('notes', '')
        
        if action not in ['approve', 'reject']:
            return Response(
                {'error': 'Action must be "approve" or "reject"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            example = Example.objects.get(id=example_id, project_id=project_id)
        except Example.DoesNotExist:
            return Response(
                {'error': 'Example not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        example.reviewed_by = request.user
        example.reviewed_at = timezone.now()
        example.review_notes = notes
        example.assignment_status = 'approved' if action == 'approve' else 'rejected'
        example.save()
        
        return Response({
            'id': example.id,
            'status': example.assignment_status,
            'reviewed_by': request.user.username
        })


# URL patterns to add to examples/urls.py:
"""
from .views_patch import BulkAssignmentView, AutoAssignView, ReviewQueueView, ReviewActionView

urlpatterns += [
    path('projects/<int:project_id>/examples/assign/', BulkAssignmentView.as_view()),
    path('projects/<int:project_id>/examples/auto-assign/', AutoAssignView.as_view()),
    path('projects/<int:project_id>/examples/review-queue/', ReviewQueueView.as_view()),
    path('projects/<int:project_id>/examples/<int:example_id>/review/', ReviewActionView.as_view()),
]
"""

