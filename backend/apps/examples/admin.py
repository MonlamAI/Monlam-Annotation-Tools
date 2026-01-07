"""
Example admin configuration.
"""

from django.contrib import admin
from .models import Example, Comment


@admin.register(Example)
class ExampleAdmin(admin.ModelAdmin):
    list_display = ['id', 'project', 'display_text_preview', 'created_at']
    list_filter = ['project', 'created_at']
    search_fields = ['text', 'upload_name', 'uuid']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['project']
    
    def display_text_preview(self, obj):
        text = obj.display_text
        return text[:50] + '...' if len(text) > 50 else text
    display_text_preview.short_description = 'Text'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'example', 'user', 'text_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['text', 'user__username']
    raw_id_fields = ['example', 'user']
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Text'

