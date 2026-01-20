# ============================================================================
# CHECK API RESPONSE
# ============================================================================
# Simulate what the API endpoint returns to see what UI would receive
# ============================================================================

from assignment.models_separate import Assignment
from assignment.serializers import AssignmentSerializer
from projects.models import Project
from django.http import HttpRequest
from django.contrib.auth import get_user_model

User = get_user_model()
PROJECT_ID = 18  # TTSEPHEL project

print("=" * 80)
print("CHECKING API RESPONSE (what UI receives)")
print("=" * 80)

project = Project.objects.get(id=PROJECT_ID)
print(f"\nProject: {project.id} - {project.name}")

# Get assignments as API would return
assignments = Assignment.objects.filter(project=project, is_active=True).select_related('assigned_to', 'reviewed_by')

print(f"\nTotal assignments: {assignments.count()}")

# Check for assignments with status='approved' in API response
approved_in_api = []
for assignment in assignments:
    serializer = AssignmentSerializer(assignment)
    api_data = serializer.data
    
    if api_data['status'] == 'approved':
        approved_in_api.append({
            'assignment_id': assignment.id,
            'example_id': assignment.example_id,
            'api_status': api_data['status'],
            'reviewed_by': api_data.get('reviewed_by_username'),
            'has_final_approval': api_data.get('has_final_approval'),
            'reviewed_by_role': api_data.get('reviewed_by_role')
        })

print(f"\n[1] Assignments with status='approved' in API response: {len(approved_in_api)}")

if approved_in_api:
    print("\n  These would show 'APPROVED' in UI:")
    for item in approved_in_api[:10]:
        print(f"    - Assignment {item['assignment_id']} (Example {item['example_id']}): status={item['api_status']}, reviewed_by={item['reviewed_by']}, has_final_approval={item['has_final_approval']}")
else:
    print("  ✓ No assignments with status='approved' in API response")

# Check specific examples from image
print(f"\n[2] Checking specific examples (615-619) API response:")
for example_id in [615, 616, 617, 618, 619]:
    assignment = Assignment.objects.filter(example_id=example_id, project=project, is_active=True).first()
    if assignment:
        serializer = AssignmentSerializer(assignment)
        api_data = serializer.data
        print(f"\n  Example {example_id}:")
        print(f"    API status: {api_data['status']}")
        print(f"    reviewed_by: {api_data.get('reviewed_by_username')}")
        print(f"    reviewed_by_role: {api_data.get('reviewed_by_role')}")
        print(f"    has_final_approval: {api_data.get('has_final_approval')}")
        print(f"    → UI would show: {api_data['status'].upper() if api_data['status'] == 'approved' else api_data['status'].upper()}")

print("\n" + "=" * 80)

