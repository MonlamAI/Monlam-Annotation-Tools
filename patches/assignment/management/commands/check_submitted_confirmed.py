"""
Django management command: check_submitted_confirmed

Checks if submitted (AnnotationTracking) and confirmed (ExampleState) counts are tallying.

Usage:
    python manage.py check_submitted_confirmed
    python manage.py check_submitted_confirmed --verbose
    python manage.py check_submitted_confirmed --project-id 1
"""

from django.core.management.base import BaseCommand
from django.db.models import Q
from examples.models import Example, ExampleState
from assignment.simple_tracking import AnnotationTracking


class Command(BaseCommand):
    help = 'Check if submitted and confirmed counts are tallying'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for mismatches',
        )
        parser.add_argument(
            '--project-id',
            type=int,
            help='Check specific project only',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        project_id = options.get('project_id')
        
        self.stdout.write("=" * 80)
        self.stdout.write("Checking Submitted vs Confirmed Tally")
        self.stdout.write("=" * 80)
        
        # Build base querysets
        submitted_qs = AnnotationTracking.objects.filter(
            status='submitted',
            annotated_by__isnull=False
        )
        confirmed_qs = ExampleState.objects.filter(
            confirmed_by__isnull=False
        )
        
        if project_id:
            submitted_qs = submitted_qs.filter(project_id=project_id)
            confirmed_qs = confirmed_qs.filter(example__project_id=project_id)
            self.stdout.write(f"\nFiltering for Project ID: {project_id}\n")
        
        # Get counts
        submitted_count = submitted_qs.count()
        confirmed_count = confirmed_qs.count()
        
        # Get unique example IDs
        submitted_example_ids = set(
            submitted_qs.values_list('example_id', flat=True)
        )
        confirmed_example_ids = set(
            confirmed_qs.values_list('example_id', flat=True)
        )
        
        # Find mismatches
        submitted_not_confirmed = submitted_example_ids - confirmed_example_ids
        confirmed_not_submitted = confirmed_example_ids - submitted_example_ids
        
        # Print summary
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("Summary:")
        self.stdout.write("=" * 80)
        self.stdout.write(f"Submitted (AnnotationTracking): {submitted_count}")
        self.stdout.write(f"Confirmed (ExampleState):       {confirmed_count}")
        self.stdout.write(f"Difference:                      {submitted_count - confirmed_count}")
        self.stdout.write("=" * 80)
        
        # Print mismatch details
        if submitted_not_confirmed:
            self.stdout.write(f"\n⚠️  Found {len(submitted_not_confirmed)} submitted examples WITHOUT confirmed state:")
            if verbose:
                for example_id in sorted(list(submitted_not_confirmed))[:50]:  # Show first 50
                    tracking = AnnotationTracking.objects.filter(
                        example_id=example_id,
                        status='submitted',
                        annotated_by__isnull=False
                    ).first()
                    if tracking:
                        self.stdout.write(
                            f"  - Example {example_id}: submitted by {tracking.annotated_by.username if tracking.annotated_by else 'N/A'} "
                            f"(Project {tracking.project_id})"
                        )
                if len(submitted_not_confirmed) > 50:
                    self.stdout.write(f"  ... and {len(submitted_not_confirmed) - 50} more")
            else:
                self.stdout.write(f"  Run with --verbose to see details")
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ All submitted examples have confirmed state"))
        
        if confirmed_not_submitted:
            self.stdout.write(f"\n⚠️  Found {len(confirmed_not_submitted)} confirmed examples WITHOUT submitted tracking:")
            if verbose:
                for example_id in sorted(list(confirmed_not_submitted))[:50]:  # Show first 50
                    state = ExampleState.objects.filter(
                        example_id=example_id,
                        confirmed_by__isnull=False
                    ).first()
                    if state:
                        self.stdout.write(
                            f"  - Example {example_id}: confirmed by {state.confirmed_by.username if state.confirmed_by else 'N/A'} "
                            f"(Project {state.example.project_id if state.example else 'N/A'})"
                        )
                if len(confirmed_not_submitted) > 50:
                    self.stdout.write(f"  ... and {len(confirmed_not_submitted) - 50} more")
            else:
                self.stdout.write(f"  Run with --verbose to see details")
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ All confirmed examples have submitted tracking"))
        
        # Overall status
        self.stdout.write("\n" + "=" * 80)
        if submitted_not_confirmed or confirmed_not_submitted:
            self.stdout.write(self.style.WARNING("⚠️  MISMATCHES FOUND"))
            self.stdout.write("   Run: python manage.py backfill_example_state --verbose")
            self.stdout.write("   to fix missing ExampleState records")
        else:
            self.stdout.write(self.style.SUCCESS("✅ PERFECT MATCH - All counts are tallying!"))
        self.stdout.write("=" * 80)
        
        # Additional breakdown by project if not filtering
        if not project_id:
            self.stdout.write("\n" + "=" * 80)
            self.stdout.write("Breakdown by Project:")
            self.stdout.write("=" * 80)
            
            from projects.models import Project
            
            projects = Project.objects.all().order_by('id')
            for project in projects:
                proj_submitted = AnnotationTracking.objects.filter(
                    project=project,
                    status='submitted',
                    annotated_by__isnull=False
                ).count()
                proj_confirmed = ExampleState.objects.filter(
                    example__project=project,
                    confirmed_by__isnull=False
                ).count()
                
                if proj_submitted != proj_confirmed:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Project {project.id} ({project.name[:30]}): "
                            f"Submitted={proj_submitted}, Confirmed={proj_confirmed}, "
                            f"Diff={proj_submitted - proj_confirmed}"
                        )
                    )
                else:
                    self.stdout.write(
                        f"Project {project.id} ({project.name[:30]}): "
                        f"Submitted={proj_submitted}, Confirmed={proj_confirmed} ✓"
                    )

