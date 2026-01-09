"""
Simple Annotation Tracking System

Tracks:
- Who annotated an example (first person to submit)
- Who reviewed it (approver/project manager)
- Status (pending, submitted, approved, rejected)

No complex assignment system - just tracking who did what.
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AnnotationTracking(models.Model):
    """
    Simple tracking of who annotated and who reviewed each example
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
    
    # Who annotated this example (first person to submit)
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
    
    # Who reviewed this example
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_examples'
    )
    
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),           # Not annotated yet
        ('submitted', 'Submitted'),       # Annotated, awaiting review
        ('approved', 'Approved'),         # Approved by reviewer
        ('rejected', 'Rejected'),         # Rejected, needs revision
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    review_notes = models.TextField(blank=True, default='')
    
    # Locking fields (to prevent simultaneous editing)
    locked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='locked_examples'
    )
    
    locked_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'annotation_tracking'
        unique_together = [('project', 'example')]
        indexes = [
            models.Index(fields=['project', 'example']),
            models.Index(fields=['project', 'status']),
            models.Index(fields=['annotated_by']),
            models.Index(fields=['reviewed_by']),
            models.Index(fields=['locked_by']),
        ]
    
    def __str__(self):
        return f"Tracking for Example {self.example_id} in Project {self.project_id}"

