"""
Assignment System - Model Patches for Doccano

This file contains the model field additions needed for task assignment.
These need to be added to the Example model in examples/models.py

To apply:
1. Add these fields to the Example model
2. Run: python manage.py makemigrations
3. Run: python manage.py migrate
"""

# Add these imports to examples/models.py:
# from django.conf import settings

# Add these fields to the Example class in examples/models.py:

ASSIGNMENT_FIELDS = '''
    # Assignment fields
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_examples',
        help_text='User assigned to annotate this example'
    )
    
    assignment_status = models.CharField(
        max_length=20,
        choices=[
            ('unassigned', 'Unassigned'),
            ('assigned', 'Assigned'),
            ('in_progress', 'In Progress'),
            ('submitted', 'Submitted for Review'),
            ('approved', 'Approved'),
            ('rejected', 'Needs Revision'),
        ],
        default='unassigned',
        db_index=True
    )
    
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_examples',
        help_text='Approver who reviewed this example'
    )
    
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, default='')
'''

print("Add the ASSIGNMENT_FIELDS to your Example model in examples/models.py")

