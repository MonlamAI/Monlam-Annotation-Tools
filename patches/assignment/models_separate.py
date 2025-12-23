"""
Assignment Models - Separate table approach (NON-INVASIVE)

This module creates a separate Assignment table that references
Doccano's Example model via ForeignKey, rather than modifying
the core Example model.

Benefits:
- No migration conflicts with core Doccano
- Easy to add/remove without breaking existing data
- Can be upgraded independently
- Tracks full assignment history
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class Assignment(models.Model):
    """
    Tracks assignment of examples to annotators.
    
    Each example can have one active assignment at a time,
    but historical assignments are preserved.
    """
    
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted for Review'),
        ('approved', 'Approved'),
        ('rejected', 'Needs Revision'),
        ('reassigned', 'Reassigned'),
    ]
    
    # Reference to Example (from examples app)
    example = models.ForeignKey(
        'examples.Example',
        on_delete=models.CASCADE,
        related_name='assignments',
        help_text='The example this assignment is for'
    )
    
    # Reference to Project (for easier querying)
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='assignments',
        help_text='Project this assignment belongs to'
    )
    
    # Annotator assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignments_received',
        help_text='User assigned to annotate this example'
    )
    
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignments_given',
        help_text='Admin who made the assignment'
    )
    
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='assigned',
        db_index=True
    )
    
    # Progress tracking
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    # Review tracking
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignments_reviewed',
        help_text='Approver who reviewed this'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, default='')
    
    # Is this the current/active assignment?
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        ordering = ['-assigned_at']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['example', 'is_active']),
        ]
    
    def __str__(self):
        return f"Assignment #{self.id}: Example {self.example_id} -> {self.assigned_to}"
    
    def start(self):
        """Mark assignment as in progress."""
        self.status = 'in_progress'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])
    
    def submit(self):
        """Submit for review."""
        self.status = 'submitted'
        self.submitted_at = timezone.now()
        self.save(update_fields=['status', 'submitted_at'])
    
    def approve(self, reviewer, notes=''):
        """Approve the annotation."""
        self.status = 'approved'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'review_notes'])
    
    def reject(self, reviewer, notes=''):
        """Reject and request revision."""
        self.status = 'rejected'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'review_notes'])
    
    def reassign(self, new_user, assigned_by):
        """Reassign to a different user."""
        # Deactivate current assignment
        self.is_active = False
        self.status = 'reassigned'
        self.save(update_fields=['is_active', 'status'])
        
        # Create new assignment
        return Assignment.objects.create(
            example=self.example,
            project=self.project,
            assigned_to=new_user,
            assigned_by=assigned_by,
            is_active=True
        )
    
    @classmethod
    def get_active_assignment(cls, example):
        """Get the current active assignment for an example."""
        return cls.objects.filter(example=example, is_active=True).first()
    
    @classmethod
    def bulk_assign(cls, examples, user, assigned_by, project):
        """Assign multiple examples to a user."""
        # Deactivate any existing active assignments
        cls.objects.filter(
            example__in=examples,
            is_active=True
        ).update(is_active=False, status='reassigned')
        
        # Create new assignments
        assignments = [
            cls(
                example=ex,
                project=project,
                assigned_to=user,
                assigned_by=assigned_by,
                is_active=True
            )
            for ex in examples
        ]
        return cls.objects.bulk_create(assignments)


class AssignmentBatch(models.Model):
    """
    Tracks batches of assignments for easier management.
    When admin assigns 100 items to annotator01, this creates one batch.
    """
    
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='assignment_batches'
    )
    
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assignment_batches_received'
    )
    
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assignment_batches_given'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Stats
    total_count = models.PositiveIntegerField(default=0)
    completed_count = models.PositiveIntegerField(default=0)
    approved_count = models.PositiveIntegerField(default=0)
    
    notes = models.TextField(blank=True, default='')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Assignment batches'
    
    def __str__(self):
        return f"Batch #{self.id}: {self.total_count} items -> {self.assigned_to}"
    
    def update_stats(self):
        """Update completion statistics."""
        assignments = Assignment.objects.filter(
            project=self.project,
            assigned_to=self.assigned_to,
            assigned_at__gte=self.created_at
        )
        self.total_count = assignments.count()
        self.completed_count = assignments.filter(status__in=['submitted', 'approved']).count()
        self.approved_count = assignments.filter(status='approved').count()
        self.save(update_fields=['total_count', 'completed_count', 'approved_count'])

