"""
Patch for Doccano's Example Serializer
Adds assignment information to example API responses
"""

from rest_framework import serializers
from examples.serializers import ExampleSerializer as OriginalExampleSerializer


class ExampleSerializer(OriginalExampleSerializer):
    """
    Extended Example Serializer with assignment information
    """
    annotated_by = serializers.SerializerMethodField()
    reviewed_by = serializers.SerializerMethodField()
    assignment_status = serializers.SerializerMethodField()
    annotated_by_username = serializers.SerializerMethodField()
    reviewed_by_username = serializers.SerializerMethodField()
    
    class Meta(OriginalExampleSerializer.Meta):
        fields = OriginalExampleSerializer.Meta.fields + [
            'annotated_by',
            'reviewed_by',
            'assignment_status',
            'annotated_by_username',
            'reviewed_by_username',
        ]
    
    def get_annotated_by(self, obj):
        """Get the ID of the user assigned to this example"""
        try:
            from assignment.models import Assignment
            assignment = Assignment.objects.filter(
                example_id=obj.id,
                project_id=obj.project_id
            ).first()
            return assignment.assigned_to_id if assignment else None
        except Exception:
            return None
    
    def get_reviewed_by(self, obj):
        """Get the ID of the reviewer"""
        try:
            from assignment.models import Assignment
            assignment = Assignment.objects.filter(
                example_id=obj.id,
                project_id=obj.project_id
            ).first()
            return assignment.reviewed_by_id if assignment else None
        except Exception:
            return None
    
    def get_assignment_status(self, obj):
        """Get the assignment status"""
        try:
            from assignment.models import Assignment
            assignment = Assignment.objects.filter(
                example_id=obj.id,
                project_id=obj.project_id
            ).first()
            return assignment.status if assignment else 'unassigned'
        except Exception:
            return 'unassigned'
    
    def get_annotated_by_username(self, obj):
        """Get the username of the assigned user"""
        try:
            from assignment.models import Assignment
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            assignment = Assignment.objects.filter(
                example_id=obj.id,
                project_id=obj.project_id
            ).select_related('assigned_to').first()
            
            if assignment and assignment.assigned_to:
                return assignment.assigned_to.username
            return None
        except Exception:
            return None
    
    def get_reviewed_by_username(self, obj):
        """Get the username of the reviewer"""
        try:
            from assignment.models import Assignment
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            assignment = Assignment.objects.filter(
                example_id=obj.id,
                project_id=obj.project_id
            ).select_related('reviewed_by').first()
            
            if assignment and assignment.reviewed_by:
                return assignment.reviewed_by.username
            return None
        except Exception:
            return None

