"""
Serializers for Completion Tracking

REST API serializers for completion matrix and tracking.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class AnnotatorCompletionStatusSerializer(serializers.Serializer):
    """Serializer for AnnotatorCompletionStatus model."""
    
    id = serializers.IntegerField(read_only=True)
    example_id = serializers.IntegerField()
    annotator_id = serializers.IntegerField()
    annotator_username = serializers.CharField(source='annotator.username', read_only=True)
    is_completed = serializers.BooleanField()
    completed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    annotation_count = serializers.IntegerField(read_only=True)


class ApproverCompletionStatusSerializer(serializers.Serializer):
    """Serializer for ApproverCompletionStatus model."""
    
    id = serializers.IntegerField(read_only=True)
    example_id = serializers.IntegerField()
    approver_id = serializers.IntegerField()
    approver_username = serializers.CharField(source='approver.username', read_only=True)
    status = serializers.ChoiceField(choices=[
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ])
    reviewed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    review_notes = serializers.CharField(allow_blank=True, default='')


class ExampleCompletionDetailSerializer(serializers.Serializer):
    """Detailed completion info for a single example."""
    
    example_id = serializers.IntegerField()
    assignment_id = serializers.IntegerField(allow_null=True)
    status = serializers.CharField()
    is_completed = serializers.BooleanField()
    completed_at = serializers.DateTimeField(allow_null=True)
    started_at = serializers.DateTimeField(allow_null=True)
    submitted_at = serializers.DateTimeField(allow_null=True)


class AnnotatorMatrixRowSerializer(serializers.Serializer):
    """Serializer for a single annotator's row in the matrix."""
    
    annotator_id = serializers.IntegerField()
    annotator_username = serializers.CharField()
    total_assigned = serializers.IntegerField()
    completed = serializers.IntegerField()
    in_progress = serializers.IntegerField()
    submitted = serializers.IntegerField()
    approved = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    examples = ExampleCompletionDetailSerializer(many=True)


class ApproverMatrixRowSerializer(serializers.Serializer):
    """Serializer for a single approver's row in the matrix."""
    
    approver_id = serializers.IntegerField()
    approver_username = serializers.CharField()
    total_to_review = serializers.IntegerField()
    approved = serializers.IntegerField()
    rejected = serializers.IntegerField()
    pending = serializers.IntegerField()
    approval_rate = serializers.FloatField()
    examples = serializers.ListField()


class CompletionSummarySerializer(serializers.Serializer):
    """Serializer for project-wide summary statistics."""
    
    total_examples = serializers.IntegerField()
    assigned_examples = serializers.IntegerField()
    unassigned_examples = serializers.IntegerField()
    completed_examples = serializers.IntegerField()
    approved_examples = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    approval_rate = serializers.FloatField()


class CompleteMatrixSerializer(serializers.Serializer):
    """Serializer for the complete completion matrix."""
    
    project_id = serializers.IntegerField()
    project_name = serializers.CharField()
    annotators = AnnotatorMatrixRowSerializer(many=True)
    approvers = ApproverMatrixRowSerializer(many=True)
    summary = CompletionSummarySerializer()


class UserStatsSerializer(serializers.Serializer):
    """Serializer for individual user statistics."""
    
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    role = serializers.CharField()
    annotator_stats = serializers.DictField()
    approver_stats = serializers.DictField()


class CompletionActionSerializer(serializers.Serializer):
    """Serializer for completion actions (approve/reject/complete)."""
    
    notes = serializers.CharField(allow_blank=True, required=False)


class BulkCompletionUpdateSerializer(serializers.Serializer):
    """Serializer for bulk completion updates."""
    
    example_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text='List of example IDs to update'
    )
    action = serializers.ChoiceField(
        choices=['complete', 'incomplete', 'approve', 'reject'],
        help_text='Action to perform'
    )
    notes = serializers.CharField(
        allow_blank=True,
        required=False,
        help_text='Optional notes for approval/rejection'
    )

