"""
Views for Monlam custom UI pages.
Includes completion dashboard API and template views.

Note: Client-side routing (metrics redirect, dataset, etc.) is handled by Vue router.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Q

from apps.projects.models import Project, Member, MemberRole
from apps.examples.models import Example
from apps.monlam_tracking.models import AnnotationTracking, TrackingStatus


@login_required
def completion_dashboard(request, project_id):
    """
    Completion dashboard view.
    Shows overall progress, annotator performance, and reviewer performance.
    """
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user has access (must be PM or Admin)
    if not request.user.is_superuser:
        member = Member.objects.filter(
            project=project,
            user=request.user,
            role__in=[MemberRole.PROJECT_MANAGER, MemberRole.PROJECT_ADMIN, MemberRole.APPROVER]
        ).first()
        
        if not member:
            return redirect('project_detail', project_id=project_id)
    
    # Get statistics
    total_examples = Example.objects.filter(project=project).count()
    
    # Status counts
    status_counts = AnnotationTracking.objects.filter(
        project=project
    ).values('status').annotate(count=Count('id'))
    
    status_dict = {item['status']: item['count'] for item in status_counts}
    
    # Calculate pending
    tracked_count = AnnotationTracking.objects.filter(project=project).count()
    pending_count = total_examples - tracked_count + status_dict.get('pending', 0)
    
    # Annotator performance
    annotator_stats = AnnotationTracking.objects.filter(
        project=project,
        annotated_by__isnull=False
    ).values('annotated_by__username').annotate(
        completed=Count('id'),
        approved=Count('id', filter=Q(status=TrackingStatus.APPROVED)),
        rejected=Count('id', filter=Q(status=TrackingStatus.REJECTED))
    ).order_by('-completed')
    
    annotators = []
    for stat in annotator_stats:
        completed = stat['completed']
        approved = stat['approved']
        success_rate = (approved / completed * 100) if completed > 0 else 0
        annotators.append({
            'username': stat['annotated_by__username'],
            'completed': completed,
            'approved': approved,
            'rejected': stat['rejected'],
            'success_rate': round(success_rate, 1)
        })
    
    # Reviewer performance
    reviewer_stats = AnnotationTracking.objects.filter(
        project=project,
        reviewed_by__isnull=False
    ).values('reviewed_by__username').annotate(
        reviewed=Count('id'),
        approved=Count('id', filter=Q(status=TrackingStatus.APPROVED)),
        rejected=Count('id', filter=Q(status=TrackingStatus.REJECTED))
    ).order_by('-reviewed')
    
    reviewers = []
    for stat in reviewer_stats:
        reviewed = stat['reviewed']
        approved = stat['approved']
        approval_rate = (approved / reviewed * 100) if reviewed > 0 else 0
        reviewers.append({
            'username': stat['reviewed_by__username'],
            'reviewed': reviewed,
            'approved': approved,
            'rejected': stat['rejected'],
            'approval_rate': round(approval_rate, 1)
        })
    
    # Calculate completion rate
    approved_count = status_dict.get('approved', 0)
    completion_rate = (approved_count / total_examples * 100) if total_examples > 0 else 0
    
    context = {
        'project': project,
        'stats': {
            'total': total_examples,
            'pending': pending_count,
            'in_progress': status_dict.get('in_progress', 0),
            'submitted': status_dict.get('submitted', 0),
            'approved': approved_count,
            'rejected': status_dict.get('rejected', 0),
            'completion_rate': round(completion_rate, 1)
        },
        'annotators': annotators,
        'reviewers': reviewers,
    }
    
    return render(request, 'monlam_ui/completion_dashboard.html', context)


@login_required
def completion_dashboard_api(request, project_id):
    """
    JSON API endpoint for completion dashboard data.
    Used by Vue frontend.
    """
    project = get_object_or_404(Project, id=project_id)
    
    # Check access
    if not request.user.is_superuser:
        member = Member.objects.filter(
            project=project,
            user=request.user
        ).first()
        
        if not member:
            return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Get statistics (same as above)
    total_examples = Example.objects.filter(project=project).count()
    
    status_counts = AnnotationTracking.objects.filter(
        project=project
    ).values('status').annotate(count=Count('id'))
    
    status_dict = {item['status']: item['count'] for item in status_counts}
    
    tracked_count = AnnotationTracking.objects.filter(project=project).count()
    pending_count = total_examples - tracked_count + status_dict.get('pending', 0)
    
    approved_count = status_dict.get('approved', 0)
    completion_rate = (approved_count / total_examples * 100) if total_examples > 0 else 0
    
    # Annotator stats
    annotator_stats = list(AnnotationTracking.objects.filter(
        project=project,
        annotated_by__isnull=False
    ).values('annotated_by__id', 'annotated_by__username').annotate(
        completed=Count('id'),
        approved=Count('id', filter=Q(status=TrackingStatus.APPROVED)),
        rejected=Count('id', filter=Q(status=TrackingStatus.REJECTED))
    ).order_by('-completed'))
    
    for stat in annotator_stats:
        completed = stat['completed']
        approved = stat['approved']
        stat['success_rate'] = round((approved / completed * 100) if completed > 0 else 0, 1)
    
    # Reviewer stats
    reviewer_stats = list(AnnotationTracking.objects.filter(
        project=project,
        reviewed_by__isnull=False
    ).values('reviewed_by__id', 'reviewed_by__username').annotate(
        reviewed=Count('id'),
        approved=Count('id', filter=Q(status=TrackingStatus.APPROVED)),
        rejected=Count('id', filter=Q(status=TrackingStatus.REJECTED))
    ).order_by('-reviewed'))
    
    for stat in reviewer_stats:
        reviewed = stat['reviewed']
        approved = stat['approved']
        stat['approval_rate'] = round((approved / reviewed * 100) if reviewed > 0 else 0, 1)
    
    return JsonResponse({
        'project': {
            'id': project.id,
            'name': project.name,
            'tibetan_name': project.tibetan_name,
        },
        'stats': {
            'total': total_examples,
            'pending': pending_count,
            'in_progress': status_dict.get('in_progress', 0),
            'submitted': status_dict.get('submitted', 0),
            'approved': approved_count,
            'rejected': status_dict.get('rejected', 0),
            'completion_rate': round(completion_rate, 1)
        },
        'annotators': annotator_stats,
        'reviewers': reviewer_stats,
    })

