#!/usr/bin/env python
"""
Diagnostic script to compare tgonpo and kunchoedon's AnnotationTracking records
to understand why kunchoedon gets payment but tgonpo doesn't.
"""

import os
import sys
import django

# Setup Django (matching check_tracking.py pattern)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
sys.path.insert(0, '/doccano/backend')
django.setup()

from django.contrib.auth import get_user_model
from assignment.simple_tracking import AnnotationTracking
from examples.models import Example
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

def get_user_tracking_data(username):
    """Get all tracking data for a user"""
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        print(f"❌ User '{username}' not found")
        return None
    
    tracking_records = AnnotationTracking.objects.filter(
        annotated_by=user
    ).select_related('example', 'project', 'annotated_by').order_by('annotated_at')
    
    print(f"\n{'='*80}")
    print(f"📊 Tracking Data for: {username} ({user.id})")
    print(f"{'='*80}")
    print(f"Total Tracking Records: {tracking_records.count()}\n")
    
    if tracking_records.count() == 0:
        print("⚠️  No tracking records found!")
        return None
    
    # Group by status
    status_counts = {}
    for t in tracking_records:
        status = t.status or 'None'
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("Status Breakdown:")
    for status, count in sorted(status_counts.items()):
        print(f"  - {status}: {count}")
    
    # Check for missing annotated_at
    missing_annotated_at = tracking_records.filter(annotated_at__isnull=True).count()
    print(f"\nMissing annotated_at: {missing_annotated_at}")
    
    # Check for missing annotated_by
    missing_annotated_by = tracking_records.filter(annotated_by__isnull=True).count()
    print(f"Missing annotated_by: {missing_annotated_by}")
    
    # Get example details
    print(f"\n{'─'*80}")
    print("Example Details:")
    print(f"{'─'*80}")
    
    examples_data = []
    for t in tracking_records:
        ex = t.example
        project_name = t.project.name
        
        # Get audio duration from meta
        duration = 0.0
        duration_minutes = 0.0
        if ex.meta and isinstance(ex.meta, dict):
            duration = ex.meta.get('duration', ex.meta.get('audio_duration', 0.0))
            if duration and isinstance(duration, (int, float)):
                duration_minutes = float(duration) / 60.0
        
        # Get text
        text = ex.text or ''
        text_length = len(text)
        
        examples_data.append({
            'example_id': ex.id,
            'project': project_name,
            'status': t.status,
            'annotated_at': t.annotated_at,
            'reviewed_at': t.reviewed_at,
            'duration_seconds': duration,
            'duration_minutes': duration_minutes,
            'text_length': text_length,
            'has_text': bool(text),
            'has_duration': bool(duration),
        })
        
        print(f"\nExample {ex.id} ({project_name}):")
        print(f"  Status: {t.status}")
        print(f"  Annotated At: {t.annotated_at}")
        print(f"  Reviewed At: {t.reviewed_at}")
        print(f"  Audio Duration: {duration} seconds ({duration_minutes:.2f} minutes)")
        print(f"  Text Length: {text_length} chars")
        print(f"  Has Text: {bool(text)}")
        print(f"  Has Duration: {bool(duration)}")
    
    return {
        'user': user,
        'tracking_records': tracking_records,
        'examples_data': examples_data,
        'status_counts': status_counts,
        'missing_annotated_at': missing_annotated_at,
    }

def simulate_payment_calculation(username, examples_data, date_range_days=30):
    """Simulate the payment calculation logic"""
    print(f"\n{'='*80}")
    print(f"💰 Simulating Payment Calculation for: {username}")
    print(f"{'='*80}")
    
    # Simulate date range (last 30 days by default)
    end_datetime = timezone.now()
    start_datetime = end_datetime - timedelta(days=date_range_days)
    
    print(f"Date Range: {start_datetime} to {end_datetime}")
    
    # Group by project
    project_data = {}
    
    for ex_data in examples_data:
        project_name = ex_data['project']
        
        # Check if this example would be included in payment calculation
        # Based on line 1364: if t.annotated_by and t.status == 'submitted' and t.annotated_at:
        annotated_at = ex_data['annotated_at']
        status = ex_data['status']
        
        would_be_included = (
            annotated_at is not None and
            status == 'submitted' and
            start_datetime <= annotated_at <= end_datetime
        )
        
        if project_name not in project_data:
            project_data[project_name] = {
                'total_examples': 0,
                'included_examples': 0,
                'audio_minutes': 0.0,
                'syllables': 0,
                'by_status': {}
            }
        
        project_data[project_name]['total_examples'] += 1
        project_data[project_name]['by_status'][status] = project_data[project_name]['by_status'].get(status, 0) + 1
        
        if would_be_included:
            project_data[project_name]['included_examples'] += 1
            project_data[project_name]['audio_minutes'] += ex_data['duration_minutes']
            # Note: We can't count syllables without the actual text, but we can note if text exists
            if ex_data['has_text']:
                project_data[project_name]['syllables'] += 1  # Placeholder
    
    print(f"\nPayment Calculation Simulation:")
    for project_name, data in project_data.items():
        print(f"\nProject: {project_name}")
        print(f"  Total Examples: {data['total_examples']}")
        print(f"  Status Breakdown: {data['by_status']}")
        print(f"  Examples with status='submitted' AND annotated_at in range: {data['included_examples']}")
        print(f"  Audio Minutes (for included): {data['audio_minutes']:.2f}")
        
        if data['included_examples'] == 0:
            print(f"  ⚠️  NO EXAMPLES WOULD BE INCLUDED IN PAYMENT CALCULATION!")
            print(f"     Reasons:")
            for ex_data in examples_data:
                if ex_data['project'] == project_name:
                    status = ex_data['status']
                    annotated_at = ex_data['annotated_at']
                    
                    reasons = []
                    if annotated_at is None:
                        reasons.append("missing annotated_at")
                    elif status != 'submitted':
                        reasons.append(f"status is '{status}' (not 'submitted')")
                    elif not (start_datetime <= annotated_at <= end_datetime):
                        reasons.append(f"annotated_at ({annotated_at}) outside date range")
                    
                    if reasons:
                        print(f"       - Example {ex_data['example_id']}: {', '.join(reasons)}")

def compare_users():
    """Compare tgonpo and kunchoedon"""
    print("\n" + "="*80)
    print("🔍 PAYMENT CALCULATION DIAGNOSTIC")
    print("="*80)
    
    tgonpo_data = get_user_tracking_data('tgonpo')
    kunchoedon_data = get_user_tracking_data('kunchoedon')
    
    if not tgonpo_data or not kunchoedon_data:
        print("\n❌ Could not retrieve data for one or both users")
        return
    
    # Simulate payment calculation
    print("\n" + "="*80)
    print("SIMULATING PAYMENT CALCULATION LOGIC")
    print("="*80)
    
    simulate_payment_calculation('tgonpo', tgonpo_data['examples_data'])
    simulate_payment_calculation('kunchoedon', kunchoedon_data['examples_data'])
    
    # Compare key differences
    print("\n" + "="*80)
    print("🔍 KEY DIFFERENCES")
    print("="*80)
    
    tgonpo_statuses = tgonpo_data['status_counts']
    kunchoedon_statuses = kunchoedon_data['status_counts']
    
    print(f"\ntgonpo statuses: {tgonpo_statuses}")
    print(f"kunchoedon statuses: {kunchoedon_statuses}")
    
    tgonpo_submitted = tgonpo_statuses.get('submitted', 0)
    kunchoedon_submitted = kunchoedon_statuses.get('submitted', 0)
    
    print(f"\ntgonpo 'submitted' count: {tgonpo_submitted}")
    print(f"kunchoedon 'submitted' count: {kunchoedon_submitted}")
    
    tgonpo_missing_at = tgonpo_data['missing_annotated_at']
    kunchoedon_missing_at = kunchoedon_data['missing_annotated_at']
    
    print(f"\ntgonpo missing annotated_at: {tgonpo_missing_at}")
    print(f"kunchoedon missing annotated_at: {kunchoedon_missing_at}")
    
    # Check annotated_at timestamps
    print(f"\n{'─'*80}")
    print("Annotated At Timestamps:")
    print(f"{'─'*80}")
    
    print("\ntgonpo:")
    for ex_data in tgonpo_data['examples_data']:
        print(f"  Example {ex_data['example_id']}: {ex_data['annotated_at']} (status: {ex_data['status']})")
    
    print("\nkunchoedon:")
    for ex_data in kunchoedon_data['examples_data']:
        print(f"  Example {ex_data['example_id']}: {ex_data['annotated_at']} (status: {ex_data['status']})")

if __name__ == '__main__':
    compare_users()

