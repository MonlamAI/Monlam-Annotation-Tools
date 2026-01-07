# Generated manually for Monlam Doccano

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0001_initial'),
        ('examples', '0001_initial'),
    ]

    operations = [
        # Label Types
        migrations.CreateModel(
            name='CategoryType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=255)),
                ('prefix_key', models.CharField(blank=True, max_length=10, null=True)),
                ('suffix_key', models.CharField(blank=True, max_length=10, null=True)),
                ('background_color', models.CharField(default='#209cee', max_length=7)),
                ('text_color', models.CharField(default='#ffffff', max_length=7)),
                ('tibetan_text', models.CharField(blank=True, default='', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='categorytypes', to='projects.project')),
            ],
            options={
                'db_table': 'labels_categorytype',
                'ordering': ['text'],
                'unique_together': {('project', 'text')},
            },
        ),
        migrations.CreateModel(
            name='SpanType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=255)),
                ('prefix_key', models.CharField(blank=True, max_length=10, null=True)),
                ('suffix_key', models.CharField(blank=True, max_length=10, null=True)),
                ('background_color', models.CharField(default='#209cee', max_length=7)),
                ('text_color', models.CharField(default='#ffffff', max_length=7)),
                ('tibetan_text', models.CharField(blank=True, default='', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='spantypes', to='projects.project')),
            ],
            options={
                'db_table': 'labels_spantype',
                'ordering': ['text'],
                'unique_together': {('project', 'text')},
            },
        ),
        migrations.CreateModel(
            name='RelationType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=255)),
                ('prefix_key', models.CharField(blank=True, max_length=10, null=True)),
                ('suffix_key', models.CharField(blank=True, max_length=10, null=True)),
                ('background_color', models.CharField(default='#209cee', max_length=7)),
                ('text_color', models.CharField(default='#ffffff', max_length=7)),
                ('tibetan_text', models.CharField(blank=True, default='', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='relationtypes', to='projects.project')),
            ],
            options={
                'db_table': 'labels_relationtype',
                'ordering': ['text'],
                'unique_together': {('project', 'text')},
            },
        ),
        # Annotations
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('example', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='categorys', to='examples.example')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='categorys', to=settings.AUTH_USER_MODEL)),
                ('label', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='annotations', to='labels.categorytype')),
            ],
            options={
                'db_table': 'labels_category',
                'unique_together': {('example', 'user', 'label')},
            },
        ),
        migrations.CreateModel(
            name='Span',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('start_offset', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('end_offset', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('example', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='spans', to='examples.example')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='spans', to=settings.AUTH_USER_MODEL)),
                ('label', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='annotations', to='labels.spantype')),
            ],
            options={
                'db_table': 'labels_span',
            },
        ),
        migrations.CreateModel(
            name='TextLabel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('text', models.TextField()),
                ('example', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='textlabels', to='examples.example')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='textlabels', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'labels_textlabel',
            },
        ),
        migrations.CreateModel(
            name='Relation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('example', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='relations', to='examples.example')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='relations', to=settings.AUTH_USER_MODEL)),
                ('label', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='annotations', to='labels.relationtype')),
                ('from_span', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='from_relations', to='labels.span')),
                ('to_span', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='to_relations', to='labels.span')),
            ],
            options={
                'db_table': 'labels_relation',
            },
        ),
        migrations.CreateModel(
            name='BoundingBox',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('x', models.FloatField()),
                ('y', models.FloatField()),
                ('width', models.FloatField()),
                ('height', models.FloatField()),
                ('example', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='boundingboxs', to='examples.example')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='boundingboxs', to=settings.AUTH_USER_MODEL)),
                ('label', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bounding_boxes', to='labels.categorytype')),
            ],
            options={
                'db_table': 'labels_boundingbox',
            },
        ),
    ]

