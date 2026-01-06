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

