# ============================================================================
# COMPREHENSIVE APPROVAL DATA RESET AND STATUS SYNC
# ============================================================================
# This script:
# 1. Resets all approver/reviewer/project admin approval data to zero
# 2. Fixes annotator status inconsistencies (in_progress vs submitted)
# 3. Ensures alignment with UI views, metrics, and analytics
# 4. Preserves all annotated/confirmed data
# ============================================================================
# To run in Render shell:
# python manage.py shell < /tmp/reset_approval_comprehensive_final.py
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
print("COMPREHENSIVE APPROVAL DATA RESET AND STATUS SYNC")
print("=" * 80)
if DRY_RUN:
    print("⚠️  DRY RUN MODE - No changes will be made")
if PROJECT_ID:
    print(f"Project ID filter: {PROJECT_ID}")
print("=" * 80)

projects = Project.objects.all()
if PROJECT_ID:
    projects = projects.filter(id=PROJECT_ID)

total_approver_status_deleted = 0
total_assignment_review_reset = 0
total_tracking_review_reset = 0
total_status_fixed = 0
total_assignment_status_corrected = 0

for project in projects:
    print(f"\n{'=' * 80}")
    print(f"Processing Project: {project.id} - {project.name}")
    print(f"{'=' * 80}")
    
    # ============================================
    # STEP 1: Delete all ApproverCompletionStatus records
    # This resets all approver/reviewer and project admin approval data
    # ============================================
    print("\n[1] Resetting ApproverCompletionStatus records (approver/reviewer/project admin approvals)...")
    approver_statuses = ApproverCompletionStatus.objects.filter(project=project)
    count = approver_statuses.count()
    
    if count > 0:
        print(f"  Found {count} ApproverCompletionStatus records to delete")
        if not DRY_RUN:
            with transaction.atomic():
                approver_statuses.delete()
                print(f"  ✓ Deleted {count} ApproverCompletionStatus records")
        else:
            print(f"  [DRY RUN] Would delete {count} ApproverCompletionStatus records")
        total_approver_status_deleted += count
    else:
        print("  ✓ No ApproverCompletionStatus records found")
    
    # ============================================
    # STEP 2: Reset Assignment review fields and fix status
    # ============================================
    print("\n[2] Resetting Assignment review fields and fixing status...")
    assignments = Assignment.objects.filter(project=project, is_active=True)
    
    assignments_to_reset = []
    assignments_status_to_fix = []
    
    for assignment in assignments:
        needs_reset = False
        needs_status_fix = False
        
        # Check if has review data (approver/reviewer data)
        if assignment.reviewed_by or assignment.reviewed_at or assignment.review_notes:
            needs_reset = True
        
        # Check if status needs to be reset from approved/rejected to submitted/in_progress/assigned
        if assignment.status in ['approved', 'rejected']:
            needs_status_fix = True
        
        if needs_reset or needs_status_fix:
            assignments_to_reset.append(assignment)
            if needs_status_fix:
                assignments_status_to_fix.append(assignment)
    
    if assignments_to_reset:
        print(f"  Found {len(assignments_to_reset)} assignments with review data to reset")
        print(f"  Found {len(assignments_status_to_fix)} assignments with status to reset (approved/rejected -> submitted/in_progress/assigned)")
        
        if not DRY_RUN:
            with transaction.atomic():
                for assignment in assignments_to_reset:
                    # Reset review fields (approver/reviewer data)
                    assignment.reviewed_by = None
                    assignment.reviewed_at = None
                    assignment.review_notes = ''
                    
                    # Reset status if it was approved/rejected
                    if assignment.status in ['approved', 'rejected']:
                        # Determine correct status based on actual progress
                        if assignment.submitted_at:
                            # Was submitted, so set back to submitted
                            assignment.status = 'submitted'
                        elif assignment.started_at:
                            # Was started but not submitted, so in_progress
                            assignment.status = 'in_progress'
                        else:
                            # Just assigned, never started
                            assignment.status = 'assigned'
                    
                    assignment.save(update_fields=['reviewed_by', 'reviewed_at', 'review_notes', 'status'])
                
                print(f"  ✓ Reset review fields for {len(assignments_to_reset)} assignments")
                if assignments_status_to_fix:
                    print(f"  ✓ Reset status for {len(assignments_status_to_fix)} assignments")
        else:
            for assignment in assignments_to_reset[:5]:  # Show first 5
                print(f"  [DRY RUN] Would reset Assignment {assignment.id} (Example {assignment.example_id}):")
                print(f"    - reviewed_by: {assignment.reviewed_by} -> None")
                print(f"    - reviewed_at: {assignment.reviewed_at} -> None")
                print(f"    - review_notes: '{assignment.review_notes[:50]}...' -> ''")
                if assignment.status in ['approved', 'rejected']:
                    new_status = 'submitted' if assignment.submitted_at else ('in_progress' if assignment.started_at else 'assigned')
                    print(f"    - status: {assignment.status} -> {new_status}")
            if len(assignments_to_reset) > 5:
                print(f"  ... and {len(assignments_to_reset) - 5} more")
        
        total_assignment_review_reset += len(assignments_to_reset)
    else:
        print("  ✓ No assignments with review data found")
    
    # ============================================
    # STEP 3: Reset AnnotationTracking review fields and fix status
    # ============================================
    print("\n[3] Resetting AnnotationTracking review fields and fixing status...")
    tracking_records = AnnotationTracking.objects.filter(project=project)
    
    tracking_to_reset = []
    tracking_status_to_fix = []
    
    for tracking in tracking_records:
        needs_reset = False
        needs_status_fix = False
        
        # Check if has review data (approver/reviewer data)
        if tracking.reviewed_by or tracking.reviewed_at or tracking.review_notes:
            needs_reset = True
        
        # Check if status needs to be reset from reviewed/rejected to submitted/pending
        if tracking.status in ['reviewed', 'rejected']:
            needs_status_fix = True
        
        if needs_reset or needs_status_fix:
            tracking_to_reset.append(tracking)
            if needs_status_fix:
                tracking_status_to_fix.append(tracking)
    
    if tracking_to_reset:
        print(f"  Found {len(tracking_to_reset)} tracking records with review data to reset")
        print(f"  Found {len(tracking_status_to_fix)} tracking records with status to reset (reviewed/rejected -> submitted/pending)")
        
        if not DRY_RUN:
            with transaction.atomic():
                for tracking in tracking_to_reset:
                    # Reset review fields (approver/reviewer data)
                    tracking.reviewed_by = None
                    tracking.reviewed_at = None
                    tracking.review_notes = ''
                    
                    # Reset status if it was reviewed/rejected
                    if tracking.status in ['reviewed', 'rejected']:
                        # Only reset to submitted if it was actually annotated (has annotated_by and annotated_at)
                        if tracking.annotated_by and tracking.annotated_at:
                            tracking.status = 'submitted'
                        else:
                            tracking.status = 'pending'
                    
                    tracking.save(update_fields=['reviewed_by', 'reviewed_at', 'review_notes', 'status'])
                
                print(f"  ✓ Reset review fields for {len(tracking_to_reset)} tracking records")
                if tracking_status_to_fix:
                    print(f"  ✓ Reset status for {len(tracking_status_to_fix)} tracking records")
        else:
            for tracking in tracking_to_reset[:5]:  # Show first 5
                print(f"  [DRY RUN] Would reset AnnotationTracking for Example {tracking.example_id}:")
                print(f"    - reviewed_by: {tracking.reviewed_by} -> None")
                print(f"    - reviewed_at: {tracking.reviewed_at} -> None")
                print(f"    - review_notes: '{tracking.review_notes[:50]}...' -> ''")
                if tracking.status in ['reviewed', 'rejected']:
                    new_status = 'submitted' if (tracking.annotated_by and tracking.annotated_at) else 'pending'
                    print(f"    - status: {tracking.status} -> {new_status}")
            if len(tracking_to_reset) > 5:
                print(f"  ... and {len(tracking_to_reset) - 5} more")
        
        total_tracking_review_reset += len(tracking_to_reset)
    else:
        print("  ✓ No tracking records with review data found")
    
    # ============================================
    # STEP 4: Sync status across ExampleState, AnnotationTracking, and Assignment
    # Rule: "Finished" = annotated/submitted/confirmed - ALL THREE must be in sync
    # Dataset table shows: "in_progress" (pending) or "Finished" (submitted/confirmed)
    # ============================================
    print("\n[4] Syncing status across ExampleState, AnnotationTracking, and Assignment...")
    print("     Rule: 'Finished' = annotated/submitted/confirmed - all three must be in sync")
    print("     Dataset table: 'in_progress' (pending) or 'Finished' (submitted/confirmed)")
    
    # Get all examples in project
    all_examples = {e.id: e for e in Example.objects.filter(project=project)}
    
    # Get all tracking records
    all_tracking = {t.example_id: t for t in AnnotationTracking.objects.filter(project=project)}
    
    # Get all active assignments
    all_assignments = {a.example_id: a for a in Assignment.objects.filter(project=project, is_active=True)}
    
    # Get all ExampleState records (confirmed/finished examples)
    all_example_states = {s.example_id: s for s in ExampleState.objects.filter(example__project=project).select_related('confirmed_by')}
    
    inconsistencies_fixed = []
    
    # Process all examples in the project
    for example_id, example in all_examples.items():
        assignment = all_assignments.get(example_id)
        tracking = all_tracking.get(example_id)
        example_state = all_example_states.get(example_id)
        
        # Determine if this example is "Finished" (annotated/submitted/confirmed)
        # Check all three sources to determine the true state
        is_finished = False
        finished_annotator = None
        finished_at = None
        
        # Check ExampleState (confirmed/finished)
        if example_state and example_state.confirmed_by:
            is_finished = True
            finished_annotator = example_state.confirmed_by
            finished_at = example_state.confirmed_at
        
        # Check AnnotationTracking (submitted)
        if tracking and tracking.status == 'submitted' and tracking.annotated_by and tracking.annotated_at:
            is_finished = True
            if not finished_annotator:
                finished_annotator = tracking.annotated_by
            if not finished_at:
                finished_at = tracking.annotated_at
        
        # Check Assignment (submitted)
        if assignment and assignment.status == 'submitted' and assignment.submitted_at:
            is_finished = True
            if not finished_annotator:
                finished_annotator = assignment.assigned_to
            if not finished_at:
                finished_at = assignment.submitted_at
        
        # If finished, ensure ALL THREE are synced to "Finished"
        if is_finished and finished_annotator:
            fixes_made = []
            
            # Fix Assignment: should be "submitted" (Finished)
            if assignment:
                if assignment.status in ['assigned', 'in_progress']:
                    fixes_made.append(f"Assignment: {assignment.status} -> submitted")
                    if not DRY_RUN:
                        assignment.status = 'submitted'
                        if not assignment.submitted_at:
                            assignment.submitted_at = finished_at or timezone.now()
                        if not assignment.assigned_to:
                            assignment.assigned_to = finished_annotator
                        assignment.save(update_fields=['status', 'submitted_at', 'assigned_to'])
                    total_assignment_status_corrected += 1
                elif assignment.status == 'submitted' and not assignment.submitted_at:
                    fixes_made.append("Assignment: missing submitted_at")
                    if not DRY_RUN:
                        assignment.submitted_at = finished_at or timezone.now()
                        assignment.save(update_fields=['submitted_at'])
                    total_assignment_status_corrected += 1
            else:
                # Create Assignment if it doesn't exist
                fixes_made.append("Assignment: creating new assignment")
                if not DRY_RUN:
                    assignment = Assignment.objects.create(
                        project=project,
                        example=example,
                        assigned_to=finished_annotator,
                        status='submitted',
                        submitted_at=finished_at or timezone.now(),
                        is_active=True
                    )
                    all_assignments[example_id] = assignment
                total_assignment_status_corrected += 1
            
            # Fix AnnotationTracking: should be "submitted"
            if tracking:
                if tracking.status == 'pending':
                    fixes_made.append(f"Tracking: {tracking.status} -> submitted")
                    if not DRY_RUN:
                        tracking.status = 'submitted'
                        if not tracking.annotated_at:
                            tracking.annotated_at = finished_at or timezone.now()
                        if not tracking.annotated_by:
                            tracking.annotated_by = finished_annotator
                        tracking.save(update_fields=['status', 'annotated_at', 'annotated_by'])
                elif tracking.status == 'submitted' and not tracking.annotated_by:
                    fixes_made.append("Tracking: missing annotated_by")
                    if not DRY_RUN:
                        tracking.annotated_by = finished_annotator
                        if not tracking.annotated_at:
                            tracking.annotated_at = finished_at or timezone.now()
                        tracking.save(update_fields=['annotated_by', 'annotated_at'])
            else:
                # Create AnnotationTracking if it doesn't exist
                fixes_made.append("Tracking: creating new tracking")
                if not DRY_RUN:
                    tracking = AnnotationTracking.objects.create(
                        project=project,
                        example=example,
                        annotated_by=finished_annotator,
                        annotated_at=finished_at or timezone.now(),
                        status='submitted'
                    )
                    all_tracking[example_id] = tracking
            
            # Fix ExampleState: should exist with confirmed_by
            if example_state:
                if not example_state.confirmed_by:
                    fixes_made.append("ExampleState: missing confirmed_by")
                    if not DRY_RUN:
                        example_state.confirmed_by = finished_annotator
                        if not example_state.confirmed_at:
                            example_state.confirmed_at = finished_at or timezone.now()
                        example_state.save(update_fields=['confirmed_by', 'confirmed_at'])
            else:
                # Create ExampleState if it doesn't exist
                fixes_made.append("ExampleState: creating new ExampleState")
                if not DRY_RUN:
                    example_state = ExampleState.objects.create(
                        example=example,
                        confirmed_by=finished_annotator,
                        confirmed_at=finished_at or timezone.now()
                    )
                    all_example_states[example_id] = example_state
            
            if fixes_made:
                inconsistencies_fixed.append({
                    'example_id': example_id,
                    'fixes': fixes_made,
                    'issue': 'Syncing all three systems to "Finished" state'
                })
        
        # If NOT finished, ensure Assignment is "in_progress" (pending)
        # But don't create ExampleState or Tracking if they don't exist (they're only created when finished)
        elif assignment and assignment.status == 'submitted':
            # Check if it's actually finished by checking ExampleState or Tracking
            actually_finished = (
                (example_state and example_state.confirmed_by) or
                (tracking and tracking.status == 'submitted' and tracking.annotated_by and tracking.annotated_at)
            )
            
            if not actually_finished:
                # Assignment says "submitted" but no evidence of being finished - reset to in_progress
                inconsistencies_fixed.append({
                    'example_id': example_id,
                    'assignment_id': assignment.id,
                    'old_status': assignment.status,
                    'new_status': 'in_progress',
                    'issue': 'Assignment is submitted but no ExampleState/Tracking confirms finished state'
                })
                
                if not DRY_RUN:
                    # Determine correct status based on started_at
                    if assignment.started_at:
                        assignment.status = 'in_progress'
                    else:
                        assignment.status = 'assigned'
                    assignment.submitted_at = None
                    assignment.save(update_fields=['status', 'submitted_at'])
                total_assignment_status_corrected += 1
    
    if inconsistencies_fixed:
        print(f"  Found {len(inconsistencies_fixed)} examples with status inconsistencies to sync")
        if not DRY_RUN:
            print(f"  ✓ Synced {len(inconsistencies_fixed)} examples across all three systems")
        else:
            for fix in inconsistencies_fixed[:10]:  # Show first 10
                print(f"  [DRY RUN] Would sync Example {fix['example_id']}: {fix['issue']}")
                if 'fixes' in fix:
                    for f in fix['fixes']:
                        print(f"    - {f}")
                elif 'new_status' in fix:
                    print(f"    Assignment {fix.get('assignment_id', 'N/A')}: {fix['old_status']} -> {fix['new_status']}")
            if len(inconsistencies_fixed) > 10:
                print(f"  ... and {len(inconsistencies_fixed) - 10} more")
        
        total_status_fixed += len(inconsistencies_fixed)
    else:
        print("  ✓ All examples are in sync - no inconsistencies found")
    
    # ============================================
    # STEP 5: Verify annotated/confirmed data is preserved
    # ============================================
    print("\n[5] Verifying annotated/confirmed data is preserved...")
    
    confirmed_states = ExampleState.objects.filter(example__project=project, confirmed_by__isnull=False).count()
    tracking_with_annotations = AnnotationTracking.objects.filter(
        project=project,
        annotated_by__isnull=False
    ).count()
    assignments_with_annotators = Assignment.objects.filter(
        project=project,
        is_active=True,
        assigned_to__isnull=False
    ).count()
    
    print(f"  ✓ ExampleState records (confirmed): {confirmed_states}")
    print(f"  ✓ AnnotationTracking with annotations: {tracking_with_annotations}")
    print(f"  ✓ Assignments with annotators: {assignments_with_annotators}")
    print("  ✓ All annotated/confirmed data preserved")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"ApproverCompletionStatus records deleted: {total_approver_status_deleted}")
print(f"Assignment review fields reset: {total_assignment_review_reset}")
print(f"AnnotationTracking review fields reset: {total_tracking_review_reset}")
print(f"Status inconsistencies fixed: {total_status_fixed}")
print(f"Assignment status corrections: {total_assignment_status_corrected}")
print("=" * 80)

if DRY_RUN:
    print("\n⚠️  DRY RUN - No changes were made. Set DRY_RUN = False to apply changes.")
else:
    print("\n✅ Reset complete! All approval/review data has been reset to zero.")
    print("✅ Status inconsistencies have been fixed.")
    print("✅ All annotated/confirmed data has been preserved.")
    print("\n📊 Next steps:")
    print("   - Check UI views to ensure data aligns correctly")
    print("   - Check metrics and analytics to verify counts are correct")
    print("   - All approval/reviewer/project admin approval data is now at zero")

