"""
Assignment Models

This module re-exports models from models_separate.py to make them
available via the standard Django app.models pattern.

This allows ForeignKey references like 'assignment.Assignment' to work correctly.
"""

# Import all models from models_separate so they're available as assignment.models.*
from .models_separate import Assignment, AssignmentBatch

# Make them available at the module level for Django's model resolution
__all__ = ['Assignment', 'AssignmentBatch']

