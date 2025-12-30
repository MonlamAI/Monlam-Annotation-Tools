"""
Migration for Completion Tracking Models

This migration adds the completion tracking tables:
- AnnotatorCompletionStatus
- ApproverCompletionStatus

Run with: python manage.py migrate assignment
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assignment', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('examples', '__first__'),
        ('projects', '__first__'),
    ]

    operations = [
        # Create AnnotatorCompletionStatus model
        migrations.CreateModel(
            name='AnnotatorCompletionStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_completed', models.BooleanField(default=False)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('annotation_count', models.IntegerField(default=0)),
                ('annotator', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='annotation_completions',
                    to=settings.AUTH_USER_MODEL
                )),
                ('assignment', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='completion_status',
                    to='assignment.assignment'
                )),
                ('example', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='annotator_completions',
                    to='examples.example'
                )),
                ('project', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='annotator_completions',
                    to='projects.project'
                )),
            ],
            options={
                'indexes': [
                    models.Index(fields=['project', 'annotator', 'is_completed'], name='assignment_annotator_proj_idx'),
                    models.Index(fields=['example', 'is_completed'], name='assignment_annotator_ex_idx'),
                ],
            },
        ),
        
        # Create ApproverCompletionStatus model
        migrations.CreateModel(
            name='ApproverCompletionStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending Review'),
                        ('approved', 'Approved'),
                        ('rejected', 'Rejected')
                    ],
                    default='pending',
                    max_length=20
                )),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('review_notes', models.TextField(blank=True, default='')),
                ('approver', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='approval_completions',
                    to=settings.AUTH_USER_MODEL
                )),
                ('assignment', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='approval_status',
                    to='assignment.assignment'
                )),
                ('example', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='approver_completions',
                    to='examples.example'
                )),
                ('project', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='approver_completions',
                    to='projects.project'
                )),
            ],
            options={
                'indexes': [
                    models.Index(fields=['project', 'approver', 'status'], name='assignment_approver_proj_idx'),
                    models.Index(fields=['example', 'status'], name='assignment_approver_ex_idx'),
                ],
            },
        ),
        
        # Add unique constraints
        migrations.AddConstraint(
            model_name='annotatorcompletionstatus',
            constraint=models.UniqueConstraint(
                fields=['example', 'annotator'],
                name='unique_annotator_completion'
            ),
        ),
        
        migrations.AddConstraint(
            model_name='approvercompletionstatus',
            constraint=models.UniqueConstraint(
                fields=['example', 'approver'],
                name='unique_approver_completion'
            ),
        ),
    ]

