"""
AnnotationTracking model for Monlam Doccano.
Core model for tracking annotation status, reviews, and example locking.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class TrackingStatus(models.TextChoices):
    """Status choices for annotation tracking."""
    PENDING = 'pending', 'Pending'
    IN_PROGRESS = 'in_progress', 'In Progress'
    SUBMITTED = 'submitted', 'Submitted'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'


class AnnotationTracking(models.Model):
    """
    Tracks annotation and review status for each example.
    
    One tracking record per (project, example) pair.
    
    Workflow:
    1. Example starts as 'pending' (no tracking record or status=pending)
    2. Annotator opens example -> status='in_progress', locked_by=user
    3. Annotator saves annotation -> status='submitted'
    4. Reviewer approves -> status='approved', example hidden from annotators
    5. Reviewer rejects -> status='rejected', visible to original annotator only
    """
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='tracking_records'
    )
    example = models.OneToOneField(
        'examples.Example',
        on_delete=models.CASCADE,
        related_name='tracking'
    )
    
    # Tracking fields
    annotated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='annotations_tracked'
    )
    annotated_at = models.DateTimeField(null=True, blank=True)
    
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews_tracked'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=TrackingStatus.choices,
        default=TrackingStatus.PENDING
    )
    
    # Review notes (especially important for rejections)
    review_notes = models.TextField(blank=True, default='')
    
    # Example locking to prevent simultaneous editing
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='locked_examples'
    )
    locked_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'monlam_tracking_annotationtracking'
        unique_together = ('project', 'example')
        ordering = ['example__id']
        indexes = [
            models.Index(fields=['project', 'example']),
            models.Index(fields=['project', 'status']),
            models.Index(fields=['annotated_by']),
            models.Index(fields=['reviewed_by']),
            models.Index(fields=['locked_by']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Tracking for Example #{self.example_id}: {self.status}"
    
    @property
    def is_locked(self):
        """Check if example is currently locked."""
        if not self.locked_by:
            return False
        
        # Check if lock has expired (15 minutes timeout)
        if self.locked_at:
            lock_timeout = settings.MONLAM_SETTINGS.get('LOCK_TIMEOUT_MINUTES', 15)
            lock_expiry = self.locked_at + timezone.timedelta(minutes=lock_timeout)
            if timezone.now() > lock_expiry:
                # Lock expired, auto-release
                self.release_lock()
                return False
        
        return True
    
    def acquire_lock(self, user):
        """
        Acquire lock on this example for the user.
        Returns True if lock acquired, False if already locked by another user.
        """
        if self.is_locked and self.locked_by != user:
            return False
        
        self.locked_by = user
        self.locked_at = timezone.now()
        self.save(update_fields=['locked_by', 'locked_at', 'updated_at'])
        return True
    
    def release_lock(self):
        """Release the lock on this example."""
        self.locked_by = None
        self.locked_at = None
        self.save(update_fields=['locked_by', 'locked_at', 'updated_at'])
    
    def mark_in_progress(self, user):
        """Mark example as in progress by the user."""
        self.status = TrackingStatus.IN_PROGRESS
        self.annotated_by = user
        self.save(update_fields=['status', 'annotated_by', 'updated_at'])
    
    def mark_submitted(self, user):
        """Mark example as submitted after annotation."""
        self.status = TrackingStatus.SUBMITTED
        self.annotated_by = user
        self.annotated_at = timezone.now()
        self.release_lock()
        self.save(update_fields=['status', 'annotated_by', 'annotated_at', 
                                  'locked_by', 'locked_at', 'updated_at'])
    
    def approve(self, reviewer, notes=''):
        """Approve the annotation."""
        self.status = TrackingStatus.APPROVED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 
                                  'review_notes', 'updated_at'])
    
    def reject(self, reviewer, notes):
        """Reject the annotation with required notes."""
        self.status = TrackingStatus.REJECTED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 
                                  'review_notes', 'updated_at'])


def get_or_create_tracking(project, example):
    """
    Get or create a tracking record for an example.
    Utility function used by signals and views.
    """
    tracking, created = AnnotationTracking.objects.get_or_create(
        project=project,
        example=example,
        defaults={'status': TrackingStatus.PENDING}
    )
    return tracking

