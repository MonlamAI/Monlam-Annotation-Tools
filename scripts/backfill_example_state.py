"""
Backfill ExampleState for existing submitted annotations

This script creates ExampleState records for all examples that have been
submitted (have AnnotationTracking with status='submitted') but don't have
a corresponding ExampleState record.

Run this script on Render after deploying the fix to ensure all existing
submitted examples show the tick mark correctly.

Usage:
    python scripts/backfill_example_state.py
    or
    python manage.py shell < scripts/backfill_example_state.py
"""

import os
import sys
import django

# Setup Django environment
if __name__ == '__main__':
    # Add the project directory to the path
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_dir)
    
    # Set the Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
    
    django.setup()

from django.utils import timezone
from examples.models import Example, ExampleState
from assignment.simple_tracking import AnnotationTracking


def backfill_example_states():
    """
    Backfill ExampleState records for all submitted examples.
    """
    print("=" * 80)
    print("Backfilling ExampleState for submitted examples")
    print("=" * 80)
    
    # Find all submitted tracking records
    submitted_trackings = AnnotationTracking.objects.filter(
        status='submitted',
        annotated_by__isnull=False
    ).select_related('example', 'annotated_by')
    
    total_count = submitted_trackings.count()
    print(f"\nFound {total_count} submitted examples to check")
    
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
                    existing_state.confirmed_by = annotated_by
                    existing_state.confirmed_at = annotated_at
                    existing_state.save()
                    updated_count += 1
                    print(f"  ✓ Updated ExampleState for example {example.id} (annotated by {annotated_by.username})")
                else:
                    skipped_count += 1
                    if skipped_count <= 10:  # Only print first 10 skipped
                        print(f"  - Skipped example {example.id} (already has ExampleState)")
            else:
                # Create new ExampleState
                ExampleState.objects.create(
                    example=example,
                    confirmed_by=annotated_by,
                    confirmed_at=annotated_at
                )
                created_count += 1
                if created_count <= 20:  # Print first 20 created
                    print(f"  ✓ Created ExampleState for example {example.id} (annotated by {annotated_by.username})")
                elif created_count == 21:
                    print(f"  ... (continuing, will show summary at end)")
        
        except Exception as e:
            error_count += 1
            print(f"  ✗ Error processing example {tracking.example_id}: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("Summary:")
    print("=" * 80)
    print(f"Total submitted examples checked: {total_count}")
    print(f"  ✓ Created: {created_count}")
    print(f"  ↻ Updated: {updated_count}")
    print(f"  - Skipped (already exists): {skipped_count}")
    print(f"  ✗ Errors: {error_count}")
    print("=" * 80)
    
    if created_count > 0 or updated_count > 0:
        print("\n✅ Backfill completed successfully!")
        print(f"   {created_count + updated_count} examples now have ExampleState records")
    else:
        print("\n✅ All examples already have ExampleState records - no changes needed")
    
    return {
        'total': total_count,
        'created': created_count,
        'updated': updated_count,
        'skipped': skipped_count,
        'errors': error_count
    }


if __name__ == '__main__':
    try:
        result = backfill_example_states()
        sys.exit(0 if result['errors'] == 0 else 1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

