"""
Integrate Assignment URLs into Doccano's main urls.py

This script modifies Doccano's urls.py to register the assignment app endpoints.
It should be run during Docker build.
"""

import sys

URLS_FILE = '/doccano/backend/config/urls.py'

# The URL pattern to add
ASSIGNMENT_URL_PATTERN = """
    # Monlam: Assignment and Completion Tracking APIs
    path('v1/projects/<int:project_id>/assignments/', include('assignment.urls')),
"""

def integrate_urls():
    """Add assignment URLs to Doccano's main urls.py"""
    try:
        with open(URLS_FILE, 'r') as f:
            content = f.read()
        
        # Check if already added
        if 'assignment.urls' in content:
            print("✅ Assignment URLs already integrated")
            return True
        
        # Find the urlpatterns list
        if 'urlpatterns = [' not in content:
            print("❌ Could not find urlpatterns in urls.py")
            return False
        
        # Add the assignment URL pattern before the closing bracket
        # Find the last path() entry and add after it
        lines = content.split('\n')
        new_lines = []
        added = False
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            
            # Look for the last path() entry in urlpatterns
            if not added and 'path(' in line and 'urlpatterns' not in line:
                # Check if next non-empty line is closing bracket
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                
                if j < len(lines) and ']' in lines[j]:
                    # This is the last entry, add our URL before the closing bracket
                    new_lines.append(ASSIGNMENT_URL_PATTERN)
                    added = True
        
        if not added:
            print("❌ Could not find where to insert assignment URLs")
            return False
        
        # Write back
        with open(URLS_FILE, 'w') as f:
            f.write('\n'.join(new_lines))
        
        print("✅ Successfully integrated assignment URLs into urls.py")
        return True
        
    except Exception as e:
        print(f"❌ Error integrating URLs: {e}")
        return False

if __name__ == '__main__':
    success = integrate_urls()
    sys.exit(0 if success else 1)

