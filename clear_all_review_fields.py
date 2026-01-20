# ============================================================================
# CLEAR ALL REVIEW FIELDS
# ============================================================================
# This ensures ALL review/approval fields are cleared, not just status
# ============================================================================

from django.db import transaction
from assignment.models_separate import Assignment
from assignment.simple_tracking import AnnotationTracking
from projects.models import Project

DRY_RUN = False
PROJECT_ID = 18  # TTSEPHEL project

print("=" * 80)
print("CLEARING ALL REVIEW FIELDS")
print("=" * 80)
if DRY_RUN:
    print("⚠️  DRY RUN MODE")
print("=" * 80)

project = Project.objects.get(id=PROJECT_ID)

# Clear Assignment review fields
assignments_with_review = Assignment.objects.filter(
    project=project,
    is_active=True
).exclude(
    reviewed_by__isnull=True,
    reviewed_at__isnull=True,
    review_notes=''
).exclude(
    reviewed_by__isnull=True,
    reviewed_at__isnull=True
).distinct()

# Actually, let's check all assignments
all_assignments = Assignment.objects.filter(project=project, is_active=True)
assignments_to_clear = []

for assignment in all_assignments:
    if assignment.reviewed_by or assignment.reviewed_at or assignment.review_notes or assignment.status in ['approved', 'rejected']:
        assignments_to_clear.append(assignment)

print(f"\n[1] Assignments with review data: {len(assignments_to_clear)}")

if not DRY_RUN:
    with transaction.atomic():
        for assignment in assignments_to_clear:
            assignment.reviewed_by = None
            assignment.reviewed_at = None
            assignment.review_notes = ''
            if assignment.status in ['approved', 'rejected']:
                if assignment.submitted_at:
                    assignment.status = 'submitted'
                elif assignment.started_at:
                    assignment.status = 'in_progress'
                else:
                    assignment.status = 'assigned'
            assignment.save(update_fields=['reviewed_by', 'reviewed_at', 'review_notes', 'status'])
    print(f"  ✓ Cleared review fields for {len(assignments_to_clear)} assignments")
else:
    for assignment in assignments_to_clear[:5]:
        print(f"  [DRY RUN] Would clear Assignment {assignment.id}: reviewed_by={assignment.reviewed_by}, status={assignment.status}")

# Clear AnnotationTracking review fields
tracking_with_review = AnnotationTracking.objects.filter(project=project).exclude(
    reviewed_by__isnull=True,
    reviewed_at__isnull=True,
    review_notes=''
).distinct()

tracking_to_clear = []
for tracking in AnnotationTracking.objects.filter(project=project):
    if tracking.reviewed_by or tracking.reviewed_at or tracking.review_notes or tracking.status in ['reviewed', 'rejected']:
        tracking_to_clear.append(tracking)

print(f"\n[2] AnnotationTracking with review data: {len(tracking_to_clear)}")

if not DRY_RUN:
    with transaction.atomic():
        for tracking in tracking_to_clear:
            tracking.reviewed_by = None
            tracking.reviewed_at = None
            tracking.review_notes = ''
            if tracking.status in ['reviewed', 'rejected']:
                if tracking.annotated_by and tracking.annotated_at:
                    tracking.status = 'submitted'
                else:
                    tracking.status = 'pending'
            tracking.save(update_fields=['reviewed_by', 'reviewed_at', 'review_notes', 'status'])
    print(f"  ✓ Cleared review fields for {len(tracking_to_clear)} tracking records")

print("\n" + "=" * 80)
print("COMPLETE")
print("=" * 80)

