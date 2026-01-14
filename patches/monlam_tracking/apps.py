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
            from examples import views as examples_views
            
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
            
            print('[Monlam Tracking] ✅ Applied queryset-level filtering (with lock filtering) to example viewsets')
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

