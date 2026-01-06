"""
Assignment Serializers

REST API serializers for the Assignment system.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user info for assignment display."""
    class Meta:
        model = User
        fields = ['id', 'username']


class AssignmentSerializer(serializers.Serializer):
    """
    Serializer for Assignment model.
    Note: Using Serializer instead of ModelSerializer to avoid
    import issues until the app is properly installed.
    """
    id = serializers.IntegerField(read_only=True)
    example_id = serializers.IntegerField()
    project_id = serializers.IntegerField()
    assigned_to_id = serializers.IntegerField(allow_null=True)
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    assigned_by_id = serializers.IntegerField(allow_null=True, read_only=True)
    assigned_at = serializers.DateTimeField(read_only=True)
    status = serializers.ChoiceField(choices=[
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted for Review'),
        ('approved', 'Approved'),
        ('rejected', 'Needs Revision'),
    ])
    started_at = serializers.DateTimeField(read_only=True, allow_null=True)
    submitted_at = serializers.DateTimeField(read_only=True, allow_null=True)
    reviewed_by_id = serializers.IntegerField(read_only=True, allow_null=True)
    reviewed_by_username = serializers.CharField(source='reviewed_by.username', read_only=True)
    reviewed_by_role = serializers.SerializerMethodField()
    reviewed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    review_notes = serializers.CharField(allow_blank=True, default='')
    is_active = serializers.BooleanField(default=True)
    
    def get_reviewed_by_role(self, obj):
        """
        Get the role of the reviewer (approver or project_manager).
        This helps distinguish between approver approval and PM final approval.
        """
        if not obj.reviewed_by:
            return None
        
        try:
            from projects.models import RoleMapping
            
            # Get reviewer's role in this project
            role_mapping = RoleMapping.objects.filter(
                user=obj.reviewed_by,
                project=obj.project
            ).first()
            
            if role_mapping:
                return role_mapping.role.name  # Returns 'project_manager', 'approver', etc.
        except Exception:
            pass
        
        return 'reviewer'  # Default fallback


class BulkAssignmentSerializer(serializers.Serializer):
    """Serializer for bulk assignment operations."""
    example_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text='List of example IDs to assign'
    )
    assigned_to_id = serializers.IntegerField(
        help_text='User ID to assign examples to'
    )


class AssignmentStatsSerializer(serializers.Serializer):
    """Statistics for assignment tracking."""
    username = serializers.CharField()
    user_id = serializers.IntegerField()
    total_assigned = serializers.IntegerField()
    in_progress = serializers.IntegerField()
    submitted = serializers.IntegerField()
    approved = serializers.IntegerField()
    rejected = serializers.IntegerField()
    completion_rate = serializers.FloatField()

