#!/usr/bin/env python3
"""
Patch script to fix critical bug in Doccano's example delete endpoint.

This patches /doccano/backend/examples/views/example.py to prevent
accidental deletion of all examples when delete_ids is empty.
"""

import re
import sys

def patch_example_delete(file_path):
    """Patch the delete method in ExampleList class."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Pattern to match the delete method
        old_pattern = r'    def delete\(self, request, \*args, \*\*kwargs\):\s+queryset = self\.project\.examples\s+delete_ids = request\.data\["ids"\]\s+if delete_ids:\s+queryset\.filter\(pk__in=delete_ids\)\.delete\(\)\s+else:\s+queryset\.all\(\)\.delete\(\)\s+return Response\(status=status\.HTTP_204_NO_CONTENT\)'
        
        # New implementation
        new_code = '''    def delete(self, request, *args, **kwargs):
        queryset = self.project.examples
        delete_ids = request.data.get("ids", [])
        
        # CRITICAL FIX: Prevent accidental deletion of all examples
        # If no IDs provided or empty list, return error instead of deleting everything
        if not delete_ids:
            return Response(
                {"error": "No example IDs provided. Cannot delete examples without specifying IDs."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Only delete the specified examples
        deleted_count = queryset.filter(pk__in=delete_ids).delete()[0]
        return Response(
            {"message": f"Successfully deleted {deleted_count} example(s)", "deleted_count": deleted_count},
            status=status.HTTP_200_OK
        )'''
        
        # Try multiline pattern match
        pattern = r'(\s+)def delete\(self, request, \*args, \*\*kwargs\):.*?return Response\(status=status\.HTTP_204_NO_CONTENT\)'
        
        if re.search(pattern, content, re.DOTALL):
            # Replace the entire method
            content = re.sub(pattern, new_code, content, flags=re.DOTALL)
            
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"✅ Successfully patched {file_path}")
            return True
        else:
            # Try simpler approach - find the method and replace line by line
            lines = content.split('\n')
            new_lines = []
            i = 0
            in_delete_method = False
            indent_level = 0
            
            while i < len(lines):
                line = lines[i]
                
                # Detect start of delete method
                if 'def delete(self, request, *args, **kwargs):' in line and not in_delete_method:
                    in_delete_method = True
                    indent_level = len(line) - len(line.lstrip())
                    new_lines.append(line)
                    i += 1
                    continue
                
                # If we're in the delete method, skip old lines until we find the return statement
                if in_delete_method:
                    # Check if this is the return statement that ends the method
                    if 'return Response(status=status.HTTP_204_NO_CONTENT)' in line:
                        # Add the new implementation
                        new_lines.append('        queryset = self.project.examples')
                        new_lines.append('        delete_ids = request.data.get("ids", [])')
                        new_lines.append('')
                        new_lines.append('        # CRITICAL FIX: Prevent accidental deletion of all examples')
                        new_lines.append('        # If no IDs provided or empty list, return error instead of deleting everything')
                        new_lines.append('        if not delete_ids:')
                        new_lines.append('            return Response(')
                        new_lines.append('                {"error": "No example IDs provided. Cannot delete examples without specifying IDs."},')
                        new_lines.append('                status=status.HTTP_400_BAD_REQUEST')
                        new_lines.append('            )')
                        new_lines.append('')
                        new_lines.append('        # Only delete the specified examples')
                        new_lines.append('        deleted_count = queryset.filter(pk__in=delete_ids).delete()[0]')
                        new_lines.append('        return Response(')
                        new_lines.append('            {"message": f"Successfully deleted {deleted_count} example(s)", "deleted_count": deleted_count},')
                        new_lines.append('            status=status.HTTP_200_OK')
                        new_lines.append('        )')
                        in_delete_method = False
                        i += 1
                        continue
                    else:
                        # Skip old lines of the delete method
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
        return False

if __name__ == '__main__':
    file_path = '/doccano/backend/examples/views/example.py'
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    
    success = patch_example_delete(file_path)
    sys.exit(0 if success else 1)

