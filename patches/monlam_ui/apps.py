"""
Monlam UI Django App Configuration
"""

from django.apps import AppConfig


class MonlamUiConfig(AppConfig):
    """Configuration for Monlam UI app."""
    name = 'monlam_ui'
    verbose_name = 'Monlam UI Extensions'
    default_auto_field = 'django.db.models.BigAutoField'
    
    def ready(self):
        """Called when Django starts."""
        # Import any signals or initialization code here
        pass



