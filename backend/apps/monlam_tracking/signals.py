"""
Django signals for automatic annotation tracking.
Auto-updates tracking status when annotations are created.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from apps.labels.models import Category, Span, TextLabel, Relation, BoundingBox
from .models import AnnotationTracking, TrackingStatus


def update_tracking_on_annotation(instance, created):
    """
    Update tracking when an annotation is created or updated.
    
    Called by signal handlers for all annotation types.
    """
    if not hasattr(instance, 'example') or not instance.example:
        return
    
    example = instance.example
    project = example.project
    user = instance.user if hasattr(instance, 'user') else None
    
    if not user:
        return
    
    # Get or create tracking record
    tracking, _ = AnnotationTracking.objects.get_or_create(
        project=project,
        example=example,
        defaults={
            'status': TrackingStatus.SUBMITTED,
            'annotated_by': user,
            'annotated_at': timezone.now()
        }
    )
    
    # Update tracking if annotation was just created and status is pending/in_progress
    if created and tracking.status in [TrackingStatus.PENDING, TrackingStatus.IN_PROGRESS, TrackingStatus.REJECTED]:
        tracking.status = TrackingStatus.SUBMITTED
        tracking.annotated_by = user
        tracking.annotated_at = timezone.now()
        # Release lock if any
        tracking.locked_by = None
        tracking.locked_at = None
        tracking.save(update_fields=[
            'status', 'annotated_by', 'annotated_at',
            'locked_by', 'locked_at', 'updated_at'
        ])


# ============================================
# Signal handlers for each annotation type
# ============================================

@receiver(post_save, sender=Category)
def track_category_annotation(sender, instance, created, **kwargs):
    """Track category annotations."""
    update_tracking_on_annotation(instance, created)


@receiver(post_save, sender=Span)
def track_span_annotation(sender, instance, created, **kwargs):
    """Track span annotations."""
    update_tracking_on_annotation(instance, created)


@receiver(post_save, sender=TextLabel)
def track_text_label_annotation(sender, instance, created, **kwargs):
    """Track text label annotations (STT, seq2seq)."""
    update_tracking_on_annotation(instance, created)


@receiver(post_save, sender=Relation)
def track_relation_annotation(sender, instance, created, **kwargs):
    """Track relation annotations."""
    update_tracking_on_annotation(instance, created)


@receiver(post_save, sender=BoundingBox)
def track_bounding_box_annotation(sender, instance, created, **kwargs):
    """Track bounding box annotations."""
    update_tracking_on_annotation(instance, created)


# ============================================
# Cleanup handlers (optional)
# ============================================

def check_annotations_remaining(example):
    """
    Check if any annotations remain on an example after deletion.
    If none remain, reset tracking status to pending.
    """
    has_annotations = any([
        example.categorys.exists(),
        example.spans.exists(),
        example.textlabels.exists(),
        example.relations.exists(),
        example.boundingboxs.exists(),
    ])
    
    if not has_annotations:
        try:
            tracking = AnnotationTracking.objects.get(example=example)
            if tracking.status in [TrackingStatus.IN_PROGRESS, TrackingStatus.SUBMITTED]:
                tracking.status = TrackingStatus.PENDING
                tracking.annotated_by = None
                tracking.annotated_at = None
                tracking.save(update_fields=['status', 'annotated_by', 'annotated_at', 'updated_at'])
        except AnnotationTracking.DoesNotExist:
            pass


@receiver(post_delete, sender=Category)
def on_category_delete(sender, instance, **kwargs):
    """Reset tracking if all annotations deleted."""
    if hasattr(instance, 'example') and instance.example:
        check_annotations_remaining(instance.example)


@receiver(post_delete, sender=Span)
def on_span_delete(sender, instance, **kwargs):
    """Reset tracking if all annotations deleted."""
    if hasattr(instance, 'example') and instance.example:
        check_annotations_remaining(instance.example)


@receiver(post_delete, sender=TextLabel)
def on_text_label_delete(sender, instance, **kwargs):
    """Reset tracking if all annotations deleted."""
    if hasattr(instance, 'example') and instance.example:
        check_annotations_remaining(instance.example)

