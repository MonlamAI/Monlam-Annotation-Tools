"""
Assignment System - Serializer Patches for Doccano

Add assignment fields to the Example serializer.
"""

from rest_framework import serializers


# Add these fields to ExampleSerializer in examples/serializers.py:

ADDITIONAL_FIELDS = '''
    assigned_to_username = serializers.SerializerMethodField()
    assignment_status = serializers.CharField(read_only=True)
    reviewed_by_username = serializers.SerializerMethodField()
    reviewed_at = serializers.DateTimeField(read_only=True)
    
    def get_assigned_to_username(self, obj):
        return obj.assigned_to.username if obj.assigned_to else None
    
    def get_reviewed_by_username(self, obj):
        return obj.reviewed_by.username if obj.reviewed_by else None
'''

# Update Meta.fields to include:
META_FIELDS_ADDITION = '''
    fields = [
        "id",
        "filename",
        "meta",
        "annotation_approver",
        "comment_count",
        "text",
        "is_confirmed",
        "upload_name",
        "score",
        # Assignment fields
        "assigned_to_username",
        "assignment_status",
        "reviewed_by_username",
        "reviewed_at",
    ]
'''


class ExampleSerializerWithAssignment:
    """
    Example of patched serializer with assignment fields.
    Copy this pattern into your serializers.py
    """
    
    # Add these method fields
    assigned_to_username = serializers.SerializerMethodField()
    assignment_status = serializers.CharField(read_only=True)
    reviewed_by_username = serializers.SerializerMethodField()
    reviewed_at = serializers.DateTimeField(read_only=True)
    
    def get_assigned_to_username(self, obj):
        if hasattr(obj, 'assigned_to') and obj.assigned_to:
            return obj.assigned_to.username
        return None
    
    def get_reviewed_by_username(self, obj):
        if hasattr(obj, 'reviewed_by') and obj.reviewed_by:
            return obj.reviewed_by.username
        return None

