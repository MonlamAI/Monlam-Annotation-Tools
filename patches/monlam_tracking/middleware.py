"""
Monlam Visibility Middleware

A SAFE approach to filter examples for annotators.
This runs at request/response time, NOT during app initialization.

How it works:
1. Intercepts API responses to /v1/projects/{id}/examples
2. Filters results based on user role and tracking status
3. Does NOT modify views or querysets directly
"""

import json
import re
from datetime import timedelta
from django.utils import timezone


class VisibilityMiddleware:
    """
    Middleware to filter example visibility for annotators.
    
    - Admins/Managers/Approvers: See all examples
    - Annotators: See only unannotated + own rejected + own locked
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Regex to match examples API endpoint
        self.examples_pattern = re.compile(r'^/v1/projects/(\d+)/examples/?$')
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Only process GET requests to examples API
        if request.method != 'GET':
            return response
        
        # Check if this is an examples API call
        match = self.examples_pattern.match(request.path)
        if not match:
            return response
        
        print(f'[Monlam Middleware] 🔍 Processing {request.path} for user {request.user}')
        
        # Don't filter if not authenticated
        if not request.user.is_authenticated:
            print('[Monlam Middleware] User not authenticated, skipping filter')
            return response
        
        # Superusers see everything
        if request.user.is_superuser:
            print('[Monlam Middleware] Superuser, showing all')
            return response
        
        project_id = match.group(1)
        
        try:
            # Check user's role
            if self._is_privileged_user(request.user, project_id):
                print(f'[Monlam Middleware] User {request.user.username} is privileged, showing all')
                return response
            
            print(f'[Monlam Middleware] User {request.user.username} is annotator, filtering...')
            # Filter the response for annotators
            return self._filter_response(response, request.user, project_id)
            
        except Exception as e:
            print(f'[Monlam Middleware] Error: {e}')
            import traceback
            traceback.print_exc()
            # On error, return original response (fail open for safety)
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
            
            # Parse response
            data = json.loads(response.content)
            
            # Get results list
            results = data.get('results', [])
            if not results:
                return response
            
            # Get tracking data
            from assignment.simple_tracking import AnnotationTracking
            
            tracking_qs = AnnotationTracking.objects.filter(
                project_id=project_id
            ).select_related('annotated_by', 'locked_by')
            
            tracking_map = {t.example_id: t for t in tracking_qs}
            
            # Filter results
            filtered_results = []
            for example in results:
                example_id = example.get('id')
                if example_id is None:
                    continue
                
                tracking = tracking_map.get(example_id)
                
                if self._should_show_example(tracking, user):
                    filtered_results.append(example)
            
            # Update response
            data['results'] = filtered_results
            data['count'] = len(filtered_results)
            
            # Create new response
            from django.http import JsonResponse
            new_response = JsonResponse(data)
            
            # Copy headers
            for header, value in response.items():
                if header.lower() not in ['content-length', 'content-type']:
                    new_response[header] = value
            
            print(f'[Monlam Middleware] Filtered: {len(results)} → {len(filtered_results)} examples for {user.username}')
            
            return new_response
            
        except Exception as e:
            print(f'[Monlam Middleware] Filter error: {e}')
            return response
    
    def _should_show_example(self, tracking, user):
        """Determine if an example should be visible to this user."""
        
        # No tracking = unannotated = show
        if not tracking:
            print(f'[Visibility] Example has no tracking → SHOW')
            return True
        
        example_id = tracking.example_id
        status = tracking.status
        annotated_by = tracking.annotated_by
        
        print(f'[Visibility] Example {example_id}: status={status}, annotated_by={annotated_by}, user={user}')
        
        # Check locking first
        if tracking.locked_by:
            if tracking.locked_by == user:
                print(f'[Visibility] Example {example_id}: Locked by me → SHOW')
                return True
            else:
                if tracking.locked_at:
                    lock_expiry = tracking.locked_at + timedelta(minutes=30)
                    if timezone.now() < lock_expiry:
                        print(f'[Visibility] Example {example_id}: Locked by {tracking.locked_by} → HIDE')
                        return False
        
        # Pending = show
        if status == 'pending':
            print(f'[Visibility] Example {example_id}: Pending → SHOW')
            return True
        
        # Rejected and annotated by current user = show (needs to fix)
        if status == 'rejected' and annotated_by == user:
            print(f'[Visibility] Example {example_id}: Rejected by me → SHOW')
            return True
        
        # Annotated by someone else = hide
        if annotated_by and annotated_by != user:
            print(f'[Visibility] Example {example_id}: Annotated by {annotated_by}, not me → HIDE')
            return False
        
        # Annotated by current user and submitted/approved = hide
        if annotated_by == user and status in ['submitted', 'approved']:
            print(f'[Visibility] Example {example_id}: Annotated by me, {status} → HIDE')
            return False
        
        # Default: show
        print(f'[Visibility] Example {example_id}: Default → SHOW')
        return True

