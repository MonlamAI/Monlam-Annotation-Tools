"""
Django Signals for Auto-Tracking

Automatically creates tracking records when annotations are saved.
Uses Django's signal system properly.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


def setup_annotation_signals():
    """
    Connect signal handlers for annotation models.
    Called from apps.py ready() method.
    """
    try:
        # Import annotation models
        from labels.models import Category, Span, TextLabel
        
        # Models to track
        models_to_track = [Category, Span, TextLabel]
        
        for model in models_to_track:
            post_save.connect(
                track_annotation_saved,
                sender=model,
                dispatch_uid=f'monlam_track_{model.__name__}'
            )
            print(f'[Monlam Signals] ✅ Connected tracking for {model.__name__}')
        
        return True
        
    except Exception as e:
        print(f'[Monlam Signals] ⚠️ Setup failed: {e}')
        return False


def track_annotation_saved(sender, instance, created, **kwargs):
    """
    Signal handler that tracks when an annotation is created.
    
    Creates or updates AnnotationTracking record.
    """
    if not created:
        return  # Only track new annotations
    
    try:
        from assignment.simple_tracking import AnnotationTracking
        
        # Get example and user
        example = instance.example
        user = instance.user if hasattr(instance, 'user') else None
        
        if not user or not example:
            return
        
        # Create or update tracking
        tracking, tracking_created = AnnotationTracking.objects.get_or_create(
            project=example.project,
            example=example,
            defaults={
                'annotated_by': user,
                'annotated_at': timezone.now(),
                'status': 'submitted'
            }
        )
        
        # If tracking exists but no annotator yet, update it
        if not tracking_created and not tracking.annotated_by:
            tracking.annotated_by = user
            tracking.annotated_at = timezone.now()
            tracking.status = 'submitted'
            tracking.save()
            print(f'[Monlam Signals] ✅ Updated tracking for example {example.id}')
        elif tracking_created:
            print(f'[Monlam Signals] ✅ Created tracking for example {example.id}')
        
        # CRITICAL: Also create ExampleState to mark as confirmed (same as tick mark)
        # This ensures Enter key and tick mark both create ExampleState
        # This is essential for completion dashboard to show correct counts
        if tracking.annotated_by:
            try:
                from examples.models import ExampleState
                import traceback
                
                # Use example as lookup, update confirmed_by and confirmed_at
                # This makes Enter key equivalent to clicking tick mark
                state, state_created = ExampleState.objects.update_or_create(
                    example=example,
                    defaults={
                        'confirmed_by': tracking.annotated_by,
                        'confirmed_at': tracking.annotated_at or timezone.now()
                    }
                )
                
                if state_created:
                    print(f'[Monlam Signals] ✅ Created ExampleState for example {example.id} (Enter key pressed)')
                else:
                    print(f'[Monlam Signals] ✅ Updated ExampleState for example {example.id} (Enter key pressed)')
                    
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                print(f'[Monlam Signals] ❌ CRITICAL: Could not create ExampleState for example {example.id}')
                print(f'[Monlam Signals] Error: {e}')
                print(f'[Monlam Signals] Traceback: {error_trace}')
                # Try again with more explicit error handling
                try:
                    # Force create if update_or_create failed
                    from examples.models import ExampleState
                    ExampleState.objects.create(
                        example=example,
                        confirmed_by=tracking.annotated_by,
                        confirmed_at=tracking.annotated_at or timezone.now()
                    )
                    print(f'[Monlam Signals] ✅ Retry successful: Created ExampleState for example {example.id}')
                except Exception as e2:
                    # Check if it's because ExampleState already exists (that's okay)
                    if 'unique constraint' in str(e2).lower() or 'already exists' in str(e2).lower():
                        print(f'[Monlam Signals] ✅ ExampleState already exists for example {example.id} (this is okay)')
                    else:
                        print(f'[Monlam Signals] ❌ Retry also failed: {e2}')
                        print(f'[Monlam Signals] Traceback: {traceback.format_exc()}')
                    # Don't fail the whole signal, but log the error prominently
        
    except Exception as e:
        print(f'[Monlam Signals] ⚠️ Tracking failed: {e}')

