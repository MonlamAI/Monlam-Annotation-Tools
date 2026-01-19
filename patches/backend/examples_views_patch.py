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
        
        # Check if user is project member using Doccano's Member model
        from projects.models import Member
        try:
            member = Member.objects.filter(project=project, user=user).first()
            if not member:
                # User is not a project member
                return queryset.none()
            
            # Check if user is project creator or has admin role (they see everything)
            role_name = member.role.name.lower() if member.role and member.role.name else ''
            is_project_admin = (
                project.created_by == user or
                'admin' in role_name or
                'manager' in role_name
            )
            
            if is_project_admin:
                return queryset
            
            # Check if user is approver (they also see everything for reviewing)
            is_approver = 'approver' in role_name
            if is_approver:
                return queryset
        except Exception as e:
            import sys
            print(f'[ExampleVisibilityMixin] Error checking membership: {e}', file=sys.stderr, flush=True)
            # If we can't check membership, be safe and return empty
            return queryset.none()
        
        # Import tracking model
        try:
            from assignment.simple_tracking import AnnotationTracking
        except ImportError:
            # If tracking not available, return full queryset
            import sys
            print('[ExampleVisibilityMixin] ⚠️ Tracking not available, returning full queryset', file=sys.stderr, flush=True)
            return queryset
        
        # Get all tracking records for this project
        # Use project_id instead of project object to avoid issues
        tracking_qs = AnnotationTracking.objects.filter(
            project_id=project_id
        ).select_related('annotated_by', 'reviewed_by')
        
        # Get all example IDs in this project - EXPLICITLY filter by project_id to prevent cross-project contamination
        all_example_ids = set(queryset.filter(project_id=project_id).values_list('id', flat=True))
        
        if not all_example_ids:
            # No examples in project, return empty
            return queryset.none()
        
        # Build filter conditions
        show_example_ids = []
        hide_example_ids = []
        
        # Check tracking status
        for tracking in tracking_qs:
            example_id = tracking.example_id
            
            # Skip if this example doesn't exist in the queryset
            if example_id not in all_example_ids:
                continue
            
            # CRITICAL: If annotated_by is set and it's NOT the current user, HIDE it
            # This ensures examples annotated by other annotators are never visible
            if tracking.annotated_by and tracking.annotated_by != user:
                hide_example_ids.append(example_id)
                continue  # Skip other checks - already hidden
            
            # If annotated_by is set and it IS the current user, check status
            if tracking.annotated_by == user:
                # Show if rejected (needs fixing by original annotator)
                if tracking.status == 'rejected':
                    show_example_ids.append(example_id)
                # Hide if submitted or approved (already done, no longer editable)
                elif tracking.status in ['submitted', 'approved', 'reviewed']:
                    hide_example_ids.append(example_id)
                # If status is 'pending' but annotated_by is set, it means user started working on it
                # Show it so they can continue (but it's already hidden from others above)
                elif tracking.status == 'pending':
                    show_example_ids.append(example_id)
            
            # If no annotated_by set and status is pending, show to everyone (unannotated)
            elif not tracking.annotated_by and tracking.status == 'pending':
                show_example_ids.append(example_id)
            
            # Hide if approved/reviewed (completely done, regardless of who did it)
            elif tracking.status in ['approved', 'reviewed']:
                hide_example_ids.append(example_id)
        
        # Examples with no tracking record = unannotated = show to everyone
        tracked_ids = set(t.example_id for t in tracking_qs if t.example_id in all_example_ids)
        untracked_ids = all_example_ids - tracked_ids
        
        # Final list: (explicitly shown + untracked) - explicitly hidden
        final_ids = (set(show_example_ids) | untracked_ids) - set(hide_example_ids)
        
        # Debug logging
        import sys
        print(f'[ExampleVisibilityMixin] User: {user.username}, Project: {project_id}', file=sys.stderr, flush=True)
        print(f'[ExampleVisibilityMixin] Total examples: {len(all_example_ids)}, Tracked: {len(tracked_ids)}, Untracked: {len(untracked_ids)}', file=sys.stderr, flush=True)
        print(f'[ExampleVisibilityMixin] Show: {len(show_example_ids)}, Hide: {len(hide_example_ids)}', file=sys.stderr, flush=True)
        print(f'[ExampleVisibilityMixin] Final IDs: {len(final_ids)}', file=sys.stderr, flush=True)
        
        # Safety check: if final_ids is empty but there are untracked examples, something went wrong
        # In that case, show untracked examples (they're unannotated and should be visible)
        if not final_ids and untracked_ids:
            print(f'[ExampleVisibilityMixin] ⚠️ WARNING: Final IDs empty but untracked exists, showing untracked only', file=sys.stderr, flush=True)
            final_ids = untracked_ids
        
        # CRITICAL SAFETY: If still empty and there are examples in the project, 
        # something is wrong with filtering - return all examples to prevent breaking the UI
        # This should only happen if there's a bug in the filtering logic
        if not final_ids and all_example_ids:
            print(f'[ExampleVisibilityMixin] ⚠️ CRITICAL: No examples visible but project has {len(all_example_ids)} examples!', file=sys.stderr, flush=True)
            print(f'[ExampleVisibilityMixin] ⚠️ Returning all examples to prevent empty page (filtering may have bug)', file=sys.stderr, flush=True)
            # Return queryset filtered by project (safety fallback)
            return queryset.filter(project_id=project_id)
        
        # If project has no examples, return empty
        if not final_ids:
            print(f'[ExampleVisibilityMixin] ⚠️ No examples visible to user {user.username} (project may be empty)', file=sys.stderr, flush=True)
            return queryset.none()
        
        # Filter by project_id AND final_ids to ensure we only return examples from this project
        return queryset.filter(project_id=project_id, id__in=final_ids)

