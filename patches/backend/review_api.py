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


def get_current_example(request, project_id):
    """
    Get the current example ID for the user in a project.
    Uses Doccano's logic to find the next unconfirmed example.
    
    GET /v1/projects/{project_id}/current-example/
    Returns: {"example_id": 123, "total": 54, "position": 2}
    """
    from examples.models import Example, ExampleState
    from projects.models import Project
    
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        return JsonResponse({'error': 'Project not found'}, status=404)
    
    # Get all examples for this project
    examples = Example.objects.filter(project=project).order_by('id')
    total = examples.count()
    
    if total == 0:
        return JsonResponse({'error': 'No examples in project'}, status=404)
    
    # Find the first example that:
    # 1. User hasn't confirmed yet (if collaborative mode)
    # 2. Or any unconfirmed example
    if project.collaborative_annotation:
        # In collaborative mode, find examples user hasn't confirmed
        confirmed_ids = ExampleState.objects.filter(
            confirmed_by=request.user
        ).values_list('example_id', flat=True)
        current_example = examples.exclude(id__in=confirmed_ids).first()
    else:
        # In individual mode, find any unconfirmed example
        confirmed_ids = ExampleState.objects.filter(
            example__project=project
        ).values_list('example_id', flat=True)
        current_example = examples.exclude(id__in=confirmed_ids).first()
    
    # If all are confirmed, return the last one
    if not current_example:
        current_example = examples.last()
    
    # Calculate position
    position = list(examples.values_list('id', flat=True)).index(current_example.id) + 1
    
    return JsonResponse({
        'example_id': current_example.id,
        'total': total,
        'position': position,
        'filename': str(current_example.filename) if current_example.filename else None
    })


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


@csrf_protect
@require_POST
def review_current_example_simple(request, project_id):
    """
    Simple endpoint: Review current example without needing example_id.
    Frontend only needs to send project_id and action.
    Backend finds the current example automatically.
    
    POST /v1/projects/{project_id}/review-current/
    Body: {"action": "approve" | "reject", "notes": "optional"}
    
    This is the preferred endpoint - no example ID needed!
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
    except Project.DoesNotExist:
        return JsonResponse({'error': 'Project not found'}, status=404)
    
    # Strategy 1: Get from URL if example_id is in path (if called from example-specific endpoint)
    example_id_from_url = None
    if hasattr(request, 'resolver_match') and request.resolver_match:
        kwargs = request.resolver_match.kwargs
        example_id_from_url = kwargs.get('example_id')
    
    # Strategy 2: Find current example for user (unconfirmed examples)
    current_example = None
    
    if example_id_from_url:
        try:
            current_example = Example.objects.get(pk=example_id_from_url, project=project)
        except Example.DoesNotExist:
            pass
    
    if not current_example:
        # Get examples ordered by ID
        examples = Example.objects.filter(project=project).order_by('id')
        
        if project.collaborative_annotation:
            # In collaborative mode: find examples user hasn't confirmed
            confirmed_ids = ExampleState.objects.filter(
                confirmed_by=request.user,
                example__project=project
            ).values_list('example_id', flat=True)
            current_example = examples.exclude(id__in=confirmed_ids).first()
        else:
            # In individual mode: find any unconfirmed example
            confirmed_ids = ExampleState.objects.filter(
                example__project=project
            ).values_list('example_id', flat=True)
            current_example = examples.exclude(id__in=confirmed_ids).first()
        
        # If all confirmed, get the last one (or first one)
        if not current_example:
            current_example = examples.first()
    
    if not current_example:
        return JsonResponse({'error': 'No examples found in project'}, status=404)
    
    # Now review this example
    if action == 'approve':
        current_example.annotations_approved_by = request.user
        current_example.save(update_fields=['annotations_approved_by'])
        
        ExampleState.objects.update_or_create(
            example=current_example,
            confirmed_by=request.user,
            defaults={'confirmed_at': timezone.now()}
        )
        review_text = f"[APPROVED] {notes}" if notes else "[APPROVED]"
    else:
        current_example.annotations_approved_by = None
        current_example.save(update_fields=['annotations_approved_by'])
        ExampleState.objects.filter(example=current_example).delete()
        review_text = f"[REJECTED] {notes}" if notes else "[REJECTED] Please revise"
    
    Comment.objects.create(
        example=current_example,
        user=request.user,
        text=review_text
    )
    
    return JsonResponse({
        'status': 'success',
        'action': action,
        'example_id': current_example.id,
        'reviewed_by': request.user.username,
        'message': f'Successfully {action}d example {current_example.id}'
    })



