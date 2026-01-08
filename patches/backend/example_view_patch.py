"""
Patch for Doccano's Example View to add visibility filtering.

This is a more direct approach than using REST_FRAMEWORK filter backends,
which Doccano might not use properly.
"""

def patch_example_view():
    """
    Patch Doccano's ExampleListAPI to filter examples based on user role.
    
    Returns True if patching succeeded.
    """
    try:
        from examples.views import ExampleListAPI
        from django.db.models import Q
        
        # Store original get_queryset
        original_get_queryset = ExampleListAPI.get_queryset
        
        def patched_get_queryset(self):
            """
            Override get_queryset to filter based on annotation tracking.
            
            - Admins/Managers/Approvers: See all examples
            - Annotators: See only unannotated + own rejected examples
            """
            queryset = original_get_queryset(self)
            user = self.request.user
            
            # Superusers see everything
            if not user.is_authenticated or user.is_superuser:
                return queryset
            
            # Get project
            project_id = self.kwargs.get('project_id')
            if not project_id:
                return queryset
            
            try:
                from projects.models import Project
                from roles.models import Member
                
                project = Project.objects.get(pk=project_id)
                
                # Project creator sees everything
                if project.created_by == user:
                    return queryset
                
                # Check user's role
                try:
                    member = Member.objects.get(user=user, project=project)
                    role_name = member.role.name.lower() if member.role.name else ''
                    
                    # Privileged roles see all
                    if 'admin' in role_name or 'manager' in role_name or 'approver' in role_name:
                        print(f'[Monlam Visibility] {user.username} is {role_name} - showing ALL examples')
                        return queryset
                    
                    print(f'[Monlam Visibility] {user.username} is {role_name} - applying filters')
                    
                except Member.DoesNotExist:
                    print(f'[Monlam Visibility] {user.username} not a member - showing none')
                    return queryset.none()
                
                # Apply filtering for annotators
                from assignment.simple_tracking import AnnotationTracking
                from datetime import timedelta
                
                # Get all tracking records for this project
                tracking_qs = AnnotationTracking.objects.filter(project_id=project_id)
                
                # Build sets of example IDs to show/hide
                show_ids = set()
                hide_ids = set()
                
                for tracking in tracking_qs:
                    example_id = tracking.example_id
                    
                    # LOCKING: Hide examples locked by others (within 30 min)
                    if tracking.locked_by and tracking.locked_by != user:
                        if tracking.locked_at:
                            lock_expiry = tracking.locked_at + timedelta(minutes=30)
                            if timezone.now() < lock_expiry:
                                hide_ids.add(example_id)
                                continue  # Skip other checks, this is locked
                    
                    # Pending = show (not yet annotated)
                    if tracking.status == 'pending':
                        show_ids.add(example_id)
                    
                    # Rejected by current user = show (needs to fix)
                    elif tracking.status == 'rejected' and tracking.annotated_by == user:
                        show_ids.add(example_id)
                    
                    # Annotated by someone else = hide
                    elif tracking.annotated_by and tracking.annotated_by != user:
                        hide_ids.add(example_id)
                    
                    # Annotated by this user and submitted/approved = hide
                    elif tracking.annotated_by == user and tracking.status in ['submitted', 'approved']:
                        hide_ids.add(example_id)
                
                # Examples without tracking = not annotated = show
                all_example_ids = set(queryset.values_list('id', flat=True))
                tracked_ids = set(tracking_qs.values_list('example_id', flat=True))
                untracked_ids = all_example_ids - tracked_ids
                
                # Final filter: (show + untracked) - hide
                visible_ids = (show_ids | untracked_ids) - hide_ids
                
                print(f'[Monlam Visibility] Showing {len(visible_ids)} of {len(all_example_ids)} examples')
                return queryset.filter(id__in=visible_ids)
                
            except Exception as e:
                print(f'[Monlam Visibility] Error: {e}')
                import traceback
                traceback.print_exc()
                return queryset
        
        # Apply the patch
        ExampleListAPI.get_queryset = patched_get_queryset
        print('[Monlam Visibility] ✅ Patched ExampleListAPI.get_queryset')
        return True
        
    except Exception as e:
        print(f'[Monlam Visibility] ❌ Patch failed: {e}')
        import traceback
        traceback.print_exc()
        return False

