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
        
        # Import and register the visibility filter backend
        try:
            from .filters import register_visibility_filter
            register_visibility_filter()
            print('[Monlam Tracking] ✅ Visibility filter registered')
        except Exception as e:
            print(f'[Monlam Tracking] ⚠️ Visibility filter not registered: {e}')
        
        # Set up auto-tracking signals
        try:
            from .signals import setup_annotation_signals
            setup_annotation_signals()
            print('[Monlam Tracking] ✅ Auto-tracking signals connected')
        except Exception as e:
            print(f'[Monlam Tracking] ⚠️ Auto-tracking not set up: {e}')

