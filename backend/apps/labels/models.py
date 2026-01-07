"""
Label models for Monlam Doccano.
Includes label types (categories) and annotations (spans, categories, text labels).
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class LabelType(models.Model):
    """
    Base class for label types (categories that can be applied).
    """
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='%(class)ss'
    )
    text = models.CharField(max_length=255)
    prefix_key = models.CharField(max_length=10, blank=True, null=True)
    suffix_key = models.CharField(max_length=10, blank=True, null=True)
    background_color = models.CharField(max_length=7, default='#209cee')
    text_color = models.CharField(max_length=7, default='#ffffff')
    
    # Tibetan support
    tibetan_text = models.CharField(max_length=255, blank=True, default='')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        ordering = ['text']


class CategoryType(LabelType):
    """Label type for document classification."""
    
    class Meta:
        db_table = 'labels_categorytype'
        unique_together = ('project', 'text')
    
    def __str__(self):
        return self.text


class SpanType(LabelType):
    """Label type for sequence labeling (NER, etc.)."""
    
    class Meta:
        db_table = 'labels_spantype'
        unique_together = ('project', 'text')
    
    def __str__(self):
        return self.text


class RelationType(LabelType):
    """Label type for relation extraction."""
    
    class Meta:
        db_table = 'labels_relationtype'
        unique_together = ('project', 'text')
    
    def __str__(self):
        return self.text


# ============================================
# Annotation Models (actual labels applied to examples)
# ============================================

class Annotation(models.Model):
    """
    Base class for annotations.
    """
    example = models.ForeignKey(
        'examples.Example',
        on_delete=models.CASCADE,
        related_name='%(class)ss'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='%(class)ss'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class Category(Annotation):
    """
    Category annotation for document classification.
    """
    label = models.ForeignKey(
        CategoryType,
        on_delete=models.CASCADE,
        related_name='annotations'
    )
    
    class Meta:
        db_table = 'labels_category'
        unique_together = ('example', 'user', 'label')
    
    def __str__(self):
        return f"{self.label.text} on Example #{self.example_id}"
    
    @property
    def project(self):
        return self.example.project


class Span(Annotation):
    """
    Span annotation for sequence labeling (NER, POS tagging, etc.).
    """
    label = models.ForeignKey(
        SpanType,
        on_delete=models.CASCADE,
        related_name='annotations'
    )
    start_offset = models.IntegerField(validators=[MinValueValidator(0)])
    end_offset = models.IntegerField(validators=[MinValueValidator(0)])
    
    class Meta:
        db_table = 'labels_span'
    
    def __str__(self):
        return f"{self.label.text} [{self.start_offset}:{self.end_offset}] on Example #{self.example_id}"
    
    @property
    def project(self):
        return self.example.project
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_offset >= self.end_offset:
            raise ValidationError('start_offset must be less than end_offset')


class TextLabel(Annotation):
    """
    Text label annotation for seq2seq, translation, STT, etc.
    """
    text = models.TextField()
    
    class Meta:
        db_table = 'labels_textlabel'
    
    def __str__(self):
        text_preview = self.text[:30] if len(self.text) > 30 else self.text
        return f"'{text_preview}' on Example #{self.example_id}"
    
    @property
    def project(self):
        return self.example.project


class Relation(Annotation):
    """
    Relation annotation between two spans.
    """
    label = models.ForeignKey(
        RelationType,
        on_delete=models.CASCADE,
        related_name='annotations'
    )
    from_span = models.ForeignKey(
        Span,
        on_delete=models.CASCADE,
        related_name='from_relations'
    )
    to_span = models.ForeignKey(
        Span,
        on_delete=models.CASCADE,
        related_name='to_relations'
    )
    
    class Meta:
        db_table = 'labels_relation'
    
    def __str__(self):
        return f"{self.from_span} -> {self.label.text} -> {self.to_span}"
    
    @property
    def project(self):
        return self.example.project


class BoundingBox(Annotation):
    """
    Bounding box annotation for image annotation.
    """
    label = models.ForeignKey(
        CategoryType,
        on_delete=models.CASCADE,
        related_name='bounding_boxes'
    )
    x = models.FloatField()
    y = models.FloatField()
    width = models.FloatField()
    height = models.FloatField()
    
    class Meta:
        db_table = 'labels_boundingbox'
    
    def __str__(self):
        return f"{self.label.text} at ({self.x}, {self.y}) on Example #{self.example_id}"
    
    @property
    def project(self):
        return self.example.project

