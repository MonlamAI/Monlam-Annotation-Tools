# Simple migration for AnnotationTracking
# Avoids constraint/index issues by only creating what we need

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0001_initial'),
        ('examples', '0001_initial'),
        ('assignment', '0003_example_locking'),
    ]

    operations = [
        # Only create the AnnotationTracking table if it doesn't exist
        migrations.CreateModel(
            name='AnnotationTracking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('annotated_at', models.DateTimeField(blank=True, null=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'),
                        ('submitted', 'Submitted'),
                        ('approved', 'Approved'),
                        ('rejected', 'Rejected')
                    ],
                    default='pending',
                    max_length=20
                )),
                ('review_notes', models.TextField(blank=True, default='')),
                ('locked_at', models.DateTimeField(blank=True, null=True)),
                ('annotated_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='annotated_examples',
                    to=settings.AUTH_USER_MODEL
                )),
                ('example', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='annotation_tracking',
                    to='examples.example'
                )),
                ('locked_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='locked_examples',
                    to=settings.AUTH_USER_MODEL
                )),
                ('project', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='annotation_tracking',
                    to='projects.project'
                )),
                ('reviewed_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='reviewed_examples',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'db_table': 'annotation_tracking',
            },
        ),
        # Add unique constraint
        migrations.AddConstraint(
            model_name='annotationtracking',
            constraint=models.UniqueConstraint(
                fields=['project', 'example'],
                name='annotation_tracking_project_example_unique'
            ),
        ),
        # Add basic indexes
        migrations.AddIndex(
            model_name='annotationtracking',
            index=models.Index(fields=['project', 'example'], name='anno_track_proj_ex_idx'),
        ),
        migrations.AddIndex(
            model_name='annotationtracking',
            index=models.Index(fields=['project', 'status'], name='anno_track_proj_status_idx'),
        ),
        migrations.AddIndex(
            model_name='annotationtracking',
            index=models.Index(fields=['annotated_by'], name='anno_track_annotated_idx'),
        ),
        migrations.AddIndex(
            model_name='annotationtracking',
            index=models.Index(fields=['reviewed_by'], name='anno_track_reviewed_idx'),
        ),
        migrations.AddIndex(
            model_name='annotationtracking',
            index=models.Index(fields=['locked_by'], name='anno_track_locked_idx'),
        ),
    ]

