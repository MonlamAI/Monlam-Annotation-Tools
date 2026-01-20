# ============================================================================
# DIAGNOSTIC SCRIPT - Check actual database state
# ============================================================================
# This script checks what's actually in the database to understand why
# the UI shows "In progress" + "APPROVED" but the fix script finds nothing
# ============================================================================

from assignment.completion_tracking import ApproverCompletionStatus
from assignment.models_separate import Assignment
from assignment.simple_tracking import AnnotationTracking
from examples.models import ExampleState, Example
from projects.models import Project
from django.contrib.auth import get_user_model

User = get_user_model()
PROJECT_ID = 18  # TTSEPHEL project

print("=" * 80)
print("DIAGNOSTIC: Checking actual database state")
print("=" * 80)

project = Project.objects.get(id=PROJECT_ID)
print(f"\nProject: {project.id} - {project.name}")

# Check assignments with status='approved'
approved_assignments = Assignment.objects.filter(project=project, status='approved', is_active=True)
print(f"\n[1] Assignments with status='approved': {approved_assignments.count()}")

for assignment in approved_assignments[:10]:  # Show first 10
    example_state = ExampleState.objects.filter(example_id=assignment.example_id).first()
    has_approval_record = ApproverCompletionStatus.objects.filter(
        example_id=assignment.example_id,
        project=project,
        status='approved'
    ).exists()
    
    print(f"\n  Assignment {assignment.id} (Example {assignment.example_id}):")
    print(f"    - status: {assignment.status}")
    print(f"    - assigned_to: {assignment.assigned_to.username if assignment.assigned_to else None}")
    print(f"    - submitted_at: {assignment.submitted_at}")
    print(f"    - started_at: {assignment.started_at}")
    print(f"    - reviewed_by: {assignment.reviewed_by.username if assignment.reviewed_by else None}")
    print(f"    - ExampleState.confirmed_by: {example_state.confirmed_by.username if example_state and example_state.confirmed_by else None}")
    print(f"    - Has ApproverCompletionStatus: {has_approval_record}")
    print(f"    → Would show: {'Finished' if (example_state and example_state.confirmed_by) else 'In progress'} + {'APPROVED' if assignment.status == 'approved' else assignment.status}")

# Check ApproverCompletionStatus records
approval_records = ApproverCompletionStatus.objects.filter(project=project, status='approved')
print(f"\n[2] ApproverCompletionStatus records with status='approved': {approval_records.count()}")

for approval in approval_records[:10]:  # Show first 10
    assignment = Assignment.objects.filter(example_id=approval.example_id, project=project, is_active=True).first()
    example_state = ExampleState.objects.filter(example_id=approval.example_id).first()
    
    print(f"\n  ApproverCompletionStatus {approval.id} (Example {approval.example_id}):")
    print(f"    - approver: {approval.approver.username}")
    print(f"    - status: {approval.status}")
    print(f"    - Assignment.status: {assignment.status if assignment else 'No assignment'}")
    print(f"    - ExampleState.confirmed_by: {example_state.confirmed_by.username if example_state and example_state.confirmed_by else None}")
    print(f"    → Would show: {'Finished' if (example_state and example_state.confirmed_by) else 'In progress'} + {'APPROVED' if (approval.status == 'approved' or (assignment and assignment.status == 'approved')) else 'SUBMITTED'}")

# Check examples with ExampleState but no confirmed_by (would show "In progress")
example_states_no_confirmed = ExampleState.objects.filter(example__project=project, confirmed_by__isnull=True)
print(f"\n[3] ExampleState records WITHOUT confirmed_by: {example_states_no_confirmed.count()}")

# Check examples that would show "In progress" + "APPROVED"
print(f"\n[4] Checking for 'In progress' + 'APPROVED' cases:")
in_progress_approved = []
for assignment in approved_assignments:
    example_state = ExampleState.objects.filter(example_id=assignment.example_id).first()
    if not example_state or not example_state.confirmed_by:
        in_progress_approved.append({
            'assignment_id': assignment.id,
            'example_id': assignment.example_id,
            'assignment_status': assignment.status,
            'has_confirmed_by': bool(example_state and example_state.confirmed_by)
        })

print(f"  Found {len(in_progress_approved)} cases of 'In progress' + 'APPROVED'")
for case in in_progress_approved[:10]:
    print(f"    - Assignment {case['assignment_id']} (Example {case['example_id']}): status={case['assignment_status']}, confirmed_by={case['has_confirmed_by']}")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)

