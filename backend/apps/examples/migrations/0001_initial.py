# Generated manually for Monlam Doccano

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Example',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(blank=True, default='')),
                ('upload_name', models.CharField(blank=True, default='', max_length=512)),
                ('filename', models.FileField(blank=True, null=True, upload_to='examples/')),
                ('meta', models.JSONField(blank=True, default=dict)),
                ('uuid', models.CharField(blank=True, default='', max_length=36)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='examples', to='projects.project')),
            ],
            options={
                'db_table': 'examples_example',
                'ordering': ['id'],
            },
        ),
        migrations.AddIndex(
            model_name='example',
            index=models.Index(fields=['project'], name='examples_ex_project_3f1c7e_idx'),
        ),
        migrations.AddIndex(
            model_name='example',
            index=models.Index(fields=['uuid'], name='examples_ex_uuid_ab1234_idx'),
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('example', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='examples.example')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='example_comments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'examples_comment',
                'ordering': ['-created_at'],
            },
        ),
    ]

