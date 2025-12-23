"""
Patched models.py for Doccano with Assignment System.

This file replaces /doccano/backend/examples/models.py
Adds task assignment and review tracking fields.
"""

import uuid

from django.conf import settings
from django.db import models


class Example(models.Model):
    """
    Example model with assignment support.
    Each example can be assigned to a specific annotator.
    """
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True, unique=True)
    meta = models.JSONField(default=dict)
    filename = models.FileField(default=".", max_length=1024)
    upload_name = models.CharField(max_length=512, default="")
    text = models.TextField(null=True, blank=True)
    score = models.FloatField(default=100)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    annotations_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_examples",
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="examples",
    )

    # ============================================
    # ASSIGNMENT FIELDS - Added for task assignment
    # ============================================
    
    ASSIGNMENT_STATUS_CHOICES = [
        ('unassigned', 'Unassigned'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted for Review'),
        ('approved', 'Approved'),
        ('rejected', 'Needs Revision'),
    ]
    
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_examples',
        help_text='User assigned to annotate this example'
    )
    
    assignment_status = models.CharField(
        max_length=20,
        choices=ASSIGNMENT_STATUS_CHOICES,
        default='unassigned',
        db_index=True
    )
    
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_examples',
        help_text='Approver who reviewed this example'
    )
    
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, default='')

    # ============================================
    # END ASSIGNMENT FIELDS
    # ============================================

    @property
    def comment_count(self) -> int:
        return Comment.objects.filter(example=self.id).count()

    class Meta:
        ordering = ["created_at"]


class ExampleState(models.Model):
    """
    Tracks confirmation state per example per user.
    """
    example = models.ForeignKey(
        to=Example,
        on_delete=models.CASCADE,
        related_name="states",
    )
    confirmed_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    confirmed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("example", "confirmed_by"),)


class Comment(models.Model):
    """
    Comments on examples.
    """
    text = models.TextField()
    example = models.ForeignKey(
        to=Example,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def username(self) -> str:
        return self.user.username if self.user else ""

    class Meta:
        ordering = ["created_at"]

