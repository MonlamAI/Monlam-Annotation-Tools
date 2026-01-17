"""
Django management command: backfill_example_state

Backfills ExampleState records for all submitted examples that don't have one.

Usage:
    python manage.py backfill_example_state
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from examples.models import Example, ExampleState
from assignment.simple_tracking import AnnotationTracking


class Command(BaseCommand):
    help = 'Backfill ExampleState records for all submitted examples'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each example',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        self.stdout.write("=" * 80)
        self.stdout.write("Backfilling ExampleState for submitted examples")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        self.stdout.write("=" * 80)
        
        # Find ALL tracking records with annotators (not just 'submitted' status)
        # This includes 'pending', 'submitted', 'approved', 'rejected'
        # We want to ensure all examples that have been annotated also have ExampleState
        all_trackings = AnnotationTracking.objects.filter(
            annotated_by__isnull=False
        ).select_related('example', 'annotated_by')
        
        # Also find ExampleState records that might not have AnnotationTracking
        # This handles cases where tick mark was clicked but no annotation was created
        all_example_states = ExampleState.objects.filter(
            confirmed_by__isnull=False
        ).select_related('example', 'confirmed_by')
        
        total_trackings = all_trackings.count()
        total_states = all_example_states.count()
        
        self.stdout.write(f"\nFound {total_trackings} AnnotationTracking records with annotators")
        self.stdout.write(f"Found {total_states} ExampleState records")
        
        # Get set of example IDs that already have ExampleState
        examples_with_state = set(
            ExampleState.objects.filter(confirmed_by__isnull=False).values_list('example_id', flat=True)
        )
        
        # Find trackings that need ExampleState created
        trackings_needing_state = [
            t for t in all_trackings 
            if t.example_id not in examples_with_state
        ]
        
        total_count = len(trackings_needing_state)
        self.stdout.write(f"Found {total_count} AnnotationTracking records WITHOUT ExampleState\n")
        
        # Diagnostic: Show status breakdown
        if verbose:
            from django.db.models import Count
            status_breakdown = AnnotationTracking.objects.filter(
                annotated_by__isnull=False
            ).values('status').annotate(count=Count('id')).order_by('status')
            
            self.stdout.write("\nStatus breakdown of AnnotationTracking records:")
            for item in status_breakdown:
                self.stdout.write(f"  {item['status']}: {item['count']}")
            
            # Show how many have ExampleState vs don't
            tracking_with_state = AnnotationTracking.objects.filter(
                annotated_by__isnull=False,
                example_id__in=examples_with_state
            ).count()
            tracking_without_state = total_trackings - tracking_with_state
            self.stdout.write(f"\nAnnotationTracking records:")
            self.stdout.write(f"  With ExampleState: {tracking_with_state}")
            self.stdout.write(f"  Without ExampleState: {tracking_without_state}")
            self.stdout.write("")
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        for tracking in trackings_needing_state:
            try:
                example = tracking.example
                annotated_by = tracking.annotated_by
                annotated_at = tracking.annotated_at or timezone.now()
                
                # Check if ExampleState already exists for this example
                existing_state = ExampleState.objects.filter(example=example).first()
                
                if existing_state:
                    # Update if the confirmed_by is different or not set
                    if existing_state.confirmed_by != annotated_by:
                        if verbose:
                            self.stdout.write(
                                f"  ↻ Would update ExampleState for example {example.id} "
                                f"(annotated by {annotated_by.username})"
                            )
                        if not dry_run:
                            existing_state.confirmed_by = annotated_by
                            existing_state.confirmed_at = annotated_at
                            existing_state.save()
                            updated_count += 1
                            if verbose:
                                self.stdout.write(self.style.SUCCESS(f"    ✓ Updated"))
                        else:
                            updated_count += 1
                    else:
                        skipped_count += 1
                        if verbose and skipped_count <= 10:
                            self.stdout.write(
                                f"  - Skipped example {example.id} (already has ExampleState)"
                            )
                else:
                    # Create new ExampleState
                    if verbose:
                        self.stdout.write(
                            f"  ✓ Would create ExampleState for example {example.id} "
                            f"(annotated by {annotated_by.username})"
                        )
                    if not dry_run:
                        ExampleState.objects.create(
                            example=example,
                            confirmed_by=annotated_by,
                            confirmed_at=annotated_at
                        )
                        created_count += 1
                        if verbose:
                            self.stdout.write(self.style.SUCCESS(f"    ✓ Created"))
                    else:
                        created_count += 1
            
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Error processing example {tracking.example_id}: {e}")
                )
        
        # PHASE 2: Create AnnotationTracking for ExampleState records that don't have it
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("Phase 2: Creating AnnotationTracking for ExampleState records")
        self.stdout.write("=" * 80)
        
        # Get set of example IDs that already have AnnotationTracking
        examples_with_tracking = set(
            AnnotationTracking.objects.filter(annotated_by__isnull=False).values_list('example_id', flat=True)
        )
        
        # Find ExampleState records that need AnnotationTracking
        states_needing_tracking = [
            state for state in all_example_states
            if state.example_id not in examples_with_tracking
        ]
        
        tracking_created_count = 0
        tracking_error_count = 0
        
        self.stdout.write(f"\nFound {len(states_needing_tracking)} ExampleState records WITHOUT AnnotationTracking\n")
        
        for state in states_needing_tracking:
            try:
                example = state.example
                confirmed_by = state.confirmed_by
                confirmed_at = state.confirmed_at or timezone.now()
                
                if verbose:
                    self.stdout.write(
                        f"  ✓ Would create AnnotationTracking for example {example.id} "
                        f"(confirmed by {confirmed_by.username})"
                    )
                
                if not dry_run:
                    # Create AnnotationTracking with status based on whether it's been reviewed
                    # If confirmed_at is recent and no review, it's likely 'submitted'
                    # Otherwise check if there's any approval/rejection info
                    status = 'submitted'  # Default to submitted
                    
                    AnnotationTracking.objects.create(
                        project=example.project,
                        example=example,
                        annotated_by=confirmed_by,
                        annotated_at=confirmed_at,
                        status=status
                    )
                    tracking_created_count += 1
                    if verbose:
                        self.stdout.write(self.style.SUCCESS(f"    ✓ Created"))
                else:
                    tracking_created_count += 1
                    
            except Exception as e:
                tracking_error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Error creating AnnotationTracking for example {state.example_id}: {e}")
                )
        
        # Summary
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("Summary:")
        self.stdout.write("=" * 80)
        self.stdout.write(f"Phase 1 - AnnotationTracking → ExampleState:")
        self.stdout.write(f"  Total checked: {total_count}")
        self.stdout.write(f"  ✓ Would create: {created_count}" if dry_run else f"  ✓ Created: {created_count}")
        self.stdout.write(f"  ↻ Would update: {updated_count}" if dry_run else f"  ↻ Updated: {updated_count}")
        self.stdout.write(f"  - Skipped (already exists): {skipped_count}")
        self.stdout.write(f"  ✗ Errors: {error_count}")
        self.stdout.write("")
        self.stdout.write(f"Phase 2 - ExampleState → AnnotationTracking:")
        self.stdout.write(f"  Total checked: {len(states_needing_tracking)}")
        self.stdout.write(f"  ✓ Would create: {tracking_created_count}" if dry_run else f"  ✓ Created: {tracking_created_count}")
        self.stdout.write(f"  ✗ Errors: {tracking_error_count}")
        self.stdout.write("=" * 80)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n⚠️  DRY RUN - No changes were made"))
            self.stdout.write("   Run without --dry-run to apply changes")
        elif created_count > 0 or updated_count > 0 or tracking_created_count > 0:
            total_fixed = created_count + updated_count + tracking_created_count
            self.stdout.write(self.style.SUCCESS("\n✅ Backfill completed successfully!"))
            self.stdout.write(f"   {created_count + updated_count} ExampleState records created/updated")
            self.stdout.write(f"   {tracking_created_count} AnnotationTracking records created")
            self.stdout.write(f"   Total: {total_fixed} records synchronized")
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ All examples already have matching ExampleState and AnnotationTracking records - no changes needed"))

