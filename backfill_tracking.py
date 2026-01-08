"""
Backfill Tracking Records for Existing Annotations

Run this on Render Shell:
    export DJANGO_SETTINGS_MODULE=config.settings.production
    python backfill_tracking.py

This will:
1. Find all examples that have annotations but no tracking record
2. Create tracking records with status='submitted' and the first annotator
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
sys.path.insert(0, '/doccano/backend')
django.setup()

from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model

User = get_user_model()

def backfill_tracking():
    print("=" * 60)
    print("BACKFILLING TRACKING RECORDS FOR EXISTING ANNOTATIONS")
    print("=" * 60)
    
    try:
        from projects.models import Project
        from examples.models import Example
        from assignment.simple_tracking import AnnotationTracking
        
        # Get annotation models - Doccano has different types
        annotation_models = []
        
        try:
            from labels.models import Category
            annotation_models.append(('Category', Category))
        except ImportError:
            pass
        
        try:
            from labels.models import Span
            annotation_models.append(('Span', Span))
        except ImportError:
            pass
        
        try:
            from labels.models import TextLabel
            annotation_models.append(('TextLabel', TextLabel))
        except ImportError:
            pass
        
        try:
            from labels.models import Relation
            annotation_models.append(('Relation', Relation))
        except ImportError:
            pass
        
        print(f"\nFound annotation models: {[name for name, _ in annotation_models]}")
        
        # Get all projects
        projects = Project.objects.all()
        print(f"Found {projects.count()} projects")
        
        total_created = 0
        total_skipped = 0
        
        for project in projects:
            print(f"\n--- Project {project.id}: {project.name} ---")
            
            # Get all examples in this project
            examples = Example.objects.filter(project=project)
            print(f"  Examples: {examples.count()}")
            
            # Get existing tracking records
            existing_tracking = set(
                AnnotationTracking.objects.filter(project=project)
                .values_list('example_id', flat=True)
            )
            print(f"  Existing tracking records: {len(existing_tracking)}")
            
            # Find examples with annotations
            for example in examples:
                if example.id in existing_tracking:
                    continue  # Already has tracking
                
                # Check each annotation model for this example
                annotator = None
                annotated_at = None
                has_annotation = False
                
                for model_name, model_class in annotation_models:
                    try:
                        # Check if this example has annotations
                        annotations = model_class.objects.filter(example=example)
                        if annotations.exists():
                            has_annotation = True
                            # Get the first annotation's user and time
                            first_annotation = annotations.order_by('created_at').first()
                            if first_annotation and hasattr(first_annotation, 'user'):
                                annotator = first_annotation.user
                                annotated_at = getattr(first_annotation, 'created_at', timezone.now())
                                break
                    except Exception as e:
                        pass
                
                if has_annotation:
                    # Create tracking record
                    try:
                        with transaction.atomic():
                            AnnotationTracking.objects.create(
                                project=project,
                                example=example,
                                annotated_by=annotator,
                                annotated_at=annotated_at or timezone.now(),
                                status='submitted'
                            )
                            total_created += 1
                            print(f"  ✅ Created tracking for example {example.id} (annotator: {annotator})")
                    except Exception as e:
                        print(f"  ❌ Error creating tracking for example {example.id}: {e}")
                        total_skipped += 1
                else:
                    # No annotation = pending (don't create record, middleware handles this)
                    pass
        
        print("\n" + "=" * 60)
        print(f"DONE!")
        print(f"  Created: {total_created} tracking records")
        print(f"  Skipped/Errors: {total_skipped}")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    backfill_tracking()

