# ============================================================================
# CHECK reviewed_by FIELD
# ============================================================================
# Check if Assignment.reviewed_by is set (this might cause UI to show APPROVED)
# ============================================================================

from assignment.models_separate import Assignment
from examples.models import ExampleState
from projects.models import Project

PROJECT_ID = 18  # TTSEPHEL project

print("=" * 80)
print("CHECKING Assignment.reviewed_by FIELD")
print("=" * 80)

project = Project.objects.get(id=PROJECT_ID)
print(f"\nProject: {project.id} - {project.name}")

# Check assignments with reviewed_by set
assignments_with_reviewer = Assignment.objects.filter(
    project=project,
    is_active=True,
    reviewed_by__isnull=False
)

print(f"\n[1] Assignments with reviewed_by set: {assignments_with_reviewer.count()}")

for assignment in assignments_with_reviewer[:20]:
    example_state = ExampleState.objects.filter(example_id=assignment.example_id).first()
    annotator_status = "Finished" if (example_state and example_state.confirmed_by) else "In progress"
    
    print(f"\n  Assignment {assignment.id} (Example {assignment.example_id}):")
    print(f"    - status: {assignment.status}")
    print(f"    - reviewed_by: {assignment.reviewed_by.username if assignment.reviewed_by else None}")
    print(f"    - reviewed_at: {assignment.reviewed_at}")
    print(f"    - review_notes: {assignment.review_notes[:50] if assignment.review_notes else ''}")
    print(f"    - ExampleState.confirmed_by: {example_state.confirmed_by.username if example_state and example_state.confirmed_by else None}")
    print(f"    → Would show: {annotator_status} + {'APPROVED' if assignment.reviewed_by else assignment.status}")

# Check if UI might be using reviewed_by to determine APPROVED
print(f"\n[2] Checking if UI uses reviewed_by to show APPROVED:")
print(f"    If UI checks 'if reviewed_by exists, show APPROVED', then:")
print(f"    - {assignments_with_reviewer.count()} assignments would show APPROVED")
print(f"    - Even though status might be 'submitted' or 'in_progress'")

print("\n" + "=" * 80)
print("SOLUTION: Clear reviewed_by field for all assignments")
print("=" * 80)

