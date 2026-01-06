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
    
    context = {
        'project': project,
        'project_id': project_id,
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
    """
    from projects.models import Project
    from assignment.models_separate import Assignment
    
    project = get_object_or_404(Project, pk=project_id)
    
    # Check access
    if not request.user.is_superuser:
        if not project.members.filter(id=request.user.id).exists():
            return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Get overall stats
    total_examples = project.examples.count()
    assignments = Assignment.objects.filter(project=project, is_active=True)
    
    assigned_count = assignments.count()
    completed_count = assignments.filter(status='completed').count()
    submitted_count = assignments.filter(status='submitted').count()
    approved_count = assignments.filter(status='approved').count()
    rejected_count = assignments.filter(status='rejected').count()
    
    # Per-annotator stats
    annotator_stats = assignments.values(
        'assigned_to__id',
        'assigned_to__username'
    ).annotate(
        total_assigned=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        submitted=Count('id', filter=Q(status='submitted')),
        approved=Count('id', filter=Q(status='approved')),
        rejected=Count('id', filter=Q(status='rejected')),
    ).order_by('assigned_to__username')
    
    # Per-approver stats
    approver_stats = assignments.filter(
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
            'assigned': assigned_count,
            'completed': completed_count,
            'submitted': submitted_count,
            'approved': approved_count,
            'rejected': rejected_count,
            'unassigned': total_examples - assigned_count,
        },
        'annotators': list(annotator_stats),
        'approvers': list(approver_stats),
    })

