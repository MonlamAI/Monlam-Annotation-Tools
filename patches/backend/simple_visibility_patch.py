"""
Simple Visibility Patch - Hide Confirmed Examples from Annotators

Uses Doccano's built-in ExampleState to filter examples:
- Annotators: Only see examples where they haven't confirmed yet
- Approvers/Admins: See all examples
"""

from django.db.models import Q


def patch_example_queryset():
    """
    Monkey-patch Doccano's ExampleViewSet to filter based on confirmation status.
    This is the simplest approach using Doccano's built-in state system.
    """
    try:
        from examples.views import ExampleViewSet
        from roles.models import Member
        
        # Save original get_queryset
        original_get_queryset = ExampleViewSet.get_queryset
        
        def filtered_get_queryset(self):
            """
            Filter examples based on user role and confirmation status.
            
            Rules:
            1. Admins/Superusers: See all examples
            2. Project creators: See all examples
            3. Approvers: See all examples
            4. Annotators: Only see unconfirmed examples + their own
            """
            queryset = original_get_queryset(self)
            user = self.request.user
            
            # Admins see everything
            if not user.is_authenticated or user.is_superuser:
                return queryset
            
            # Get project from URL
            project_id = self.kwargs.get('project_id')
            if not project_id:
                return queryset
            
            try:
                from projects.models import Project
                project = Project.objects.get(pk=project_id)
                
                # Project creator sees everything
                if project.created_by == user:
                    return queryset
                
                # Check user's role
                try:
                    member = Member.objects.get(user=user, project=project)
                    role_name = member.role.name.lower() if member.role else ''
                    
                    # Privileged roles see everything
                    is_privileged = (
                        'admin' in role_name or
                        'manager' in role_name or
                        'approver' in role_name or
                        'approval' in role_name
                    )
                    
                    if is_privileged:
                        print(f'[Monlam Visibility] User {user.username} is {role_name} - seeing all examples')
                        return queryset
                    
                    # Annotators: Filter to show only unconfirmed examples
                    print(f'[Monlam Visibility] User {user.username} is {role_name} - filtering to unconfirmed')
                    
                    # Get all example states for this project
                    from examples.models import ExampleState
                    
                    # Find examples that are confirmed by ANYONE
                    confirmed_ids = ExampleState.objects.filter(
                        example__project_id=project_id,
                        confirmed_by__isnull=False
                    ).values_list('example_id', flat=True)
                    
                    # Hide confirmed examples from annotators
                    return queryset.exclude(id__in=confirmed_ids)
                    
                except Member.DoesNotExist:
                    print(f'[Monlam Visibility] User {user.username} not a project member')
                    return queryset.none()
                    
            except Exception as e:
                print(f'[Monlam Visibility] Error: {e}')
                return queryset
        
        # Apply the patch
        ExampleViewSet.get_queryset = filtered_get_queryset
        print('[Monlam Visibility] ✅ Patched ExampleViewSet to hide confirmed examples from annotators')
        return True
        
    except Exception as e:
        print(f'[Monlam Visibility] ⚠️ Failed to patch: {e}')
        import traceback
        traceback.print_exc()
        return False


def apply_visibility_patch():
    """
    Entry point to apply the visibility patch.
    Called from Django app ready() or settings.
    """
    return patch_example_queryset()

