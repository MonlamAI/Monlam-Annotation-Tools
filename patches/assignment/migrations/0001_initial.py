"""
Initial migration for Assignment app.

This creates the Assignment and AssignmentBatch tables.
Run after installing the app:
    python manage.py migrate assignment
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('examples', '0001_initial'),
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Assignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(
                    choices=[
                        ('assigned', 'Assigned'),
                        ('in_progress', 'In Progress'),
                        ('submitted', 'Submitted for Review'),
                        ('approved', 'Approved'),
                        ('rejected', 'Needs Revision'),
                        ('reassigned', 'Reassigned'),
                    ],
                    db_index=True,
                    default='assigned',
                    max_length=20
                )),
                ('assigned_at', models.DateTimeField(auto_now_add=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('review_notes', models.TextField(blank=True, default='')),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('assigned_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='assignments_given',
                    to=settings.AUTH_USER_MODEL
                )),
                ('assigned_to', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='assignments_received',
                    to=settings.AUTH_USER_MODEL
                )),
                ('example', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='assignments',
                    to='examples.example'
                )),
                ('project', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='assignments',
                    to='projects.project'
                )),
                ('reviewed_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='assignments_reviewed',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'ordering': ['-assigned_at'],
            },
        ),
        migrations.CreateModel(
            name='AssignmentBatch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('total_count', models.PositiveIntegerField(default=0)),
                ('completed_count', models.PositiveIntegerField(default=0)),
                ('approved_count', models.PositiveIntegerField(default=0)),
                ('notes', models.TextField(blank=True, default='')),
                ('assigned_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='assignment_batches_given',
                    to=settings.AUTH_USER_MODEL
                )),
                ('assigned_to', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='assignment_batches_received',
                    to=settings.AUTH_USER_MODEL
                )),
                ('project', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='assignment_batches',
                    to='projects.project'
                )),
            ],
            options={
                'verbose_name_plural': 'Assignment batches',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='assignment',
            index=models.Index(fields=['project', 'status'], name='assignment_project_status_idx'),
        ),
        migrations.AddIndex(
            model_name='assignment',
            index=models.Index(fields=['assigned_to', 'status'], name='assignment_user_status_idx'),
        ),
        migrations.AddIndex(
            model_name='assignment',
            index=models.Index(fields=['example', 'is_active'], name='assignment_example_active_idx'),
        ),
    ]

