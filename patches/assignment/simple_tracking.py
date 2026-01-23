"""
Simple Annotation Tracking System

Tracks:
- Who annotated an example (annotated_by) - for comprehensive metrics
- Who reviewed it (reviewed_by) - for comprehensive metrics  
- Status (pending, submitted, reviewed, rejected)
- Timestamps for when annotated and reviewed

Note: Fields are kept for comprehensive data tracking and metrics,
but not displayed in dataset table (single annotator per project).
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AnnotationTracking(models.Model):
    """
    Simple tracking of example status with comprehensive data tracking.
    Tracks who annotated and who reviewed for metrics, but simplified for single annotator workflow.
    """
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='annotation_tracking'
    )
    
    example = models.ForeignKey(
        'examples.Example',
        on_delete=models.CASCADE,
        related_name='annotation_tracking'
    )
    
    # Who annotated this example (kept for comprehensive metrics)
    annotated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='annotated_examples'
    )
    
    annotated_at = models.DateTimeField(null=True, blank=True)
    
    # Time tracking
    started_at = models.DateTimeField(null=True, blank=True)  # When annotator started
    time_spent_seconds = models.IntegerField(null=True, blank=True)  # Calculated duration
    
    # Who reviewed this example (kept for comprehensive metrics)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_examples'
    )
    
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Status - shows if reviewed or not after submission
    STATUS_CHOICES = [
        ('pending', 'Pending'),           # Not annotated yet
        ('submitted', 'Submitted'),       # Annotated and submitted, awaiting review
        ('reviewed', 'Reviewed'),         # Reviewed and approved (changed from 'approved')
        ('rejected', 'Rejected'),         # Rejected, needs revision
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    review_notes = models.TextField(blank=True, default='')
    
    class Meta:
        db_table = 'annotation_tracking'
        unique_together = [('project', 'example')]
        indexes = [
            models.Index(fields=['project', 'example']),
            models.Index(fields=['project', 'status']),
            models.Index(fields=['annotated_by']),
            models.Index(fields=['reviewed_by']),
        ]
    
    def __str__(self):
        return f"Tracking for Example {self.example_id} in Project {self.project_id} - Status: {self.status}"


class SkippedExample(models.Model):
    """
    Tracks examples that annotators have permanently skipped (with a reason).
    These examples will not appear in the annotator's view anymore.
    
    Note: This is different from temporary skipping (just navigating away).
    Permanent skip means the annotator doesn't want to see this example again.
    """
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='skipped_examples'
    )
    
    example = models.ForeignKey(
        'examples.Example',
        on_delete=models.CASCADE,
        related_name='skipped_by_annotators'
    )
    
    skipped_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='skipped_examples',
        help_text='The annotator who skipped this example'
    )
    
    skipped_at = models.DateTimeField(auto_now_add=True)
    
    reason = models.TextField(
        blank=True,
        default='',
        help_text='Reason why this example was skipped (e.g., "Poor audio quality", "Not relevant", etc.)'
    )
    
    class Meta:
        db_table = 'skipped_example'
        unique_together = [('project', 'example', 'skipped_by')]
        indexes = [
            models.Index(fields=['project', 'skipped_by']),
            models.Index(fields=['example']),
        ]
    
    def __str__(self):
        return f"Example {self.example_id} skipped by {self.skipped_by.username} in Project {self.project_id}"

