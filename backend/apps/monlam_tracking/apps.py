"""
App configuration for monlam_tracking.
"""

from django.apps import AppConfig


class MonlamTrackingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.monlam_tracking'
    verbose_name = 'Monlam Annotation Tracking'
    
    def ready(self):
        # Import signals to register them
        from . import signals  # noqa: F401

