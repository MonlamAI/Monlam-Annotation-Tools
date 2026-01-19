"""
Remove example locking fields from AnnotationTracking model.

This migration removes:
- locked_by: User who currently has the example locked
- locked_at: When the example was locked
- Index on locked_by field

Locking system is no longer needed as we have single annotator per project.
"""

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('assignment', '0006_annotation_tracking_simple'),
    ]

    operations = [
        # Remove index on locked_by first (before removing the field)
        migrations.RemoveIndex(
            model_name='annotationtracking',
            name='anno_track_locked_idx',
        ),
        # Remove locked_by field
        migrations.RemoveField(
            model_name='annotationtracking',
            name='locked_by',
        ),
        # Remove locked_at field
        migrations.RemoveField(
            model_name='annotationtracking',
            name='locked_at',
        ),
    ]

