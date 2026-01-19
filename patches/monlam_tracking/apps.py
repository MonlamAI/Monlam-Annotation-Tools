"""
Monlam Tracking App Configuration

Proper Django AppConfig that initializes auto-tracking signals
after all apps are loaded.

Auto-tracking signals automatically create AnnotationTracking records
when annotations are saved, ensuring the system tracks who annotated what.
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
        
        # No backend filtering - frontend toolbar handles filtering
        # The frontend (patches/frontend/index.html) sets default filter to "undone" 
        # for annotators on annotation pages using Doccano's native toolbar filter
        # This allows:
        # 1. Dataset table to show all examples (no filtering)
        # 2. Annotation page toolbar to filter using Doccano's native mechanism (isChecked query param)
        # 3. Detail views to access any example by ID (no filtering)
        
        print('[Monlam Tracking] ✅ No backend filtering - using frontend toolbar filter')
        print('[Monlam Tracking] ✅ Frontend will set default filter to "undone" for annotators on annotation pages')
        
        # Set up auto-tracking signals
        try:
            from .signals import setup_annotation_signals, setup_example_state_signals
            setup_annotation_signals()
            setup_example_state_signals()  # Also track ExampleState (tick mark)
            print('[Monlam Tracking] ✅ Auto-tracking signals connected')
        except Exception as e:
            print(f'[Monlam Tracking] ⚠️ Auto-tracking not set up: {e}')

