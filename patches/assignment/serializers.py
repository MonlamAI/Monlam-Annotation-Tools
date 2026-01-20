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
    annotated_by_id = serializers.SerializerMethodField()
    annotated_by_username = serializers.SerializerMethodField()
    assigned_by_id = serializers.IntegerField(allow_null=True, read_only=True)
    assigned_at = serializers.DateTimeField(read_only=True)
    status = serializers.SerializerMethodField()
    started_at = serializers.DateTimeField(read_only=True, allow_null=True)
    submitted_at = serializers.DateTimeField(read_only=True, allow_null=True)
    reviewed_by_id = serializers.SerializerMethodField()
    reviewed_by_username = serializers.SerializerMethodField()
    reviewed_by_role = serializers.SerializerMethodField()
    reviewed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    review_notes = serializers.CharField(allow_blank=True, default='')
    is_active = serializers.BooleanField(default=True)
    
    # Final approval fields (project_admin approval)
    final_approval_by_id = serializers.SerializerMethodField()
    final_approval_by_username = serializers.SerializerMethodField()
    final_approval_at = serializers.SerializerMethodField()
    has_final_approval = serializers.SerializerMethodField()
    
    def get_status(self, obj):
        """
        Compute status based on:
        1. If example is NOT finished (ExampleState.confirmed_by is None): return annotator progress status
        2. If example IS finished: check ApproverCompletionStatus for approval status
        
        This ensures "approved" is only shown for finished examples.
        """
        try:
            # First check if example is finished (ExampleState.confirmed_by exists)
            from examples.models import ExampleState
            example_state = ExampleState.objects.filter(
                example=obj.example
            ).select_related('confirmed_by').first()
            
            is_finished = example_state and example_state.confirmed_by is not None
            
            # Debug logging for specific examples that show the issue
            if obj.example_id in [615, 616, 617, 618, 619]:
                print(f'[Serializer Debug] Example {obj.example_id}: is_finished={is_finished}, ExampleState.confirmed_by={example_state.confirmed_by.username if example_state and example_state.confirmed_by else "NULL"}, Assignment.status={obj.status}')
            
            # If not finished, return annotator progress status (never show submitted/approved/rejected)
            if not is_finished:
                # Unfinished examples can only be 'assigned' or 'in_progress'
                # Never 'submitted', 'approved', or 'rejected' because those require the example to be finished
                if obj.status in ['approved', 'rejected', 'submitted']:
                    # If assignment says approved/rejected/submitted but example isn't finished, fix it
                    if obj.started_at:
                        return 'in_progress'
                    else:
                        return 'assigned'
                # If status is already 'assigned' or 'in_progress', return it
                if obj.status in ['assigned', 'in_progress']:
                    return obj.status
                # Fallback: determine based on whether work has started
                if obj.started_at:
                    return 'in_progress'
                else:
                    return 'assigned'
            
            # Example is finished - check ApproverCompletionStatus for approval status
            from assignment.completion_tracking import ApproverCompletionStatus
            
            # Check for rejections first (rejected takes precedence)
            has_rejection = ApproverCompletionStatus.objects.filter(
                example=obj.example,
                project=obj.project,
                status='rejected'
            ).exists()
            
            if has_rejection:
                return 'rejected'
            
            # Check for approvals
            has_approval = ApproverCompletionStatus.objects.filter(
                example=obj.example,
                project=obj.project,
                status='approved'
            ).exists()
            
            if has_approval:
                return 'approved'
            
            # Finished but not yet approved/rejected = submitted
            return 'submitted'
            
        except Exception as e:
            # Fallback to assignment status if there's an error
            return obj.status
    
    def get_annotated_by_id(self, obj):
        """Get who actually annotated this example (from AnnotationTracking)."""
        try:
            from assignment.simple_tracking import AnnotationTracking
            tracking = AnnotationTracking.objects.filter(
                project=obj.project,
                example=obj.example
            ).select_related('annotated_by').first()
            
            if tracking and tracking.annotated_by:
                return tracking.annotated_by.id
            
            # Fallback: check ExampleState if no tracking
            from examples.models import ExampleState
            state = ExampleState.objects.filter(
                example=obj.example
            ).select_related('confirmed_by').first()
            
            if state and state.confirmed_by:
                return state.confirmed_by.id
        except Exception:
            pass
        
        # Final fallback: use assigned_to
        return obj.assigned_to.id if obj.assigned_to else None
    
    def get_annotated_by_username(self, obj):
        """Get username of who actually annotated this example (from AnnotationTracking)."""
        try:
            from assignment.simple_tracking import AnnotationTracking
            tracking = AnnotationTracking.objects.filter(
                project=obj.project,
                example=obj.example
            ).select_related('annotated_by').first()
            
            if tracking and tracking.annotated_by:
                return tracking.annotated_by.username
            
            # Fallback: check ExampleState if no tracking
            from examples.models import ExampleState
            state = ExampleState.objects.filter(
                example=obj.example
            ).select_related('confirmed_by').first()
            
            if state and state.confirmed_by:
                return state.confirmed_by.username
        except Exception:
            pass
        
        # Final fallback: use assigned_to
        return obj.assigned_to.username if obj.assigned_to else None
    
    def get_reviewed_by_id(self, obj):
        """Get annotation_approver who reviewed (not project_admin)."""
        try:
            from assignment.completion_tracking import ApproverCompletionStatus
            from projects.models import Member
            from assignment.roles import ROLE_ANNOTATION_APPROVER
            
            # Find annotation_approver approval for this example
            approvals = ApproverCompletionStatus.objects.filter(
                example=obj.example,
                project=obj.project,
                status='approved'
            ).select_related('approver')
            
            for approval in approvals:
                member = Member.objects.filter(
                    user=approval.approver,
                    project=obj.project
                ).select_related('role').first()
                
                if member and member.role and member.role.name.lower() == ROLE_ANNOTATION_APPROVER:
                    return approval.approver.id
        except Exception:
            pass
        # Fallback to Assignment.reviewed_by if no annotation_approver found
        return obj.reviewed_by.id if obj.reviewed_by else None
    
    def get_reviewed_by_username(self, obj):
        """Get annotation_approver username who reviewed (not project_admin)."""
        try:
            from assignment.completion_tracking import ApproverCompletionStatus
            from projects.models import Member
            from assignment.roles import ROLE_ANNOTATION_APPROVER
            
            # Find annotation_approver approval for this example
            approvals = ApproverCompletionStatus.objects.filter(
                example=obj.example,
                project=obj.project,
                status='approved'
            ).select_related('approver')
            
            for approval in approvals:
                member = Member.objects.filter(
                    user=approval.approver,
                    project=obj.project
                ).select_related('role').first()
                
                if member and member.role and member.role.name.lower() == ROLE_ANNOTATION_APPROVER:
                    return approval.approver.username
        except Exception:
            pass
        # Fallback to Assignment.reviewed_by if no annotation_approver found
        return obj.reviewed_by.username if obj.reviewed_by else None
    
    def get_reviewed_by_role(self, obj):
        """
        Get the role of the reviewer (annotation_approver, not project_admin).
        This shows who did the initial review.
        """
        try:
            from assignment.completion_tracking import ApproverCompletionStatus
            from projects.models import Member
            from assignment.roles import ROLE_ANNOTATION_APPROVER
            
            # Find annotation_approver approval for this example
            approvals = ApproverCompletionStatus.objects.filter(
                example=obj.example,
                project=obj.project,
                status='approved'
            ).select_related('approver')
            
            for approval in approvals:
                member = Member.objects.filter(
                    user=approval.approver,
                    project=obj.project
                ).select_related('role').first()
                
                if member and member.role and member.role.name.lower() == ROLE_ANNOTATION_APPROVER:
                    return ROLE_ANNOTATION_APPROVER
        except Exception:
            pass
        
        # Fallback: check Assignment.reviewed_by if no annotation_approver found
        if obj.reviewed_by:
            try:
                from projects.models import Member
                member = Member.objects.filter(
                    user=obj.reviewed_by,
                    project=obj.project
                ).select_related('role').first()
                
                if member and member.role:
                    role_name = member.role.name.lower()
                    # Only return if it's NOT project_admin (project_admin goes in final approval)
                    if role_name != 'project_admin':
                        return role_name
            except Exception:
                pass
        
        return None
    
    def get_final_approval_by_id(self, obj):
        """Get project_admin who gave final approval."""
        try:
            from assignment.completion_tracking import ApproverCompletionStatus
            from projects.models import Member
            from assignment.roles import ROLE_PROJECT_ADMIN
            
            # Find project_admin approval for this example
            approvals = ApproverCompletionStatus.objects.filter(
                example=obj.example,
                project=obj.project,
                status='approved'
            ).select_related('approver')
            
            for approval in approvals:
                member = Member.objects.filter(
                    user=approval.approver,
                    project=obj.project
                ).select_related('role').first()
                
                if member and member.role and member.role.name.lower() == ROLE_PROJECT_ADMIN:
                    return approval.approver.id
        except Exception:
            pass
        return None
    
    def get_final_approval_by_username(self, obj):
        """Get project_admin username who gave final approval."""
        try:
            from assignment.completion_tracking import ApproverCompletionStatus
            from projects.models import Member
            from assignment.roles import ROLE_PROJECT_ADMIN
            
            # Find project_admin approval for this example
            approvals = ApproverCompletionStatus.objects.filter(
                example=obj.example,
                project=obj.project,
                status='approved'
            ).select_related('approver')
            
            for approval in approvals:
                member = Member.objects.filter(
                    user=approval.approver,
                    project=obj.project
                ).select_related('role').first()
                
                if member and member.role and member.role.name.lower() == ROLE_PROJECT_ADMIN:
                    return approval.approver.username
        except Exception:
            pass
        return None
    
    def get_final_approval_at(self, obj):
        """Get when project_admin gave final approval."""
        try:
            from assignment.completion_tracking import ApproverCompletionStatus
            from projects.models import Member
            from assignment.roles import ROLE_PROJECT_ADMIN
            
            # Find project_admin approval for this example
            approvals = ApproverCompletionStatus.objects.filter(
                example=obj.example,
                project=obj.project,
                status='approved'
            ).select_related('approver').order_by('-reviewed_at')
            
            for approval in approvals:
                member = Member.objects.filter(
                    user=approval.approver,
                    project=obj.project
                ).select_related('role').first()
                
                if member and member.role and member.role.name.lower() == ROLE_PROJECT_ADMIN:
                    return approval.reviewed_at
        except Exception:
            pass
        return None
    
    def get_has_final_approval(self, obj):
        """Check if example has final approval from project_admin."""
        return self.get_final_approval_by_id(obj) is not None


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

