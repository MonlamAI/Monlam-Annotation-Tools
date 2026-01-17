"""
Auto-tracking of Annotations

Automatically create tracking records when annotations are saved.
This ensures the system tracks who annotated what without manual API calls.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


def setup_auto_tracking():
    """
    Set up signal handlers to auto-track annotations
    """
    try:
        # Import models
        from labels.models import Label, Category, Span, TextLabel, Relation
        from assignment.simple_tracking import AnnotationTracking
        
        # Common models that represent annotations
        annotation_models = [Label, Category, Span, TextLabel, Relation]
        
        def track_annotation(sender, instance, created, **kwargs):
            """
            Track when an annotation is created or updated
            """
            if not created:
                return  # Only track new annotations
            
            try:
                # Get the example and user
                example = instance.example
                user = instance.user if hasattr(instance, 'user') else None
                
                if not user:
                    return
                
                # Create or update tracking record
                tracking, tracking_created = AnnotationTracking.objects.get_or_create(
                    project=example.project,
                    example=example,
                    defaults={
                        'annotated_by': user,
                        'annotated_at': timezone.now(),
                        'status': 'submitted'
                    }
                )
                
                # If tracking already exists, update it
                if not tracking_created and not tracking.annotated_by:
                    tracking.annotated_by = user
                    tracking.annotated_at = timezone.now()
                    tracking.status = 'submitted'
                    tracking.save()
                
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
                        print(f"[Monlam] ✅ Created/Updated ExampleState for example {example.id}")
                    except Exception as e:
                        print(f"[Monlam] ⚠️ Could not create ExampleState: {e}")
                        # Don't fail the whole signal if ExampleState creation fails
                    
                print(f"[Monlam] ✅ Auto-tracked annotation by {user.username} on example {example.id}")
                
            except Exception as e:
                print(f"[Monlam] ⚠️ Auto-tracking failed: {e}")
        
        # Connect signal handlers for all annotation models
        for model in annotation_models:
            try:
                post_save.connect(track_annotation, sender=model)
                print(f"[Monlam] ✅ Connected auto-tracking for {model.__name__}")
            except Exception as e:
                print(f"[Monlam] ⚠️ Could not connect auto-tracking for {model.__name__}: {e}")
        
        return True
        
    except Exception as e:
        print(f"[Monlam] ⚠️ Auto-tracking setup failed: {e}")
        return False


# Set up on import
setup_auto_tracking()

