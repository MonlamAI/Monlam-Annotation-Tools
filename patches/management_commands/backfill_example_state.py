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
        
        # Find all submitted tracking records
        submitted_trackings = AnnotationTracking.objects.filter(
            status='submitted',
            annotated_by__isnull=False
        ).select_related('example', 'annotated_by')
        
        total_count = submitted_trackings.count()
        self.stdout.write(f"\nFound {total_count} submitted examples to check\n")
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        for tracking in submitted_trackings:
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
        
        # Summary
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("Summary:")
        self.stdout.write("=" * 80)
        self.stdout.write(f"Total submitted examples checked: {total_count}")
        self.stdout.write(f"  ✓ Would create: {created_count}" if dry_run else f"  ✓ Created: {created_count}")
        self.stdout.write(f"  ↻ Would update: {updated_count}" if dry_run else f"  ↻ Updated: {updated_count}")
        self.stdout.write(f"  - Skipped (already exists): {skipped_count}")
        self.stdout.write(f"  ✗ Errors: {error_count}")
        self.stdout.write("=" * 80)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n⚠️  DRY RUN - No changes were made"))
            self.stdout.write("   Run without --dry-run to apply changes")
        elif created_count > 0 or updated_count > 0:
            self.stdout.write(self.style.SUCCESS("\n✅ Backfill completed successfully!"))
            self.stdout.write(f"   {created_count + updated_count} examples now have ExampleState records")
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ All examples already have ExampleState records - no changes needed"))








