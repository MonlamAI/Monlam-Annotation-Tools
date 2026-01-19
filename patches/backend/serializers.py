"""
Patched serializers.py for Doccano with external URL support + tracking status.

This file replaces /doccano/backend/examples/serializers.py

Features:
1. Fixes external URLs (don't add /media/ prefix)
2. Adds tracking status (annotated_by/reviewed_by tracked in backend but NOT exposed in API)
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
    
    # ========================================
    # MONLAM: Tracking status only (annotated_by/reviewed_by tracked in backend but not exposed)
    # ========================================
    tracking_status = serializers.SerializerMethodField()

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
            return instance.filename.url
        return None
    
    # ========================================
    # MONLAM: Tracking status getter (annotated_by/reviewed_by tracked in backend but not exposed)
    # ========================================
    
    def get_tracking_status(self, obj):
        """Get the tracking status"""
        try:
            # Try to get from prefetched data first (for efficiency)
            if hasattr(obj, 'tracking'):
                tracking = obj.tracking
                return tracking.status if tracking else 'pending'
            
            # Fallback: query database
            from assignment.simple_tracking import AnnotationTracking
            tracking = AnnotationTracking.objects.filter(
                example_id=obj.id,
                project_id=obj.project_id
            ).first()
            
            return tracking.status if tracking else 'pending'
        except Exception as e:
            # Silently fail if tracking table doesn't exist yet
            return 'pending'

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
            # MONLAM: Tracking status only (annotated_by/reviewed_by tracked in backend but not exposed)
            "tracking_status",
        ]
        read_only_fields = [
            "filename", 
            "is_confirmed", 
            "upload_name",
            # MONLAM: Tracking status is read-only
            "tracking_status",
        ]


class ExampleStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExampleState
        fields = ("id", "example", "confirmed_by", "confirmed_at")
        read_only_fields = ("id", "example", "confirmed_by", "confirmed_at")
