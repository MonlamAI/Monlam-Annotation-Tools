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


# ============================================
# ANALYTICS DASHBOARD
# ============================================

def has_analytics_access(user):
    """
    Check if user has access to analytics dashboard.
    
    Access granted to:
    - Superusers (Admin)
    - Staff users
    - Users with project_manager role in any project
    - Users with project_admin role in any project
    - Users with annotation_approver role in any project
    """
    if not user.is_authenticated:
        return False
    
    # Superusers and staff always have access
    if user.is_superuser or user.is_staff:
        return True
    
    # Check if user has manager/admin/approver role in any project
    try:
        from roles.models import Role, Member
        
        # Get role IDs for privileged roles
        privileged_roles = Role.objects.filter(
            name__in=['project_admin', 'project_manager', 'annotation_approver']
        ).values_list('id', flat=True)
        
        # Check if user is a member with any of these roles
        return Member.objects.filter(
            user=user,
            role_id__in=privileged_roles
        ).exists()
    except Exception as e:
        # If role checking fails, deny access (fail secure)
        print(f"[Analytics] Role check error: {e}")
        return False


@login_required
def analytics_dashboard(request):
    """
    Main analytics dashboard page.
    URL: /monlam/analytics/
    
    ACCESS: Admin, Staff, Project Managers, Project Admins, Approvers
    """
    if not has_analytics_access(request.user):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden(
            '<h1>Access Denied</h1>'
            '<p>You do not have permission to view the Analytics Dashboard.</p>'
            '<p>This page is available to Project Managers, Approvers, and Admins only.</p>'
            '<p><a href="/projects/">← Return to Projects</a></p>'
        )
    
    return render(request, 'monlam_ui/analytics_dashboard.html')


@login_required
@require_http_methods(["GET"])
def analytics_api(request):
    """
    API endpoint for analytics data.
    URL: /monlam/analytics/api/
    
    ACCESS: Admin, Staff, Project Managers, Project Admins, Approvers
    
    Query params:
    - date_range: today, yesterday, last_7_days, last_30_days, this_month, last_month, this_year, custom
    - project_id: optional, filter by project
    - start_date: for custom range (YYYY-MM-DD)
    - end_date: for custom range (YYYY-MM-DD)
    """
    # Check access
    if not has_analytics_access(request.user):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    from datetime import datetime, timedelta
    from django.utils import timezone
    from projects.models import Project
    from examples.models import Example, ExampleState
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Parse query params
    date_range = request.GET.get('date_range', 'last_30_days')
    project_id = request.GET.get('project_id', '')
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')
    
    # Calculate date range
    today = timezone.now().date()
    
    if date_range == 'today':
        start_date = today
        end_date = today
    elif date_range == 'yesterday':
        start_date = today - timedelta(days=1)
        end_date = today - timedelta(days=1)
    elif date_range == 'last_7_days':
        start_date = today - timedelta(days=7)
        end_date = today
    elif date_range == 'last_30_days':
        start_date = today - timedelta(days=30)
        end_date = today
    elif date_range == 'this_month':
        start_date = today.replace(day=1)
        end_date = today
    elif date_range == 'last_month':
        first_of_this_month = today.replace(day=1)
        end_date = first_of_this_month - timedelta(days=1)
        start_date = end_date.replace(day=1)
    elif date_range == 'this_year':
        start_date = today.replace(month=1, day=1)
        end_date = today
    elif date_range == 'custom' and start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        start_date = today - timedelta(days=30)
        end_date = today
    
    # Convert to datetime with timezone
    start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
    end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
    
    # Get projects
    if project_id:
        projects = Project.objects.filter(id=project_id)
    else:
        projects = Project.objects.all()
    
    # Get all example IDs for these projects
    example_ids = list(Example.objects.filter(project__in=projects).values_list('id', flat=True))
    
    # Get ExampleState data (confirmations)
    states = ExampleState.objects.filter(
        example_id__in=example_ids,
        confirmed_at__gte=start_datetime,
        confirmed_at__lte=end_datetime
    ).select_related('confirmed_by', 'example')
    
    # Get tracking data
    try:
        from assignment.simple_tracking import AnnotationTracking
        tracking = AnnotationTracking.objects.filter(
            project__in=projects
        ).select_related('annotated_by', 'reviewed_by')
    except:
        tracking = []
    
    # Summary stats
    total_examples = len(example_ids)
    confirmed_count = states.count()
    pending_count = total_examples - ExampleState.objects.filter(example_id__in=example_ids).count()
    
    approved_count = 0
    rejected_count = 0
    if tracking:
        approved_count = tracking.filter(status='approved').count()
        rejected_count = tracking.filter(status='rejected').count()
    
    # Get unique annotators in this period
    active_annotators = states.values('confirmed_by').distinct().count()
    
    # Per-annotator stats
    annotator_stats = {}
    for state in states:
        if state.confirmed_by:
            username = state.confirmed_by.username
            if username not in annotator_stats:
                annotator_stats[username] = {
                    'username': username,
                    'total': 0,
                    'approved': 0,
                    'rejected': 0,
                    'pending': 0,
                    'first_date': state.confirmed_at.date(),
                    'last_date': state.confirmed_at.date()
                }
            annotator_stats[username]['total'] += 1
            if state.confirmed_at.date() < annotator_stats[username]['first_date']:
                annotator_stats[username]['first_date'] = state.confirmed_at.date()
            if state.confirmed_at.date() > annotator_stats[username]['last_date']:
                annotator_stats[username]['last_date'] = state.confirmed_at.date()
    
    # Add tracking status
    if tracking:
        for t in tracking:
            if t.annotated_by and t.annotated_by.username in annotator_stats:
                if t.status == 'approved':
                    annotator_stats[t.annotated_by.username]['approved'] += 1
                elif t.status == 'rejected':
                    annotator_stats[t.annotated_by.username]['rejected'] += 1
    
    # Calculate derived stats
    for username, stats in annotator_stats.items():
        stats['pending'] = stats['total'] - stats['approved'] - stats['rejected']
        if stats['pending'] < 0:
            stats['pending'] = 0
        
        reviewed = stats['approved'] + stats['rejected']
        stats['approval_rate'] = round((stats['approved'] / reviewed * 100) if reviewed > 0 else 0)
        
        # Days active
        days = (stats['last_date'] - stats['first_date']).days + 1
        stats['avg_per_day'] = stats['total'] / days if days > 0 else 0
        
        # Remove date objects (not JSON serializable)
        del stats['first_date']
        del stats['last_date']
    
    annotator_list = sorted(annotator_stats.values(), key=lambda x: -x['total'])
    
    # Per-project stats
    project_stats = []
    for project in projects:
        proj_examples = Example.objects.filter(project=project).count()
        proj_confirmed = ExampleState.objects.filter(example__project=project).count()
        project_stats.append({
            'id': project.id,
            'name': project.name,
            'total': proj_examples,
            'confirmed': proj_confirmed,
            'pending': proj_examples - proj_confirmed
        })
    
    # Daily activity
    daily_activity = {}
    for state in states:
        date_str = state.confirmed_at.strftime('%Y-%m-%d')
        if date_str not in daily_activity:
            daily_activity[date_str] = {
                'date': date_str,
                'annotations': 0,
                'approved': 0,
                'rejected': 0,
                'users': set()
            }
        daily_activity[date_str]['annotations'] += 1
        if state.confirmed_by:
            daily_activity[date_str]['users'].add(state.confirmed_by.username)
    
    # Add tracking to daily activity
    if tracking:
        for t in tracking:
            if t.reviewed_at:
                date_str = t.reviewed_at.strftime('%Y-%m-%d')
                if date_str in daily_activity:
                    if t.status == 'approved':
                        daily_activity[date_str]['approved'] += 1
                    elif t.status == 'rejected':
                        daily_activity[date_str]['rejected'] += 1
    
    # Convert sets to counts
    daily_list = []
    for date_str in sorted(daily_activity.keys()):
        day = daily_activity[date_str]
        daily_list.append({
            'date': day['date'],
            'annotations': day['annotations'],
            'approved': day['approved'],
            'rejected': day['rejected'],
            'active_users': len(day['users'])
        })
    
    return JsonResponse({
        'summary': {
            'total_examples': total_examples,
            'confirmed': confirmed_count,
            'pending': pending_count,
            'approved': approved_count,
            'rejected': rejected_count,
            'active_annotators': active_annotators
        },
        'annotators': annotator_list,
        'projects': project_stats,
        'daily_activity': daily_list,
        'date_range': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        }
    })

