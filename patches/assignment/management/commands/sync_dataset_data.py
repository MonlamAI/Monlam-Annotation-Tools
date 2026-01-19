"""
Django management command: sync_dataset_data

Syncs ExampleState, AnnotationTracking, and Assignment data to fix existing inconsistencies.
This fixes issues like missing annotator names in the dataset table.

Usage:
    python manage.py sync_dataset_data
    python manage.py sync_dataset_data --dry-run
    python manage.py sync_dataset_data --project-id 123
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from examples.models import Example, ExampleState
from assignment.simple_tracking import AnnotationTracking
from assignment.models_separate import Assignment


class Command(BaseCommand):
    help = 'Sync ExampleState, AnnotationTracking, and Assignment data to fix inconsistencies'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--project-id',
            type=int,
            help='Only sync data for a specific project ID',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each example',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        project_id = options.get('project_id')
        verbose = options.get('verbose', False)
        
        self.stdout.write("=" * 80)
        self.stdout.write("Syncing ExampleState, AnnotationTracking, and Assignment Data")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        if project_id:
            self.stdout.write(f"Project ID filter: {project_id}")
        self.stdout.write("=" * 80)
        
        # Build base querysets
        tracking_filter = Q(annotated_by__isnull=False)
        state_filter = Q()
        
        if project_id:
            tracking_filter &= Q(project_id=project_id)
            state_filter &= Q(example__project_id=project_id)
        
        # Get all relevant records
        all_trackings = AnnotationTracking.objects.filter(tracking_filter).select_related(
            'project', 'example', 'annotated_by'
        )
        
        all_states = ExampleState.objects.filter(state_filter).select_related(
            'example', 'confirmed_by'
        )
        
        # Create maps for quick lookup
        tracking_map = {t.example_id: t for t in all_trackings}
        state_map = {s.example_id: s for s in all_states}
        
        # Get all example IDs we need to process
        all_example_ids = set(tracking_map.keys()) | set(state_map.keys())
        
        if project_id:
            # Get examples from the project
            project_examples = Example.objects.filter(project_id=project_id)
            all_example_ids &= set(project_examples.values_list('id', flat=True))
        
        self.stdout.write(f"\nFound {len(all_example_ids)} examples to process")
        self.stdout.write(f"  - {len(tracking_map)} have AnnotationTracking")
        self.stdout.write(f"  - {len(state_map)} have ExampleState")
        self.stdout.write("")
        
        # Counters
        tracking_created = 0
        tracking_updated = 0
        state_created = 0
        state_updated = 0
        assignment_created = 0
        assignment_updated = 0
        errors = 0
        
        # PHASE 1: AnnotationTracking → ExampleState
        self.stdout.write("Phase 1: Creating/Updating ExampleState from AnnotationTracking...")
        for example_id in all_example_ids:
            tracking = tracking_map.get(example_id)
            state = state_map.get(example_id)
            
            if tracking and tracking.annotated_by:
                try:
                    if not state:
                        # Create ExampleState from AnnotationTracking
                        if not dry_run:
                            ExampleState.objects.create(
                                example=tracking.example,
                                confirmed_by=tracking.annotated_by,
                                confirmed_at=tracking.annotated_at or timezone.now()
                            )
                        state_created += 1
                        if verbose:
                            self.stdout.write(f"  ✓ Would create ExampleState for example {example_id} (annotated by {tracking.annotated_by.username})" if dry_run else f"  ✓ Created ExampleState for example {example_id} (annotated by {tracking.annotated_by.username})")
                    elif not state.confirmed_by:
                        # Update ExampleState with confirmed_by from AnnotationTracking
                        if not dry_run:
                            state.confirmed_by = tracking.annotated_by
                            state.confirmed_at = tracking.annotated_at or state.confirmed_at or timezone.now()
                            state.save()
                        state_updated += 1
                        if verbose:
                            self.stdout.write(f"  ↻ Would update ExampleState for example {example_id} (added confirmed_by: {tracking.annotated_by.username})" if dry_run else f"  ↻ Updated ExampleState for example {example_id} (added confirmed_by: {tracking.annotated_by.username})")
                except Exception as e:
                    errors += 1
                    self.stdout.write(self.style.ERROR(f"  ✗ Error processing example {example_id}: {e}"))
        
        # PHASE 2: ExampleState → AnnotationTracking
        self.stdout.write("\nPhase 2: Creating/Updating AnnotationTracking from ExampleState...")
        for example_id in all_example_ids:
            state = state_map.get(example_id)
            tracking = tracking_map.get(example_id)
            
            if state and state.confirmed_by:
                try:
                    if not tracking:
                        # Create AnnotationTracking from ExampleState
                        if not dry_run:
                            AnnotationTracking.objects.create(
                                project=state.example.project,
                                example=state.example,
                                annotated_by=state.confirmed_by,
                                annotated_at=state.confirmed_at or timezone.now(),
                                status='submitted'  # Confirmed = submitted for review
                            )
                        tracking_created += 1
                        if verbose:
                            self.stdout.write(f"  ✓ Would create AnnotationTracking for example {example_id} (confirmed by {state.confirmed_by.username})" if dry_run else f"  ✓ Created AnnotationTracking for example {example_id} (confirmed by {state.confirmed_by.username})")
                    elif not tracking.annotated_by:
                        # Update AnnotationTracking with annotated_by from ExampleState
                        if not dry_run:
                            tracking.annotated_by = state.confirmed_by
                            tracking.annotated_at = state.confirmed_at or tracking.annotated_at or timezone.now()
                            if tracking.status == 'pending':
                                tracking.status = 'submitted'
                            tracking.save()
                        tracking_updated += 1
                        if verbose:
                            self.stdout.write(f"  ↻ Would update AnnotationTracking for example {example_id} (added annotated_by: {state.confirmed_by.username})" if dry_run else f"  ↻ Updated AnnotationTracking for example {example_id} (added annotated_by: {state.confirmed_by.username})")
                except Exception as e:
                    errors += 1
                    self.stdout.write(self.style.ERROR(f"  ✗ Error processing example {example_id}: {e}"))
        
        # PHASE 3: Sync Assignment status
        self.stdout.write("\nPhase 3: Syncing Assignment status...")
        
        # Refresh maps after updates
        if not dry_run:
            all_trackings = AnnotationTracking.objects.filter(tracking_filter).select_related(
                'project', 'example', 'annotated_by'
            )
            tracking_map = {t.example_id: t for t in all_trackings}
        
        assignment_filter = Q(is_active=True)
        if project_id:
            assignment_filter &= Q(project_id=project_id)
        
        assignments = Assignment.objects.filter(assignment_filter).select_related(
            'project', 'example', 'assigned_to'
        )
        
        for assignment in assignments:
            example_id = assignment.example_id
            tracking = tracking_map.get(example_id)
            state = state_map.get(example_id)
            
            try:
                needs_update = False
                update_fields = []
                
                # Update status based on tracking
                if tracking:
                    if tracking.status == 'submitted' and assignment.status in ['assigned', 'in_progress', 'pending']:
                        assignment.status = 'submitted'
                        assignment.submitted_at = tracking.annotated_at or timezone.now()
                        needs_update = True
                        update_fields.extend(['status', 'submitted_at'])
                    
                    # Update assigned_to if missing
                    if not assignment.assigned_to and tracking.annotated_by:
                        assignment.assigned_to = tracking.annotated_by
                        needs_update = True
                        update_fields.append('assigned_to')
                
                # Update assigned_to from state if still missing
                if not assignment.assigned_to and state and state.confirmed_by:
                    assignment.assigned_to = state.confirmed_by
                    needs_update = True
                    if 'assigned_to' not in update_fields:
                        update_fields.append('assigned_to')
                
                if needs_update:
                    if not dry_run:
                        assignment.save(update_fields=update_fields)
                    assignment_updated += 1
                    if verbose:
                        self.stdout.write(f"  ↻ Would update Assignment for example {example_id}" if dry_run else f"  ↻ Updated Assignment for example {example_id}")
                
                # Create Assignment if it doesn't exist but tracking/state does
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f"  ✗ Error processing assignment for example {example_id}: {e}"))
        
        # PHASE 4: Create missing Assignments
        self.stdout.write("\nPhase 4: Creating missing Assignments...")
        for example_id in all_example_ids:
            tracking = tracking_map.get(example_id)
            state = state_map.get(example_id)
            
            # Check if assignment exists
            assignment_exists = Assignment.objects.filter(
                example_id=example_id,
                is_active=True
            ).exists()
            
            if not assignment_exists:
                # Determine who to assign to
                assigned_to = None
                if tracking and tracking.annotated_by:
                    assigned_to = tracking.annotated_by
                elif state and state.confirmed_by:
                    assigned_to = state.confirmed_by
                
                if assigned_to:
                    try:
                        if not dry_run:
                            # Get project from tracking or state
                            if tracking:
                                project = tracking.project
                            elif state:
                                project = state.example.project
                            else:
                                continue
                            
                            # Determine status
                            status = 'submitted'
                            submitted_at = None
                            if tracking:
                                if tracking.status == 'submitted':
                                    status = 'submitted'
                                    submitted_at = tracking.annotated_at
                                elif tracking.status == 'approved':
                                    status = 'approved'
                                elif tracking.status == 'rejected':
                                    status = 'rejected'
                            
                            Assignment.objects.create(
                                project=project,
                                example_id=example_id,
                                assigned_to=assigned_to,
                                status=status,
                                submitted_at=submitted_at,
                                is_active=True
                            )
                        assignment_created += 1
                        if verbose:
                            self.stdout.write(f"  ✓ Would create Assignment for example {example_id} (assigned to {assigned_to.username})" if dry_run else f"  ✓ Created Assignment for example {example_id} (assigned to {assigned_to.username})")
                    except Exception as e:
                        errors += 1
                        self.stdout.write(self.style.ERROR(f"  ✗ Error creating assignment for example {example_id}: {e}"))
        
        # Summary
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("Summary:")
        self.stdout.write("=" * 80)
        self.stdout.write(f"Phase 1 - AnnotationTracking → ExampleState:")
        self.stdout.write(f"  ✓ {'Would create' if dry_run else 'Created'}: {state_created}")
        self.stdout.write(f"  ↻ {'Would update' if dry_run else 'Updated'}: {state_updated}")
        self.stdout.write(f"\nPhase 2 - ExampleState → AnnotationTracking:")
        self.stdout.write(f"  ✓ {'Would create' if dry_run else 'Created'}: {tracking_created}")
        self.stdout.write(f"  ↻ {'Would update' if dry_run else 'Updated'}: {tracking_updated}")
        self.stdout.write(f"\nPhase 3 - Assignment Status Sync:")
        self.stdout.write(f"  ↻ {'Would update' if dry_run else 'Updated'}: {assignment_updated}")
        self.stdout.write(f"\nPhase 4 - Create Missing Assignments:")
        self.stdout.write(f"  ✓ {'Would create' if dry_run else 'Created'}: {assignment_created}")
        self.stdout.write(f"\nErrors: {errors}")
        self.stdout.write("=" * 80)
        
        total_fixed = state_created + state_updated + tracking_created + tracking_updated + assignment_created + assignment_updated
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n⚠️  DRY RUN - No changes were made"))
            self.stdout.write("   Run without --dry-run to apply changes")
        elif total_fixed > 0:
            self.stdout.write(self.style.SUCCESS(f"\n✅ Sync completed successfully!"))
            self.stdout.write(f"   Total records synchronized: {total_fixed}")
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ All data is already synchronized - no changes needed"))

