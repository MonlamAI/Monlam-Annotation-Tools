"""
Add example locking fields to Assignment model.

This migration adds:
- locked_by: User who currently has the example locked
- locked_at: When the example was locked
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('assignment', '0002_completion_tracking'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='locked_by',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='locked_assignments',
                to=settings.AUTH_USER_MODEL,
                help_text='User who currently has this example locked for editing'
            ),
        ),
        migrations.AddField(
            model_name='assignment',
            name='locked_at',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text='When the example was locked'
            ),
        ),
    ]



