"""
Project models for Monlam Doccano.
Includes project types and role-based access control.
"""

from django.db import models
from django.conf import settings


class ProjectType(models.TextChoices):
    """Types of annotation projects."""
    SEQUENCE_LABELING = 'sequence_labeling', 'Sequence Labeling'
    DOCUMENT_CLASSIFICATION = 'document_classification', 'Document Classification'
    SEQ2SEQ = 'seq2seq', 'Sequence to Sequence'
    SPEECH_TO_TEXT = 'speech_to_text', 'Speech to Text'
    IMAGE_CLASSIFICATION = 'image_classification', 'Image Classification'
    BOUNDING_BOX = 'bounding_box', 'Bounding Box'
    SEGMENTATION = 'segmentation', 'Segmentation'
    IMAGE_CAPTIONING = 'image_captioning', 'Image Captioning'


class Project(models.Model):
    """
    Annotation project model.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    project_type = models.CharField(
        max_length=50,
        choices=ProjectType.choices,
        default=ProjectType.SEQUENCE_LABELING
    )
    
    # Tibetan name support
    tibetan_name = models.CharField(max_length=255, blank=True, default='')
    
    # Project settings
    guideline = models.TextField(blank=True, default='')
    random_order = models.BooleanField(default=False)
    collaborative_annotation = models.BooleanField(default=False)
    single_class_classification = models.BooleanField(default=False)
    allow_overlapping = models.BooleanField(default=False)
    grapheme_mode = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Creator
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_projects'
    )
    
    class Meta:
        db_table = 'projects_project'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def is_stt_project(self):
        """Check if this is a Speech-to-Text project."""
        return self.project_type == ProjectType.SPEECH_TO_TEXT


class MemberRole(models.TextChoices):
    """Roles for project members."""
    ANNOTATOR = 'annotator', 'Annotator'
    APPROVER = 'approver', 'Approver'
    PROJECT_MANAGER = 'project_manager', 'Project Manager'
    PROJECT_ADMIN = 'project_admin', 'Project Admin'


class Member(models.Model):
    """
    Project membership with role-based access.
    
    Roles:
    - Annotator: Can only annotate pending examples and their rejected ones
    - Approver: Can annotate and review (approve/reject) all examples
    - Project Manager: Approver + visibility of completion matrix
    - Project Admin: Full access to everything
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='members'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='project_memberships'
    )
    role = models.CharField(
        max_length=20,
        choices=MemberRole.choices,
        default=MemberRole.ANNOTATOR
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'projects_member'
        unique_together = ('project', 'user')
        ordering = ['project', 'role', 'user__username']
    
    def __str__(self):
        return f"{self.user.username} - {self.role} in {self.project.name}"
    
    @property
    def can_annotate(self):
        """All roles can annotate."""
        return True
    
    @property
    def can_review(self):
        """Approvers, PMs, and Admins can review."""
        return self.role in [
            MemberRole.APPROVER,
            MemberRole.PROJECT_MANAGER,
            MemberRole.PROJECT_ADMIN
        ]
    
    @property
    def can_see_all(self):
        """Approvers, PMs, and Admins can see all examples."""
        return self.role in [
            MemberRole.APPROVER,
            MemberRole.PROJECT_MANAGER,
            MemberRole.PROJECT_ADMIN
        ]
    
    @property
    def can_manage(self):
        """PMs and Admins can manage (limited for PM, full for Admin)."""
        return self.role in [
            MemberRole.PROJECT_MANAGER,
            MemberRole.PROJECT_ADMIN
        ]
    
    @property
    def is_admin(self):
        """Only Project Admins have full access."""
        return self.role == MemberRole.PROJECT_ADMIN

