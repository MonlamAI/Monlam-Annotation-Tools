# Generated manually for Monlam Doccano

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0001_initial'),
        ('examples', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnnotationTracking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('annotated_at', models.DateTimeField(blank=True, null=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), ('submitted', 'Submitted'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('review_notes', models.TextField(blank=True, default='')),
                ('locked_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('annotated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='annotations_tracked', to=settings.AUTH_USER_MODEL)),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviews_tracked', to=settings.AUTH_USER_MODEL)),
                ('locked_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='locked_examples', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tracking_records', to='projects.project')),
                ('example', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='tracking', to='examples.example')),
            ],
            options={
                'db_table': 'monlam_tracking_annotationtracking',
                'ordering': ['example__id'],
                'unique_together': {('project', 'example')},
            },
        ),
        migrations.AddIndex(
            model_name='annotationtracking',
            index=models.Index(fields=['project', 'example'], name='monlam_trac_project_1a2b3c_idx'),
        ),
        migrations.AddIndex(
            model_name='annotationtracking',
            index=models.Index(fields=['project', 'status'], name='monlam_trac_project_4d5e6f_idx'),
        ),
        migrations.AddIndex(
            model_name='annotationtracking',
            index=models.Index(fields=['annotated_by'], name='monlam_trac_annotat_7g8h9i_idx'),
        ),
        migrations.AddIndex(
            model_name='annotationtracking',
            index=models.Index(fields=['reviewed_by'], name='monlam_trac_reviewe_0j1k2l_idx'),
        ),
        migrations.AddIndex(
            model_name='annotationtracking',
            index=models.Index(fields=['locked_by'], name='monlam_trac_locked__3m4n5o_idx'),
        ),
        migrations.AddIndex(
            model_name='annotationtracking',
            index=models.Index(fields=['status'], name='monlam_trac_status_6p7q8r_idx'),
        ),
    ]

