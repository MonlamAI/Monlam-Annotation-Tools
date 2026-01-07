"""
Label admin configuration.
"""

from django.contrib import admin
from .models import (
    CategoryType, SpanType, RelationType,
    Category, Span, TextLabel, Relation, BoundingBox
)


# ============================================
# Label Type Admins
# ============================================

@admin.register(CategoryType)
class CategoryTypeAdmin(admin.ModelAdmin):
    list_display = ['text', 'project', 'background_color', 'created_at']
    list_filter = ['project', 'created_at']
    search_fields = ['text', 'tibetan_text']


@admin.register(SpanType)
class SpanTypeAdmin(admin.ModelAdmin):
    list_display = ['text', 'project', 'background_color', 'created_at']
    list_filter = ['project', 'created_at']
    search_fields = ['text', 'tibetan_text']


@admin.register(RelationType)
class RelationTypeAdmin(admin.ModelAdmin):
    list_display = ['text', 'project', 'background_color', 'created_at']
    list_filter = ['project', 'created_at']
    search_fields = ['text', 'tibetan_text']


# ============================================
# Annotation Admins
# ============================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'example', 'label', 'user', 'created_at']
    list_filter = ['label', 'created_at']
    raw_id_fields = ['example', 'user', 'label']


@admin.register(Span)
class SpanAdmin(admin.ModelAdmin):
    list_display = ['id', 'example', 'label', 'start_offset', 'end_offset', 'user', 'created_at']
    list_filter = ['label', 'created_at']
    raw_id_fields = ['example', 'user', 'label']


@admin.register(TextLabel)
class TextLabelAdmin(admin.ModelAdmin):
    list_display = ['id', 'example', 'text_preview', 'user', 'created_at']
    list_filter = ['created_at']
    raw_id_fields = ['example', 'user']
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Text'


@admin.register(Relation)
class RelationAdmin(admin.ModelAdmin):
    list_display = ['id', 'example', 'label', 'from_span', 'to_span', 'user', 'created_at']
    list_filter = ['label', 'created_at']
    raw_id_fields = ['example', 'user', 'label', 'from_span', 'to_span']


@admin.register(BoundingBox)
class BoundingBoxAdmin(admin.ModelAdmin):
    list_display = ['id', 'example', 'label', 'x', 'y', 'width', 'height', 'user', 'created_at']
    list_filter = ['label', 'created_at']
    raw_id_fields = ['example', 'user', 'label']

