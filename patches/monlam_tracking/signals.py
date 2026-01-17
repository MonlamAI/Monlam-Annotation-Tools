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
        
        # Also create ExampleState to mark as confirmed (for tick mark in UI)
        # This ensures the example shows as completed/confirmed in Doccano's native UI
        if tracking.annotated_by:
            try:
                from examples.models import ExampleState
                # Use example as lookup, update confirmed_by and confirmed_at
                ExampleState.objects.update_or_create(
                    example=example,
                    defaults={
                        'confirmed_by': tracking.annotated_by,
                        'confirmed_at': tracking.annotated_at or timezone.now()
                    }
                )
                print(f'[Monlam Signals] ✅ Created/Updated ExampleState for example {example.id}')
            except Exception as e:
                print(f'[Monlam Signals] ⚠️ Could not create ExampleState: {e}')
                # Don't fail the whole signal if ExampleState creation fails
        
    except Exception as e:
        print(f'[Monlam Signals] ⚠️ Tracking failed: {e}')

