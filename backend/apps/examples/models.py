"""
Example models for Monlam Doccano.
Examples are the individual items being annotated.
"""

from django.db import models
from django.conf import settings


class Example(models.Model):
    """
    An example is a single item to be annotated.
    This could be a text, audio file, or image depending on project type.
    """
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='examples'
    )
    
    # Primary data field (text for text projects)
    text = models.TextField(blank=True, default='')
    
    # File fields for media projects
    upload_name = models.CharField(max_length=512, blank=True, default='')
    filename = models.FileField(upload_to='examples/', blank=True, null=True)
    
    # Metadata
    meta = models.JSONField(default=dict, blank=True)
    
    # UUID for external reference
    uuid = models.CharField(max_length=36, blank=True, default='')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'examples_example'
        ordering = ['id']
        indexes = [
            models.Index(fields=['project']),
            models.Index(fields=['uuid']),
        ]
    
    def __str__(self):
        text_preview = self.text[:50] if self.text else self.upload_name
        return f"Example #{self.id}: {text_preview}"
    
    @property
    def display_text(self):
        """Return text or filename for display."""
        return self.text if self.text else self.upload_name
    
    @property
    def file_url(self):
        """Return URL to the file if exists."""
        if self.filename:
            return self.filename.url
        return None


class Comment(models.Model):
    """
    Comments on examples for discussion/feedback.
    """
    example = models.ForeignKey(
        Example,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='example_comments'
    )
    text = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'examples_comment'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on Example #{self.example_id}"

