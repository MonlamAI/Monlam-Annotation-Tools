"""
Auto-create TextLabels for STT examples after import.

This module automatically creates TextLabel annotations when importing
STT data with pre-filled transcripts (text field).
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
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
    from apps.labels.models import TextLabel
    
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
        logger.info(f"[Monlam] Auto-created TextLabel for example {example.id}")
        return label
    except Exception as e:
        logger.error(f"[Monlam] Failed to create TextLabel for example {example.id}: {e}")
        return None


def bulk_create_text_labels_for_project(project, user=None):
    """
    Create TextLabels for all STT examples in a project that have text but no label.
    
    Args:
        project: The Project instance
        user: The user to assign as annotator
    
    Returns:
        Number of labels created
    """
    from apps.labels.models import TextLabel
    from .models import Example
    
    # Check if this is an STT project
    if project.project_type not in ['speech_to_text', 'Speech2text']:
        return 0
    
    if user is None:
        User = get_user_model()
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.first()
    
    if not user:
        logger.warning("No user found for bulk text label creation")
        return 0
    
    # Get examples that have text but no TextLabel
    example_ids_with_labels = TextLabel.objects.filter(
        example__project=project
    ).values_list('example_id', flat=True)
    
    examples_to_label = Example.objects.filter(
        project=project
    ).exclude(
        text=''
    ).exclude(
        text__isnull=True
    ).exclude(
        id__in=example_ids_with_labels
    )
    
    if not examples_to_label.exists():
        return 0
    
    # Bulk create TextLabels
    labels = [
        TextLabel(example=ex, user=user, text=ex.text)
        for ex in examples_to_label
    ]
    
    try:
        TextLabel.objects.bulk_create(labels, ignore_conflicts=True)
        logger.info(f"[Monlam] Bulk created {len(labels)} TextLabels for project {project.id}")
        return len(labels)
    except Exception as e:
        logger.error(f"[Monlam] Failed to bulk create TextLabels: {e}")
        return 0


def setup_auto_text_label_signal():
    """
    Set up signal handler to auto-create TextLabels for STT examples.
    Called from apps.py ready() method.
    """
    from .models import Example
    
    @receiver(post_save, sender=Example)
    def auto_create_text_label(sender, instance, created, **kwargs):
        """
        Automatically create TextLabel when Example is saved with text.
        Only runs for newly created examples in STT projects.
        """
        if not created:
            return
            
        # Check if this is an STT project
        try:
            if instance.project.project_type not in ['speech_to_text', 'Speech2text']:
                return
        except:
            return
        
        if instance.text:
            create_text_label_for_example(instance)
    
    logger.info("[Monlam] Auto TextLabel signal registered")

