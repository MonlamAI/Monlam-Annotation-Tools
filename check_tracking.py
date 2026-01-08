"""
Diagnostic script to check tracking records

Run on Render Shell:
    export DJANGO_SETTINGS_MODULE=config.settings.production
    python check_tracking.py
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
sys.path.insert(0, '/doccano/backend')
django.setup()

def check_tracking():
    print("=" * 60)
    print("CHECKING TRACKING RECORDS")
    print("=" * 60)
    
    try:
        from assignment.simple_tracking import AnnotationTracking
        from examples.models import Example
        from projects.models import Project
        
        # Get all projects
        for project in Project.objects.all():
            print(f"\n--- Project {project.id}: {project.name} ---")
            
            total_examples = Example.objects.filter(project=project).count()
            tracking_records = AnnotationTracking.objects.filter(project=project)
            tracked_count = tracking_records.count()
            
            print(f"  Total examples: {total_examples}")
            print(f"  Tracking records: {tracked_count}")
            print(f"  Untracked examples: {total_examples - tracked_count}")
            
            # Show status breakdown
            print("\n  Status breakdown:")
            for status in ['pending', 'submitted', 'approved', 'rejected']:
                count = tracking_records.filter(status=status).count()
                print(f"    {status}: {count}")
            
            # Show sample tracking records
            print("\n  Sample tracking records:")
            for t in tracking_records[:5]:
                annotator = t.annotated_by.username if t.annotated_by else 'None'
                reviewer = t.reviewed_by.username if t.reviewed_by else 'None'
                print(f"    Example {t.example_id}: status={t.status}, annotated_by={annotator}, reviewed_by={reviewer}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    check_tracking()

