#!/usr/bin/env python
"""
Fix ApproverCompletionStatus records for unfinished examples.
This removes invalid approval records that cause "In progress" + "APPROVED" display.
"""

import os
import sys
import django

if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
    django.setup()

from django.db import transaction
from assignment.completion_tracking import ApproverCompletionStatus
from examples.models import ExampleState
from projects.models import Project

DRY_RUN = False  # Set to True to preview changes

print("=" * 80)
print("FIXING INVALID ApproverCompletionStatus RECORDS")
print("=" * 80)
if DRY_RUN:
    print("⚠️  DRY RUN MODE - No changes will be made")
print("=" * 80)

projects = Project.objects.all()
total_deleted = 0
total_checked = 0

for project in projects:
    print(f"\n{'=' * 80}")
    print(f"Processing Project: {project.id} - {project.name}")
    print(f"{'=' * 80}")
    
    # Get all ApproverCompletionStatus records for this project
    approver_statuses = ApproverCompletionStatus.objects.filter(project=project).select_related('example')
    
    # Get all ExampleState records for examples in this project
    example_ids = list(approver_statuses.values_list('example_id', flat=True).distinct())
    example_states = ExampleState.objects.filter(example_id__in=example_ids).select_related('confirmed_by')
    
    # Create map for quick lookup
    states_map = {s.example_id: s for s in example_states}
    
    deleted_in_project = 0
    
    for ap_status in approver_statuses:
        total_checked += 1
        example_id = ap_status.example_id
        example_state = states_map.get(example_id)
        
        # Check if example is finished
        is_finished = example_state and example_state.confirmed_by is not None
        
        # If NOT finished but has ApproverCompletionStatus → INVALID, should be deleted
        if not is_finished:
            print(f"  🔧 Example {example_id}: Deleting invalid ApproverCompletionStatus (ID: {ap_status.id}, status: '{ap_status.status}', approver: {ap_status.approver.username})")
            print(f"     Reason: Example not finished (ExampleState.confirmed_by is NULL)")
            
            if not DRY_RUN:
                with transaction.atomic():
                    ap_status.delete()
            deleted_in_project += 1
            total_deleted += 1
    
    print(f"\n  ✓ Checked {approver_statuses.count()} ApproverCompletionStatus records")
    if deleted_in_project > 0:
        print(f"  ✅ Deleted {deleted_in_project} invalid records")
    else:
        print(f"  ✓ No invalid records found")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total ApproverCompletionStatus records checked: {total_checked}")
print(f"Total invalid records deleted: {total_deleted}")
print("=" * 80)

if DRY_RUN:
    print("\n⚠️  DRY RUN - No changes were made. Set DRY_RUN = False to apply changes.")
else:
    print("\n✅ Fix complete! All invalid ApproverCompletionStatus records have been deleted.")
    print("   Refresh the dataset page to see the corrected statuses.")
    print("   'In progress' examples should no longer show 'APPROVED'.")

