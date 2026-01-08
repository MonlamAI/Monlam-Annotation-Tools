"""
Monlam Visibility Middleware

A SAFE approach to filter examples for annotators.
This runs at request/response time, NOT during app initialization.

How it works:
1. Intercepts API responses to /v1/projects/{id}/examples
2. Filters results based on user role and ExampleState (confirmation)
3. For single-item requests (limit=1), returns the Nth VISIBLE example
4. Does NOT modify views or querysets directly
"""

import json
import re
import sys
from datetime import timedelta
from django.utils import timezone


def log(msg):
    """Force immediate output to stderr"""
    print(msg, file=sys.stderr, flush=True)


class VisibilityMiddleware:
    """
    Middleware to filter example visibility for annotators.
    
    - Admins/Managers/Approvers: See all examples
    - Annotators: See only unannotated + own rejected + own locked
    
    IMPORTANT: Handles both list requests AND single-item requests correctly.
    """
    
    def __init__(self, get_response):
        log('[Monlam MW] 🚀 VisibilityMiddleware initialized!')
        self.get_response = get_response
        # Regex to match examples API endpoint
        self.examples_pattern = re.compile(r'^/v1/projects/(\d+)/examples/?$')
    
    def __call__(self, request):
        # Debug: Log EVERY request to see if middleware is active
        if '/examples' in request.path:
            log(f'[Monlam MW] 📥 Request: {request.method} {request.path}')
        
        # Only process GET requests to examples API
        if request.method != 'GET':
            return self.get_response(request)
        
        # Check if this is an examples API call
        match = self.examples_pattern.match(request.path)
        if not match:
            return self.get_response(request)
        
        # Don't filter if not authenticated
        if not request.user.is_authenticated:
            log('[Monlam Middleware] User not authenticated, skipping filter')
            return self.get_response(request)
        
        # Superusers see everything
        if request.user.is_superuser:
            log('[Monlam Middleware] Superuser, showing all')
            return self.get_response(request)
        
        project_id = match.group(1)
        
        try:
            # Check user's role
            if self._is_privileged_user(request.user, project_id):
                log(f'[Monlam Middleware] User {request.user.username} is privileged, showing all')
                return self.get_response(request)
            
            log(f'[Monlam Middleware] 🔍 User {request.user.username} is annotator')
            
            # Parse query params
            query_string = request.META.get('QUERY_STRING', '')
            limit_match = re.search(r'limit=(\d+)', query_string)
            offset_match = re.search(r'offset=(\d+)', query_string)
            
            limit = int(limit_match.group(1)) if limit_match else 10
            offset = int(offset_match.group(1)) if offset_match else 0
            
            log(f'[Monlam Middleware] Requested: limit={limit}, offset={offset}')
            
            # For single-item requests (annotation page), we need special handling
            # to return the Nth VISIBLE example, not the Nth overall example
            if limit == 1:
                return self._handle_single_item_request(request, project_id, offset)
            
            # For list requests, filter the response
            response = self.get_response(request)
            return self._filter_response(response, request.user, project_id)
            
        except Exception as e:
            log(f'[Monlam Middleware] Error: {e}')
            import traceback
            traceback.print_exc()
            # On error, return original response (fail open for safety)
            return self.get_response(request)
    
    def _handle_single_item_request(self, request, project_id, offset):
        """
        Handle limit=1 requests (annotation page).
        Returns the Nth VISIBLE example, not the Nth overall example.
        """
        log(f'[Monlam Middleware] 🎯 Single-item request: finding visible example at index {offset}')
        
        try:
            from examples.models import Example, ExampleState
            from django.http import JsonResponse
            
            # Get all examples for this project, ordered by ID
            all_examples = list(Example.objects.filter(project_id=project_id).order_by('id'))
            
            # Get confirmation states
            confirmed_states = ExampleState.objects.filter(
                example__project_id=project_id
            ).select_related('confirmed_by')
            confirmed_map = {state.example_id: state.confirmed_by for state in confirmed_states}
            
            # Get locking data
            from assignment.simple_tracking import AnnotationTracking
            tracking_qs = AnnotationTracking.objects.filter(project_id=project_id).select_related('locked_by')
            tracking_map = {t.example_id: t for t in tracking_qs}
            
            # Build list of VISIBLE examples
            visible_examples = []
            for example in all_examples:
                confirmed_by = confirmed_map.get(example.id)
                tracking = tracking_map.get(example.id)
                
                if self._should_show_example(example.id, confirmed_by, tracking, request.user):
                    visible_examples.append(example)
            
            log(f'[Monlam Middleware] Total: {len(all_examples)}, Visible: {len(visible_examples)}')
            
            # Get the example at the requested offset in the VISIBLE list
            if offset >= len(visible_examples):
                log(f'[Monlam Middleware] Offset {offset} beyond visible count {len(visible_examples)}')
                # Return empty result
                return JsonResponse({
                    'count': len(visible_examples),
                    'next': None,
                    'previous': None,
                    'results': []
                })
            
            example = visible_examples[offset]
            log(f'[Monlam Middleware] ✅ Returning visible example at index {offset}: ID={example.id}')
            
            # Serialize the example
            example_data = {
                'id': example.id,
                'uuid': str(example.uuid) if hasattr(example, 'uuid') else None,
                'text': example.text if hasattr(example, 'text') else '',
                'meta': example.meta if hasattr(example, 'meta') else {},
                'filename': example.filename if hasattr(example, 'filename') else '',
                'upload_name': example.upload_name if hasattr(example, 'upload_name') else '',
                'is_confirmed': example.id in confirmed_map,
                'annotation_approver': None,
            }
            
            return JsonResponse({
                'count': len(visible_examples),
                'next': f'/v1/projects/{project_id}/examples?limit=1&offset={offset+1}' if offset + 1 < len(visible_examples) else None,
                'previous': f'/v1/projects/{project_id}/examples?limit=1&offset={offset-1}' if offset > 0 else None,
                'results': [example_data]
            })
            
        except Exception as e:
            log(f'[Monlam Middleware] Single-item error: {e}')
            import traceback
            traceback.print_exc()
            # Fallback to original response
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

