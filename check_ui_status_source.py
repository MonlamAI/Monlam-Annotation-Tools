# ============================================================================
# CHECK UI STATUS SOURCE
# ============================================================================
# This script checks what the API actually returns and how the UI determines status
# ============================================================================

from assignment.completion_tracking import ApproverCompletionStatus
from assignment.models_separate import Assignment
from assignment.simple_tracking import AnnotationTracking
from examples.models import ExampleState, Example
from projects.models import Project
from django.contrib.auth import get_user_model
from assignment.serializers import AssignmentSerializer

User = get_user_model()
PROJECT_ID = 18  # TTSEPHEL project

print("=" * 80)
print("CHECKING WHAT API RETURNS FOR UI")
print("=" * 80)

project = Project.objects.get(id=PROJECT_ID)
print(f"\nProject: {project.id} - {project.name}")

# Get assignments as the API would return them
assignments = Assignment.objects.filter(project=project, is_active=True).select_related('assigned_to', 'reviewed_by')[:20]

print(f"\n[1] Checking first 20 assignments (as API would return):")
print(f"Total active assignments: {Assignment.objects.filter(project=project, is_active=True).count()}")

for assignment in assignments:
    example_state = ExampleState.objects.filter(example_id=assignment.example_id).first()
    
    # Check ApproverCompletionStatus
    has_approval = ApproverCompletionStatus.objects.filter(
        example_id=assignment.example_id,
        project=project,
        status='approved'
    ).exists()
    
    # Serialize as API would
    serializer = AssignmentSerializer(assignment)
    api_data = serializer.data
    
    # Determine what UI would show
    # Annotator status: "Finished" if ExampleState.confirmed_by exists, else "In progress"
    annotator_status = "Finished" if (example_state and example_state.confirmed_by) else "In progress"
    
    # Approval status: Based on Assignment.status or ApproverCompletionStatus
    approval_status = None
    if api_data['status'] == 'approved':
        approval_status = "APPROVED"
    elif api_data['status'] == 'submitted':
        approval_status = "SUBMITTED"
    elif api_data['status'] == 'rejected':
        approval_status = "REJECTED"
    elif has_approval:
        approval_status = "APPROVED"  # Even if Assignment.status is not 'approved'
    
    # Check if this would show "In progress" + "APPROVED"
    is_invalid = (annotator_status == "In progress" and approval_status == "APPROVED")
    
    if is_invalid or assignment.example_id in [615, 616, 617, 618, 619]:  # Show the ones from the image
        print(f"\n  Example {assignment.example_id}:")
        print(f"    Assignment.status: {api_data['status']}")
        print(f"    Assignment.reviewed_by: {api_data.get('reviewed_by_username')}")
        print(f"    Assignment.has_final_approval: {api_data.get('has_final_approval')}")
        print(f"    ExampleState.confirmed_by: {example_state.confirmed_by.username if example_state and example_state.confirmed_by else None}")
        print(f"    Has ApproverCompletionStatus: {has_approval}")
        print(f"    → UI would show: {annotator_status} + {approval_status or '(no status)'}")
        if is_invalid:
            print(f"    ⚠️  INVALID COMBINATION!")

# Check specific examples from the image (615, 616, 617, 618, 619)
print(f"\n[2] Checking specific examples from image:")
for example_id in [615, 616, 617, 618, 619]:
    try:
        example = Example.objects.get(id=example_id, project=project)
        assignment = Assignment.objects.filter(example_id=example_id, project=project, is_active=True).first()
        example_state = ExampleState.objects.filter(example_id=example_id).first()
        tracking = AnnotationTracking.objects.filter(example_id=example_id, project=project).first()
        has_approval = ApproverCompletionStatus.objects.filter(
            example_id=example_id,
            project=project,
            status='approved'
        ).exists()
        
        print(f"\n  Example {example_id}:")
        print(f"    Assignment: {assignment.id if assignment else 'None'}")
        if assignment:
            print(f"      - status: {assignment.status}")
            print(f"      - assigned_to: {assignment.assigned_to.username if assignment.assigned_to else None}")
            print(f"      - submitted_at: {assignment.submitted_at}")
            print(f"      - reviewed_by: {assignment.reviewed_by.username if assignment.reviewed_by else None}")
        print(f"    ExampleState: {example_state.id if example_state else 'None'}")
        if example_state:
            print(f"      - confirmed_by: {example_state.confirmed_by.username if example_state.confirmed_by else None}")
        print(f"    AnnotationTracking: {tracking.id if tracking else 'None'}")
        if tracking:
            print(f"      - status: {tracking.status}")
            print(f"      - annotated_by: {tracking.annotated_by.username if tracking.annotated_by else None}")
        print(f"    Has ApproverCompletionStatus (approved): {has_approval}")
        
        # What UI would show
        annotator_status = "Finished" if (example_state and example_state.confirmed_by) else "In progress"
        if assignment:
            if assignment.status == 'approved' or has_approval:
                approval_status = "APPROVED"
            elif assignment.status == 'submitted':
                approval_status = "SUBMITTED"
            else:
                approval_status = None
        else:
            approval_status = None
        
        print(f"    → UI would show: {annotator_status} + {approval_status or '(no status)'}")
        
    except Example.DoesNotExist:
        print(f"\n  Example {example_id}: NOT FOUND")

print("\n" + "=" * 80)

