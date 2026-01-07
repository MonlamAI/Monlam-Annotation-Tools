"""
Serializers for annotation tracking.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import AnnotationTracking, TrackingStatus

User = get_user_model()


class TrackingSerializer(serializers.ModelSerializer):
    """Full serializer for tracking records."""
    annotated_by_username = serializers.CharField(
        source='annotated_by.username', 
        read_only=True,
        default=None
    )
    reviewed_by_username = serializers.CharField(
        source='reviewed_by.username', 
        read_only=True,
        default=None
    )
    locked_by_username = serializers.CharField(
        source='locked_by.username', 
        read_only=True,
        default=None
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    example_id = serializers.IntegerField(source='example.id', read_only=True)
    
    class Meta:
        model = AnnotationTracking
        fields = [
            'id', 'project', 'example_id',
            'annotated_by', 'annotated_by_username', 'annotated_at',
            'reviewed_by', 'reviewed_by_username', 'reviewed_at',
            'status', 'status_display', 'review_notes',
            'locked_by', 'locked_by_username', 'locked_at', 'is_locked',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'project', 'example_id', 'created_at', 'updated_at']


class TrackingStatusSerializer(serializers.Serializer):
    """Minimal serializer for just status info."""
    example_id = serializers.IntegerField()
    status = serializers.CharField()
    status_display = serializers.CharField()
    annotated_by = serializers.CharField(allow_null=True)
    reviewed_by = serializers.CharField(allow_null=True)
    is_locked = serializers.BooleanField()
    locked_by = serializers.CharField(allow_null=True)


class ApproveSerializer(serializers.Serializer):
    """Serializer for approve action."""
    notes = serializers.CharField(required=False, allow_blank=True, default='')


class RejectSerializer(serializers.Serializer):
    """Serializer for reject action. Notes are required."""
    notes = serializers.CharField(required=True, min_length=1)
    
    def validate_notes(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                'Rejection reason is required and cannot be empty.'
            )
        return value.strip()


class LockSerializer(serializers.Serializer):
    """Serializer for lock/unlock actions."""
    pass


class TrackingSummarySerializer(serializers.Serializer):
    """Serializer for tracking summary statistics."""
    total = serializers.IntegerField()
    pending = serializers.IntegerField()
    in_progress = serializers.IntegerField()
    submitted = serializers.IntegerField()
    approved = serializers.IntegerField()
    rejected = serializers.IntegerField()
    completion_rate = serializers.FloatField()


class AnnotatorPerformanceSerializer(serializers.Serializer):
    """Serializer for annotator performance metrics."""
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    completed = serializers.IntegerField()
    approved = serializers.IntegerField()
    rejected = serializers.IntegerField()
    success_rate = serializers.FloatField()


class ReviewerPerformanceSerializer(serializers.Serializer):
    """Serializer for reviewer performance metrics."""
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    reviewed = serializers.IntegerField()
    approved = serializers.IntegerField()
    rejected = serializers.IntegerField()
    approval_rate = serializers.FloatField()

