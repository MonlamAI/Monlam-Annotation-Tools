"""
Patch for Doccano's Example Serializer
Adds tracking information to example API responses

Simple tracking system - no assignments, just tracking who did what.
"""

from rest_framework import serializers
from examples.serializers import ExampleSerializer as OriginalExampleSerializer


class ExampleSerializer(OriginalExampleSerializer):
    """
    Extended Example Serializer with annotation tracking
    """
    annotated_by_username = serializers.SerializerMethodField()
    reviewed_by_username = serializers.SerializerMethodField()
    tracking_status = serializers.SerializerMethodField()
    
    class Meta(OriginalExampleSerializer.Meta):
        fields = OriginalExampleSerializer.Meta.fields + [
            'annotated_by_username',
            'reviewed_by_username',
            'tracking_status',
        ]
    
    def get_annotated_by_username(self, obj):
        """Get the username of who annotated this example"""
        try:
            # Try to get from prefetched data first (for efficiency)
            if hasattr(obj, 'tracking'):
                tracking = obj.tracking
                if tracking and tracking.annotated_by:
                    return tracking.annotated_by.username
                return None
            
            # Fallback: query database
            from assignment.simple_tracking import AnnotationTracking
            tracking = AnnotationTracking.objects.filter(
                example_id=obj.id,
                project_id=obj.project_id
            ).select_related('annotated_by').first()
            
            if tracking and tracking.annotated_by:
                return tracking.annotated_by.username
            return None
        except Exception:
            return None
    
    def get_reviewed_by_username(self, obj):
        """Get the username of who reviewed this example"""
        try:
            # Try to get from prefetched data first (for efficiency)
            if hasattr(obj, 'tracking'):
                tracking = obj.tracking
                if tracking and tracking.reviewed_by:
                    return tracking.reviewed_by.username
                return None
            
            # Fallback: query database
            from assignment.simple_tracking import AnnotationTracking
            tracking = AnnotationTracking.objects.filter(
                example_id=obj.id,
                project_id=obj.project_id
            ).select_related('reviewed_by').first()
            
            if tracking and tracking.reviewed_by:
                return tracking.reviewed_by.username
            return None
        except Exception:
            return None
    
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
        except Exception:
            return 'pending'

