# Assignment System Integration Guide

This guide explains how to integrate the task assignment and review system into your Doccano fork.

## Overview

### Features Added:
1. **Task Assignment** - Assign examples to specific annotators
2. **Assignment Restriction** - Annotators only see their assigned items
3. **Auto-Assignment** - Distribute items evenly among annotators
4. **Review Queue** - Dedicated UI for approvers
5. **Approve/Reject** - Clear approval workflow

---

## Step 1: Database Migration

### Add fields to Example model

Edit `/doccano/backend/examples/models.py`:

```python
from django.conf import settings

class Example(models.Model):
    # ... existing fields ...
    
    # ADD THESE FIELDS:
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_examples'
    )
    
    assignment_status = models.CharField(
        max_length=20,
        choices=[
            ('unassigned', 'Unassigned'),
            ('assigned', 'Assigned'),
            ('in_progress', 'In Progress'),
            ('submitted', 'Submitted for Review'),
            ('approved', 'Approved'),
            ('rejected', 'Needs Revision'),
        ],
        default='unassigned',
        db_index=True
    )
    
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_examples'
    )
    
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, default='')
```

### Run migrations

```bash
python manage.py makemigrations examples
python manage.py migrate
```

---

## Step 2: Backend Views

### Copy `views_patch.py` to backend

Copy the views and add to URL patterns:

Edit `/doccano/backend/examples/urls.py`:

```python
from .views_assignment import (
    BulkAssignmentView,
    AutoAssignView,
    ReviewQueueView,
    ReviewActionView,
    AssignmentStatsView
)

urlpatterns += [
    path(
        'projects/<int:project_id>/examples/assign/',
        BulkAssignmentView.as_view(),
        name='bulk-assign'
    ),
    path(
        'projects/<int:project_id>/examples/auto-assign/',
        AutoAssignView.as_view(),
        name='auto-assign'
    ),
    path(
        'projects/<int:project_id>/examples/review-queue/',
        ReviewQueueView.as_view(),
        name='review-queue'
    ),
    path(
        'projects/<int:project_id>/examples/<int:example_id>/review/',
        ReviewActionView.as_view(),
        name='review-action'
    ),
    path(
        'projects/<int:project_id>/examples/assignment-stats/',
        AssignmentStatsView.as_view(),
        name='assignment-stats'
    ),
]
```

---

## Step 3: Filter Examples by Assignment

### Modify the Example list view

Edit `/doccano/backend/examples/views.py`:

Find the `ExampleList` or `ExampleListAPI` view and modify `get_queryset`:

```python
def get_queryset(self):
    queryset = super().get_queryset()
    user = self.request.user
    project = self.get_project()
    
    # Check user's role
    member = project.members.filter(user=user).first()
    if not member:
        return queryset.none()
    
    role_name = member.role.name.lower()
    
    # Admins and Approvers see everything
    if role_name in ['project_admin', 'annotation_approver']:
        return queryset
    
    # Annotators ONLY see their assigned items
    return queryset.filter(assigned_to=user)
```

---

## Step 4: Frontend Components

### Add AssignmentPanel to Dataset page

Edit `/doccano/frontend/pages/projects/_id/dataset/index.vue`:

```vue
<template>
  <!-- Add after the data table -->
  <assignment-panel
    v-if="isAdmin"
    :project-id="projectId"
    :selected-items="selected"
    @assigned="refresh"
  />
</template>

<script>
import AssignmentPanel from '~/components/AssignmentPanel.vue'

export default {
  components: { AssignmentPanel },
  // ...
}
</script>
```

### Add Review Queue page

Create `/doccano/frontend/pages/projects/_id/review.vue`:

```vue
<template>
  <review-queue :project-id="projectId" />
</template>

<script>
import ReviewQueue from '~/components/ReviewQueue.vue'

export default {
  components: { ReviewQueue },
  computed: {
    projectId() {
      return parseInt(this.$route.params.id)
    }
  }
}
</script>
```

### Add navigation link

Edit the project sidebar to add "Review Queue" link for approvers.

---

## Step 5: Update Serializers

Edit `/doccano/backend/examples/serializers.py`:

```python
class ExampleSerializer(serializers.ModelSerializer):
    # ... existing fields ...
    
    # ADD THESE:
    assigned_to_username = serializers.SerializerMethodField()
    assignment_status = serializers.CharField(read_only=True)
    
    def get_assigned_to_username(self, obj):
        return obj.assigned_to.username if obj.assigned_to else None
    
    class Meta:
        model = Example
        fields = [
            # ... existing fields ...
            'assigned_to_username',
            'assignment_status',
        ]
```

---

## Step 6: Dockerfile Changes

Add to your Dockerfile to copy the new files:

```dockerfile
# Copy assignment system patches
COPY patches/assignment/views_patch.py /doccano/backend/examples/views_assignment.py
COPY patches/assignment/frontend/AssignmentPanel.vue /doccano/frontend/components/
COPY patches/assignment/frontend/ReviewQueue.vue /doccano/frontend/components/
```

---

## Workflow After Integration

### For Admins:
1. Import data (all items start as "unassigned")
2. Go to Dataset → Assignment Panel
3. Select annotators → Click "Auto-Assign"
4. Items are distributed evenly

### For Annotators:
1. Login → See ONLY their assigned items
2. Annotate → Click checkmark (status → "submitted")
3. Cannot see others' items

### For Approvers:
1. Login → Go to "Review Queue"
2. See all submitted items
3. Play audio, check transcript
4. Click Approve or Reject
5. Rejected items go back to annotator

---

## Database Views for Tracking

```sql
-- Assignment overview
CREATE VIEW assignment_overview AS
SELECT 
    p.name AS project,
    u.username AS annotator,
    COUNT(*) FILTER (WHERE e.assignment_status = 'assigned') AS assigned,
    COUNT(*) FILTER (WHERE e.assignment_status = 'in_progress') AS in_progress,
    COUNT(*) FILTER (WHERE e.assignment_status = 'submitted') AS submitted,
    COUNT(*) FILTER (WHERE e.assignment_status = 'approved') AS approved,
    COUNT(*) FILTER (WHERE e.assignment_status = 'rejected') AS rejected
FROM examples_example e
JOIN projects_project p ON e.project_id = p.id
LEFT JOIN auth_user u ON e.assigned_to_id = u.id
GROUP BY p.name, u.username;

-- Review activity
CREATE VIEW review_activity AS
SELECT 
    u.username AS reviewer,
    DATE(e.reviewed_at) AS review_date,
    COUNT(*) AS items_reviewed,
    COUNT(*) FILTER (WHERE e.assignment_status = 'approved') AS approved,
    COUNT(*) FILTER (WHERE e.assignment_status = 'rejected') AS rejected
FROM examples_example e
JOIN auth_user u ON e.reviewed_by_id = u.id
WHERE e.reviewed_at IS NOT NULL
GROUP BY u.username, DATE(e.reviewed_at);
```

---

## Testing

1. Create test users (1 admin, 1 approver, 2 annotators)
2. Import sample data
3. Auto-assign to annotators
4. Login as annotator → verify only sees assigned items
5. Annotate and submit
6. Login as approver → verify Review Queue works
7. Approve/Reject → verify status updates

---

## Estimated Implementation Time

| Task | Time |
|------|------|
| Model changes + migration | 30 min |
| Backend views | 2 hours |
| Frontend components | 3-4 hours |
| Integration & testing | 2-3 hours |
| **Total** | **~1 day** |

