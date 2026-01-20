# Quick check for approved status in API
from assignment.models_separate import Assignment
from assignment.serializers import AssignmentSerializer
from projects.models import Project

project = Project.objects.get(id=18)
assignments = Assignment.objects.filter(project=project, is_active=True, status='approved')
print(f"Assignments with status='approved' in DB: {assignments.count()}")

# Check what API returns
approved_in_api = []
for assignment in Assignment.objects.filter(project=project, is_active=True)[:100]:
    serializer = AssignmentSerializer(assignment)
    if serializer.data['status'] == 'approved':
        approved_in_api.append(assignment.example_id)

print(f"Assignments with status='approved' in API response (first 100): {len(approved_in_api)}")
if approved_in_api:
    print(f"Example IDs: {approved_in_api[:10]}")

