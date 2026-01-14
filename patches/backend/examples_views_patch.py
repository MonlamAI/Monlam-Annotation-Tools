"""
Patch for Doccano's Examples Views
Adds visibility filtering so annotators only see their own examples + unannotated ones
"""

from django.db.models import Q
from rest_framework import viewsets, status as http_status
from rest_framework.decorators import action
from rest_framework.response import Response


class ExampleVisibilityMixin:
    """
    Mixin to filter examples based on annotation tracking
    
    Rules:
    1. Admins see everything
    2. Project Managers see everything
    3. Approvers/Reviewers see everything
    4. Annotators see:
       - Unannotated examples (pending status)
       - Their own examples (if not submitted/approved)
       - Their rejected examples (to fix)
    """
    
    def get_queryset(self):
        """
        Filter examples based on user role and tracking status
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user.is_authenticated:
            return queryset.none()
        
        # Admins see everything
        if user.is_superuser:
            return queryset
        
        # Get project from URL
        project_id = self.kwargs.get('project_id')
        if not project_id:
            return queryset
        
        from projects.models import Project
        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return queryset.none()
        
        # Check if user is project member
        if not project.members.filter(id=user.id).exists():
            return queryset.none()
        
        # Check if user is project creator or admin (they see everything)
        is_project_admin = (
            project.created_by == user or
            user in project.admins.all() if hasattr(project, 'admins') else False
        )
        
        if is_project_admin:
            return queryset
        
        # Try to determine if user is a reviewer/approver
        # For now, assume non-admins who aren't project admins might be annotators
        # More sophisticated role checking can be added here
        
        # Import tracking model
        try:
            from assignment.simple_tracking import AnnotationTracking
            from django.utils import timezone
            from datetime import timedelta
        except ImportError:
            # If tracking not available, return full queryset
            return queryset
        
        # Get all tracking records for this project
        tracking_qs = AnnotationTracking.objects.filter(
            project=project
        ).select_related('annotated_by', 'reviewed_by', 'locked_by')
        
        # Build filter conditions
        show_example_ids = []
        hide_example_ids = []
        locked_by_others = set()
        
        # First pass: Check for locked examples (highest priority)
        for tracking in tracking_qs:
            example_id = tracking.example_id
            
            # Check if locked by someone else
            if tracking.locked_by and tracking.locked_by != user:
                if tracking.locked_at:
                    lock_expiry = tracking.locked_at + timedelta(minutes=5)
                    if timezone.now() < lock_expiry:
                        # Still locked by someone else - HIDE
                        locked_by_others.add(example_id)
                        hide_example_ids.append(example_id)
                        continue  # Skip other checks for this example
                    else:
                        # Lock expired, clear it
                        tracking.locked_by = None
                        tracking.locked_at = None
                        tracking.save(update_fields=['locked_by', 'locked_at'])
        
        # Second pass: Check tracking status (only for non-locked examples)
        for tracking in tracking_qs:
            example_id = tracking.example_id
            
            # Skip if already hidden due to locking
            if example_id in locked_by_others:
                continue
            
            # Show if pending (unannotated)
            if tracking.status == 'pending':
                show_example_ids.append(example_id)
            
            # Show if rejected and annotated by this user (needs fixing)
            elif tracking.status == 'rejected' and tracking.annotated_by == user:
                show_example_ids.append(example_id)
            
            # Show if in_progress by this user
            elif tracking.status == 'in_progress' and tracking.annotated_by == user:
                show_example_ids.append(example_id)
            
            # Hide if submitted by this user (already done, awaiting review)
            elif tracking.status == 'submitted' and tracking.annotated_by == user:
                hide_example_ids.append(example_id)
            
            # Hide if approved (completely done)
            elif tracking.status == 'approved':
                hide_example_ids.append(example_id)
            
            # Hide if annotated by someone else
            elif tracking.annotated_by and tracking.annotated_by != user:
                hide_example_ids.append(example_id)
        
        # Get all example IDs in this project
        all_example_ids = set(queryset.filter(project=project).values_list('id', flat=True))
        
        # Examples with no tracking record = unannotated = show to everyone (unless locked)
        tracked_ids = set(t.example_id for t in tracking_qs)
        untracked_ids = all_example_ids - tracked_ids
        
        # Final list: (explicitly shown + untracked) - explicitly hidden - locked by others
        final_ids = (set(show_example_ids) | untracked_ids) - set(hide_example_ids) - locked_by_others
        
        return queryset.filter(id__in=final_ids)

