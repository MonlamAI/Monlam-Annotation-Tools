"""
Example serializers for API.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Example, Comment

User = get_user_model()


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for example comments."""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'example', 'user', 'username', 'text', 
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class ExampleSerializer(serializers.ModelSerializer):
    """
    Base serializer for examples.
    Extended by EnhancedExampleSerializer to include tracking data.
    """
    comment_count = serializers.SerializerMethodField()
    audio_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Example
        fields = [
            'id', 'project', 'text', 'upload_name', 'filename', 
            'file_url', 'meta', 'uuid', 'display_text',
            'audio_url', 'comment_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_comment_count(self, obj):
        return obj.comments.count()
    
    def get_audio_url(self, obj):
        """Extract audio URL from meta field for S3 audio playback."""
        meta = obj.meta or {}
        return (
            meta.get('audio_url') or 
            meta.get('audio') or 
            meta.get('audio_link') or 
            meta.get('filename') or  # Doccano STT format uses 'filename' for remote URLs
            meta.get('file_name') or
            meta.get('s3_url') or
            meta.get('media_url') or
            meta.get('sound_url') or
            obj.filename or  # Also check the model's filename field
            ''
        )


class EnhancedExampleSerializer(ExampleSerializer):
    """
    Enhanced serializer with annotation tracking data.
    Includes annotated_by, reviewed_by, and status fields.
    """
    annotated_by = serializers.SerializerMethodField()
    reviewed_by = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    review_notes = serializers.SerializerMethodField()
    locked_by = serializers.SerializerMethodField()
    
    class Meta(ExampleSerializer.Meta):
        fields = ExampleSerializer.Meta.fields + [
            'annotated_by', 'reviewed_by', 'status', 
            'status_display', 'review_notes', 'locked_by'
        ]
    
    def _get_tracking(self, obj):
        """Get the tracking record for this example (cached)."""
        if not hasattr(obj, '_tracking_cache'):
            from apps.monlam_tracking.models import AnnotationTracking
            obj._tracking_cache = AnnotationTracking.objects.filter(
                example=obj
            ).select_related('annotated_by', 'reviewed_by', 'locked_by').first()
        return obj._tracking_cache
    
    def get_annotated_by(self, obj):
        tracking = self._get_tracking(obj)
        if tracking and tracking.annotated_by:
            return {
                'id': tracking.annotated_by.id,
                'username': tracking.annotated_by.username
            }
        return None
    
    def get_reviewed_by(self, obj):
        tracking = self._get_tracking(obj)
        if tracking and tracking.reviewed_by:
            return {
                'id': tracking.reviewed_by.id,
                'username': tracking.reviewed_by.username
            }
        return None
    
    def get_status(self, obj):
        tracking = self._get_tracking(obj)
        return tracking.status if tracking else 'pending'
    
    def get_status_display(self, obj):
        tracking = self._get_tracking(obj)
        if tracking:
            return tracking.get_status_display()
        return 'Pending'
    
    def get_review_notes(self, obj):
        tracking = self._get_tracking(obj)
        return tracking.review_notes if tracking else ''
    
    def get_locked_by(self, obj):
        tracking = self._get_tracking(obj)
        if tracking and tracking.locked_by:
            return {
                'id': tracking.locked_by.id,
                'username': tracking.locked_by.username
            }
        return None


class ExampleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating examples."""
    
    class Meta:
        model = Example
        fields = ['text', 'upload_name', 'filename', 'meta', 'uuid']


class ExampleBulkCreateSerializer(serializers.Serializer):
    """Serializer for bulk creating examples."""
    examples = ExampleCreateSerializer(many=True)
    
    def create(self, validated_data):
        project = self.context['project']
        examples_data = validated_data['examples']
        examples = [
            Example(project=project, **data)
            for data in examples_data
        ]
        return Example.objects.bulk_create(examples)

