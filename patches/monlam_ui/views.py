"""
Monlam UI Views

Django views that integrate with Doccano's existing authentication system.
These views serve enhanced UI components for the completion tracking system.
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q


from django.views import View
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.urls import reverse


class DatasetRedirectView(View):
    """
    Redirect standard dataset page to enhanced dataset view.
    Intercepts /projects/{id}/dataset and redirects to /monlam/{id}/dataset-enhanced/
    
    EXCEPTION: Project Admins (role=3) are NOT redirected - they need
    the original dataset page for upload/download functionality.
    """
    def get(self, request, project_id):
        # Check if user is a Project Admin for this project
        try:
            from projects.models import Project
            from roles.models import RoleMember
            
            PROJECT_ADMIN_ROLE = 3  # Doccano's Project Admin role ID
            
            # Check if user is project admin
            is_admin = RoleMember.objects.filter(
                project_id=project_id,
                member_id=request.user.id,
                role_id=PROJECT_ADMIN_ROLE
            ).exists()
            
            if is_admin:
                # Project Admins should NOT be redirected
                # Return None to let the request continue to Doccano's original view
                # We can't directly call Doccano's view, so we'll raise an exception
                # that signals "let the original view handle this"
                from django.http import Http404
                raise Http404("Let original view handle this")
            
        except Exception as e:
            # If anything goes wrong, redirect to enhanced view (safer default)
            print(f"[Monlam] Error checking admin role: {e}")
        
        # Non-admins: redirect to enhanced view
        return redirect(f'/monlam/{project_id}/dataset-enhanced/')


class MetricsRedirectView(View):
    """
    Redirect standard metrics page to completion dashboard.
    Intercepts /projects/{id}/metrics and redirects to /monlam/{project_id}/completion/
    """
    def get(self, request, project_id):
        return redirect(f'/monlam/{project_id}/completion/')


@login_required
def project_landing(request, project_id):
    """
    Landing page for Monlam custom features.
    Shows cards linking to:
    - Enhanced Dataset View
    - Completion Dashboard
    - Standard Project
    """
    from projects.models import Project
    
    project = get_object_or_404(Project, pk=project_id)
    
    # Check access
    if not request.user.is_superuser:
        if not project.members.filter(id=request.user.id).exists():
            return render(request, '403.html', status=403)
    
    context = {
        'project': project,
        'project_id': project_id,
    }
    
    return render(request, 'monlam_ui/project_landing.html', context)


@login_required
def completion_dashboard(request, project_id):
    """
    Completion Dashboard for Project Managers
    
    Shows:
    - Overall project completion statistics
    - Per-annotator progress
    - Per-approver review status
    - Examples completion matrix
    """
    from projects.models import Project
    from assignment.models_separate import Assignment
    
    project = get_object_or_404(Project, pk=project_id)
    
    # Check if user has access to this project
    if not request.user.is_superuser:
        # Check if user is a member of this project
        if not project.members.filter(id=request.user.id).exists():
            return render(request, '403.html', status=403)
    
    context = {
        'project': project,
        'project_id': project_id,
    }
    
    return render(request, 'monlam_ui/completion_dashboard.html', context)


@login_required
def enhanced_dataset(request, project_id):
    """
    Enhanced Dataset View with Assignment Status
    
    Shows the dataset table with additional columns:
    - Assigned To
    - Annotation Status
    - Approval Status
    """
    from projects.models import Project
    
    project = get_object_or_404(Project, pk=project_id)
    
    # Check access
    if not request.user.is_superuser:
        if not project.members.filter(id=request.user.id).exists():
            return render(request, '403.html', status=403)
    
    # Get project type and convert to URL format
    # Database has: Speech2text, SequenceLabeling, etc.
    # URL needs: speech-to-text, sequence-labeling, etc.
    project_type_raw = project.project_type
    
    # Convert to URL-friendly format
    type_mapping = {
        'Speech2text': 'speech-to-text',
        'DocumentClassification': 'document-classification',
        'SequenceLabeling': 'sequence-labeling',
        'Seq2seq': 'sequence-to-sequence',
        'IntentDetectionAndSlotFilling': 'intent-detection-and-slot-filling',
        'ImageClassification': 'image-classification',
        'ImageCaptioning': 'image-captioning',
        'BoundingBox': 'bounding-box',
        'Segmentation': 'segmentation',
    }
    
    project_type = type_mapping.get(project_type_raw, project_type_raw.lower())
    
    context = {
        'project': project,
        'project_id': project_id,
        'project_type': project_type,
    }
    
    return render(request, 'monlam_ui/enhanced_dataset.html', context)


@login_required
def annotation_with_approval(request, project_id, example_id):
    """
    Annotation Page with Approval Interface
    
    Enhanced annotation view that shows:
    - Approval status chain (Annotator → Approver → Project Manager)
    - Approve/Reject buttons for approvers and project managers
    - Audio auto-loop for STT projects
    """
    from projects.models import Project
    from examples.models import Example
    from assignment.models_separate import Assignment
    
    project = get_object_or_404(Project, pk=project_id)
    example = get_object_or_404(Example, pk=example_id, project=project)
    
    # Check access
    if not request.user.is_superuser:
        if not project.members.filter(id=request.user.id).exists():
            return render(request, '403.html', status=403)
    
    # Get assignment for this example
    try:
        assignment = Assignment.objects.get(project=project, example=example, is_active=True)
    except Assignment.DoesNotExist:
        assignment = None
    
    context = {
        'project': project,
        'example': example,
        'assignment': assignment,
        'project_id': project_id,
        'example_id': example_id,
    }
    
    return render(request, 'monlam_ui/annotation_with_approval.html', context)


@login_required
@require_http_methods(["GET"])
def api_dataset_assignments(request, project_id):
    """
    API endpoint to get all assignments for dataset view
    Returns assignment data for each example in the project
    """
    from projects.models import Project
    from assignment.models_separate import Assignment
    from assignment.serializers import AssignmentSerializer
    
    project = get_object_or_404(Project, pk=project_id)
    
    # Check access
    if not request.user.is_superuser:
        if not project.members.filter(id=request.user.id).exists():
            return JsonResponse({'error': 'Permission denied'}, status=403)
    
    assignments = Assignment.objects.filter(
        project=project,
        is_active=True
    ).select_related('assigned_to', 'reviewed_by')
    
    serializer = AssignmentSerializer(assignments, many=True)
    
    return JsonResponse({
        'count': assignments.count(),
        'results': serializer.data
    })


@login_required
@require_http_methods(["GET"])
def api_completion_stats(request, project_id):
    """
    API endpoint for completion statistics
    Used by the completion dashboard
    
    Uses BOTH:
    - ExampleState (Doccano's native confirmation via checkmark)
    - AnnotationTracking (our approve/reject workflow)
    """
    from projects.models import Project
    from examples.models import ExampleState
    from assignment.simple_tracking import AnnotationTracking
    
    project = get_object_or_404(Project, pk=project_id)
    
    # Check access
    if not request.user.is_superuser:
        if not project.members.filter(id=request.user.id).exists():
            return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Get overall stats
    total_examples = project.examples.count()
    
    # Get CONFIRMED examples from Doccano's ExampleState (checkmark clicked)
    example_ids = list(project.examples.values_list('id', flat=True))
    confirmed_states = ExampleState.objects.filter(
        example_id__in=example_ids
    ).select_related('confirmed_by')
    confirmed_count = confirmed_states.count()
    
    # Get tracking stats (our approve/reject workflow)
    tracking = AnnotationTracking.objects.filter(project=project)
    approved_count = tracking.filter(status='approved').count()
    rejected_count = tracking.filter(status='rejected').count()
    
    # Submitted = confirmed but not yet approved/rejected
    submitted_count = confirmed_count - approved_count - rejected_count
    if submitted_count < 0:
        submitted_count = 0
    
    pending_count = total_examples - confirmed_count
    
    # Per-annotator stats from ExampleState (who confirmed each example)
    annotator_dict = {}
    for state in confirmed_states:
        if state.confirmed_by:
            username = state.confirmed_by.username
            user_id = state.confirmed_by.id
            if username not in annotator_dict:
                annotator_dict[username] = {
                    'annotated_by__id': user_id,
                    'annotated_by__username': username,
                    'total_annotated': 0,
                    'submitted': 0,
                    'approved': 0,
                    'rejected': 0,
                }
            annotator_dict[username]['total_annotated'] += 1
    
    # Add tracking status to annotator stats
    for t in tracking:
        if t.annotated_by:
            username = t.annotated_by.username
            if username in annotator_dict:
                if t.status == 'approved':
                    annotator_dict[username]['approved'] += 1
                elif t.status == 'rejected':
                    annotator_dict[username]['rejected'] += 1
                elif t.status == 'submitted':
                    annotator_dict[username]['submitted'] += 1
    
    # Calculate submitted (total - approved - rejected) for each annotator
    for username, stats in annotator_dict.items():
        stats['submitted'] = stats['total_annotated'] - stats['approved'] - stats['rejected']
        if stats['submitted'] < 0:
            stats['submitted'] = 0
    
    annotator_stats = sorted(annotator_dict.values(), key=lambda x: x['annotated_by__username'])
    
    # Per-approver stats (who approved/rejected)
    approver_stats = tracking.filter(
        reviewed_by__isnull=False
    ).values(
        'reviewed_by__id',
        'reviewed_by__username'
    ).annotate(
        total_reviewed=Count('id'),
        approved=Count('id', filter=Q(status='approved')),
        rejected=Count('id', filter=Q(status='rejected')),
    ).order_by('reviewed_by__username')
    
    return JsonResponse({
        'summary': {
            'total_examples': total_examples,
            'confirmed': confirmed_count,  # New: from ExampleState
            'pending': pending_count,
            'submitted': submitted_count,
            'approved': approved_count,
            'rejected': rejected_count,
        },
        'annotators': annotator_stats,
        'approvers': list(approver_stats),
    })

