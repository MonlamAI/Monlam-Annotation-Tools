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

# Import role constants for consistency
try:
    from assignment.roles import (
        ROLE_PROJECT_ADMIN,
        ROLE_ANNOTATION_APPROVER,
        ROLE_PROJECT_MANAGER
    )
except ImportError:
    # Fallback if import fails
    ROLE_PROJECT_ADMIN = 'project_admin'
    ROLE_ANNOTATION_APPROVER = 'annotation_approver'
    ROLE_PROJECT_MANAGER = 'project_manager'


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
            from projects.models import Project, Member
            
            # Check if user is project admin by role name
            is_admin = Member.objects.filter(
                project_id=project_id,
                user=request.user
            ).select_related('role').filter(
                role__name__iexact=ROLE_PROJECT_ADMIN
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
    from projects.models import Project, Member
    
    project = get_object_or_404(Project, pk=project_id)
    
    # Check access
    if not request.user.is_superuser:
        if not Member.objects.filter(project_id=project_id, user=request.user).exists():
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
    from projects.models import Project, Member
    
    project = get_object_or_404(Project, pk=project_id)
    
    # Check if user has access to this project
    if not request.user.is_superuser:
        # Check if user is a member of this project (via role_mappings)
        if not Member.objects.filter(project_id=project_id, user=request.user).exists():
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
    from projects.models import Project, Member
    
    project = get_object_or_404(Project, pk=project_id)
    
    # Check access
    if not request.user.is_superuser:
        if not Member.objects.filter(project_id=project_id, user=request.user).exists():
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
    - Multi-level approval status (annotation_approver and project_admin)
    """
    from projects.models import Project, Member
    from examples.models import Example
    from assignment.models_separate import Assignment
    from assignment.completion_tracking import ApproverCompletionStatus
    import json
    
    project = get_object_or_404(Project, pk=project_id)
    example = get_object_or_404(Example, pk=example_id, project=project)
    
    # Check access
    if not request.user.is_superuser:
        if not Member.objects.filter(project_id=project_id, user=request.user).exists():
            return render(request, '403.html', status=403)
    
    # Get assignment for this example
    try:
        assignment = Assignment.objects.get(project=project, example=example, is_active=True)
    except Assignment.DoesNotExist:
        assignment = None
    
    # Get all approver completions for this example (multi-level approval)
    all_approvals = ApproverCompletionStatus.objects.filter(
        example=example
    ).select_related('approver').order_by('-reviewed_at')
    
    # Build approvals list with role information
    approvals_list = []
    annotation_approver_approved = False
    project_admin_approved = False
    
    for ap in all_approvals:
        # Get approver's role
        try:
            member = Member.objects.filter(project=project, user=ap.approver).select_related('role').first()
            approver_role = member.role.name.lower() if member and member.role else None
        except Exception:
            approver_role = None
        
        approvals_list.append({
            'approver_id': ap.approver.id,
            'approver_username': ap.approver.username,
            'approver_role': approver_role or 'unknown',
            'status': ap.status,
            'reviewed_at': ap.reviewed_at.isoformat() if ap.reviewed_at else None,
            'review_notes': ap.review_notes or ''
        })
        
        # Check if annotation_approver has approved
        if approver_role == ROLE_ANNOTATION_APPROVER and ap.status == 'approved':
            annotation_approver_approved = True
        
        # Check if project_admin has approved
        if approver_role == ROLE_PROJECT_ADMIN and ap.status == 'approved':
            project_admin_approved = True
    
    # Check if example is submitted
    is_submitted = False
    if assignment and assignment.status == 'submitted':
        is_submitted = True
    else:
        # Also check AnnotationTracking status
        from assignment.simple_tracking import AnnotationTracking
        tracking = AnnotationTracking.objects.filter(
            project=project,
            example=example
        ).first()
        if tracking and tracking.status == 'submitted':
            is_submitted = True
    
    # Check if current user can approve (is approver or admin)
    can_approve = False
    user_role = None
    can_review_now = False
    try:
        member = Member.objects.filter(project=project, user=request.user).select_related('role').first()
        if member and member.role:
            user_role = member.role.name.lower()
            can_approve = any(r in user_role for r in ['approver', 'manager', 'admin'])
            
            # Check if user can review now (with role-specific rules)
            if can_approve:
                if user_role == ROLE_PROJECT_ADMIN:
                    # Project admin can only review if annotation_approver has approved
                    can_review_now = annotation_approver_approved
                elif user_role == ROLE_ANNOTATION_APPROVER:
                    # Annotation approvers can only review if example is submitted
                    can_review_now = is_submitted
                elif user_role == ROLE_PROJECT_MANAGER:
                    # Project managers can always review
                    can_review_now = True
                else:
                    # Other roles (shouldn't reach here, but safe fallback)
                    can_review_now = False
    except Exception:
        pass
    
    # Check if current user has already approved/rejected
    current_user_approval = None
    for ap in all_approvals:
        if ap.approver == request.user:
            current_user_approval = {
                'status': ap.status,
                'reviewed_at': ap.reviewed_at.isoformat() if ap.reviewed_at else None,
                'review_notes': ap.review_notes
            }
            break
    
    context = {
        'project': project,
        'example': example,
        'assignment': assignment,
        'project_id': project_id,
        'example_id': example_id,
        'all_approvals': json.dumps(approvals_list),
        'annotation_approver_approved': annotation_approver_approved,
        'project_admin_approved': project_admin_approved,
        'can_approve': can_approve,
        'user_role': user_role,
        'can_review_now': can_review_now,
        'is_submitted': is_submitted,
        'current_user_approval': json.dumps(current_user_approval) if current_user_approval else None,
    }
    
    return render(request, 'monlam_ui/annotation_with_approval.html', context)


@login_required
@require_http_methods(["GET"])
def api_dataset_assignments(request, project_id):
    """
    API endpoint to get all assignments for dataset view
    Returns assignment data for each example in the project
    """
    from projects.models import Project, Member
    from assignment.models_separate import Assignment
    from assignment.serializers import AssignmentSerializer
    
    project = get_object_or_404(Project, pk=project_id)
    
    # Check access
    if not request.user.is_superuser:
        if not Member.objects.filter(project_id=project_id, user=request.user).exists():
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
    
    Terminology:
    - "Annotated" (total_annotated): Count of examples confirmed by annotator (ExampleState records)
      This means the annotator clicked the checkmark to mark completion.
    
    - "Submitted": Count of confirmed examples that are awaiting review (not yet approved/rejected)
      Formula: submitted = total_annotated - approved - rejected
      This represents work that's done but not yet reviewed.
    
    - "Approved": Count of examples approved by reviewers (from AnnotationTracking.status='approved')
    
    - "Rejected": Count of examples rejected by reviewers (from AnnotationTracking.status='rejected')
    
    Note: ExampleState and AnnotationTracking are matched by example_id to ensure accurate counts.
    """
    from projects.models import Project, Member
    from examples.models import ExampleState
    from assignment.simple_tracking import AnnotationTracking
    
    project = get_object_or_404(Project, pk=project_id)
    
    # Check access
    if not request.user.is_superuser:
        if not Member.objects.filter(project_id=project_id, user=request.user).exists():
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
    
    # Get final approvals (project_admin approvals only)
    from assignment.completion_tracking import ApproverCompletionStatus
    from assignment.roles import ROLE_PROJECT_ADMIN
    
    # Get all project_admin members
    admin_members = Member.objects.filter(
        project=project
    ).select_related('role').filter(
        role__name__iexact=ROLE_PROJECT_ADMIN
    )
    admin_user_ids = [m.user_id for m in admin_members]
    
    # Count final approvals by project_admin
    # Final Approved = total number of approvals made by project_admin users
    # Each approval action by a project_admin counts as 1 Final Approved
    print(f'[Completion Stats] Finding project_admin users: {admin_user_ids}')
    if admin_user_ids:
        final_approved_count = ApproverCompletionStatus.objects.filter(
            project=project,
            status='approved',
            approver_id__in=admin_user_ids
        ).count()  # Count total approvals by project_admin, not distinct examples
        print(f'[Completion Stats] Final approved count (total approvals by project_admin): {final_approved_count}')
    else:
        # Fallback: check by role name directly if admin_user_ids is empty
        final_approved_count = 0
        for ap_completion in ApproverCompletionStatus.objects.filter(
            project=project,
            status='approved'
        ).select_related('approver'):
            if ap_completion.approver:
                try:
                    approver_member = Member.objects.filter(
                        user=ap_completion.approver,
                        project=project
                    ).select_related('role').first()
                    if approver_member and approver_member.role:
                        role_name = approver_member.role.name.lower().strip()
                        if role_name == ROLE_PROJECT_ADMIN or 'project_admin' in role_name:
                            final_approved_count += 1  # Count each approval
                except Exception:
                    pass
        print(f'[Completion Stats] Final approved count (fallback): {final_approved_count}')
    
    # Submitted = confirmed but not yet approved/rejected
    submitted_count = confirmed_count - approved_count - rejected_count
    if submitted_count < 0:
        submitted_count = 0
    
    pending_count = total_examples - confirmed_count
    
    # Per-annotator stats - combine ExampleState (confirmed) and AnnotationTracking
    # Build a mapping of example_id -> tracking status for efficient lookup
    tracking_by_example = {}
    for t in tracking:
        if t.example_id:
            tracking_by_example[t.example_id] = t
    
    annotator_dict = {}
    
    # Process ExampleState records (confirmed examples) and match with tracking
    for state in confirmed_states:
        if state.confirmed_by:
            username = state.confirmed_by.username
            user_id = state.confirmed_by.id
            example_id = state.example_id
            
            if username not in annotator_dict:
                annotator_dict[username] = {
                    'annotated_by__id': user_id,
                    'annotated_by__username': username,
                    'total_annotated': 0,  # Count of confirmed examples
                    'submitted': 0,
                    'approved': 0,
                    'rejected': 0,
                }
            
            annotator_dict[username]['total_annotated'] += 1
            
            # Check tracking status for this specific example
            # IMPORTANT: Only count if this example was annotated by this user
            tracking_record = tracking_by_example.get(example_id)
            if tracking_record:
                # Only count if the tracking record's annotated_by matches this user
                # This ensures we only count approvals/rejections for examples this annotator actually worked on
                if tracking_record.annotated_by and tracking_record.annotated_by.id == user_id:
                    # Match by example_id to get accurate status
                    if tracking_record.status == 'approved':
                        annotator_dict[username]['approved'] += 1
                    elif tracking_record.status == 'rejected':
                        annotator_dict[username]['rejected'] += 1
                    elif tracking_record.status == 'submitted':
                        annotator_dict[username]['submitted'] += 1
                    # If status is 'pending', it's still submitted (confirmed but not reviewed)
                    elif tracking_record.status == 'pending':
                        annotator_dict[username]['submitted'] += 1
                else:
                    # Tracking exists but for different annotator - this confirmed example is submitted
                    annotator_dict[username]['submitted'] += 1
            else:
                # No tracking record exists - confirmed but not yet reviewed = submitted
                annotator_dict[username]['submitted'] += 1
    
    # Also add annotators from AnnotationTracking who may not have confirmed yet
    # This ensures all annotators with tracked work appear in the dashboard
    for t in tracking:
        if t.annotated_by:
            username = t.annotated_by.username
            user_id = t.annotated_by.id
            
            if username not in annotator_dict:
                # Add annotator if they have tracking but no confirmations yet
                annotator_dict[username] = {
                    'annotated_by__id': user_id,
                    'annotated_by__username': username,
                    'total_annotated': 0,  # Will remain 0 if no confirmations
                    'submitted': 0,
                    'approved': 0,
                    'rejected': 0,
                }
            
            # Only count if this example wasn't already counted above (via ExampleState)
            # Check if this example has an ExampleState record
            example_has_state = any(
                state.example_id == t.example_id 
                for state in confirmed_states 
                if state.confirmed_by and state.confirmed_by.username == username
            )
            
            if not example_has_state:
                # This example has tracking but no confirmation - count based on status
                if t.status == 'approved':
                    annotator_dict[username]['approved'] += 1
                elif t.status == 'rejected':
                    annotator_dict[username]['rejected'] += 1
                elif t.status == 'submitted' or t.status == 'pending':
                    annotator_dict[username]['submitted'] += 1
    
    # Final calculation: ensure total_annotated = submitted + approved + rejected for all annotators
    # This ensures consistency even if tracking records are missing or mismatched
    for username, stats in annotator_dict.items():
        if stats['total_annotated'] > 0:
            # Recalculate submitted to ensure: total_annotated = submitted + approved + rejected
            calculated_submitted = stats['total_annotated'] - stats['approved'] - stats['rejected']
            if calculated_submitted >= 0:
                stats['submitted'] = calculated_submitted
            else:
                # If calculated_submitted < 0, it means we have more approved/rejected than confirmed
                # This can happen if approvals/rejections exist for examples not confirmed by this annotator
                # Reset to 0 and adjust approved/rejected to match total_annotated
                stats['submitted'] = 0
                # Cap approved + rejected at total_annotated
                total_status = stats['approved'] + stats['rejected']
                if total_status > stats['total_annotated']:
                    # Proportionally adjust if needed (though this shouldn't happen with proper matching)
                    ratio = stats['total_annotated'] / total_status if total_status > 0 else 1
                    stats['approved'] = int(stats['approved'] * ratio)
                    stats['rejected'] = int(stats['rejected'] * ratio)
        else:
            # No confirmations: ensure submitted + approved + rejected makes sense
            # For annotators without confirmations, keep counts as-is from tracking
            pass
    
    annotator_stats = sorted(annotator_dict.values(), key=lambda x: x['annotated_by__username'])
    
    # Per-approver stats (who approved/rejected)
    # Get all approver completions for this project
    approver_completions = ApproverCompletionStatus.objects.filter(
        project=project
    ).select_related('approver')
    
    # Debug: Check how many records we found
    approver_count = approver_completions.count()
    print(f'[Completion Stats] Found {approver_count} ApproverCompletionStatus records for project {project_id}')
    
    # Build approver stats with role and final approval info
    approver_dict = {}
    approver_roles_cache = {}  # Cache roles per approver to avoid repeated lookups
    
    # Process ApproverCompletionStatus records (primary source)
    processed_count = 0
    error_count = 0
    for ap_completion in approver_completions:
        try:
            # Skip if approver is None (shouldn't happen but be safe)
            if not ap_completion.approver:
                print(f'[Completion Stats] Warning: ApproverCompletionStatus {ap_completion.id} has no approver')
                error_count += 1
                continue
                
            approver_id = ap_completion.approver.id
            approver_username = ap_completion.approver.username
            
            # Get approver's role (cache it to avoid repeated lookups)
            if approver_id not in approver_roles_cache:
                approver_role = None
                try:
                    approver_member = Member.objects.filter(
                        user=ap_completion.approver,
                        project=project
                    ).select_related('role').first()
                    if approver_member and approver_member.role:
                        approver_role = approver_member.role.name.lower().strip()
                except Exception as e:
                    print(f'[Completion Stats] Error getting approver role: {e}')
                    approver_role = None
                approver_roles_cache[approver_id] = approver_role
            else:
                approver_role = approver_roles_cache[approver_id]
            
            if approver_id not in approver_dict:
                approver_dict[approver_id] = {
                    'reviewed_by__id': approver_id,
                    'reviewed_by__username': approver_username,
                    'role': approver_role or 'unknown',
                    'total_reviewed': 0,
                    'approved': 0,
                    'final_approved': 0,
                    'rejected': 0,
                }
            
            approver_dict[approver_id]['total_reviewed'] += 1
            print(f'[Completion Stats] Processing approver {approver_username}: example {ap_completion.example_id}, status {ap_completion.status}, total_reviewed now {approver_dict[approver_id]["total_reviewed"]}')
            
            if ap_completion.status == 'approved':
                approver_dict[approver_id]['approved'] += 1
                # Count as final approved if this approver is project_admin
                # Use robust comparison: check exact match or if 'project_admin' is in role name
                is_project_admin = (
                    approver_role == ROLE_PROJECT_ADMIN or 
                    (approver_role and 'project_admin' in approver_role) or
                    approver_dict[approver_id]['role'] == ROLE_PROJECT_ADMIN or
                    (approver_dict[approver_id]['role'] and 'project_admin' in approver_dict[approver_id]['role'])
                )
                if is_project_admin:
                    approver_dict[approver_id]['final_approved'] += 1
            elif ap_completion.status == 'rejected':
                approver_dict[approver_id]['rejected'] += 1
            
            processed_count += 1
        except Exception as e:
            print(f'[Completion Stats] Error processing ApproverCompletionStatus {ap_completion.id}: {e}')
            import traceback
            traceback.print_exc()
            error_count += 1
            continue
    
    print(f'[Completion Stats] Processed {processed_count} ApproverCompletionStatus records, {error_count} errors, built {len(approver_dict)} approver entries')
    
    # Also include reviewers from AnnotationTracking to ensure we capture all reviewers
    # This supplements ApproverCompletionStatus data (some reviewers might only be in AnnotationTracking)
    # Only add if not already in approver_dict (to avoid double counting)
    if True:  # Always check AnnotationTracking as supplement
        # Get reviewers from AnnotationTracking
        reviewed_tracking = tracking.filter(
            reviewed_by__isnull=False,
            status__in=['approved', 'rejected']
        ).select_related('reviewed_by')
        
        for t in reviewed_tracking:
            if t.reviewed_by:
                approver_id = t.reviewed_by.id
                approver_username = t.reviewed_by.username
                
                # Get approver's role
                if approver_id not in approver_roles_cache:
                    approver_role = None
                    try:
                        approver_member = Member.objects.filter(
                            user=t.reviewed_by,
                            project=project
                        ).select_related('role').first()
                        if approver_member and approver_member.role:
                            approver_role = approver_member.role.name.lower().strip()
                    except Exception as e:
                        print(f'[Completion Stats] Error getting approver role from tracking: {e}')
                        approver_role = None
                    approver_roles_cache[approver_id] = approver_role
                else:
                    approver_role = approver_roles_cache[approver_id]
                
                # Only add if not already processed from ApproverCompletionStatus
                # This prevents double counting if the same approver exists in both systems
                if approver_id not in approver_dict:
                    approver_dict[approver_id] = {
                        'reviewed_by__id': approver_id,
                        'reviewed_by__username': approver_username,
                        'role': approver_role or 'unknown',
                        'total_reviewed': 0,
                        'approved': 0,
                        'final_approved': 0,
                        'rejected': 0,
                    }
                    approver_dict[approver_id]['total_reviewed'] += 1
                # If already exists, don't double count (ApproverCompletionStatus is the source of truth)
                
                if t.status == 'approved':
                    approver_dict[approver_id]['approved'] += 1
                    # Check if project_admin for final approval count
                    is_project_admin = (
                        approver_role == ROLE_PROJECT_ADMIN or 
                        (approver_role and 'project_admin' in approver_role)
                    )
                    if is_project_admin:
                        approver_dict[approver_id]['final_approved'] += 1
                elif t.status == 'rejected':
                    approver_dict[approver_id]['rejected'] += 1
    
    # Ensure total_reviewed = approved + rejected + pending for each approver
    # This ensures consistency
    for approver_id, approver_data in approver_dict.items():
        calculated_total = approver_data['approved'] + approver_data['rejected']
        # If total_reviewed doesn't match, update it
        if approver_data['total_reviewed'] != calculated_total:
            print(f'[Completion Stats] Fixing total_reviewed for {approver_data["reviewed_by__username"]}: was {approver_data["total_reviewed"]}, should be {calculated_total}')
            approver_data['total_reviewed'] = calculated_total
    
    approver_stats = sorted(approver_dict.values(), key=lambda x: x['reviewed_by__username'])
    
    # Debug: Log what we're returning
    print(f'[Completion Stats] Found {len(approver_stats)} approvers: {[a["reviewed_by__username"] for a in approver_stats]}')
    for a in approver_stats:
        print(f'  - {a["reviewed_by__username"]}: total_reviewed={a["total_reviewed"]}, approved={a["approved"]}, final_approved={a["final_approved"]}, rejected={a["rejected"]}')
    
    return JsonResponse({
        'summary': {
            'total_examples': total_examples,
            'confirmed': confirmed_count,  # New: from ExampleState
            'pending': pending_count,
            'submitted': submitted_count,
            'approved': approved_count,  # All approvals
            'final_approved': final_approved_count,  # Final approvals by project_admin
            'rejected': rejected_count,
        },
        'annotators': annotator_stats,
        'approvers': approver_stats,
    })


# ============================================
# CHANGE PASSWORD
# ============================================

@login_required
def change_password(request):
    """
    Password change page for users.
    """
    return render(request, 'monlam_ui/change_password.html')


@login_required
@require_http_methods(["POST"])
def api_change_password(request):
    """
    API endpoint to change user password.
    POST /monlam/api/change-password/
    {
        "old_password": "current_password",
        "new_password1": "new_password",
        "new_password2": "new_password"
    }
    """
    from django.contrib.auth import update_session_auth_hash
    from django.http import JsonResponse
    import json
    import traceback
    import sys
    
    # Log the request for debugging
    print(f'[Password Change API] Request from user: {request.user.username}', file=sys.stderr, flush=True)
    print(f'[Password Change API] Method: {request.method}', file=sys.stderr, flush=True)
    print(f'[Password Change API] Content-Type: {request.content_type}', file=sys.stderr, flush=True)
    print(f'[Password Change API] Is authenticated: {request.user.is_authenticated}', file=sys.stderr, flush=True)
    
    try:
        # Parse JSON body
        if request.content_type and 'application/json' in request.content_type:
            data = json.loads(request.body)
        else:
            # Try to parse anyway
            data = json.loads(request.body)
        
        old_password = data.get('old_password')
        new_password1 = data.get('new_password1')
        new_password2 = data.get('new_password2')
        
        print(f'[Password Change API] Fields received: old_password={bool(old_password)}, new_password1={bool(new_password1)}, new_password2={bool(new_password2)}', file=sys.stderr, flush=True)
        
        if not old_password or not new_password1 or not new_password2:
            print('[Password Change API] Missing required fields', file=sys.stderr, flush=True)
            return JsonResponse({
                'error': 'All fields are required'
            }, status=400)
        
        # Check if new passwords match
        if new_password1 != new_password2:
            print('[Password Change API] Passwords do not match', file=sys.stderr, flush=True)
            return JsonResponse({
                'new_password2': ['New passwords do not match']
            }, status=400)
        
        # Check password length
        if len(new_password1) < 8:
            print('[Password Change API] Password too short', file=sys.stderr, flush=True)
            return JsonResponse({
                'new_password2': ['Password must be at least 8 characters long']
            }, status=400)
        
        # Verify old password
        user = request.user
        if not user.check_password(old_password):
            print('[Password Change API] Old password incorrect', file=sys.stderr, flush=True)
            return JsonResponse({
                'old_password': ['Current password is incorrect']
            }, status=400)
        
        # Set new password
        print('[Password Change API] Setting new password...', file=sys.stderr, flush=True)
        user.set_password(new_password1)
        user.save()
        
        # Update session to prevent logout
        update_session_auth_hash(request, user)
        
        print('[Password Change API] Password changed successfully', file=sys.stderr, flush=True)
        return JsonResponse({
            'success': True,
            'message': 'Password changed successfully'
        })
        
    except json.JSONDecodeError as e:
        print(f'[Password Change API] JSON decode error: {e}', file=sys.stderr, flush=True)
        print(f'[Password Change API] Request body: {request.body}', file=sys.stderr, flush=True)
        return JsonResponse({
            'error': 'Invalid JSON: ' + str(e)
        }, status=400)
    except Exception as e:
        print(f'[Password Change API] Exception: {e}', file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        return JsonResponse({
            'error': 'Server error: ' + str(e)
        }, status=500)


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
        from projects.models import Member
        
        # Check if user is a member with any of these privileged roles (by role name)
        return Member.objects.filter(
            user=user
        ).select_related('role').filter(
            role__name__in=[ROLE_PROJECT_ADMIN, ROLE_PROJECT_MANAGER, ROLE_ANNOTATION_APPROVER]
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
    
    # Get tracking data - filter by date range for activity tracking
    try:
        from assignment.simple_tracking import AnnotationTracking
        # Get tracking data within date range (based on annotated_at or reviewed_at)
        # Include if annotated_at is in range OR reviewed_at is in range
        tracking_in_range = AnnotationTracking.objects.filter(
            project__in=projects
        ).filter(
            Q(annotated_at__isnull=False, annotated_at__gte=start_datetime, annotated_at__lte=end_datetime) |
            Q(reviewed_at__isnull=False, reviewed_at__gte=start_datetime, reviewed_at__lte=end_datetime)
        ).select_related('annotated_by', 'reviewed_by')
        
        # Also get all tracking for payment calculation (not filtered by date)
        tracking_all = AnnotationTracking.objects.filter(
            project__in=projects
        ).select_related('annotated_by', 'reviewed_by')
    except:
        tracking_in_range = []
        tracking_all = []
    
    # Summary stats
    total_examples = len(example_ids)
    confirmed_count = states.count()
    pending_count = total_examples - ExampleState.objects.filter(example_id__in=example_ids).count()
    
    approved_count = 0
    rejected_count = 0
    final_approved_count = 0
    if tracking_all:
        approved_count = tracking_all.filter(status='approved').count()
        rejected_count = tracking_all.filter(status='rejected').count()
    
    # Get final approvals (project_admin approvals only)
    try:
        from assignment.completion_tracking import ApproverCompletionStatus
        from assignment.roles import ROLE_PROJECT_ADMIN
        
        # Get all project_admin members across all projects
        admin_members = Member.objects.filter(
            project__in=projects
        ).select_related('role').filter(
            role__name__iexact=ROLE_PROJECT_ADMIN
        )
        admin_user_ids = [m.user_id for m in admin_members]
        
        # Count final approvals by project_admin
        final_approved_count = ApproverCompletionStatus.objects.filter(
            project__in=projects,
            status='approved',
            approver_id__in=admin_user_ids
        ).values('example').distinct().count()
    except Exception as e:
        print(f"[Analytics] Error calculating final approvals: {e}")
        final_approved_count = 0
    
    # Get unique annotators in this period (from both states and tracking)
    annotator_usernames_from_states = set(states.values_list('confirmed_by__username', flat=True).distinct())
    annotator_usernames_from_tracking = set(tracking_in_range.values_list('annotated_by__username', flat=True).distinct())
    all_annotator_usernames = annotator_usernames_from_states | annotator_usernames_from_tracking
    active_annotators = len(all_annotator_usernames)
    
    # Per-annotator stats - build from states (confirmations in date range)
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
                    'total_time_seconds': 0,
                    'first_date': state.confirmed_at.date(),
                    'last_date': state.confirmed_at.date()
                }
            annotator_stats[username]['total'] += 1
            if state.confirmed_at.date() < annotator_stats[username]['first_date']:
                annotator_stats[username]['first_date'] = state.confirmed_at.date()
            if state.confirmed_at.date() > annotator_stats[username]['last_date']:
                annotator_stats[username]['last_date'] = state.confirmed_at.date()
    
    # Add annotators from tracking who aren't in states (they annotated/reviewed in date range but confirmation was outside)
    for t in tracking_in_range:
        if t.annotated_by:
            username = t.annotated_by.username
            if username not in annotator_stats:
                # Initialize with date from tracking
                date_to_use = t.annotated_at.date() if t.annotated_at else today
                annotator_stats[username] = {
                    'username': username,
                    'total': 0,
                    'approved': 0,
                    'rejected': 0,
                    'pending': 0,
                    'total_time_seconds': 0,
                    'first_date': date_to_use,
                    'last_date': date_to_use
                }
            # Update dates if needed
            if t.annotated_at:
                track_date = t.annotated_at.date()
                if track_date < annotator_stats[username]['first_date']:
                    annotator_stats[username]['first_date'] = track_date
                if track_date > annotator_stats[username]['last_date']:
                    annotator_stats[username]['last_date'] = track_date
    
    # Add tracking status and time spent (from tracking_in_range for activity, tracking_all for payment)
    total_time_all = 0
    if tracking_in_range:
        for t in tracking_in_range:
            if t.annotated_by and t.annotated_by.username in annotator_stats:
                if t.status == 'approved':
                    annotator_stats[t.annotated_by.username]['approved'] += 1
                elif t.status == 'rejected':
                    annotator_stats[t.annotated_by.username]['rejected'] += 1
                
                # Add time spent
                if hasattr(t, 'time_spent_seconds') and t.time_spent_seconds:
                    annotator_stats[t.annotated_by.username]['total_time_seconds'] += t.time_spent_seconds
                    total_time_all += t.time_spent_seconds
    
    # ============================================
    # PAYMENT CALCULATION
    # ============================================
    from .payment_utils import count_tibetan_syllables, calculate_payment
    
    # Get examples with their metadata for payment calculation
    examples_with_meta = Example.objects.filter(
        id__in=example_ids
    ).select_related('project').only('id', 'project', 'meta', 'text')
    
    # Build mapping of example_id -> (project_name, duration, text)
    example_meta_map = {}
    for ex in examples_with_meta:
        duration = 0.0
        if ex.meta and isinstance(ex.meta, dict):
            # Try different possible keys for duration
            duration = ex.meta.get('duration', ex.meta.get('audio_duration', 0.0))
            if duration and isinstance(duration, (int, float)):
                duration = float(duration) / 60.0  # Convert seconds to minutes
        example_meta_map[ex.id] = {
            'project_name': ex.project.name,
            'duration_minutes': duration,
            'text': ex.text or ''
        }
    
    # Calculate payment per annotator (grouped by project)
    # Payment is based on SUBMITTED examples (not approved)
    annotator_payment_data = {}  # username -> {project_name -> {audio_minutes, submitted_segments, submitted_syllables}}
    reviewer_payment_data = {}   # username -> {project_name -> {reviewed_syllables}}
    
    # Process tracking data for payment calculation (use tracking_all for payment, not filtered by date)
    if tracking_all:
        for t in tracking_all:
            if t.example_id not in example_meta_map:
                continue
            
            ex_meta = example_meta_map[t.example_id]
            project_name = ex_meta['project_name']
            duration = ex_meta['duration_minutes']
            text = ex_meta['text']
            
            # Annotator payment (for SUBMITTED examples - not approved)
            if t.annotated_by and t.status == 'submitted':
                username = t.annotated_by.username
                if username not in annotator_payment_data:
                    annotator_payment_data[username] = {}
                if project_name not in annotator_payment_data[username]:
                    annotator_payment_data[username][project_name] = {
                        'audio_minutes': 0.0,
                        'submitted_segments': 0,
                        'submitted_syllables': 0
                    }
                annotator_payment_data[username][project_name]['audio_minutes'] += duration
                annotator_payment_data[username][project_name]['submitted_segments'] += 1
                # Count syllables for submitted examples
                syllables = count_tibetan_syllables(text)
                annotator_payment_data[username][project_name]['submitted_syllables'] += syllables
            
            # Reviewer payment (for approved examples - same structure as annotators)
            # Reviewers get the same payment as annotators: audio + segments/syllables
            if t.reviewed_by and t.status == 'approved' and t.reviewed_by != t.annotated_by:
                username = t.reviewed_by.username
                if username not in reviewer_payment_data:
                    reviewer_payment_data[username] = {}
                if project_name not in reviewer_payment_data[username]:
                    reviewer_payment_data[username][project_name] = {
                        'audio_minutes': 0.0,
                        'reviewed_segments': 0,  # Each reviewed example counts as a segment
                        'reviewed_syllables': 0
                    }
                reviewer_payment_data[username][project_name]['audio_minutes'] += duration
                reviewer_payment_data[username][project_name]['reviewed_segments'] += 1
                # Count syllables from the annotation text
                syllables = count_tibetan_syllables(text)
                reviewer_payment_data[username][project_name]['reviewed_syllables'] += syllables
    
    # Calculate payments for annotators
    for username, stats in annotator_stats.items():
        stats['total_audio_minutes'] = 0.0
        stats['total_syllables'] = 0
        stats['total_rupees'] = 0.0
        stats['payment_breakdown'] = []
        
        # Annotator payment (based on submitted examples)
        if username in annotator_payment_data:
            for project_name, data in annotator_payment_data[username].items():
                payment = calculate_payment(
                    project_name=project_name,
                    total_audio_minutes=data['audio_minutes'],
                    approved_segments=data['submitted_segments'],  # Use submitted_segments for payment
                    reviewed_syllables=data.get('submitted_syllables', 0),  # Use submitted_syllables for payment
                    is_reviewer=False
                )
                stats['total_audio_minutes'] += data['audio_minutes']
                stats['total_syllables'] += data.get('submitted_syllables', 0)
                stats['total_rupees'] += payment['total_rupees']
                if payment['configured']:
                    stats['payment_breakdown'].append(f"{project_name}: {payment['breakdown']}")
        
        # Reviewer payment (if user also reviewed - same structure as annotators)
        if username in reviewer_payment_data:
            for project_name, data in reviewer_payment_data[username].items():
                # Reviewers get the same payment structure as annotators
                # Use reviewed_segments for segment-based projects, reviewed_syllables for syllable-based projects
                payment = calculate_payment(
                    project_name=project_name,
                    total_audio_minutes=data['audio_minutes'],
                    approved_segments=data['reviewed_segments'],  # Use reviewed_segments for segment rate
                    reviewed_syllables=data['reviewed_syllables'],  # Use reviewed_syllables for syllable rate
                    is_reviewer=False  # Same calculation as annotators
                )
                stats['total_audio_minutes'] += data['audio_minutes']
                stats['total_syllables'] += data['reviewed_syllables']
                stats['total_rupees'] += payment['total_rupees']
                if payment['configured']:
                    stats['payment_breakdown'].append(f"{project_name} (Review): {payment['breakdown']}")
        
        stats['total_audio_minutes'] = round(stats['total_audio_minutes'], 2)
        stats['total_rupees'] = round(stats['total_rupees'], 2)
    
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
        
        # Format time spent
        total_seconds = stats['total_time_seconds']
        if total_seconds > 0:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            stats['total_time_formatted'] = f"{hours}h {minutes}m"
            stats['avg_time_per_example'] = round(total_seconds / stats['total']) if stats['total'] > 0 else 0
            avg_mins = stats['avg_time_per_example'] // 60
            avg_secs = stats['avg_time_per_example'] % 60
            stats['avg_time_formatted'] = f"{avg_mins}m {avg_secs}s"
        else:
            stats['total_time_formatted'] = 'N/A'
            stats['avg_time_per_example'] = 0
            stats['avg_time_formatted'] = 'N/A'
        
        # Remove date objects (not JSON serializable)
        del stats['first_date']
        del stats['last_date']
    
    annotator_list = sorted(annotator_stats.values(), key=lambda x: -x['total'])
    
    # Calculate payment summary
    total_payment_rupees = sum(stats['total_rupees'] for stats in annotator_stats.values())
    total_audio_minutes = sum(stats['total_audio_minutes'] for stats in annotator_stats.values())
    total_syllables = sum(stats['total_syllables'] for stats in annotator_stats.values())
    
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
    
    # Add tracking to daily activity (use tracking_in_range for daily stats)
    if tracking_in_range:
        for t in tracking_in_range:
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
    
    # Get reviewer stats (separate from annotators) - use ApproverCompletionStatus for accurate tracking
    reviewer_stats = {}
    approver_roles_cache = {}  # Cache roles per (username, project_id) to avoid repeated lookups
    use_fallback = False
    
    try:
        # Use ApproverCompletionStatus for more accurate reviewer tracking
        approver_completions = ApproverCompletionStatus.objects.filter(
            project__in=projects
        ).select_related('approver', 'example')
        
        # Check if we have any ApproverCompletionStatus records
        if not approver_completions.exists():
            use_fallback = True
        
        for ap_completion in approver_completions:
            username = ap_completion.approver.username
            project_id = ap_completion.project.id
            cache_key = f"{username}_{project_id}"
            
            if username not in reviewer_stats:
                reviewer_stats[username] = {
                    'username': username,
                    'total_reviewed': 0,
                    'approved': 0,
                    'final_approved': 0,
                    'rejected': 0,
                    'total_audio_minutes': 0.0,
                    'total_syllables': 0,
                    'total_rupees': 0.0,
                    'payment_breakdown': []
                }
            
            reviewer_stats[username]['total_reviewed'] += 1
            
            # Get approver's role (cache it to avoid repeated lookups)
            if cache_key not in approver_roles_cache:
                approver_role = None
                try:
                    approver_member = Member.objects.filter(
                        user=ap_completion.approver,
                        project=ap_completion.project
                    ).select_related('role').first()
                    if approver_member and approver_member.role:
                        approver_role = approver_member.role.name.lower().strip()
                except Exception as e:
                    print(f'[Analytics] Error getting approver role: {e}')
                    approver_role = None
                approver_roles_cache[cache_key] = approver_role
            else:
                approver_role = approver_roles_cache[cache_key]
            
            if ap_completion.status == 'approved':
                reviewer_stats[username]['approved'] += 1
                # Count as final approved if this approver is project_admin
                # Use robust comparison: check exact match or if 'project_admin' is in role name
                is_project_admin = (
                    approver_role == ROLE_PROJECT_ADMIN or 
                    (approver_role and 'project_admin' in approver_role)
                )
                if is_project_admin:
                    reviewer_stats[username]['final_approved'] += 1
                
                # Add payment data for reviewers (only for approved reviews)
                if ap_completion.example_id in example_meta_map:
                    ex_meta = example_meta_map[ap_completion.example_id]
                    reviewer_stats[username]['total_audio_minutes'] += ex_meta['duration_minutes']
                    syllables = count_tibetan_syllables(ex_meta['text'])
                    reviewer_stats[username]['total_syllables'] += syllables
            elif ap_completion.status == 'rejected':
                reviewer_stats[username]['rejected'] += 1
        
        # If no ApproverCompletionStatus records found, use fallback
        if use_fallback:
            print("[Analytics] No ApproverCompletionStatus records found, using AnnotationTracking fallback")
    except Exception as e:
        print(f"[Analytics] Error calculating reviewer stats from ApproverCompletionStatus: {e}")
        use_fallback = True
    
    # Fallback to AnnotationTracking if ApproverCompletionStatus is empty or failed
    if use_fallback or not reviewer_stats:
        if tracking_in_range:
            for t in tracking_in_range:
                if t.reviewed_by and t.status in ['approved', 'rejected']:
                    username = t.reviewed_by.username
                    project_id = t.project.id
                    cache_key = f"{username}_{project_id}"
                    
                    if username not in reviewer_stats:
                        reviewer_stats[username] = {
                            'username': username,
                            'total_reviewed': 0,
                            'approved': 0,
                            'final_approved': 0,
                            'rejected': 0,
                            'total_audio_minutes': 0.0,
                            'total_syllables': 0,
                            'total_rupees': 0.0,
                            'payment_breakdown': []
                        }
                    reviewer_stats[username]['total_reviewed'] += 1
                    
                    if t.status == 'approved':
                        reviewer_stats[username]['approved'] += 1
                        
                        # Check if this reviewer is project_admin and count as final_approved
                        if cache_key not in approver_roles_cache:
                            approver_role = None
                            try:
                                approver_member = Member.objects.filter(
                                    user=t.reviewed_by,
                                    project=t.project
                                ).select_related('role').first()
                                if approver_member and approver_member.role:
                                    approver_role = approver_member.role.name.lower().strip()
                            except Exception as e:
                                print(f'[Analytics] Error getting approver role in fallback: {e}')
                                approver_role = None
                            approver_roles_cache[cache_key] = approver_role
                        else:
                            approver_role = approver_roles_cache[cache_key]
                        
                        # Count as final approved if this approver is project_admin
                        is_project_admin = (
                            approver_role == ROLE_PROJECT_ADMIN or 
                            (approver_role and 'project_admin' in approver_role)
                        )
                        if is_project_admin:
                            reviewer_stats[username]['final_approved'] += 1
                        
                        # Add payment data for reviewers (only for approved reviews)
                        if t.example_id in example_meta_map:
                            ex_meta = example_meta_map[t.example_id]
                            reviewer_stats[username]['total_audio_minutes'] += ex_meta['duration_minutes']
                            syllables = count_tibetan_syllables(ex_meta['text'])
                            reviewer_stats[username]['total_syllables'] += syllables
                    elif t.status == 'rejected':
                        reviewer_stats[username]['rejected'] += 1
    
    # Calculate reviewer payments (use tracking_all for payment calculation)
    for username, stats in reviewer_stats.items():
        # Group by project for payment calculation
        reviewer_projects = {}
        if tracking_all:
            for t in tracking_all:
                if t.reviewed_by and t.reviewed_by.username == username and t.status == 'approved':
                    if t.example_id in example_meta_map:
                        ex_meta = example_meta_map[t.example_id]
                        project_name = ex_meta['project_name']
                        if project_name not in reviewer_projects:
                            reviewer_projects[project_name] = {
                                'audio_minutes': 0.0,
                                'reviewed_segments': 0,
                                'reviewed_syllables': 0
                            }
                        reviewer_projects[project_name]['audio_minutes'] += ex_meta['duration_minutes']
                        reviewer_projects[project_name]['reviewed_segments'] += 1
                        reviewer_projects[project_name]['reviewed_syllables'] += count_tibetan_syllables(ex_meta['text'])
        
        # Calculate payment for each project
        for project_name, data in reviewer_projects.items():
            payment = calculate_payment(
                project_name=project_name,
                total_audio_minutes=data['audio_minutes'],
                approved_segments=data['reviewed_segments'],
                reviewed_syllables=data['reviewed_syllables'],
                is_reviewer=False
            )
            stats['total_rupees'] += payment['total_rupees']
            if payment['configured']:
                stats['payment_breakdown'].append(f"{project_name}: {payment['breakdown']}")
        
        stats['total_audio_minutes'] = round(stats['total_audio_minutes'], 2)
        stats['total_rupees'] = round(stats['total_rupees'], 2)
    
    reviewer_list = sorted(reviewer_stats.values(), key=lambda x: -x['total_reviewed']) if reviewer_stats else []
    
    return JsonResponse({
        'summary': {
            'total_examples': total_examples,
            'confirmed': confirmed_count,
            'pending': pending_count,
            'approved': approved_count,  # All approvals
            'final_approved': final_approved_count,  # Final approvals by project_admin
            'rejected': rejected_count,
            'active_annotators': active_annotators,
            'total_time_seconds': total_time_all,
            'total_time_formatted': f"{total_time_all // 3600}h {(total_time_all % 3600) // 60}m" if total_time_all > 0 else 'N/A',
            'total_payment_rupees': round(total_payment_rupees, 2),
            'total_audio_minutes': round(total_audio_minutes, 2),
            'total_syllables': total_syllables
        },
        'annotators': annotator_list if annotator_list else [],
        'reviewers': reviewer_list if reviewer_list else [],
        'projects': project_stats if project_stats else [],
        'daily_activity': daily_list if daily_list else [],
        'date_range': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        }
    })

