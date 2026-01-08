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
        # Try different import paths (Doccano version differences)
        ExampleListAPI = None
        
        # Try 1: Direct import from views package
        try:
            from examples.views.example import ExampleList
            ExampleListAPI = ExampleList
            print('[Monlam Visibility] Found ExampleList in examples.views.example')
        except ImportError:
            pass
        
        # Try 2: From views __init__
        if not ExampleListAPI:
            try:
                from examples.views import ExampleList
                ExampleListAPI = ExampleList
                print('[Monlam Visibility] Found ExampleList in examples.views')
            except ImportError:
                pass
        
        # Try 3: ExampleListAPI name
        if not ExampleListAPI:
            try:
                from examples.views.example import ExampleListAPI as ELA
                ExampleListAPI = ELA
                print('[Monlam Visibility] Found ExampleListAPI in examples.views.example')
            except ImportError:
                pass
        
        # Try 4: Search in views module
        if not ExampleListAPI:
            try:
                from examples import views
                # Look for any class with "Example" and "List" in name
                for name in dir(views):
                    if 'Example' in name and 'List' in name:
                        ExampleListAPI = getattr(views, name)
                        print(f'[Monlam Visibility] Found {name} in examples.views')
                        break
            except ImportError:
                pass
        
        if not ExampleListAPI:
            print('[Monlam Visibility] Could not find ExampleList view - visibility filtering disabled')
            print('[Monlam Visibility] Will rely on REST_FRAMEWORK filter backend instead')
            return False
        
        from django.db.models import Q
        from django.utils import timezone
        
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


def patch_via_url_dispatcher():
    """
    Alternative approach: Find the Example view via URL resolver.
    """
    try:
        from django.urls import resolve
        from django.utils import timezone
        
        # Try to resolve the examples URL pattern
        # Typical Doccano URL: /v1/projects/{project_id}/examples
        try:
            resolved = resolve('/v1/projects/1/examples')
            view_class = resolved.func.cls if hasattr(resolved.func, 'cls') else None
            
            if not view_class:
                print('[Monlam Visibility] Could not find view class from URL resolver')
                return False
            
            print(f'[Monlam Visibility] Found view class via URL: {view_class.__name__}')
            
            # Store original get_queryset
            if not hasattr(view_class, 'get_queryset'):
                print('[Monlam Visibility] View class has no get_queryset method')
                return False
            
            original_get_queryset = view_class.get_queryset
            
            def patched_get_queryset(self):
                """Visibility filtering via URL resolver patch."""
                queryset = original_get_queryset(self)
                user = self.request.user
                
                if not user.is_authenticated or user.is_superuser:
                    return queryset
                
                project_id = self.kwargs.get('project_id')
                if not project_id:
                    return queryset
                
                try:
                    from projects.models import Project
                    from roles.models import Member
                    
                    project = Project.objects.get(pk=project_id)
                    
                    if project.created_by == user:
                        return queryset
                    
                    try:
                        member = Member.objects.get(user=user, project=project)
                        role_name = member.role.name.lower() if member.role.name else ''
                        
                        if 'admin' in role_name or 'manager' in role_name or 'approver' in role_name:
                            return queryset
                        
                    except Member.DoesNotExist:
                        return queryset.none()
                    
                    # Apply filtering
                    from assignment.simple_tracking import AnnotationTracking
                    from datetime import timedelta
                    
                    tracking_qs = AnnotationTracking.objects.filter(project_id=project_id)
                    
                    show_ids = set()
                    hide_ids = set()
                    
                    for tracking in tracking_qs:
                        example_id = tracking.example_id
                        
                        if tracking.locked_by and tracking.locked_by != user:
                            if tracking.locked_at:
                                lock_expiry = tracking.locked_at + timedelta(minutes=30)
                                if timezone.now() < lock_expiry:
                                    hide_ids.add(example_id)
                                    continue
                        
                        if tracking.status == 'pending':
                            show_ids.add(example_id)
                        elif tracking.status == 'rejected' and tracking.annotated_by == user:
                            show_ids.add(example_id)
                        elif tracking.annotated_by and tracking.annotated_by != user:
                            hide_ids.add(example_id)
                        elif tracking.annotated_by == user and tracking.status in ['submitted', 'approved']:
                            hide_ids.add(example_id)
                    
                    all_example_ids = set(queryset.values_list('id', flat=True))
                    tracked_ids = set(tracking_qs.values_list('example_id', flat=True))
                    untracked_ids = all_example_ids - tracked_ids
                    
                    visible_ids = (show_ids | untracked_ids) - hide_ids
                    
                    print(f'[Monlam Visibility] Showing {len(visible_ids)} of {len(all_example_ids)} examples')
                    return queryset.filter(id__in=visible_ids)
                    
                except Exception as e:
                    print(f'[Monlam Visibility] Filter error: {e}')
                    return queryset
            
            view_class.get_queryset = patched_get_queryset
            print('[Monlam Visibility] ✅ Patched view via URL resolver')
            return True
            
        except Exception as e:
            print(f'[Monlam Visibility] URL resolver approach failed: {e}')
            return False
            
    except Exception as e:
        print(f'[Monlam Visibility] Alternative patch failed: {e}')
        return False

