"""
Assignment App Configuration

This is a separate Django app that adds assignment functionality
without modifying core Doccano models.
"""

from django.apps import AppConfig


class AssignmentConfig(AppConfig):
    name = 'assignment'
    verbose_name = 'Task Assignment'
    
    def ready(self):
        # Import signals when app is ready
        pass

