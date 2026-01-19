"""
Completion Tracking Models and Utilities

This module tracks per-annotator and per-approver completion status
for each example in a project. It provides a completion matrix view
for Project Managers.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.db.models import Count, Q, F
from django.contrib.auth import get_user_model

User = get_user_model()


class AnnotatorCompletionStatus(models.Model):
    """
    Tracks individual annotator's completion status for each example.
    This enables granular tracking of who completed what.
    """
    
    example = models.ForeignKey(
        'examples.Example',
        on_delete=models.CASCADE,
        related_name='annotator_completions'
    )
    
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='annotator_completions'
    )
    
    annotator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='annotation_completions'
    )
    
    # Completion status
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Link to assignment if exists
    assignment = models.ForeignKey(
        'assignment.Assignment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completion_status'
    )
    
    # Annotation count when marked complete
    annotation_count = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['example', 'annotator']
        indexes = [
            models.Index(fields=['project', 'annotator', 'is_completed']),
            models.Index(fields=['example', 'is_completed']),
        ]
    
    def __str__(self):
        status = "✓" if self.is_completed else "○"
        return f"{status} Example {self.example_id} - {self.annotator.username}"
    
    def mark_complete(self, annotation_count=0):
        """Mark this example as completed by this annotator."""
        self.is_completed = True
        self.completed_at = timezone.now()
        self.annotation_count = annotation_count
        self.save(update_fields=['is_completed', 'completed_at', 'annotation_count'])
    
    def mark_incomplete(self):
        """Mark as incomplete (e.g., after rejection)."""
        self.is_completed = False
        self.completed_at = None
        self.save(update_fields=['is_completed', 'completed_at'])


class ApproverCompletionStatus(models.Model):
    """
    Tracks individual approver's approval status for each example.
    Multiple approvers can review the same example.
    """
    
    example = models.ForeignKey(
        'examples.Example',
        on_delete=models.CASCADE,
        related_name='approver_completions'
    )
    
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='approver_completions'
    )
    
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='approval_completions'
    )
    
    # Approval status
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, default='')
    
    # Link to assignment if exists
    assignment = models.ForeignKey(
        'assignment.Assignment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approval_status'
    )
    
    class Meta:
        unique_together = ['example', 'approver']
        indexes = [
            models.Index(fields=['project', 'approver', 'status']),
            models.Index(fields=['example', 'status']),
        ]
    
    def __str__(self):
        status_icon = {
            'approved': '✓',
            'rejected': '✗',
            'pending': '○'
        }.get(self.status, '?')
        return f"{status_icon} Example {self.example_id} - {self.approver.username}"
    
    def approve(self, notes=''):
        """Mark as approved."""
        self.status = 'approved'
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save(update_fields=['status', 'reviewed_at', 'review_notes'])
    
    def reject(self, notes=''):
        """Mark as rejected."""
        self.status = 'rejected'
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save(update_fields=['status', 'reviewed_at', 'review_notes'])


class CompletionMatrix:
    """
    Utility class to generate completion matrix for Project Managers.
    Provides a comprehensive view of all annotators and approvers' progress.
    """
    
    def __init__(self, project):
        self.project = project
    
    def get_annotator_matrix(self):
        """
        Get completion matrix for all annotators in the project.
        
        Returns:
            List of dicts with structure:
            [
                {
                    'annotator_id': int,
                    'annotator_username': str,
                    'total_assigned': int,
                    'completed': int,
                    'in_progress': int,
                    'completion_rate': float,
                    'examples': [
                        {
                            'example_id': int,
                            'status': 'completed' | 'in_progress' | 'not_started',
                            'completed_at': datetime or None
                        }
                    ]
                }
            ]
        """
        from .models_separate import Assignment
        
        # Get all project members who are annotators
        annotator_role = self._get_annotator_role()
        members = self.project.members.filter(role=annotator_role)
        
        matrix = []
        for member in members:
            # Get assignments for this annotator
            assignments = Assignment.objects.filter(
                project=self.project,
                assigned_to=member.user,
                is_active=True
            )
            
            # Get completion status
            completions = AnnotatorCompletionStatus.objects.filter(
                project=self.project,
                annotator=member.user
            )
            
            total = assignments.count()
            completed = completions.filter(is_completed=True).count()
            
            # Build example details
            examples = []
            for assignment in assignments:
                completion = completions.filter(example=assignment.example).first()
                examples.append({
                    'example_id': assignment.example_id,
                    'assignment_id': assignment.id,
                    'status': assignment.status,
                    'is_completed': completion.is_completed if completion else False,
                    'completed_at': completion.completed_at if completion else None,
                    'started_at': assignment.started_at,
                    'submitted_at': assignment.submitted_at,
                })
            
            matrix.append({
                'annotator_id': member.user.id,
                'annotator_username': member.user.username,
                'total_assigned': total,
                'completed': completed,
                'in_progress': assignments.filter(status='in_progress').count(),
                'submitted': assignments.filter(status='submitted').count(),
                'approved': assignments.filter(status='approved').count(),
                'completion_rate': round((completed / total * 100), 1) if total > 0 else 0,
                'examples': examples
            })
        
        return matrix
    
    def get_approver_matrix(self):
        """
        Get approval matrix for all approvers in the project.
        
        Returns:
            List of dicts with structure:
            [
                {
                    'approver_id': int,
                    'approver_username': str,
                    'total_to_review': int,
                    'approved': int,
                    'rejected': int,
                    'pending': int,
                    'approval_rate': float,
                    'examples': [...]
                }
            ]
        """
        from .models_separate import Assignment
        
        # Get all project members who are approvers
        approver_role = self._get_approver_role()
        members = self.project.members.filter(role=approver_role)
        
        matrix = []
        for member in members:
            # Get assignments reviewed by this approver
            assignments = Assignment.objects.filter(
                project=self.project,
                reviewed_by=member.user
            )
            
            # Get approval status
            approvals = ApproverCompletionStatus.objects.filter(
                project=self.project,
                approver=member.user
            )
            
            total = approvals.count()
            approved_count = approvals.filter(status='approved').count()
            rejected_count = approvals.filter(status='rejected').count()
            pending_count = approvals.filter(status='pending').count()
            
            # Build example details
            examples = []
            for approval in approvals:
                examples.append({
                    'example_id': approval.example_id,
                    'status': approval.status,
                    'reviewed_at': approval.reviewed_at,
                    'review_notes': approval.review_notes,
                })
            
            matrix.append({
                'approver_id': member.user.id,
                'approver_username': member.user.username,
                'total_to_review': total,
                'approved': approved_count,
                'rejected': rejected_count,
                'pending': pending_count,
                'approval_rate': round((approved_count / total * 100), 1) if total > 0 else 0,
                'examples': examples
            })
        
        return matrix
    
    def get_complete_matrix(self):
        """
        Get complete matrix with both annotators and approvers.
        This is the main view for Project Managers.
        """
        return {
            'project_id': self.project.id,
            'project_name': self.project.name,
            'annotators': self.get_annotator_matrix(),
            'approvers': self.get_approver_matrix(),
            'summary': self._get_summary_stats()
        }
    
    def _get_summary_stats(self):
        """Get project-wide summary statistics."""
        from examples.models import Example
        from .models_separate import Assignment
        
        total_examples = Example.objects.filter(project=self.project).count()
        assigned_examples = Assignment.objects.filter(
            project=self.project,
            is_active=True
        ).values('example').distinct().count()
        
        completed_examples = AnnotatorCompletionStatus.objects.filter(
            project=self.project,
            is_completed=True
        ).values('example').distinct().count()
        
        # Count final approvals (project_admin approvals only)
        from projects.models import Member
        from .roles import ROLE_PROJECT_ADMIN
        
        # Get all project_admin members
        admin_members = Member.objects.filter(
            project=self.project
        ).select_related('role').filter(
            role__name__iexact=ROLE_PROJECT_ADMIN
        )
        
        admin_user_ids = [m.user_id for m in admin_members]
        
        # Count total approvals by project_admin (final approval)
        # Each approval action by a project_admin counts as 1 Final Approved
        final_approved_examples = ApproverCompletionStatus.objects.filter(
            project=self.project,
            status='approved',
            approver_id__in=admin_user_ids
        ).count()  # Count total approvals by project_admin, not distinct examples
        
        # Also count all approvals for backward compatibility
        all_approved_examples = ApproverCompletionStatus.objects.filter(
            project=self.project,
            status='approved'
        ).values('example').distinct().count()
        
        return {
            'total_examples': total_examples,
            'assigned_examples': assigned_examples,
            'unassigned_examples': total_examples - assigned_examples,
            'completed_examples': completed_examples,
            'approved_examples': all_approved_examples,  # All approvals (for backward compat)
            'final_approved_examples': final_approved_examples,  # Final approvals by project_admin
            'completion_rate': round((completed_examples / total_examples * 100), 1) if total_examples > 0 else 0,
            'approval_rate': round((all_approved_examples / total_examples * 100), 1) if total_examples > 0 else 0,
            'final_approval_rate': round((final_approved_examples / total_examples * 100), 1) if total_examples > 0 else 0
        }
    
    def _get_annotator_role(self):
        """Get the annotator role ID."""
        # Doccano role IDs (these are typically constants)
        # You may need to adjust based on actual Doccano implementation
        return 'annotator'
    
    def _get_approver_role(self):
        """Get the approver role ID."""
        return 'annotation_approver'


class CompletionMatrixUpdater:
    """
    Utility to automatically update completion tracking based on assignments.
    This should be called after annotations are created/updated.
    """
    
    @staticmethod
    def update_annotator_status(example, annotator, is_completed=True):
        """
        Update or create annotator completion status.
        
        Args:
            example: Example instance
            annotator: User instance (can be None, in which case this is a no-op)
            is_completed: Boolean
        """
        from examples.models import Example
        
        # Skip if annotator is None (assignment has no assigned user)
        if annotator is None:
            return None
        
        # Get or create completion status
        status, created = AnnotatorCompletionStatus.objects.get_or_create(
            example=example,
            annotator=annotator,
            defaults={
                'project': example.project,
                'is_completed': is_completed
            }
        )
        
        if not created and is_completed:
            # Count annotations for this example by this annotator
            annotation_count = example.annotations.filter(user=annotator).count()
            status.mark_complete(annotation_count=annotation_count)
        elif not created and not is_completed:
            status.mark_incomplete()
        
        return status
    
    @staticmethod
    def update_approver_status(example, approver, status_choice, notes=''):
        """
        Update or create approver completion status.
        
        Args:
            example: Example instance
            approver: User instance
            status_choice: 'approved', 'rejected', or 'pending'
            notes: Review notes
        """
        status, created = ApproverCompletionStatus.objects.get_or_create(
            example=example,
            approver=approver,
            defaults={
                'project': example.project,
                'status': status_choice,
                'review_notes': notes
            }
        )
        
        if not created:
            if status_choice == 'approved':
                status.approve(notes)
            elif status_choice == 'rejected':
                status.reject(notes)
        
        return status
    
    @staticmethod
    def sync_from_assignments(project):
        """
        Sync completion tracking from existing assignments.
        Useful for migrating existing data.
        
        Args:
            project: Project instance
        """
        from .models_separate import Assignment
        
        assignments = Assignment.objects.filter(project=project, is_active=True)
        
        for assignment in assignments:
            # Update annotator status (skip if assigned_to is None)
            if assignment.status in ['submitted', 'approved'] and assignment.assigned_to:
                CompletionMatrixUpdater.update_annotator_status(
                    example=assignment.example,
                    annotator=assignment.assigned_to,
                    is_completed=True
                )
            
            # Update approver status if reviewed
            if assignment.reviewed_by:
                status_map = {
                    'approved': 'approved',
                    'rejected': 'rejected'
                }
                status = status_map.get(assignment.status, 'pending')
                
                CompletionMatrixUpdater.update_approver_status(
                    example=assignment.example,
                    approver=assignment.reviewed_by,
                    status_choice=status,
                    notes=assignment.review_notes
                )

