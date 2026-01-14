"""
Monlam Tracking App Configuration

Proper Django AppConfig that initializes visibility filtering
after all apps are loaded.
"""

from django.apps import AppConfig


class MonlamTrackingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monlam_tracking'
    verbose_name = 'Monlam Annotation Tracking'
    
    def ready(self):
        """
        Initialize tracking features after Django is fully loaded.
        """
        print('[Monlam Tracking] App initializing...')
        
        # Apply visibility filtering to Doccano's example viewsets
        # This filters locked examples at the queryset level (most robust)
        try:
            # Import from the correct module path
            from examples.views.example import ExampleList, ExampleDetail
            
            # Try to import the patch - it should be in the backend directory
            try:
                from backend.examples_views_patch import ExampleVisibilityMixin
            except ImportError:
                # If that fails, try direct import (file might be in examples/)
                try:
                    from examples.examples_views_patch import ExampleVisibilityMixin
                except ImportError:
                    print('[Monlam Tracking] ⚠️ Could not find examples_views_patch - using middleware only')
                    raise
            
            # Create new classes that inherit from both the mixin and the original
            # The mixin must come FIRST so its get_queryset is called
            class PatchedExampleList(ExampleVisibilityMixin, ExampleList):
                """ExampleList with visibility filtering including lock filtering"""
                pass
            
            class PatchedExampleDetail(ExampleVisibilityMixin, ExampleDetail):
                """ExampleDetail with visibility filtering including lock filtering"""
                pass
            
            # Replace the original classes in the module
            import examples.views.example as example_views_module
            example_views_module.ExampleList = PatchedExampleList
            example_views_module.ExampleDetail = PatchedExampleDetail
            
            # Also update the views __init__.py if it exports these
            try:
                from examples import views as examples_views
                if hasattr(examples_views, 'ExampleList'):
                    examples_views.ExampleList = PatchedExampleList
                if hasattr(examples_views, 'ExampleDetail'):
                    examples_views.ExampleDetail = PatchedExampleDetail
            except:
                pass  # Not critical if __init__ doesn't export them
            
            print('[Monlam Tracking] ✅ Applied queryset-level filtering (with lock filtering) to example viewsets')
            print('[Monlam Tracking] ✅ ExampleList patched successfully')
            print('[Monlam Tracking] ✅ ExampleDetail patched successfully')
        except Exception as e:
            print(f'[Monlam Tracking] ⚠️ Could not apply queryset filtering: {e}')
            print('[Monlam Tracking] ⚠️ Falling back to middleware-only filtering')
            import traceback
            traceback.print_exc()
        
        # Set up auto-tracking signals
        try:
            from .signals import setup_annotation_signals
            setup_annotation_signals()
            print('[Monlam Tracking] ✅ Auto-tracking signals connected')
        except Exception as e:
            print(f'[Monlam Tracking] ⚠️ Auto-tracking not set up: {e}')

