#!/usr/bin/env python
"""
Simple script to fix Assignment status values.
Can be run directly: python fix_status_simple.py
Or via Django shell: python manage.py shell < fix_status_simple.py
"""

import os
import sys
import django

# Setup Django if not already set up
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
    django.setup()

from django.db import transaction
from assignment.models_separate import Assignment
from assignment.completion_tracking import ApproverCompletionStatus
from examples.models import ExampleState
from projects.models import Project

DRY_RUN = False  # Set to True to preview changes

print("=" * 80)
print("FIXING INCORRECT ASSIGNMENT STATUS VALUES")
print("=" * 80)
if DRY_RUN:
    print("⚠️  DRY RUN MODE - No changes will be made")
print("=" * 80)

projects = Project.objects.all()
total_fixed = 0
total_checked = 0

for project in projects:
    print(f"\n{'=' * 80}")
    print(f"Processing Project: {project.id} - {project.name}")
    print(f"{'=' * 80}")
    
    assignments = Assignment.objects.filter(project=project, is_active=True).select_related('example', 'assigned_to')
    example_ids = list(assignments.values_list('example_id', flat=True))
    example_states = ExampleState.objects.filter(example_id__in=example_ids).select_related('confirmed_by')
    states_map = {s.example_id: s for s in example_states}
    
    approver_statuses = ApproverCompletionStatus.objects.filter(project=project)
    approval_map = {}
    for ap_status in approver_statuses:
        example_id = ap_status.example_id
        if example_id not in approval_map:
            approval_map[example_id] = {'approved': False, 'rejected': False}
        if ap_status.status == 'approved':
            approval_map[example_id]['approved'] = True
        elif ap_status.status == 'rejected':
            approval_map[example_id]['rejected'] = True
    
    fixed_in_project = 0
    
    for assignment in assignments:
        total_checked += 1
        example_id = assignment.example_id
        example_state = states_map.get(example_id)
        is_finished = example_state and example_state.confirmed_by is not None
        
        needs_fix = False
        original_status = assignment.status
        new_status = None
        update_fields = []
        
        if not is_finished and assignment.status in ['approved', 'rejected', 'submitted']:
            needs_fix = True
            new_status = 'in_progress' if assignment.started_at else 'assigned'
            print(f"  🔧 Example {example_id}, Assignment {assignment.id}: '{original_status}' → '{new_status}' (example not finished)")
            
            if not DRY_RUN:
                assignment.status = new_status
                update_fields.append('status')
                if original_status == 'submitted' and assignment.submitted_at:
                    assignment.submitted_at = None
                    update_fields.append('submitted_at')
                if original_status in ['approved', 'rejected']:
                    if assignment.reviewed_by:
                        assignment.reviewed_by = None
                        update_fields.append('reviewed_by')
                    if assignment.reviewed_at:
                        assignment.reviewed_at = None
                        update_fields.append('reviewed_at')
                    if assignment.review_notes:
                        assignment.review_notes = ''
                        update_fields.append('review_notes')
        
        elif is_finished:
            approval_info = approval_map.get(example_id, {'approved': False, 'rejected': False})
            if approval_info['rejected']:
                expected_status = 'rejected'
            elif approval_info['approved']:
                expected_status = 'approved'
            else:
                expected_status = 'submitted'
            
            if assignment.status != expected_status:
                needs_fix = True
                new_status = expected_status
                print(f"  🔧 Example {example_id}, Assignment {assignment.id}: '{original_status}' → '{new_status}' (finished example)")
                
                if not DRY_RUN:
                    assignment.status = new_status
                    update_fields.append('status')
                    if expected_status == 'submitted' and not assignment.submitted_at:
                        assignment.submitted_at = example_state.confirmed_at or assignment.started_at
                        update_fields.append('submitted_at')
        
        if needs_fix and not DRY_RUN:
            with transaction.atomic():
                assignment.save(update_fields=update_fields)
            fixed_in_project += 1
            total_fixed += 1
    
    print(f"\n  ✓ Checked {assignments.count()} assignments")
    if fixed_in_project > 0:
        print(f"  ✅ Fixed {fixed_in_project} assignments")
    else:
        print(f"  ✓ No fixes needed")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total assignments checked: {total_checked}")
print(f"Total assignments fixed: {total_fixed}")
print("=" * 80)

if DRY_RUN:
    print("\n⚠️  DRY RUN - No changes were made. Set DRY_RUN = False to apply changes.")
else:
    print("\n✅ Fix complete! All incorrect Assignment.status values have been corrected.")
    print("   Refresh the dataset page to see the corrected statuses.")

