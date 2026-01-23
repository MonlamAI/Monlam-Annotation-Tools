#!/usr/bin/env python3
"""
Patch script to filter examples for reviewers.

When a reviewer navigates through examples, they should only see:
- Examples that are submitted (status='submitted') and not yet reviewed by them
- Rejected examples (so they can be reviewed again)
- This ensures skipped examples are accessible when navigating "next"
"""

import re
import sys

def patch_example_list_get_queryset(file_path):
    """Patch the get_queryset method in ExampleList class to filter for reviewers."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if patch already applied
        if 'MONLAM: Filter examples for reviewers' in content:
            print(f"✅ Patch already applied to {file_path}")
            return True
        
        # Pattern to match the get_queryset method
        # Match from "def get_queryset(self):" to the return statement
        pattern = r'(    def get_queryset\(self\):.*?)(        return queryset)'
        
        def replace_get_queryset(match):
            original_method = match.group(1)
            return_statement = match.group(2)
            
            # New implementation with reviewer filtering
            new_method = '''    def get_queryset(self):
        from django.db.models import Q
        queryset = self.model.objects.filter(project=self.project)
        
        # MONLAM: Filter examples for reviewers
        # Check if user is a reviewer/approver
        user = self.request.user
        project = self.project
        
        # Superusers are always reviewers (can see all examples)
        is_reviewer = user.is_superuser
        
        if not is_reviewer:
            try:
                from assignment.permissions import get_user_role
                role_name, is_privileged = get_user_role(user, project.id)
                
                # Check if user is a reviewer/approver (but not annotator)
                if is_privileged or (role_name and any(r in role_name for r in ['approver', 'manager', 'admin'])):
                    is_reviewer = True
            except Exception as e:
                print(f'[Monlam ExampleList] Error checking user role: {e}')
                # If we can't determine role, use original behavior
                is_reviewer = False
        
        # For annotators: Show only assigned examples, excluding skipped and submitted
        if not is_reviewer:
            try:
                from assignment.models_separate import Assignment
                from assignment.simple_tracking import SkippedExample, AnnotationTracking
                
                # Get example IDs assigned to this annotator (or unassigned)
                assigned_example_ids = Assignment.objects.filter(
                    project=project,
                    is_active=True
                ).filter(
                    Q(assigned_to=user) | Q(assigned_to__isnull=True)
                ).values_list('example_id', flat=True)
                
                # Filter queryset to only show assigned (or unassigned) examples
                if assigned_example_ids:
                    queryset = queryset.filter(id__in=assigned_example_ids)
                    print(f'[Monlam ExampleList] Annotator {user.username}: Showing {len(assigned_example_ids)} assigned examples')
                else:
                    # No assignments = no examples to show
                    queryset = queryset.none()
                    print(f'[Monlam ExampleList] Annotator {user.username}: No assigned examples')
                
                # Exclude permanently skipped examples
                skipped_example_ids = SkippedExample.objects.filter(
                    project=project,
                    skipped_by=user
                ).values_list('example_id', flat=True)
                
                if skipped_example_ids:
                    queryset = queryset.exclude(id__in=skipped_example_ids)
                    print(f'[Monlam ExampleList] Annotator {user.username}: Excluded {len(skipped_example_ids)} skipped examples')
                
                # Exclude submitted examples
                submitted_example_ids = AnnotationTracking.objects.filter(
                    project=project,
                    status='submitted'
                ).values_list('example_id', flat=True)
                
                if submitted_example_ids:
                    queryset = queryset.exclude(id__in=submitted_example_ids)
                    print(f'[Monlam ExampleList] Annotator {user.username}: Excluded {len(submitted_example_ids)} submitted examples')
                    
            except Exception as e:
                print(f'[Monlam ExampleList] Error filtering examples for annotator: {e}')
                import traceback
                traceback.print_exc()
                # If filtering fails, return empty queryset (fail secure for annotators)
                queryset = queryset.none()
        
        # For reviewers: Show ALL examples by default (dataset table access)
        # Only filter when explicitly in annotation workflow (no all_examples param AND specific conditions)
        # When accessing dataset table via API, show ALL examples (for project admins to see complete status)
        # When clicking "Start Annotation" button, show only submitted examples
        if is_reviewer:
            # Check if all_examples parameter is present (from dataset table or API call)
            all_examples_param = self.request.GET.get('all_examples', '').lower() == 'true'
            
            # Check if this is an annotation workflow request (has page parameter, indicating navigation to specific example)
            # Dataset table API calls typically don't have page parameter
            is_annotation_workflow = 'page' in self.request.GET
            
            # Show ALL examples if:
            # 1. all_examples=true is explicitly set, OR
            # 2. This is NOT an annotation workflow (dataset table access)
            if all_examples_param or not is_annotation_workflow:
                # User accessing from dataset table or API - show ALL examples
                # This allows project admins to see complete dataset and navigate to any example
                print(f'[Monlam ExampleList] Reviewer {user.username}: Showing ALL examples (dataset table access)')
            else:
                # User clicked "Start Annotation" and navigating to annotation - show only submitted examples
                try:
                    from assignment.simple_tracking import AnnotationTracking
                    
                    # Get examples that have been reviewed by this user
                    reviewed_example_ids = AnnotationTracking.objects.filter(
                        project=project,
                        reviewed_by=user
                    ).exclude(
                        status='rejected'  # Don't exclude rejected examples (they need re-review)
                    ).values_list('example_id', flat=True)
                    
                    # Get submitted example IDs that haven't been reviewed by this user
                    submitted_tracking = AnnotationTracking.objects.filter(
                        project=project,
                        status='submitted'
                    ).exclude(
                        example_id__in=reviewed_example_ids
                    ).values_list('example_id', flat=True)
                    
                    # Get rejected example IDs (always show these for re-review)
                    rejected_example_ids = AnnotationTracking.objects.filter(
                        project=project,
                        status='rejected'
                    ).values_list('example_id', flat=True)
                    
                    # Combine: submitted (not reviewed by this user) + rejected
                    example_ids_to_show = list(set(list(submitted_tracking) + list(rejected_example_ids)))
                    
                    # Filter queryset to only show these examples
                    if example_ids_to_show:
                        queryset = queryset.filter(id__in=example_ids_to_show)
                    else:
                        # If no examples need review, return empty queryset
                        queryset = queryset.none()
                    
                    print(f'[Monlam ExampleList] Reviewer {user.username}: Showing {len(example_ids_to_show)} examples needing review (from Start Annotation)')
                    
                except Exception as e:
                    print(f'[Monlam ExampleList] Error filtering for reviewer: {e}')
                    # If filtering fails, continue with original queryset
        
        # Original ordering logic
        if self.project.random_order:
            # Todo: fix the algorithm.
            import random
            random.seed(self.request.user.id)
            value = random.randrange(2, 20)
            from django.db.models import F
            queryset = queryset.annotate(sort_id=F("id") % value).order_by("sort_id", "id")
        else:
            queryset = queryset.order_by("created_at")
        
        return queryset'''
            
            return new_method
        
        # Try to replace the method
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, replace_get_queryset, content, flags=re.DOTALL)
            
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"✅ Successfully patched {file_path}")
            return True
        else:
            # Try line-by-line approach
            lines = content.split('\n')
            new_lines = []
            i = 0
            in_get_queryset = False
            skip_until_next_method = False
            
            while i < len(lines):
                line = lines[i]
                
                # Detect start of get_queryset method
                if 'def get_queryset(self):' in line and not in_get_queryset:
                    in_get_queryset = True
                    skip_until_next_method = True
                    
                    # Add the new method implementation
                    new_lines.append('    def get_queryset(self):')
                    new_lines.append('        from django.db.models import Q')
                    new_lines.append('        queryset = self.model.objects.filter(project=self.project)')
                    new_lines.append('')
                    new_lines.append('        # MONLAM: Filter examples for reviewers')
                    new_lines.append('        # Check if user is a reviewer/approver')
                    new_lines.append('        user = self.request.user')
                    new_lines.append('        project = self.project')
                    new_lines.append('')
                    new_lines.append('        # Superusers are always reviewers (can see all examples)')
                    new_lines.append('        is_reviewer = user.is_superuser')
                    new_lines.append('')
                    new_lines.append('        if not is_reviewer:')
                    new_lines.append('            try:')
                    new_lines.append('                from assignment.permissions import get_user_role')
                    new_lines.append('                role_name, is_privileged = get_user_role(user, project.id)')
                    new_lines.append('')
                    new_lines.append('                # Check if user is a reviewer/approver (but not annotator)')
                    new_lines.append("                if is_privileged or (role_name and any(r in role_name for r in ['approver', 'manager', 'admin'])):")
                    new_lines.append('                    is_reviewer = True')
                    new_lines.append('            except Exception as e:')
                    new_lines.append("                print(f'[Monlam ExampleList] Error checking user role: {e}')")
                    new_lines.append('                # If we can\'t determine role, use original behavior')
                    new_lines.append('                is_reviewer = False')
                    new_lines.append('')
                    new_lines.append('        # For annotators: Show only assigned examples, excluding skipped and submitted')
                    new_lines.append('        if not is_reviewer:')
                    new_lines.append('            try:')
                    new_lines.append('                from assignment.models_separate import Assignment')
                    new_lines.append('                from assignment.simple_tracking import SkippedExample, AnnotationTracking')
                    new_lines.append('')
                    new_lines.append('                # Get example IDs assigned to this annotator (or unassigned)')
                    new_lines.append('                assigned_example_ids = Assignment.objects.filter(')
                    new_lines.append('                    project=project,')
                    new_lines.append('                    is_active=True')
                    new_lines.append('                ).filter(')
                    new_lines.append('                    Q(assigned_to=user) | Q(assigned_to__isnull=True)')
                    new_lines.append('                ).values_list(\'example_id\', flat=True)')
                    new_lines.append('')
                    new_lines.append('                # Filter queryset to only show assigned (or unassigned) examples')
                    new_lines.append('                if assigned_example_ids:')
                    new_lines.append('                    queryset = queryset.filter(id__in=assigned_example_ids)')
                    new_lines.append(f"                    print(f'[Monlam ExampleList] Annotator {{user.username}}: Showing {{len(assigned_example_ids)}} assigned examples')")
                    new_lines.append('                else:')
                    new_lines.append('                    # No assignments = no examples to show')
                    new_lines.append('                    queryset = queryset.none()')
                    new_lines.append(f"                    print(f'[Monlam ExampleList] Annotator {{user.username}}: No assigned examples')")
                    new_lines.append('')
                    new_lines.append('                # Exclude permanently skipped examples')
                    new_lines.append('                skipped_example_ids = SkippedExample.objects.filter(')
                    new_lines.append('                    project=project,')
                    new_lines.append('                    skipped_by=user')
                    new_lines.append('                ).values_list(\'example_id\', flat=True)')
                    new_lines.append('')
                    new_lines.append('                if skipped_example_ids:')
                    new_lines.append('                    queryset = queryset.exclude(id__in=skipped_example_ids)')
                    new_lines.append(f"                    print(f'[Monlam ExampleList] Annotator {{user.username}}: Excluded {{len(skipped_example_ids)}} skipped examples')")
                    new_lines.append('')
                    new_lines.append('                # Exclude submitted examples')
                    new_lines.append('                submitted_example_ids = AnnotationTracking.objects.filter(')
                    new_lines.append('                    project=project,')
                    new_lines.append("                    status='submitted'")
                    new_lines.append('                ).values_list(\'example_id\', flat=True)')
                    new_lines.append('')
                    new_lines.append('                if submitted_example_ids:')
                    new_lines.append('                    queryset = queryset.exclude(id__in=submitted_example_ids)')
                    new_lines.append(f"                    print(f'[Monlam ExampleList] Annotator {{user.username}}: Excluded {{len(submitted_example_ids)}} submitted examples')")
                    new_lines.append('                    ')
                    new_lines.append('            except Exception as e:')
                    new_lines.append("                print(f'[Monlam ExampleList] Error filtering examples for annotator: {e}')")
                    new_lines.append('                import traceback')
                    new_lines.append('                traceback.print_exc()')
                    new_lines.append('                # If filtering fails, return empty queryset (fail secure for annotators)')
                    new_lines.append('                queryset = queryset.none()')
                    new_lines.append('')
                    new_lines.append('        # For reviewers: Show ALL examples by default (dataset table access)')
                    new_lines.append('        # Only filter when explicitly in annotation workflow (has page parameter)')
                    new_lines.append('        # When accessing dataset table via API, show ALL examples (for project admins to see complete status)')
                    new_lines.append('        # When clicking "Start Annotation" button, show only submitted examples')
                    new_lines.append('        if is_reviewer:')
                    new_lines.append('            # Check if all_examples parameter is present (from dataset table or API call)')
                    new_lines.append("            all_examples_param = self.request.GET.get('all_examples', '').lower() == 'true'")
                    new_lines.append('')
                    new_lines.append('            # Check if this is an annotation workflow request (has page parameter)')
                    new_lines.append('            # Dataset table API calls typically don\'t have page parameter')
                    new_lines.append("            is_annotation_workflow = 'page' in self.request.GET")
                    new_lines.append('')
                    new_lines.append('            # Show ALL examples if:')
                    new_lines.append('            # 1. all_examples=true is explicitly set, OR')
                    new_lines.append('            # 2. This is NOT an annotation workflow (dataset table access)')
                    new_lines.append('            if all_examples_param or not is_annotation_workflow:')
                    new_lines.append('                # User accessing from dataset table or API - show ALL examples')
                    new_lines.append('                # This allows project admins to see complete dataset and navigate to any example')
                    new_lines.append(f"                print(f'[Monlam ExampleList] Reviewer {{user.username}}: Showing ALL examples (dataset table access)')")
                    new_lines.append('            else:')
                    new_lines.append('                # User clicked "Start Annotation" and navigating to annotation - show only submitted examples')
                    new_lines.append('                try:')
                    new_lines.append('                    from assignment.simple_tracking import AnnotationTracking')
                    new_lines.append('')
                    new_lines.append('                    # Get examples that have been reviewed by this user')
                    new_lines.append('                    reviewed_example_ids = AnnotationTracking.objects.filter(')
                    new_lines.append('                        project=project,')
                    new_lines.append('                        reviewed_by=user')
                    new_lines.append('                    ).exclude(')
                    new_lines.append("                        status='rejected'  # Don't exclude rejected examples (they need re-review)")
                    new_lines.append('                    ).values_list(\'example_id\', flat=True)')
                    new_lines.append('')
                    new_lines.append('                    # Get submitted example IDs that haven\'t been reviewed by this user')
                    new_lines.append('                    submitted_tracking = AnnotationTracking.objects.filter(')
                    new_lines.append('                        project=project,')
                    new_lines.append("                        status='submitted'")
                    new_lines.append('                    ).exclude(')
                    new_lines.append('                        example_id__in=reviewed_example_ids')
                    new_lines.append('                    ).values_list(\'example_id\', flat=True)')
                    new_lines.append('')
                    new_lines.append('                    # Get rejected example IDs (always show these for re-review)')
                    new_lines.append('                    rejected_example_ids = AnnotationTracking.objects.filter(')
                    new_lines.append('                        project=project,')
                    new_lines.append("                        status='rejected'")
                    new_lines.append('                    ).values_list(\'example_id\', flat=True)')
                    new_lines.append('')
                    new_lines.append('                    # Combine: submitted (not reviewed by this user) + rejected')
                    new_lines.append('                    example_ids_to_show = list(set(list(submitted_tracking) + list(rejected_example_ids)))')
                    new_lines.append('')
                    new_lines.append('                    # Filter queryset to only show these examples')
                    new_lines.append('                    if example_ids_to_show:')
                    new_lines.append('                        queryset = queryset.filter(id__in=example_ids_to_show)')
                    new_lines.append('                    else:')
                    new_lines.append('                        # If no examples need review, return empty queryset')
                    new_lines.append('                        queryset = queryset.none()')
                    new_lines.append('')
                    new_lines.append("                    print(f'[Monlam ExampleList] Reviewer {user.username}: Showing {len(example_ids_to_show)} examples needing review (from Start Annotation)')")
                    new_lines.append('')
                    new_lines.append('                except Exception as e:')
                    new_lines.append("                    print(f'[Monlam ExampleList] Error filtering for reviewer: {e}')")
                    new_lines.append('                    # If filtering fails, continue with original queryset')
                    new_lines.append('')
                    new_lines.append('        # Original ordering logic')
                    new_lines.append('        if self.project.random_order:')
                    new_lines.append('            # Todo: fix the algorithm.')
                    new_lines.append('            import random')
                    new_lines.append('            random.seed(self.request.user.id)')
                    new_lines.append('            value = random.randrange(2, 20)')
                    new_lines.append('            from django.db.models import F')
                    new_lines.append('            queryset = queryset.annotate(sort_id=F("id") % value).order_by("sort_id", "id")')
                    new_lines.append('        else:')
                    new_lines.append('            queryset = queryset.order_by("created_at")')
                    new_lines.append('')
                    new_lines.append('        return queryset')
                    
                    # Skip old method lines until we find the next method or end of class
                    i += 1
                    while i < len(lines):
                        next_line = lines[i]
                        # Check if we've reached the next method (non-indented def) or end of class
                        stripped = next_line.lstrip()
                        if stripped.startswith('def ') and not stripped.startswith('def get_queryset'):
                            break
                        if stripped.startswith('class '):
                            break
                        # Also stop if we hit a property decorator or other class-level item
                        if stripped and not next_line.startswith(' ') and not next_line.startswith('\t'):
                            break
                        i += 1
                    continue
                
                # Normal line, keep it
                new_lines.append(line)
                i += 1
            
            # Write patched content
            with open(file_path, 'w') as f:
                f.write('\n'.join(new_lines))
            print(f"✅ Successfully patched {file_path}")
            return True
            
    except Exception as e:
        print(f"❌ Error patching {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    file_path = '/doccano/backend/examples/views/example.py'
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    
    success = patch_example_list_get_queryset(file_path)
    sys.exit(0 if success else 1)

