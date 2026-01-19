"""
Django management command: clean_non_member_data

Cleans up data where non-project members are stored as annotators/reviewers.
This fixes issues where users who were removed from projects still appear as annotators.

What it cleans:
1. AnnotationTracking records where annotated_by is not a project member
2. ExampleState records where confirmed_by is not a project member  
3. Assignment records where assigned_to is not a project member

It retains all data for actual project members.

Usage:
    python manage.py clean_non_member_data
    python manage.py clean_non_member_data --dry-run
    python manage.py clean_non_member_data --project-id 123
    python manage.py clean_non_member_data --verbose

Note: 
- AnnotationTracking.annotated_by and Assignment.assigned_to will be set to NULL
- ExampleState records with non-member confirmed_by will be DELETED (confirmed_by has NOT NULL constraint)
"""

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db import transaction
from examples.models import Example, ExampleState
from assignment.simple_tracking import AnnotationTracking
from assignment.models_separate import Assignment
from projects.models import Member, Project


class Command(BaseCommand):
    help = 'Clean up data where non-project members are stored as annotators/reviewers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--project-id',
            type=int,
            help='Only clean data for a specific project ID',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each record',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        project_id = options.get('project_id')
        verbose = options.get('verbose', False)
        
        self.stdout.write("=" * 80)
        self.stdout.write("Cleaning Non-Member Data from Tracking Records")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        if project_id:
            self.stdout.write(f"Project ID filter: {project_id}")
        self.stdout.write("Note: 
- AnnotationTracking.annotated_by and Assignment.assigned_to will be set to NULL
- ExampleState records with non-member confirmed_by will be DELETED (confirmed_by has NOT NULL constraint)")
        self.stdout.write("=" * 80)
        
        # Get all projects to process
        projects = Project.objects.all()
        if project_id:
            projects = projects.filter(id=project_id)
        
        total_tracking_cleaned = 0
        total_state_cleaned = 0
        total_assignment_cleaned = 0
        
        for project in projects:
            self.stdout.write(f"\n{'=' * 80}")
            self.stdout.write(f"Processing Project: {project.id} - {project.name}")
            self.stdout.write(f"{'=' * 80}")
            
            # Get all project members (including superusers)
            project_member_ids = set(
                Member.objects.filter(project=project).values_list('user_id', flat=True)
            )
            
            # Also include superusers (they're always allowed)
            from django.contrib.auth import get_user_model
            User = get_user_model()
            superuser_ids = set(
                User.objects.filter(is_superuser=True).values_list('id', flat=True)
            )
            
            # Combined set of allowed user IDs
            allowed_user_ids = project_member_ids | superuser_ids
            
            self.stdout.write(f"Project has {len(project_member_ids)} members")
            if verbose:
                members = Member.objects.filter(project=project).select_related('user')
                for member in members:
                    self.stdout.write(f"  - {member.user.username} (ID: {member.user.id})")
            
            # 1. Clean AnnotationTracking records
            tracking_records = AnnotationTracking.objects.filter(
                project=project,
                annotated_by__isnull=False
            ).select_related('annotated_by', 'example')
            
            non_member_trackings = [
                t for t in tracking_records
                if t.annotated_by_id not in allowed_user_ids
            ]
            
            if non_member_trackings:
                self.stdout.write(f"\n[AnnotationTracking] Found {len(non_member_trackings)} records with non-members:")
                for tracking in non_member_trackings:
                    self.stdout.write(
                        f"  - Example {tracking.example_id}: annotated_by={tracking.annotated_by.username} "
                        f"(ID: {tracking.annotated_by_id}, Status: {tracking.status})"
                    )
                    
                    if not dry_run:
                        with transaction.atomic():
                            tracking.annotated_by = None
                            tracking.save(update_fields=['annotated_by'])
                            self.stdout.write(self.style.SUCCESS(
                                f"    ✓ Set annotated_by to NULL"
                            ))
                    else:
                        self.stdout.write(self.style.WARNING("    [DRY RUN] Would set annotated_by to NULL"))
                
                total_tracking_cleaned += len(non_member_trackings)
            else:
                self.stdout.write(f"\n[AnnotationTracking] ✓ All records have valid project members")
            
            # 2. Clean ExampleState records
            state_records = ExampleState.objects.filter(
                example__project=project,
                confirmed_by__isnull=False
            ).select_related('confirmed_by', 'example')
            
            non_member_states = [
                s for s in state_records
                if s.confirmed_by_id not in allowed_user_ids
            ]
            
            if non_member_states:
                self.stdout.write(f"\n[ExampleState] Found {len(non_member_states)} records with non-members:")
                self.stdout.write(self.style.WARNING(
                    "  Note: ExampleState.confirmed_by has NOT NULL constraint, so records will be deleted"
                ))
                for state in non_member_states:
                    self.stdout.write(
                        f"  - Example {state.example_id}: confirmed_by={state.confirmed_by.username} "
                        f"(ID: {state.confirmed_by_id})"
                    )
                    
                    if not dry_run:
                        with transaction.atomic():
                            # ExampleState.confirmed_by has NOT NULL constraint, so we must delete the record
                            example_id = state.example_id
                            state.delete()
                            self.stdout.write(self.style.SUCCESS(
                                f"    ✓ Deleted ExampleState record (confirmed_by cannot be NULL)"
                            ))
                    else:
                        self.stdout.write(self.style.WARNING("    [DRY RUN] Would delete ExampleState record"))
                
                total_state_cleaned += len(non_member_states)
            else:
                self.stdout.write(f"\n[ExampleState] ✓ All records have valid project members")
            
            # 3. Clean Assignment records
            assignment_records = Assignment.objects.filter(
                project=project,
                is_active=True,
                assigned_to__isnull=False
            ).select_related('assigned_to', 'example')
            
            non_member_assignments = [
                a for a in assignment_records
                if a.assigned_to_id not in allowed_user_ids
            ]
            
            if non_member_assignments:
                self.stdout.write(f"\n[Assignment] Found {len(non_member_assignments)} records with non-members:")
                for assignment in non_member_assignments:
                    self.stdout.write(
                        f"  - Example {assignment.example_id}: assigned_to={assignment.assigned_to.username} "
                        f"(ID: {assignment.assigned_to_id}, Status: {assignment.status})"
                    )
                    
                    if not dry_run:
                        with transaction.atomic():
                            assignment.assigned_to = None
                            assignment.save(update_fields=['assigned_to'])
                            self.stdout.write(self.style.SUCCESS(
                                f"    ✓ Set assigned_to to NULL"
                            ))
                    else:
                        self.stdout.write(self.style.WARNING("    [DRY RUN] Would set assigned_to to NULL"))
                
                total_assignment_cleaned += len(non_member_assignments)
            else:
                self.stdout.write(f"\n[Assignment] ✓ All records have valid project members")
        
        # Summary
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("SUMMARY")
        self.stdout.write("=" * 80)
        self.stdout.write(f"AnnotationTracking records cleaned: {total_tracking_cleaned}")
        self.stdout.write(f"ExampleState records cleaned: {total_state_cleaned}")
        self.stdout.write(f"Assignment records cleaned: {total_assignment_cleaned}")
        self.stdout.write(f"Total records cleaned: {total_tracking_cleaned + total_state_cleaned + total_assignment_cleaned}")
        self.stdout.write("=" * 80)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n⚠️  DRY RUN - No changes were made. Run without --dry-run to apply changes."))
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ Cleanup complete!"))

