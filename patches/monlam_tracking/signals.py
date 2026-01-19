"""
Django Signals for Auto-Tracking

Automatically creates tracking records when annotations are saved.
Uses Django's signal system properly.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


def setup_annotation_signals():
    """
    Connect signal handlers for annotation models.
    Called from apps.py ready() method.
    """
    try:
        # Import annotation models
        from labels.models import Category, Span, TextLabel
        
        # Models to track
        models_to_track = [Category, Span, TextLabel]
        
        for model in models_to_track:
            post_save.connect(
                track_annotation_saved,
                sender=model,
                dispatch_uid=f'monlam_track_{model.__name__}'
            )
            print(f'[Monlam Signals] ✅ Connected tracking for {model.__name__}')
        
        return True
        
    except Exception as e:
        print(f'[Monlam Signals] ⚠️ Setup failed: {e}')
        return False


def track_annotation_saved(sender, instance, created, **kwargs):
    """
    Signal handler that tracks when an annotation is created.
    
    Creates or updates AnnotationTracking record.
    """
    if not created:
        return  # Only track new annotations
    
    try:
        from assignment.simple_tracking import AnnotationTracking
        
        # Get example and user
        example = instance.example
        user = instance.user if hasattr(instance, 'user') else None
        
        if not user or not example:
            return
        
        # Validate that user is a project member
        from projects.models import Member
        is_member = Member.objects.filter(
            user=user,
            project=example.project
        ).exists()
        
        # Only proceed if user is a project member or superuser
        if not is_member and not user.is_superuser:
            print(f'[Monlam Signals] ⚠️ User {user.username} is not a project member, skipping tracking')
            return
        
        # Create or update tracking (track annotated_by in backend for comprehensive metrics)
        tracking, tracking_created = AnnotationTracking.objects.get_or_create(
            project=example.project,
            example=example,
            defaults={
                'annotated_by': user,  # Track who annotated (for metrics, not exposed in API)
                'annotated_at': timezone.now(),
                'status': 'submitted'  # Submitted for review
            }
        )
        
        # Update tracking if needed
        needs_save = False
        
        # If tracking exists but annotated_by not set, update it (only if user is still a member)
        if not tracking_created and not tracking.annotated_by:
            if is_member or user.is_superuser:
                tracking.annotated_by = user
                tracking.annotated_at = timezone.now()
                tracking.status = 'submitted'
                needs_save = True
        
        # If tracking exists but status is pending, update to submitted
        if not tracking_created and tracking.status == 'pending':
            if not tracking.annotated_by and (is_member or user.is_superuser):
                tracking.annotated_by = user
            tracking.annotated_at = timezone.now()
            tracking.status = 'submitted'
            needs_save = True
        
        # CRITICAL: If example was rejected, update status to submitted (resubmission)
        # This handles the rejected → submitted transition when annotator fixes and resubmits
        if not tracking_created and tracking.status == 'rejected':
            tracking.status = 'submitted'
            tracking.annotated_at = timezone.now()  # Update timestamp to reflect resubmission
            needs_save = True
            print(f'[Monlam Signals] ✅ Resubmission: Updated rejected example {example.id} to submitted')
        
        if needs_save:
            tracking.save()
            print(f'[Monlam Signals] ✅ Updated tracking for example {example.id}')
        elif tracking_created:
            print(f'[Monlam Signals] ✅ Created tracking for example {example.id}')
        
        # CRITICAL: Also create ExampleState to mark as confirmed (same as tick mark)
        # This ensures Enter key and tick mark both create ExampleState
        # This is essential for completion dashboard to show correct counts
        # IMPORTANT: Only annotators can confirm/submit examples
        # Only create if user is still a project member AND is an annotator
        if is_member or user.is_superuser:
            # Check if user is ONLY an annotator (not approver/admin/manager)
            try:
                from assignment.tracking_api import _is_annotator_only
                if not _is_annotator_only(user, example.project):
                    print(f'[Monlam Signals] ⚠️ User {user.username} is not an annotator, preventing auto-confirmation via Enter key')
                    return  # Don't create ExampleState for non-annotators
            except Exception as role_check_error:
                print(f'[Monlam Signals] ⚠️ Could not verify user role, preventing auto-confirmation: {role_check_error}')
                return  # Be safe and don't create ExampleState
            
            try:
                from examples.models import ExampleState
                import traceback
                
                # Use example as lookup, update confirmed_by and confirmed_at
                # This makes Enter key equivalent to clicking tick mark
                state, state_created = ExampleState.objects.update_or_create(
                    example=example,
                    defaults={
                        'confirmed_by': user,  # Still need user for ExampleState
                        'confirmed_at': tracking.annotated_at or timezone.now()
                    }
                )
            
            if state_created:
                print(f'[Monlam Signals] ✅ Created ExampleState for example {example.id} (Enter key pressed)')
            else:
                print(f'[Monlam Signals] ✅ Updated ExampleState for example {example.id} (Enter key pressed)')
                
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f'[Monlam Signals] ❌ CRITICAL: Could not create ExampleState for example {example.id}')
            print(f'[Monlam Signals] Error: {e}')
            print(f'[Monlam Signals] Traceback: {error_trace}')
            # Try again with more explicit error handling (only if user is still a member)
            if is_member or user.is_superuser:
                try:
                    # Force create if update_or_create failed
                    from examples.models import ExampleState
                    ExampleState.objects.create(
                        example=example,
                        confirmed_by=user,
                        confirmed_at=tracking.annotated_at or timezone.now()
                    )
                    print(f'[Monlam Signals] ✅ Retry successful: Created ExampleState for example {example.id}')
                except Exception as e2:
                # Check if it's because ExampleState already exists (that's okay)
                if 'unique constraint' in str(e2).lower() or 'already exists' in str(e2).lower():
                    print(f'[Monlam Signals] ✅ ExampleState already exists for example {example.id} (this is okay)')
                else:
                    print(f'[Monlam Signals] ❌ Retry also failed: {e2}')
                    print(f'[Monlam Signals] Traceback: {traceback.format_exc()}')
                # Don't fail the whole signal, but log the error prominently
        
    except Exception as e:
        print(f'[Monlam Signals] ⚠️ Tracking failed: {e}')


def setup_example_state_signals():
    """
    Connect signal handlers for ExampleState model.
    This ensures that when tick mark is clicked (ExampleState created),
    it also creates/updates AnnotationTracking and Assignment.
    """
    try:
        from examples.models import ExampleState
        
        post_save.connect(
            track_example_state_saved,
            sender=ExampleState,
            dispatch_uid='monlam_track_example_state'
        )
        print('[Monlam Signals] ✅ Connected tracking for ExampleState (tick mark)')
        
        return True
        
    except Exception as e:
        print(f'[Monlam Signals] ⚠️ ExampleState signal setup failed: {e}')
        return False


def track_example_state_saved(sender, instance, created, **kwargs):
    """
    Signal handler that tracks when ExampleState is created/updated (tick mark clicked).
    
    CRITICAL: This ensures that tick mark and Enter key have the same effect:
    - Creates/updates AnnotationTracking with status='submitted'
    - Updates Assignment status to 'submitted' if exists
    
    IMPORTANT: Only annotators can confirm/submit examples via tick mark.
    Reviewers, approvers, and project admins cannot use tick mark to confirm.
    """
    if not instance.confirmed_by:
        return  # Only process if confirmed_by is set
    
    try:
        from assignment.simple_tracking import AnnotationTracking
        from assignment.models_separate import Assignment
        from projects.models import Member
        
        example = instance.example
        confirmed_by = instance.confirmed_by
        confirmed_at = instance.confirmed_at or timezone.now()
        
        # Validate that confirmed_by is still a project member
        is_member = Member.objects.filter(
            user=confirmed_by,
            project=example.project
        ).exists()
        
        # Only proceed if user is a project member or superuser
        if not is_member and not confirmed_by.is_superuser:
            print(f'[Monlam Signals] ⚠️ User {confirmed_by.username} is not a project member, skipping tracking update')
            return
        
        # CRITICAL: Only annotators can confirm/submit examples via tick mark
        # Check if user is ONLY an annotator (not approver/admin/manager)
        try:
            from assignment.tracking_api import _is_annotator_only
            if not _is_annotator_only(confirmed_by, example.project):
                print(f'[Monlam Signals] ⚠️ User {confirmed_by.username} is not an annotator, preventing tick mark confirmation')
                # Delete the ExampleState to prevent non-annotators from confirming
                instance.delete()
                return
        except Exception as role_check_error:
            # If role check fails, be safe and prevent confirmation
            print(f'[Monlam Signals] ⚠️ Could not verify user role, preventing confirmation: {role_check_error}')
            instance.delete()
            return
        
        # Create or update AnnotationTracking (track annotated_by in backend for comprehensive metrics)
        tracking, tracking_created = AnnotationTracking.objects.get_or_create(
            project=example.project,
            example=example,
            defaults={
                'annotated_by': confirmed_by,  # Track who annotated (for metrics, not exposed in API)
                'annotated_at': confirmed_at,
                'status': 'submitted'  # Confirmed = submitted for review
            }
        )
        
        needs_tracking_save = False
        
        # Update tracking if it already existed
        if not tracking_created:
            # If annotated_by not set, update it (only if user is still a member)
            if not tracking.annotated_by:
                if is_member or confirmed_by.is_superuser:
                    tracking.annotated_by = confirmed_by
                    tracking.annotated_at = confirmed_at
                    needs_tracking_save = True
            
            # If status is pending, update to submitted (confirmed = submitted)
            if tracking.status == 'pending':
                if not tracking.annotated_by and (is_member or confirmed_by.is_superuser):
                    tracking.annotated_by = confirmed_by
                tracking.annotated_at = confirmed_at
                tracking.status = 'submitted'
                needs_tracking_save = True
            
            # If status is rejected, update to submitted (resubmission)
            elif tracking.status == 'rejected':
                tracking.annotated_at = confirmed_at
                tracking.status = 'submitted'
                needs_tracking_save = True
        
        if needs_tracking_save:
            tracking.save()
            print(f'[Monlam Signals] ✅ Updated AnnotationTracking for example {example.id} (from ExampleState)')
        elif tracking_created:
            print(f'[Monlam Signals] ✅ Created AnnotationTracking for example {example.id} (from ExampleState/tick mark)')
        
        # Update Assignment status if it exists
        try:
            assignment = Assignment.objects.filter(
                project=example.project,
                example=example,
                is_active=True
            ).first()
            
            if assignment:
                # Update status to submitted if it's still pending/in_progress
                if assignment.status in ['assigned', 'in_progress', 'pending']:
                    assignment.status = 'submitted'
                    assignment.submitted_at = confirmed_at
                    if not assignment.assigned_to:
                        assignment.assigned_to = confirmed_by
                    assignment.save()
                    print(f'[Monlam Signals] ✅ Updated Assignment status to submitted for example {example.id}')
        except Exception as e:
            print(f'[Monlam Signals] ⚠️ Could not update Assignment: {e}')
            # Don't fail if Assignment doesn't exist
        
    except Exception as e:
        import traceback
        print(f'[Monlam Signals] ⚠️ ExampleState tracking failed: {e}')
        print(f'[Monlam Signals] Traceback: {traceback.format_exc()}')

