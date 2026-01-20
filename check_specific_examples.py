#!/usr/bin/env python
"""
Diagnostic script to check specific examples that show "In progress" + "APPROVED"
"""

import os
import sys
import django

if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
    django.setup()

from assignment.models_separate import Assignment
from assignment.completion_tracking import ApproverCompletionStatus
from examples.models import ExampleState, Example
from projects.models import Project

# Check the specific examples from the image
example_ids = [615, 616, 617, 618, 619]

print("=" * 80)
print("CHECKING SPECIFIC EXAMPLES")
print("=" * 80)

for example_id in example_ids:
    try:
        example = Example.objects.get(id=example_id)
        project = example.project
        
        print(f"\nExample {example_id} (Project: {project.id} - {project.name}):")
        print("-" * 80)
        
        # Check ExampleState
        example_state = ExampleState.objects.filter(example_id=example_id).first()
        is_finished = example_state and example_state.confirmed_by is not None
        print(f"  ExampleState.confirmed_by: {example_state.confirmed_by.username if example_state and example_state.confirmed_by else 'NULL'}")
        print(f"  Is Finished: {is_finished}")
        
        # Check Assignment
        assignment = Assignment.objects.filter(example_id=example_id, project=project, is_active=True).first()
        if assignment:
            print(f"  Assignment.status: {assignment.status}")
            print(f"  Assignment.started_at: {assignment.started_at}")
            print(f"  Assignment.submitted_at: {assignment.submitted_at}")
        else:
            print(f"  Assignment: None")
        
        # Check ApproverCompletionStatus
        approver_statuses = ApproverCompletionStatus.objects.filter(
            example_id=example_id,
            project=project
        )
        print(f"  ApproverCompletionStatus records: {approver_statuses.count()}")
        for ap_status in approver_statuses:
            print(f"    - ID {ap_status.id}: status='{ap_status.status}', approver={ap_status.approver.username}, reviewed_at={ap_status.reviewed_at}")
        
        # What the serializer would return
        if is_finished:
            has_rejection = approver_statuses.filter(status='rejected').exists()
            has_approval = approver_statuses.filter(status='approved').exists()
            if has_rejection:
                expected_status = 'rejected'
            elif has_approval:
                expected_status = 'approved'
            else:
                expected_status = 'submitted'
        else:
            expected_status = 'in_progress' if (assignment and assignment.started_at) else 'assigned'
        
        print(f"  Expected Status (from serializer logic): {expected_status}")
        
        # Check if there's a problem
        if not is_finished and approver_statuses.exists():
            print(f"  ⚠️  PROBLEM: Example not finished but has ApproverCompletionStatus records!")
            print(f"     This is why it shows 'APPROVED' - these records should be deleted")
        
    except Example.DoesNotExist:
        print(f"\nExample {example_id}: NOT FOUND")
    except Exception as e:
        print(f"\nExample {example_id}: ERROR - {e}")

print("\n" + "=" * 80)

