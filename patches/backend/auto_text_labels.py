"""
Auto-create TextLabels for STT examples after import.

This module patches Doccano's data import to automatically create TextLabel
annotations when importing STT data with pre-filled transcripts.

Place in: /doccano/backend/data_import/auto_text_labels.py
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from examples.models import Example
from labels.models import TextLabel
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)


def create_text_label_for_example(example, user=None):
    """
    Create a TextLabel for an example if it has text and no existing label.
    
    Args:
        example: The Example instance
        user: The user to assign as annotator (defaults to first superuser)
    
    Returns:
        TextLabel or None if label already exists or no text
    """
    # Skip if no text
    if not example.text:
        return None
    
    # Skip if already has a TextLabel
    if TextLabel.objects.filter(example=example).exists():
        return None
    
    # Get user if not provided
    if user is None:
        User = get_user_model()
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.first()
    
    if not user:
        logger.warning(f"No user found for auto text label on example {example.id}")
        return None
    
    # Create the TextLabel
    try:
        label = TextLabel.objects.create(
            example=example,
            user=user,
            text=example.text
        )
        logger.info(f"Auto-created TextLabel for example {example.id}")
        return label
    except Exception as e:
        logger.error(f"Failed to create TextLabel for example {example.id}: {e}")
        return None


def bulk_create_text_labels(examples, user=None):
    """
    Create TextLabels for multiple examples in bulk.
    
    Args:
        examples: QuerySet or list of Example instances
        user: The user to assign as annotator
    
    Returns:
        Number of labels created
    """
    if user is None:
        User = get_user_model()
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.first()
    
    if not user:
        logger.warning("No user found for bulk text label creation")
        return 0
    
    # Get examples that have text but no TextLabel
    example_ids_with_labels = TextLabel.objects.values_list('example_id', flat=True)
    
    examples_to_label = [
        ex for ex in examples 
        if ex.text and ex.id not in example_ids_with_labels
    ]
    
    if not examples_to_label:
        return 0
    
    # Bulk create TextLabels
    labels = [
        TextLabel(example=ex, user=user, text=ex.text)
        for ex in examples_to_label
    ]
    
    try:
        TextLabel.objects.bulk_create(labels, ignore_conflicts=True)
        logger.info(f"Bulk created {len(labels)} TextLabels")
        return len(labels)
    except Exception as e:
        logger.error(f"Failed to bulk create TextLabels: {e}")
        return 0


# Signal handler - triggers after each Example save
# Note: This can be slow for bulk imports, use bulk_create_text_labels instead
@receiver(post_save, sender=Example)
def auto_create_text_label(sender, instance, created, **kwargs):
    """
    Automatically create TextLabel when Example is saved with text.
    Only runs for newly created examples to avoid duplicates.
    """
    if created and instance.text:
        create_text_label_for_example(instance)

