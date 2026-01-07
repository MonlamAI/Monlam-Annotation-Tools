# Generated manually for Monlam Doccano

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, default='')),
                ('project_type', models.CharField(choices=[('sequence_labeling', 'Sequence Labeling'), ('document_classification', 'Document Classification'), ('seq2seq', 'Sequence to Sequence'), ('speech_to_text', 'Speech to Text'), ('image_classification', 'Image Classification'), ('bounding_box', 'Bounding Box'), ('segmentation', 'Segmentation'), ('image_captioning', 'Image Captioning')], default='sequence_labeling', max_length=50)),
                ('tibetan_name', models.CharField(blank=True, default='', max_length=255)),
                ('guideline', models.TextField(blank=True, default='')),
                ('random_order', models.BooleanField(default=False)),
                ('collaborative_annotation', models.BooleanField(default=False)),
                ('single_class_classification', models.BooleanField(default=False)),
                ('allow_overlapping', models.BooleanField(default=False)),
                ('grapheme_mode', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_projects', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'projects_project',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('annotator', 'Annotator'), ('approver', 'Approver'), ('project_manager', 'Project Manager'), ('project_admin', 'Project Admin')], default='annotator', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='projects.project')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='project_memberships', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'projects_member',
                'ordering': ['project', 'role', 'user__username'],
                'unique_together': {('project', 'user')},
            },
        ),
    ]

