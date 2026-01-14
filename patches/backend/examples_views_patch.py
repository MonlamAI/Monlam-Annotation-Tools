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
        Includes lock filtering to prevent conflicts between annotators
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        # Debug logging (can be removed in production)
        import sys
        print(f'[ExampleVisibilityMixin] get_queryset called for user {user.username}', file=sys.stderr, flush=True)
        
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
        # Use project_id instead of project object to avoid issues
        tracking_qs = AnnotationTracking.objects.filter(
            project_id=project_id
        ).select_related('annotated_by', 'reviewed_by', 'locked_by')
        
        # Get all example IDs in this project (queryset is already filtered by project from super())
        all_example_ids = set(queryset.values_list('id', flat=True))
        
        if not all_example_ids:
            # No examples in project, return empty
            return queryset.none()
        
        # Build filter conditions
        show_example_ids = []
        hide_example_ids = []
        locked_by_others = set()
        
        # First pass: Check for locked examples (highest priority)
        for tracking in tracking_qs:
            example_id = tracking.example_id
            
            # Skip if this example doesn't exist in the queryset
            if example_id not in all_example_ids:
                continue
            
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
            
            # Skip if this example doesn't exist in the queryset or is locked
            if example_id not in all_example_ids or example_id in locked_by_others:
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
        
        # Examples with no tracking record = unannotated = show to everyone (unless locked)
        tracked_ids = set(t.example_id for t in tracking_qs if t.example_id in all_example_ids)
        untracked_ids = all_example_ids - tracked_ids
        
        # Final list: (explicitly shown + untracked) - explicitly hidden - locked by others
        final_ids = (set(show_example_ids) | untracked_ids) - set(hide_example_ids) - locked_by_others
        
        # Debug logging
        import sys
        print(f'[ExampleVisibilityMixin] User: {user.username}, Project: {project_id}', file=sys.stderr, flush=True)
        print(f'[ExampleVisibilityMixin] Total examples: {len(all_example_ids)}, Tracked: {len(tracked_ids)}, Untracked: {len(untracked_ids)}', file=sys.stderr, flush=True)
        print(f'[ExampleVisibilityMixin] Show: {len(show_example_ids)}, Hide: {len(hide_example_ids)}, Locked by others: {len(locked_by_others)}', file=sys.stderr, flush=True)
        print(f'[ExampleVisibilityMixin] Final IDs: {len(final_ids)}', file=sys.stderr, flush=True)
        
        # Safety check: if final_ids is empty but there are untracked examples, something went wrong
        # In that case, show untracked examples (they're unannotated and should be visible)
        if not final_ids and untracked_ids:
            print(f'[ExampleVisibilityMixin] ⚠️ WARNING: Final IDs empty but untracked exists, showing untracked only', file=sys.stderr, flush=True)
            final_ids = untracked_ids - locked_by_others
        
        # If still empty, return empty queryset
        if not final_ids:
            print(f'[ExampleVisibilityMixin] ⚠️ No examples visible to user {user.username}', file=sys.stderr, flush=True)
            return queryset.none()
        
        return queryset.filter(id__in=final_ids)

