"""
Review API for Doccano

Provides approve/reject endpoints for annotation review workflow.
This extends Doccano's functionality without replacing core views.

Place in: /doccano/backend/examples/review_api.py
Then add to urls.py:
    from examples.review_api import ReviewViewSet
    path('projects/<int:project_id>/examples/<int:example_id>/review/', 
         ReviewViewSet.as_view({'post': 'review'}), name='example-review'),
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class ReviewViewSet(viewsets.ViewSet):
    """
    ViewSet for review actions on examples.
    
    Endpoints:
    - POST /projects/{project_id}/examples/{example_id}/review/
      Body: {"action": "approve" | "reject", "notes": "optional notes"}
    """
    
    permission_classes = [IsAuthenticated]
    
    def review(self, request, project_id, example_id):
        """
        Approve or reject an example's annotation.
        
        This updates the Example's annotations_approved_by field
        and optionally creates a comment with review notes.
        """
        from examples.models import Example, ExampleState, Comment
        from projects.models import Project
        
        # Get project and example
        project = get_object_or_404(Project, pk=project_id)
        example = get_object_or_404(Example, pk=example_id, project=project)
        
        # Parse request
        action = request.data.get('action', '').lower()
        notes = request.data.get('notes', '')
        
        if action not in ['approve', 'reject']:
            return Response(
                {'error': 'Action must be "approve" or "reject"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update example
        if action == 'approve':
            example.annotations_approved_by = request.user
            example.save(update_fields=['annotations_approved_by'])
            
            # Also create/update ExampleState to mark as confirmed
            ExampleState.objects.update_or_create(
                example=example,
                confirmed_by=request.user,
                defaults={'confirmed_at': timezone.now()}
            )
            
            review_text = f"[APPROVED] {notes}" if notes else "[APPROVED]"
        else:
            # For rejection, clear the approval
            example.annotations_approved_by = None
            example.save(update_fields=['annotations_approved_by'])
            
            # Remove confirmation state if exists
            ExampleState.objects.filter(example=example).delete()
            
            review_text = f"[REJECTED] {notes}" if notes else "[REJECTED] Please revise"
        
        # Add comment with review notes
        if notes or action == 'reject':
            Comment.objects.create(
                example=example,
                user=request.user,
                text=review_text
            )
        
        return Response({
            'status': 'success',
            'action': action,
            'example_id': example_id,
            'reviewed_by': request.user.username,
            'reviewed_at': timezone.now().isoformat()
        })
    
    def get_review_status(self, request, project_id, example_id):
        """
        Get the current review status of an example.
        """
        from examples.models import Example, ExampleState, Comment
        from projects.models import Project
        
        project = get_object_or_404(Project, pk=project_id)
        example = get_object_or_404(Example, pk=example_id, project=project)
        
        # Check for approval
        is_approved = example.annotations_approved_by is not None
        approved_by = example.annotations_approved_by.username if example.annotations_approved_by else None
        
        # Check for rejection in comments
        rejection_comment = Comment.objects.filter(
            example=example,
            text__startswith='[REJECTED]'
        ).order_by('-created_at').first()
        
        if is_approved:
            status_text = 'approved'
        elif rejection_comment:
            status_text = 'rejected'
        else:
            # Check if confirmed by annotator
            state = ExampleState.objects.filter(example=example).first()
            status_text = 'submitted' if state else 'pending'
        
        return Response({
            'example_id': example_id,
            'status': status_text,
            'approved_by': approved_by,
            'rejection_notes': rejection_comment.text if rejection_comment else None
        })


# Alternative: Simple function-based view for easy integration
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
import json


@csrf_protect
@require_POST
def review_example(request, project_id, example_id):
    """
    Simple function-based view for reviewing examples.
    
    POST /api/review/{project_id}/{example_id}/
    Body: {"action": "approve" | "reject", "notes": "optional"}
    """
    from examples.models import Example, ExampleState, Comment
    from projects.models import Project
    
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        data = json.loads(request.body)
        action = data.get('action', '').lower()
        notes = data.get('notes', '')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    if action not in ['approve', 'reject']:
        return JsonResponse({'error': 'Action must be "approve" or "reject"'}, status=400)
    
    try:
        project = Project.objects.get(pk=project_id)
        example = Example.objects.get(pk=example_id, project=project)
    except (Project.DoesNotExist, Example.DoesNotExist):
        return JsonResponse({'error': 'Not found'}, status=404)
    
    if action == 'approve':
        example.annotations_approved_by = request.user
        example.save(update_fields=['annotations_approved_by'])
        
        ExampleState.objects.update_or_create(
            example=example,
            confirmed_by=request.user,
            defaults={'confirmed_at': timezone.now()}
        )
        review_text = f"[APPROVED] {notes}" if notes else "[APPROVED]"
    else:
        example.annotations_approved_by = None
        example.save(update_fields=['annotations_approved_by'])
        ExampleState.objects.filter(example=example).delete()
        review_text = f"[REJECTED] {notes}" if notes else "[REJECTED] Please revise"
    
    Comment.objects.create(
        example=example,
        user=request.user,
        text=review_text
    )
    
    return JsonResponse({
        'status': 'success',
        'action': action,
        'example_id': example_id,
        'reviewed_by': request.user.username
    })

