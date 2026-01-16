"""
Monlam Visibility Middleware

Filters examples API responses to hide locked examples from other annotators.
"""

import re
import sys
import json
from datetime import timedelta
from django.utils import timezone


def log(msg):
    """Force immediate output to stderr"""
    print(msg, file=sys.stderr, flush=True)


class VisibilityMiddleware:
    """
    Middleware that filters examples API responses to hide locked examples.
    
    For annotators:
    - Hides examples locked by other users
    - Shows examples locked by themselves
    - Shows unlocked examples
    
    For privileged users (admins, managers, approvers):
    - Shows all examples (no filtering)
    """
    
    def __init__(self, get_response):
        log('[Monlam MW] 🚀 VisibilityMiddleware initialized')
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Only filter examples API endpoints for authenticated users
        if not request.user.is_authenticated:
            return response
        
        # Check if this is an examples API request
        path = request.path
        if '/v1/projects/' in path and '/examples' in path and request.method == 'GET':
            # Extract project_id from path
            match = re.search(r'/v1/projects/(\d+)/', path)
            if match:
                project_id = int(match.group(1))
                
                # Skip filtering for privileged users
                if not self._is_privileged_user(request.user, project_id):
                    # Filter the response to hide locked examples
                    response = self._filter_response(response, request.user, project_id)
        
        return response
    
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
            
            # Parse response - handle both bytes and string content
            try:
                if hasattr(response, 'content'):
                    content = response.content
                    if isinstance(content, bytes):
                        content = content.decode('utf-8')
                    data = json.loads(content)
                else:
                    # Response might not have content attribute
                    return response
            except (json.JSONDecodeError, AttributeError) as e:
                log(f'[Monlam Middleware] Could not parse response: {e}')
                return response
            
            # Handle both list responses and paginated dict responses
            if isinstance(data, list):
                # Direct list response (e.g., from detail endpoint or non-paginated list)
                results = data
                is_paginated = False
            elif isinstance(data, dict):
                # Paginated response with 'results' key
                results = data.get('results', [])
                is_paginated = True
            else:
                # Unknown format, don't filter
                return response
            
            if not results:
                return response
            
            # Get CONFIRMATION data from Doccano's ExampleState
            from examples.models import ExampleState, Example
            
            # Get all examples in this project
            all_project_examples = Example.objects.filter(project_id=project_id).values_list('id', flat=True)
            all_example_ids = list(all_project_examples)
            
            # Get confirmed examples
            all_confirmed = set(
                ExampleState.objects.filter(example_id__in=all_example_ids)
                .exclude(confirmed_by=user)  # Exclude ones confirmed by current user
                .values_list('example_id', flat=True)
            )
            my_confirmed = set(
                ExampleState.objects.filter(example_id__in=all_example_ids, confirmed_by=user)
                .values_list('example_id', flat=True)
            )
            
            # Get locked examples (excluding ones locked by current user)
            from assignment.simple_tracking import AnnotationTracking
            locked_by_others = set()
            all_tracking = AnnotationTracking.objects.filter(
                project_id=project_id,
                example_id__in=all_example_ids
            ).select_related('locked_by')
            
            for tracking in all_tracking:
                if tracking.locked_by and tracking.locked_by != user:
                    if tracking.locked_at:
                        lock_expiry = tracking.locked_at + timedelta(minutes=5)
                        if timezone.now() < lock_expiry:
                            locked_by_others.add(tracking.example_id)
            
            # Total visible = all examples - confirmed by others - confirmed by me - locked by others
            total_visible = len(all_example_ids) - len(all_confirmed) - len(my_confirmed) - len(locked_by_others)
            
            log(f'[Monlam Middleware] Total: {len(all_example_ids)}, Confirmed by others: {len(all_confirmed)}, By me: {len(my_confirmed)}, Locked by others: {len(locked_by_others)}, Visible: {total_visible}')
            
            # Get current page's confirmed states
            example_ids = [ex.get('id') for ex in results if ex.get('id')]
            confirmed_states = ExampleState.objects.filter(
                example_id__in=example_ids
            ).select_related('confirmed_by')
            
            # Map: example_id -> confirmed_by user
            confirmed_map = {state.example_id: state.confirmed_by for state in confirmed_states}
            
            # Get tracking data for locking and review status (already imported above)
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
            
            # CRITICAL FIX: If filtering resulted in empty page but there are visible examples,
            # fetch the first visible example to prevent blank page (prevents "undefined" example ID)
            if not filtered_results and total_visible > 0 and is_paginated:
                log(f'[Monlam Middleware] ⚠️ Empty page after filtering but {total_visible} visible examples exist - fetching first visible example')
                try:
                    # Get first visible example using the same logic as filtering
                    from examples.models import Example
                    visible_example_ids = set(all_example_ids) - all_confirmed - my_confirmed - locked_by_others
                    if visible_example_ids:
                        # Get the first visible example with all its data
                        first_visible_id = list(visible_example_ids)[0]
                        first_example = Example.objects.filter(id=first_visible_id).select_related('project').first()
                        if first_example:
                            # Use Doccano's serializer if available, otherwise basic serialization
                            try:
                                from examples.serializers import ExampleSerializer
                                serializer = ExampleSerializer(first_example)
                                example_dict = serializer.data
                            except (ImportError, AttributeError):
                                # Fallback: basic serialization
                                example_dict = {
                                    'id': first_example.id,
                                    'text': getattr(first_example, 'text', ''),
                                    'meta': getattr(first_example, 'meta', {}),
                                    'annotation_approver': getattr(first_example, 'annotation_approver_id', None),
                                    'created_at': first_example.created_at.isoformat() if hasattr(first_example, 'created_at') and first_example.created_at else None,
                                    'updated_at': first_example.updated_at.isoformat() if hasattr(first_example, 'updated_at') and first_example.updated_at else None,
                                }
                            
                            filtered_results = [example_dict]
                            log(f'[Monlam Middleware] ✅ Returned first visible example (ID: {first_visible_id}) to prevent blank page')
                except Exception as e:
                    log(f'[Monlam Middleware] ⚠️ Error fetching first visible example: {e}')
                    import traceback
                    traceback.print_exc()
            
            # Update response based on format
            if is_paginated:
                # Paginated response - update results and count
                data['results'] = filtered_results
                data['count'] = total_visible  # Use calculated total, not just current page
                response_data = data
                safe_param = True  # Dict can use safe=True (default)
            else:
                # Direct list response - replace with filtered list
                response_data = filtered_results
                safe_param = False  # List requires safe=False
            
            # Create new response
            from django.http import JsonResponse
            new_response = JsonResponse(response_data, safe=safe_param)
            
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
        
        Priority:
        1. Locking check (most important - prevents conflicts)
        2. Confirmation status
        3. Rejection status (for re-annotation)
        """
        
        # Check locking first (from our tracking) - 5 minute expiry to match API
        if tracking and tracking.locked_by:
            if tracking.locked_by == user:
                # Locked by me - always show
                return True
            else:
                # Locked by someone else - check if expired
                if tracking.locked_at:
                    lock_expiry = tracking.locked_at + timedelta(minutes=5)
                    if timezone.now() < lock_expiry:
                        # Still locked by someone else - HIDE
                        log(f'[Visibility] Example {example_id}: Locked by {tracking.locked_by.username} → HIDE')
                        return False
                    else:
                        # Lock expired, clear it
                        log(f'[Visibility] Example {example_id}: Lock expired, clearing')
                        tracking.locked_by = None
                        tracking.locked_at = None
                        tracking.save(update_fields=['locked_by', 'locked_at'])
        
        # Not confirmed = available for annotation = SHOW
        if not confirmed_by:
            return True
        
        # Confirmed by current user = already done by me = HIDE
        if confirmed_by == user:
            return False
        
        # Confirmed by someone else = HIDE
        if confirmed_by != user:
            return False
        
        # Check if rejected (needs re-annotation)
        if tracking and tracking.status == 'rejected' and tracking.annotated_by == user:
            return True
        
        # Default: show
        return True

