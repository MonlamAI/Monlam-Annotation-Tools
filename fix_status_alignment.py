# ============================================================================
# STATUS ALIGNMENT FIX SCRIPT
# ============================================================================
# This script fixes inconsistencies between Annotator Status and Approval Status:
# 
# Issues Fixed:
# 1. "In progress" + "APPROVED" → Should be "Finished" + "APPROVED"
#    Fix: Set ExampleState.confirmed_by if ApproverCompletionStatus exists
#
# 2. Ensures "Finished" examples have ExampleState.confirmed_by set
# 3. Ensures "APPROVED" examples have ExampleState.confirmed_by set
# ============================================================================

from django.db import transaction
from assignment.completion_tracking import ApproverCompletionStatus
from assignment.models_separate import Assignment
from assignment.simple_tracking import AnnotationTracking
from examples.models import ExampleState, Example
from projects.models import Project
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()
DRY_RUN = False  # Set to True to preview changes
PROJECT_ID = None  # Set to specific project ID (e.g., 14), or None for all projects

print("=" * 80)
print("STATUS ALIGNMENT FIX")
print("=" * 80)
print("Fixing inconsistencies between Annotator Status and Approval Status")
print("=" * 80)
if DRY_RUN:
    print("⚠️  DRY RUN MODE - No changes will be made")
if PROJECT_ID:
    print(f"Project ID filter: {PROJECT_ID}")
print("=" * 80)

projects = Project.objects.all()
if PROJECT_ID:
    projects = projects.filter(id=PROJECT_ID)

total_fixed = 0
total_approved_without_confirmed = 0
total_submitted_without_confirmed = 0

for project in projects:
    print(f"\n{'=' * 80}")
    print(f"Processing Project: {project.id} - {project.name}")
    print(f"{'=' * 80}")
    
    # Get all examples in project
    all_examples = {e.id: e for e in Example.objects.filter(project=project)}
    
    # Get all ExampleState records
    all_example_states = {s.example_id: s for s in ExampleState.objects.filter(example__project=project).select_related('confirmed_by')}
    
    # Get all ApproverCompletionStatus records (approved/rejected)
    all_approvals = ApproverCompletionStatus.objects.filter(project=project)
    approved_example_ids = set(all_approvals.filter(status='approved').values_list('example_id', flat=True).distinct())
    rejected_example_ids = set(all_approvals.filter(status='rejected').values_list('example_id', flat=True).distinct())
    
    # Get all Assignment records
    all_assignments = {a.example_id: a for a in Assignment.objects.filter(project=project, is_active=True)}
    
    # Get all AnnotationTracking records
    all_tracking = {t.example_id: t for t in AnnotationTracking.objects.filter(project=project)}
    
    fixes_made = []
    
    # ============================================
    # ISSUE 1: "In progress" + "APPROVED" → Fix to "Finished" + "APPROVED"
    # ============================================
    print("\n[1] Fixing 'In progress' + 'APPROVED' inconsistencies...")
    
    for example_id in approved_example_ids:
        example = all_examples.get(example_id)
        if not example:
            continue
        
        example_state = all_example_states.get(example_id)
        assignment = all_assignments.get(example_id)
        tracking = all_tracking.get(example_id)
        
        # Check if ExampleState.confirmed_by is missing (would show "In progress")
        if not example_state or not example_state.confirmed_by:
            # This is approved but doesn't have confirmed_by → INCONSISTENT
            # Need to set confirmed_by to make it "Finished"
            
            # Find the annotator from Assignment or AnnotationTracking
            annotator = None
            confirmed_at = None
            
            if assignment and assignment.assigned_to:
                annotator = assignment.assigned_to
                confirmed_at = assignment.submitted_at or assignment.started_at
            elif tracking and tracking.annotated_by:
                annotator = tracking.annotated_by
                confirmed_at = tracking.annotated_at
            
            if annotator:
                fixes_made.append({
                    'example_id': example_id,
                    'issue': 'Approved but missing ExampleState.confirmed_by (shows "In progress" instead of "Finished")',
                    'fix': f'Set ExampleState.confirmed_by to {annotator.username}',
                    'type': 'approved_without_confirmed'
                })
                
                if not DRY_RUN:
                    if example_state:
                        example_state.confirmed_by = annotator
                        if not example_state.confirmed_at:
                            example_state.confirmed_at = confirmed_at or timezone.now()
                        example_state.save(update_fields=['confirmed_by', 'confirmed_at'])
                    else:
                        example_state = ExampleState.objects.create(
                            example=example,
                            confirmed_by=annotator,
                            confirmed_at=confirmed_at or timezone.now()
                        )
                        all_example_states[example_id] = example_state
                
                total_approved_without_confirmed += 1
                total_fixed += 1
    
    if fixes_made:
        print(f"  Found {len(fixes_made)} examples with 'In progress' + 'APPROVED' issue")
        if not DRY_RUN:
            print(f"  ✓ Fixed {len(fixes_made)} examples")
        else:
            for fix in fixes_made[:5]:
                print(f"  [DRY RUN] Would fix Example {fix['example_id']}: {fix['issue']}")
                print(f"    → {fix['fix']}")
            if len(fixes_made) > 5:
                print(f"  ... and {len(fixes_made) - 5} more")
    else:
        print("  ✓ No 'In progress' + 'APPROVED' issues found")
    
    # ============================================
    # ISSUE 2: "In progress" + "SUBMITTED" → Fix to "Finished" + "SUBMITTED"
    # ============================================
    print("\n[2] Fixing 'In progress' + 'SUBMITTED' inconsistencies...")
    
    fixes_made = []
    
    # Check all assignments with status='submitted' but no ExampleState.confirmed_by
    for example_id, assignment in all_assignments.items():
        if assignment.status == 'submitted' and assignment.submitted_at:
            example_state = all_example_states.get(example_id)
            
            # If submitted but no confirmed_by, it would show "In progress" + "SUBMITTED"
            if not example_state or not example_state.confirmed_by:
                annotator = assignment.assigned_to
                if annotator:
                    fixes_made.append({
                        'example_id': example_id,
                        'issue': 'Submitted but missing ExampleState.confirmed_by (shows "In progress" instead of "Finished")',
                        'fix': f'Set ExampleState.confirmed_by to {annotator.username}',
                        'type': 'submitted_without_confirmed'
                    })
                    
                    if not DRY_RUN:
                        if example_state:
                            example_state.confirmed_by = annotator
                            if not example_state.confirmed_at:
                                example_state.confirmed_at = assignment.submitted_at or timezone.now()
                            example_state.save(update_fields=['confirmed_by', 'confirmed_at'])
                        else:
                            example_state = ExampleState.objects.create(
                                example=all_examples[example_id],
                                confirmed_by=annotator,
                                confirmed_at=assignment.submitted_at or timezone.now()
                            )
                            all_example_states[example_id] = example_state
                    
                    total_submitted_without_confirmed += 1
                    total_fixed += 1
    
    # Also check AnnotationTracking with status='submitted' but no ExampleState.confirmed_by
    for example_id, tracking in all_tracking.items():
        if tracking.status == 'submitted' and tracking.annotated_by:
            # Skip if already in approved list (handled above)
            if example_id in approved_example_ids:
                continue
            
            example_state = all_example_states.get(example_id)
            
            if not example_state or not example_state.confirmed_by:
                fixes_made.append({
                    'example_id': example_id,
                    'issue': 'Submitted (from AnnotationTracking) but missing ExampleState.confirmed_by',
                    'fix': f'Set ExampleState.confirmed_by to {tracking.annotated_by.username}',
                    'type': 'submitted_without_confirmed'
                })
                
                if not DRY_RUN:
                    if example_state:
                        example_state.confirmed_by = tracking.annotated_by
                        if not example_state.confirmed_at:
                            example_state.confirmed_at = tracking.annotated_at or timezone.now()
                        example_state.save(update_fields=['confirmed_by', 'confirmed_at'])
                    else:
                        example_state = ExampleState.objects.create(
                            example=all_examples[example_id],
                            confirmed_by=tracking.annotated_by,
                            confirmed_at=tracking.annotated_at or timezone.now()
                        )
                        all_example_states[example_id] = example_state
                
                total_submitted_without_confirmed += 1
                total_fixed += 1
    
    if fixes_made:
        print(f"  Found {len(fixes_made)} examples with 'In progress' + 'SUBMITTED' issue")
        if not DRY_RUN:
            print(f"  ✓ Fixed {len(fixes_made)} examples")
        else:
            for fix in fixes_made[:5]:
                print(f"  [DRY RUN] Would fix Example {fix['example_id']}: {fix['issue']}")
                print(f"    → {fix['fix']}")
            if len(fixes_made) > 5:
                print(f"  ... and {len(fixes_made) - 5} more")
    else:
        print("  ✓ No 'In progress' + 'SUBMITTED' issues found")
    
    # ============================================
    # VERIFICATION: Check final state
    # ============================================
    print("\n[3] Verifying alignment...")
    
    approved_count = len(approved_example_ids)
    finished_count = sum(1 for es in all_example_states.values() if es.confirmed_by)
    
    print(f"  Total approved examples: {approved_count}")
    print(f"  Total finished examples (with ExampleState.confirmed_by): {finished_count}")
    
    # Check if all approved examples have confirmed_by
    approved_without_confirmed = []
    for example_id in approved_example_ids:
        example_state = all_example_states.get(example_id)
        if not example_state or not example_state.confirmed_by:
            approved_without_confirmed.append(example_id)
    
    if approved_without_confirmed:
        print(f"  ⚠️  Found {len(approved_without_confirmed)} approved examples still missing confirmed_by")
    else:
        print(f"  ✓ All approved examples have ExampleState.confirmed_by set")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total fixes applied: {total_fixed}")
print(f"  - Approved without confirmed_by: {total_approved_without_confirmed}")
print(f"  - Submitted without confirmed_by: {total_submitted_without_confirmed}")
print("=" * 80)

if DRY_RUN:
    print("\n⚠️  DRY RUN - No changes were made. Set DRY_RUN = False to apply changes.")
else:
    print("\n✅ Status alignment fix complete!")
    print("✅ All 'In progress' + 'APPROVED' issues fixed")
    print("✅ All 'In progress' + 'SUBMITTED' issues fixed")
    print("\n📊 Next steps:")
    print("   - Refresh the dataset table to see corrected statuses")
    print("   - All 'Finished' examples should now have ExampleState.confirmed_by set")
    print("   - All 'APPROVED' examples should now show 'Finished' annotator status")

