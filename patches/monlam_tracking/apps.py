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
        This is the proper place for app initialization code.
        """
        print('[Monlam Tracking] App initializing...')
        
        # DIRECT PATCH: Patch Doccano's Example view for visibility filtering
        # This is more reliable than REST_FRAMEWORK filter backends
        try:
            from backend.example_view_patch import patch_example_view
            patch_example_view()
            print('[Monlam Tracking] ✅ Example view patched for visibility')
        except Exception as e:
            print(f'[Monlam Tracking] ⚠️ Example view patch failed: {e}')
            # Fallback: Try the filter backend approach
            try:
                from .filters import register_visibility_filter
                register_visibility_filter()
                print('[Monlam Tracking] ✅ Fallback: Visibility filter registered')
            except Exception as e2:
                print(f'[Monlam Tracking] ⚠️ Fallback also failed: {e2}')
        
        # Set up auto-tracking signals
        try:
            from .signals import setup_annotation_signals
            setup_annotation_signals()
            print('[Monlam Tracking] ✅ Auto-tracking signals connected')
        except Exception as e:
            print(f'[Monlam Tracking] ⚠️ Auto-tracking not set up: {e}')

