"""
Patched models.py for Doccano with Assignment System.

This file replaces /doccano/backend/examples/models.py
Adds task assignment and review tracking fields.
Based on original Doccano 1.8.4 models.py
"""

import uuid

from django.contrib.auth.models import User
from django.db import models
from django_drf_filepond.models import DrfFilePondStoredStorage

from .managers import ExampleManager, ExampleStateManager
from projects.models import Project


class Example(models.Model):
    objects = ExampleManager()

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True, unique=True)
    meta = models.JSONField(default=dict)
    filename = models.FileField(default=".", max_length=1024, storage=DrfFilePondStoredStorage())
    upload_name = models.CharField(max_length=512)
    project = models.ForeignKey(to=Project, on_delete=models.CASCADE, related_name="examples")
    annotations_approved_by = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True, blank=True)
    text = models.TextField(null=True, blank=True)
    score = models.FloatField(default=100)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

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
        to=User,
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
        to=User,
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
    def comment_count(self):
        return Comment.objects.filter(example=self.id).count()

    @property
    def data(self):
        if self.project.is_text_project:
            return self.text
        else:
            return str(self.filename)

    class Meta:
        ordering = ["created_at"]


class ExampleState(models.Model):
    objects = ExampleStateManager()
    example = models.ForeignKey(to=Example, on_delete=models.CASCADE, related_name="states")
    confirmed_by = models.ForeignKey(to=User, on_delete=models.CASCADE)
    confirmed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("example", "confirmed_by"),)


class Comment(models.Model):
    text = models.TextField()
    example = models.ForeignKey(to=Example, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def username(self):
        return self.user.username

    class Meta:
        ordering = ["created_at"]
