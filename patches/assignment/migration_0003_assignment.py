"""
Migration to add assignment fields to Example model.

Save as: /doccano/backend/examples/migrations/0003_assignment_fields.py

Run with: python manage.py migrate examples
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('examples', '0002_example_score'),  # Adjust based on your last migration
    ]

    operations = [
        migrations.AddField(
            model_name='example',
            name='assigned_to',
            field=models.ForeignKey(
                blank=True,
                help_text='User assigned to annotate this example',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='assigned_examples',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='example',
            name='assignment_status',
            field=models.CharField(
                choices=[
                    ('unassigned', 'Unassigned'),
                    ('assigned', 'Assigned'),
                    ('in_progress', 'In Progress'),
                    ('submitted', 'Submitted for Review'),
                    ('approved', 'Approved'),
                    ('rejected', 'Needs Revision')
                ],
                db_index=True,
                default='unassigned',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='example',
            name='reviewed_by',
            field=models.ForeignKey(
                blank=True,
                help_text='Approver who reviewed this example',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='reviewed_examples',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='example',
            name='reviewed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='example',
            name='review_notes',
            field=models.TextField(blank=True, default=''),
        ),
    ]

