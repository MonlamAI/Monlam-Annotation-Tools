#!/usr/bin/env python3
"""
Patch Doccano URLs to add assignment endpoints.

This script modifies the examples/urls.py to include assignment routes.
Run during container startup.
"""

import os
import sys

# Path to the urls.py file
URLS_FILE = '/doccano/backend/examples/urls.py'
BACKUP_FILE = '/doccano/backend/examples/urls.py.backup'

# Lines to add for import
IMPORT_LINES = '''
# Assignment system imports
from .views_assignment import (
    AutoAssignView,
    BulkAssignmentView,
    AssignmentStatsView,
    ReviewQueueView,
    ReviewActionView,
    SubmitForReviewView,
)
'''

# URL patterns to add
URL_PATTERNS = '''
    # Assignment API endpoints
    path("projects/<int:project_id>/assignment/bulk/", BulkAssignmentView.as_view(), name="bulk-assignment"),
    path("projects/<int:project_id>/assignment/auto/", AutoAssignView.as_view(), name="auto-assignment"),
    path("projects/<int:project_id>/assignment/stats/", AssignmentStatsView.as_view(), name="assignment-stats"),
    path("projects/<int:project_id>/review/queue/", ReviewQueueView.as_view(), name="review-queue"),
    path("projects/<int:project_id>/review/<int:example_id>/", ReviewActionView.as_view(), name="review-action"),
    path("projects/<int:project_id>/examples/<int:example_id>/submit/", SubmitForReviewView.as_view(), name="submit-for-review"),
'''

def patch_urls():
    """Patch the urls.py file to include assignment routes."""
    
    if not os.path.exists(URLS_FILE):
        print(f"Error: {URLS_FILE} not found")
        sys.exit(1)
    
    # Read current content
    with open(URLS_FILE, 'r') as f:
        content = f.read()
    
    # Check if already patched
    if 'BulkAssignmentView' in content:
        print("URLs already patched, skipping...")
        return
    
    # Backup original
    if not os.path.exists(BACKUP_FILE):
        with open(BACKUP_FILE, 'w') as f:
            f.write(content)
        print(f"Backup created: {BACKUP_FILE}")
    
    # Add imports after existing imports
    lines = content.split('\n')
    new_lines = []
    imports_added = False
    patterns_added = False
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        # Add imports after the last 'from' or 'import' line in the import section
        if not imports_added and line.startswith('from ') and 'views' in line:
            new_lines.append(IMPORT_LINES)
            imports_added = True
        
        # Add URL patterns before the closing bracket of urlpatterns
        if not patterns_added and 'urlpatterns' in line and '=' in line:
            # Find the end of urlpatterns list
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == ']':
                    # Insert before the closing bracket
                    lines[j] = URL_PATTERNS + '\n]'
                    patterns_added = True
                    break
    
    # If patterns weren't added inline, append to urlpatterns
    if not patterns_added:
        new_lines.append('\n# Assignment URL patterns')
        new_lines.append('urlpatterns += [')
        new_lines.append(URL_PATTERNS)
        new_lines.append(']')
    
    # Write patched content
    new_content = '\n'.join(new_lines)
    
    # Simpler approach: just append the patterns
    if 'BulkAssignmentView' not in new_content:
        append_content = f'''

# ============================================
# ASSIGNMENT SYSTEM ROUTES (Auto-added)
# ============================================

{IMPORT_LINES}

urlpatterns += [
{URL_PATTERNS}
]
'''
        new_content = content + append_content
    
    with open(URLS_FILE, 'w') as f:
        f.write(new_content)
    
    print("URLs patched successfully!")


if __name__ == '__main__':
    patch_urls()

