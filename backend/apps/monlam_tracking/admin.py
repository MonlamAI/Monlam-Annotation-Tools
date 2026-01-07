"""
Admin configuration for annotation tracking.
"""

from django.contrib import admin
from .models import AnnotationTracking


@admin.register(AnnotationTracking)
class AnnotationTrackingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'example', 'project', 'status', 
        'annotated_by', 'annotated_at',
        'reviewed_by', 'reviewed_at',
        'locked_by', 'is_locked'
    ]
    list_filter = ['status', 'project', 'created_at', 'annotated_at', 'reviewed_at']
    search_fields = [
        'example__text', 'example__upload_name',
        'annotated_by__username', 'reviewed_by__username',
        'review_notes'
    ]
    raw_id_fields = ['project', 'example', 'annotated_by', 'reviewed_by', 'locked_by']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Example', {
            'fields': ('project', 'example')
        }),
        ('Annotation', {
            'fields': ('annotated_by', 'annotated_at', 'status')
        }),
        ('Review', {
            'fields': ('reviewed_by', 'reviewed_at', 'review_notes')
        }),
        ('Locking', {
            'fields': ('locked_by', 'locked_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_locked(self, obj):
        return obj.is_locked
    is_locked.boolean = True
    is_locked.short_description = 'Locked'

