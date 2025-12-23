"""
Patched serializers.py for Doccano with external URL support AND Assignment fields.

This file replaces /doccano/backend/examples/serializers.py
- Fixes external URLs (don't prepend /media/)
- Adds assignment tracking fields
Based on original Doccano 1.8.4 serializers.py
"""

from rest_framework import serializers

from .models import Comment, Example, ExampleState


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = (
            "id",
            "user",
            "username",
            "example",
            "text",
            "created_at",
        )
        read_only_fields = ("user", "example")


class ExampleSerializer(serializers.ModelSerializer):
    annotation_approver = serializers.SerializerMethodField()
    is_confirmed = serializers.SerializerMethodField()
    # Override filename to handle external URLs
    filename = serializers.SerializerMethodField()
    
    # Assignment fields
    assigned_to_username = serializers.SerializerMethodField()
    assignment_status = serializers.CharField(read_only=True)
    reviewed_by_username = serializers.SerializerMethodField()

    @classmethod
    def get_annotation_approver(cls, instance):
        approver = instance.annotations_approved_by
        return approver.username if approver else None

    def get_is_confirmed(self, instance):
        user = self.context.get("request").user
        if instance.project.collaborative_annotation:
            states = instance.states.all()
        else:
            states = instance.states.filter(confirmed_by_id=user.id)
        return states.count() > 0

    def get_filename(self, instance):
        """
        Return the filename URL.
        If it's an external URL (starts with http), return as-is.
        Otherwise, return the media URL (default Django behavior).
        """
        filename_str = str(instance.filename)
        
        # Check if it's an external URL
        if filename_str.startswith('http://') or filename_str.startswith('https://'):
            return filename_str
        
        # Default behavior - return the file URL
        if instance.filename:
            try:
                return instance.filename.url
            except ValueError:
                return filename_str
        return None

    def get_assigned_to_username(self, instance):
        """Get username of assigned annotator."""
        if hasattr(instance, 'assigned_to') and instance.assigned_to:
            return instance.assigned_to.username
        return None

    def get_reviewed_by_username(self, instance):
        """Get username of reviewer."""
        if hasattr(instance, 'reviewed_by') and instance.reviewed_by:
            return instance.reviewed_by.username
        return None

    class Meta:
        model = Example
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
        ]
        read_only_fields = ["filename", "is_confirmed", "upload_name"]


class ExampleStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExampleState
        fields = ("id", "example", "confirmed_by", "confirmed_at")
        read_only_fields = ("id", "example", "confirmed_by", "confirmed_at")
