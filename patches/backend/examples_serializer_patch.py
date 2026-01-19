"""
Patch for Doccano's Example Serializer
Adds tracking status to example API responses (but NOT annotated_by/reviewed_by)

Note: annotated_by and reviewed_by are tracked in backend but NOT exposed in dataset API
for performance and privacy. Metrics can still access them via direct database queries.
"""

from rest_framework import serializers
from examples.serializers import ExampleSerializer as OriginalExampleSerializer


class ExampleSerializer(OriginalExampleSerializer):
    """
    Extended Example Serializer with tracking status only.
    Does NOT include annotated_by_username or reviewed_by_username (tracked in backend only).
    """
    tracking_status = serializers.SerializerMethodField()
    
    class Meta(OriginalExampleSerializer.Meta):
        fields = OriginalExampleSerializer.Meta.fields + [
            'tracking_status',
        ]
    
    def get_tracking_status(self, obj):
        """Get the tracking status (who annotated/reviewed is tracked in backend but not exposed)"""
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

