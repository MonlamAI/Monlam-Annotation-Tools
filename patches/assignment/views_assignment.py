"""
Assignment System Views for Doccano.

This file adds assignment API endpoints.
Place in: /doccano/backend/examples/views_assignment.py
"""

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from examples.models import Example
from projects.models import Member
from projects.permissions import IsProjectAdmin, IsProjectMember


class BulkAssignmentView(APIView):
    """
    Bulk assign examples to a user.
    
    POST /v1/projects/{project_id}/assignment/bulk/
    {
        "example_ids": [1, 2, 3],
        "user_id": 5
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, project_id):
        # Check if user is project admin
        member = Member.objects.filter(
            project_id=project_id,
            user=request.user
        ).first()
        
        if not member or member.role.name.lower() != 'project_admin':
            return Response(
                {'error': 'Only project admins can assign tasks'},
                status=status.HTTP_403_FORBIDDEN
            )
        
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
    
    POST /v1/projects/{project_id}/assignment/auto/
    {
        "user_ids": [1, 2, 3, 4, 5]
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, project_id):
        # Check if user is project admin
        member = Member.objects.filter(
            project_id=project_id,
            user=request.user
        ).first()
        
        if not member or member.role.name.lower() != 'project_admin':
            return Response(
                {'error': 'Only project admins can assign tasks'},
                status=status.HTTP_403_FORBIDDEN
            )
        
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
            return Response({
                'message': 'No unassigned examples',
                'assigned': 0
            })
        
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
            'distribution': {str(uid): len(eids) for uid, eids in assignments.items()}
        })


class AssignmentStatsView(APIView):
    """
    Get assignment statistics for a project.
    
    GET /v1/projects/{project_id}/assignment/stats/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, project_id):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Overall stats
        stats = Example.objects.filter(project_id=project_id).aggregate(
            total=Count('id'),
            unassigned=Count('id', filter=Q(assigned_to__isnull=True)),
            assigned=Count('id', filter=Q(assignment_status='assigned')),
            in_progress=Count('id', filter=Q(assignment_status='in_progress')),
            submitted=Count('id', filter=Q(assignment_status='submitted')),
            approved=Count('id', filter=Q(assignment_status='approved')),
            rejected=Count('id', filter=Q(assignment_status='rejected')),
        )
        
        # Per-user stats
        by_user = []
        user_stats = Example.objects.filter(
            project_id=project_id,
            assigned_to__isnull=False
        ).values('assigned_to', 'assigned_to__username').annotate(
            total=Count('id'),
            assigned=Count('id', filter=Q(assignment_status='assigned')),
            in_progress=Count('id', filter=Q(assignment_status='in_progress')),
            submitted=Count('id', filter=Q(assignment_status='submitted')),
            approved=Count('id', filter=Q(assignment_status='approved')),
            rejected=Count('id', filter=Q(assignment_status='rejected')),
        )
        
        for stat in user_stats:
            by_user.append({
                'id': stat['assigned_to'],
                'username': stat['assigned_to__username'],
                'total': stat['total'],
                'assigned': stat['assigned'],
                'in_progress': stat['in_progress'],
                'submitted': stat['submitted'],
                'approved': stat['approved'],
                'rejected': stat['rejected'],
            })
        
        return Response({
            'stats': stats,
            'by_user': by_user
        })


class ReviewQueueView(APIView):
    """
    Get items pending review.
    
    GET /v1/projects/{project_id}/review/queue/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, project_id):
        # Check if user is approver or admin
        member = Member.objects.filter(
            project_id=project_id,
            user=request.user
        ).first()
        
        if not member:
            return Response(
                {'error': 'Not a project member'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        role_name = member.role.name.lower()
        if role_name not in ['project_admin', 'annotation_approver']:
            return Response(
                {'error': 'Only approvers can access review queue'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        items = Example.objects.filter(
            project_id=project_id,
            assignment_status='submitted'
        ).select_related('assigned_to').order_by('created_at')
        
        data = []
        for item in items:
            filename_str = str(item.filename)
            if filename_str.startswith('http://') or filename_str.startswith('https://'):
                file_url = filename_str
            elif item.filename:
                file_url = item.filename.url
            else:
                file_url = None
            
            data.append({
                'id': item.id,
                'filename': file_url,
                'text': item.text,
                'assigned_to': item.assigned_to.username if item.assigned_to else None,
                'assignment_status': item.assignment_status,
                'created_at': item.created_at.isoformat(),
            })
        
        return Response(data)


class ReviewActionView(APIView):
    """
    Approve or reject an example.
    
    POST /v1/projects/{project_id}/review/{example_id}/
    {
        "action": "approve" | "reject",
        "notes": "Optional feedback"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, project_id, example_id):
        # Check if user is approver or admin
        member = Member.objects.filter(
            project_id=project_id,
            user=request.user
        ).first()
        
        if not member:
            return Response(
                {'error': 'Not a project member'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        role_name = member.role.name.lower()
        if role_name not in ['project_admin', 'annotation_approver']:
            return Response(
                {'error': 'Only approvers can review'},
                status=status.HTTP_403_FORBIDDEN
            )
        
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


class SubmitForReviewView(APIView):
    """
    Annotator submits their work for review.
    
    POST /v1/projects/{project_id}/examples/{example_id}/submit/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, project_id, example_id):
        try:
            example = Example.objects.get(
                id=example_id,
                project_id=project_id,
                assigned_to=request.user
            )
        except Example.DoesNotExist:
            return Response(
                {'error': 'Example not found or not assigned to you'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        example.assignment_status = 'submitted'
        example.save()
        
        return Response({
            'id': example.id,
            'status': example.assignment_status
        })

