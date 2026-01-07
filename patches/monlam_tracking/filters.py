"""
DRF Filter Backend for Visibility Filtering

Proper implementation using Django REST Framework's filter backend system.
This is the "expert" way to filter querysets in DRF views.
"""

from rest_framework import filters
from django.db.models import Q


class AnnotationVisibilityFilter(filters.BaseFilterBackend):
    """
    Filter examples based on annotation tracking status.
    
    Rules:
    - Admins: See all examples
    - Project Managers: See all examples
    - Approvers/Reviewers: See all examples
    - Annotators: See only unannotated examples + their own rejected
    """
    
    def filter_queryset(self, request, queryset, view):
        """
        Filter the queryset based on user role and tracking status.
        """
        user = request.user
        
        # Admins see everything
        if not user.is_authenticated or user.is_superuser:
            return queryset
        
        # Get project from view
        project_id = view.kwargs.get('project_id')
        if not project_id:
            return queryset
        
        # Check if user is project creator/admin or has special roles
        try:
            from projects.models import Project
            from roles.models import Member
            
            project = Project.objects.get(pk=project_id)
            
            # Project creator sees everything
            if project.created_by == user:
                return queryset
            
            # Check user's role in project
            try:
                member = Member.objects.get(user=user, project=project)
                role_name = member.role.name
                
                # These roles see all examples:
                # - project_admin
                # - project_manager  
                # - annotation_approver
                if role_name in ['project_admin', 'project_manager', 'annotation_approver']:
                    return queryset
                
                # annotator role gets filtered (continues below)
                print(f'[Monlam Filter] User {user.username} is {role_name} - applying filters')
                
            except Member.DoesNotExist:
                # Not a project member, apply restrictive filtering
                print(f'[Monlam Filter] User {user.username} not a project member')
                return queryset.none()
            
        except Exception as e:
            print(f'[Monlam Filter] Error checking project: {e}')
            return queryset
        
        # Apply filtering for annotators
        try:
            from assignment.simple_tracking import AnnotationTracking
            
            # Get tracking records for this project
            tracking_qs = AnnotationTracking.objects.filter(
                project_id=project_id
            ).select_related('annotated_by')
            
            # Build list of example IDs to show/hide
            show_ids = set()
            hide_ids = set()
            
            for tracking in tracking_qs:
                example_id = tracking.example_id
                
                # Show unannotated (pending)
                if tracking.status == 'pending':
                    show_ids.add(example_id)
                
                # Show if rejected and annotated by this user (to fix)
                elif tracking.status == 'rejected' and tracking.annotated_by == user:
                    show_ids.add(example_id)
                
                # Hide if annotated by someone else
                elif tracking.annotated_by and tracking.annotated_by != user:
                    hide_ids.add(example_id)
                
                # Hide if annotated by this user and submitted/approved
                elif tracking.annotated_by == user and tracking.status in ['submitted', 'approved']:
                    hide_ids.add(example_id)
            
            # Get all example IDs in queryset
            all_ids = set(queryset.values_list('id', flat=True))
            
            # Examples with no tracking = unannotated = show
            tracked_ids = set(t.example_id for t in tracking_qs)
            untracked_ids = all_ids - tracked_ids
            
            # Final: (show + untracked) - hide
            final_ids = (show_ids | untracked_ids) - hide_ids
            
            return queryset.filter(id__in=final_ids)
            
        except Exception as e:
            print(f'[Monlam Filter] Error filtering: {e}')
            return queryset


def register_visibility_filter():
    """
    Register the visibility filter with Doccano's example views.
    
    This is called from apps.py ready() method.
    """
    try:
        # Import Doccano's settings
        from django.conf import settings
        
        # Add our filter to DRF's DEFAULT_FILTER_BACKENDS
        if not hasattr(settings, 'REST_FRAMEWORK'):
            settings.REST_FRAMEWORK = {}
        
        if 'DEFAULT_FILTER_BACKENDS' not in settings.REST_FRAMEWORK:
            settings.REST_FRAMEWORK['DEFAULT_FILTER_BACKENDS'] = []
        
        # Convert tuple to list if necessary (Django sometimes uses tuples)
        if isinstance(settings.REST_FRAMEWORK['DEFAULT_FILTER_BACKENDS'], tuple):
            settings.REST_FRAMEWORK['DEFAULT_FILTER_BACKENDS'] = list(
                settings.REST_FRAMEWORK['DEFAULT_FILTER_BACKENDS']
            )
        
        filter_class = 'monlam_tracking.filters.AnnotationVisibilityFilter'
        
        if filter_class not in settings.REST_FRAMEWORK['DEFAULT_FILTER_BACKENDS']:
            settings.REST_FRAMEWORK['DEFAULT_FILTER_BACKENDS'].append(filter_class)
            print(f'[Monlam Filter] ✅ Added {filter_class} to DRF backends')
        else:
            print(f'[Monlam Filter] ✅ Filter already registered')
        
        return True
        
    except Exception as e:
        print(f'[Monlam Filter] ⚠️ Registration failed: {e}')
        import traceback
        traceback.print_exc()
        return False

