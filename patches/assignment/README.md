# Assignment System for Doccano

A **non-invasive** task assignment system that extends Doccano without modifying core models.

## Features

- ✅ Separate `Assignment` table (doesn't modify Example model)
- ✅ Bulk assignment of examples to annotators
- ✅ Assignment status tracking (assigned, in_progress, submitted, approved, rejected)
- ✅ Review workflow with approval/rejection
- ✅ Statistics and reporting
- ✅ Assignment history preservation
- ✅ Easy to add/remove without breaking existing data

## Installation

### Step 1: Copy the Assignment App

```bash
# Copy to Doccano backend
cp -r patches/assignment /doccano/backend/assignment
```

### Step 2: Add to INSTALLED_APPS

Edit `/doccano/backend/config/settings/base.py`:

```python
INSTALLED_APPS = [
    # ... existing apps ...
    'assignment',  # Add this line
]
```

### Step 3: Add URL Routes

Edit `/doccano/backend/config/urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    # ... existing urls ...
    path('v1/projects/<int:project_id>/assignments/', include('assignment.urls')),
]
```

### Step 4: Run Migrations

```bash
python manage.py migrate assignment
```

## API Endpoints

### List Assignments
```
GET /v1/projects/{project_id}/assignments/
GET /v1/projects/{project_id}/assignments/?status=submitted
GET /v1/projects/{project_id}/assignments/?user_id=5
```

### My Assignments
```
GET /v1/projects/{project_id}/assignments/my/
```

### Bulk Assign
```
POST /v1/projects/{project_id}/assignments/bulk/
{
    "example_ids": [1, 2, 3, 4, 5],
    "assigned_to_id": 10
}
```

### Assignment Actions
```
POST /v1/projects/{project_id}/assignments/{id}/start/
POST /v1/projects/{project_id}/assignments/{id}/submit/
POST /v1/projects/{project_id}/assignments/{id}/approve/
POST /v1/projects/{project_id}/assignments/{id}/reject/
```

### Statistics
```
GET /v1/projects/{project_id}/assignments/stats/
GET /v1/projects/{project_id}/assignments/unassigned/
```

## Database Tables

### assignment_assignment
| Column | Type | Description |
|--------|------|-------------|
| id | BigInt | Primary key |
| example_id | ForeignKey | Reference to Example |
| project_id | ForeignKey | Reference to Project |
| assigned_to_id | ForeignKey | User assigned to |
| assigned_by_id | ForeignKey | Admin who assigned |
| status | Char(20) | Current status |
| assigned_at | DateTime | When assigned |
| started_at | DateTime | When started |
| submitted_at | DateTime | When submitted |
| reviewed_by_id | ForeignKey | Reviewer user |
| reviewed_at | DateTime | When reviewed |
| review_notes | Text | Review comments |
| is_active | Boolean | Current assignment |

### assignment_assignmentbatch
Tracks batches of assignments for easier management.

## Usage in NocoDB

After installation, you can see assignments in NocoDB:

1. Connect to your PostgreSQL database
2. Look for `assignment_assignment` table
3. Create views to track:
   - Assignments per user
   - Completion rates
   - Review status

## Workflow Example

```
1. Admin imports 1000 audio files
2. Admin uses bulk assign to distribute:
   - 200 to annotator01
   - 200 to annotator02
   - 200 to annotator03
   - 200 to annotator04
   - 200 to annotator05
3. Annotators see only their assigned items
4. Annotators work and submit
5. Approver reviews submitted items
6. Approver approves or rejects with notes
7. Admin exports completed work
```

## Why Separate Table?

The previous approach modified `examples/models.py` directly, which:
- Caused migration conflicts
- Made upgrades difficult
- Risked breaking existing data

This approach:
- Uses a separate table with ForeignKey to Example
- No changes to core Doccano models
- Easy to upgrade or remove
- Preserves assignment history

## Dockerfile Integration (Future)

To add to Dockerfile:

```dockerfile
# Copy assignment app
COPY patches/assignment /doccano/backend/assignment

# Note: Migrations need to be run after container starts
# Add to startup script:
# python manage.py migrate assignment
```

