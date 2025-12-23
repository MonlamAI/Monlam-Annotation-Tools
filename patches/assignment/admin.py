"""
Assignment Admin Configuration

Register Assignment models with Django admin for easy management.
"""

from django.contrib import admin


# Note: Only register after the app is installed and migrations are run
# Uncomment below after installation:

# from .models_separate import Assignment, AssignmentBatch
#
# @admin.register(Assignment)
# class AssignmentAdmin(admin.ModelAdmin):
#     list_display = ['id', 'example_id', 'project', 'assigned_to', 'status', 'assigned_at']
#     list_filter = ['status', 'project', 'is_active']
#     search_fields = ['assigned_to__username', 'example__id']
#     raw_id_fields = ['example', 'assigned_to', 'assigned_by', 'reviewed_by']
#     date_hierarchy = 'assigned_at'
#
#
# @admin.register(AssignmentBatch)
# class AssignmentBatchAdmin(admin.ModelAdmin):
#     list_display = ['id', 'project', 'assigned_to', 'total_count', 'completed_count', 'approved_count', 'created_at']
#     list_filter = ['project']
#     search_fields = ['assigned_to__username']

