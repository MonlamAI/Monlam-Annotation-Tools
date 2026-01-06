#!/usr/bin/env python
"""
Script to create assignments for annotators.

Usage:
    python scripts/create_assignments.py --project 9 --user annotator01 --examples 1-100
    python scripts/create_assignments.py --project 9 --user annotator01 --all
"""

import os
import sys
import django

# Setup Django
sys.path.append('/doccano/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from django.contrib.auth import get_user_model
from projects.models import Project
from examples.models import Example
from assignment.models_separate import Assignment

User = get_user_model()


def create_assignments(project_id, username, example_ids=None, assign_all=False):
    """
    Create assignments for a user.
    
    Args:
        project_id: Project ID
        username: Username to assign to
        example_ids: List of example IDs (or None if assign_all)
        assign_all: If True, assign all unassigned examples
    """
    try:
        # Get project
        project = Project.objects.get(pk=project_id)
        print(f"✓ Found project: {project.name}")
        
        # Get user
        user = User.objects.get(username=username)
        print(f"✓ Found user: {user.username}")
        
        # Get examples
        if assign_all:
            # Get all examples not yet assigned
            already_assigned = Assignment.objects.filter(
                project=project,
                is_active=True
            ).values_list('example_id', flat=True)
            
            examples = Example.objects.filter(
                project=project
            ).exclude(id__in=already_assigned)
            
            print(f"✓ Found {examples.count()} unassigned examples")
        else:
            examples = Example.objects.filter(
                project=project,
                id__in=example_ids
            )
            print(f"✓ Found {examples.count()} examples")
        
        # Create assignments
        created_count = 0
        skipped_count = 0
        
        for example in examples:
            # Check if already assigned
            existing = Assignment.objects.filter(
                project=project,
                example=example,
                is_active=True
            ).exists()
            
            if existing:
                print(f"  ⊘ Example {example.id} already assigned, skipping")
                skipped_count += 1
                continue
            
            # Create assignment
            Assignment.objects.create(
                project=project,
                example=example,
                assigned_to=user,
                assigned_by=user,  # Or use admin user
                status='assigned'
            )
            created_count += 1
            print(f"  ✓ Assigned example {example.id} to {username}")
        
        print(f"\n✅ Created {created_count} assignments")
        if skipped_count > 0:
            print(f"⊘ Skipped {skipped_count} already assigned")
        
        return created_count
        
    except Project.DoesNotExist:
        print(f"❌ Project {project_id} not found")
        return 0
    except User.DoesNotExist:
        print(f"❌ User '{username}' not found")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 0


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Create assignments for annotators')
    parser.add_argument('--project', type=int, required=True, help='Project ID')
    parser.add_argument('--user', required=True, help='Username to assign to')
    parser.add_argument('--examples', help='Example IDs (e.g., "1,2,3" or "1-100")')
    parser.add_argument('--all', action='store_true', help='Assign all unassigned examples')
    
    args = parser.parse_args()
    
    # Parse example IDs
    example_ids = None
    if args.examples and not args.all:
        if '-' in args.examples:
            # Range: "1-100"
            start, end = map(int, args.examples.split('-'))
            example_ids = list(range(start, end + 1))
        else:
            # List: "1,2,3,4"
            example_ids = [int(x.strip()) for x in args.examples.split(',')]
    
    # Create assignments
    create_assignments(
        project_id=args.project,
        username=args.user,
        example_ids=example_ids,
        assign_all=args.all
    )


if __name__ == '__main__':
    main()

