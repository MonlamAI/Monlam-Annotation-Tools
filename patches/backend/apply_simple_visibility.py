"""
Apply Simple Visibility Filtering at Django Startup

This script is imported in settings.py to apply the visibility patch.
"""

import sys


def apply_at_startup():
    """
    Apply visibility filtering when Django starts.
    Only runs after all apps are loaded.
    """
    # Check if we're in a management command that doesn't need this
    if 'makemigrations' in sys.argv or 'migrate' in sys.argv:
        return
    
    # Apply the patch
    try:
        from .simple_visibility_patch import apply_visibility_patch
        apply_visibility_patch()
    except Exception as e:
        print(f'[Monlam Visibility] Could not apply at startup: {e}')


# Auto-apply when imported
# This will be called when Django loads settings
try:
    from django.apps import apps
    if apps.ready:
        apply_at_startup()
except:
    pass  # Apps not ready yet, will be called later

