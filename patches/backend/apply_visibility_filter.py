"""
Runtime Monkey-Patch to Apply Visibility Filtering

This script applies the ExampleVisibilityMixin to Doccano's example viewsets
at runtime, avoiding fragile sed commands in Dockerfile.

Add this to Django's startup by importing it in __init__.py or settings.py
"""

def apply_visibility_filtering():
    """
    Apply visibility filtering to Doccano's example viewsets
    This filters out locked examples at the queryset level (more robust than middleware)
    """
    try:
        # Import the viewsets we want to patch
        from examples import views as examples_views
        from backend.examples_views_patch import ExampleVisibilityMixin
        
        # Get the original classes
        ExampleList = examples_views.ExampleList
        ExampleDetail = examples_views.ExampleDetail
        
        # Create new classes that inherit from both the mixin and the original
        # The mixin must come FIRST so its get_queryset is called
        class PatchedExampleList(ExampleVisibilityMixin, ExampleList):
            """ExampleList with visibility filtering including lock filtering"""
            pass
        
        class PatchedExampleDetail(ExampleVisibilityMixin, ExampleDetail):
            """ExampleDetail with visibility filtering including lock filtering"""
            pass
        
        # Replace the original classes
        examples_views.ExampleList = PatchedExampleList
        examples_views.ExampleDetail = PatchedExampleDetail
        
        print("[Monlam] ✅ Applied visibility filtering (with lock filtering) to example viewsets")
        return True
        
    except Exception as e:
        print(f"[Monlam] ⚠️ Could not apply visibility filtering: {e}")
        import traceback
        traceback.print_exc()
        return False


# Apply on import
apply_visibility_filtering()

