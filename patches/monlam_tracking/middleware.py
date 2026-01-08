"""
Monlam Visibility Middleware - SIMPLIFIED

Instead of complex filtering, we now:
1. Use Doccano's native confirmed=false filter
2. Just log requests for debugging
3. Let the frontend handle filter defaults
"""

import re
import sys


def log(msg):
    """Force immediate output to stderr"""
    print(msg, file=sys.stderr, flush=True)


class VisibilityMiddleware:
    """
    Simplified middleware - just logging now.
    
    Visibility is handled by:
    1. Doccano's native ?confirmed=false filter (set via frontend)
    2. Frontend JavaScript to default filter for annotators
    """
    
    def __init__(self, get_response):
        log('[Monlam MW] 🚀 VisibilityMiddleware initialized (simplified)')
        self.get_response = get_response
    
    def __call__(self, request):
        # Just pass through - no filtering
        return self.get_response(request)
    
    def _is_privileged_user(self, user, project_id):
        """Check if user is admin/manager/approver."""
        try:
            from projects.models import Project
            from roles.models import Member
            
            project = Project.objects.get(pk=project_id)
            
            # Project creator sees all
            if project.created_by == user:
                return True
            
            # Check role
            try:
                member = Member.objects.get(user=user, project=project)
                role_name = member.role.name.lower() if member.role.name else ''
                
                # Privileged roles
                if 'admin' in role_name or 'manager' in role_name or 'approver' in role_name:
                    return True
                    
            except Member.DoesNotExist:
                pass
            
            return False
            
        except Exception:
            return False
    
    def _filter_response(self, response, user, project_id):
        """Filter the examples response for annotators."""
        try:
            # Only filter JSON responses
            content_type = response.get('Content-Type', '')
            if 'application/json' not in content_type:
                return response
            
            # Parse response
            data = json.loads(response.content)
            
            # Get results list
            results = data.get('results', [])
            if not results:
                return response
            
            # Get CONFIRMATION data from Doccano's ExampleState
            from examples.models import ExampleState, Example
            
            # Get all confirmed examples in this project (for total count)
            all_project_examples = Example.objects.filter(project_id=project_id).values_list('id', flat=True)
            all_confirmed = set(
                ExampleState.objects.filter(example_id__in=all_project_examples)
                .exclude(confirmed_by=user)  # Exclude ones confirmed by current user
                .values_list('example_id', flat=True)
            )
            my_confirmed = set(
                ExampleState.objects.filter(example_id__in=all_project_examples, confirmed_by=user)
                .values_list('example_id', flat=True)
            )
            
            # Total visible = all examples - confirmed by others - confirmed by me
            total_visible = len(all_project_examples) - len(all_confirmed) - len(my_confirmed)
            
            log(f'[Monlam Middleware] Total: {len(all_project_examples)}, Confirmed by others: {len(all_confirmed)}, By me: {len(my_confirmed)}, Visible: {total_visible}')
            
            # Get current page's confirmed states
            example_ids = [ex.get('id') for ex in results if ex.get('id')]
            confirmed_states = ExampleState.objects.filter(
                example_id__in=example_ids
            ).select_related('confirmed_by')
            
            # Map: example_id -> confirmed_by user
            confirmed_map = {state.example_id: state.confirmed_by for state in confirmed_states}
            
            # Also get our tracking data for locking and review status
            from assignment.simple_tracking import AnnotationTracking
            tracking_qs = AnnotationTracking.objects.filter(
                project_id=project_id,
                example_id__in=example_ids
            ).select_related('locked_by')
            tracking_map = {t.example_id: t for t in tracking_qs}
            
            # Filter results
            filtered_results = []
            for example in results:
                example_id = example.get('id')
                if example_id is None:
                    continue
                
                confirmed_by = confirmed_map.get(example_id)
                tracking = tracking_map.get(example_id)
                
                if self._should_show_example(example_id, confirmed_by, tracking, user):
                    filtered_results.append(example)
            
            # Update response with correct total count
            data['results'] = filtered_results
            data['count'] = total_visible  # Use calculated total, not just current page
            
            # Create new response
            from django.http import JsonResponse
            new_response = JsonResponse(data)
            
            # Copy headers
            for header, value in response.items():
                if header.lower() not in ['content-length', 'content-type']:
                    new_response[header] = value
            
            log(f'[Monlam Middleware] Page filtered: {len(results)} → {len(filtered_results)}, Total visible: {total_visible}')
            
            return new_response
            
        except Exception as e:
            log(f'[Monlam Middleware] Filter error: {e}')
            import traceback
            traceback.print_exc()
            return response
    
    def _should_show_example(self, example_id, confirmed_by, tracking, user):
        """
        Determine if an example should be visible to this user.
        
        Uses Doccano's ExampleState (confirmation) as the source of truth.
        """
        
        # Check locking first (from our tracking)
        if tracking and tracking.locked_by:
            if tracking.locked_by == user:
                log(f'[Visibility] Example {example_id}: Locked by me → SHOW')
                return True
            else:
                if tracking.locked_at:
                    lock_expiry = tracking.locked_at + timedelta(minutes=30)
                    if timezone.now() < lock_expiry:
                        log(f'[Visibility] Example {example_id}: Locked by {tracking.locked_by} → HIDE')
                        return False
        
        # Not confirmed = available for annotation = SHOW
        if not confirmed_by:
            log(f'[Visibility] Example {example_id}: Not confirmed → SHOW')
            return True
        
        # Confirmed by current user = already done by me = HIDE
        if confirmed_by == user:
            log(f'[Visibility] Example {example_id}: Confirmed by me → HIDE')
            return False
        
        # Confirmed by someone else = HIDE
        if confirmed_by != user:
            log(f'[Visibility] Example {example_id}: Confirmed by {confirmed_by.username} → HIDE')
            return False
        
        # Check if rejected (needs re-annotation)
        if tracking and tracking.status == 'rejected' and tracking.annotated_by == user:
            log(f'[Visibility] Example {example_id}: Rejected, needs my fix → SHOW')
            return True
        
        # Default: show
        log(f'[Visibility] Example {example_id}: Default → SHOW')
        return True

