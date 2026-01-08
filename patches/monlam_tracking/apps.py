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
        
        # DISABLED: View patching was causing infinite load issues
        # The visibility filtering will be handled differently
        print('[Monlam Tracking] ⚠️ View patching disabled for stability')
        
        # Set up auto-tracking signals ONLY
        try:
            from .signals import setup_annotation_signals
            setup_annotation_signals()
            print('[Monlam Tracking] ✅ Auto-tracking signals connected')
        except Exception as e:
            print(f'[Monlam Tracking] ⚠️ Auto-tracking not set up: {e}')

