# Installation Guide: Completion Tracking System

Step-by-step guide to install and configure the custom annotation status tracking system with Project Manager role.

## Prerequisites

- Monlam Doccano instance running
- Access to the backend Django application
- Database access (PostgreSQL recommended)
- Admin privileges to run migrations

## Installation Steps

### 1. Verify Files Are in Place

Ensure all the following files exist in `/doccano/backend/assignment/`:

```bash
cd /doccano/backend/assignment/

# Check for new files
ls -la completion_tracking.py
ls -la roles.py
ls -la completion_views.py
ls -la completion_serializers.py
ls -la migrations/0002_completion_tracking.py
```

If using the patches structure:

```bash
cd /path/to/monlam-doccano/patches/assignment/

# All files should be here
ls -la
```

### 2. Copy Files to Doccano Backend (if needed)

If files are in patches directory:

```bash
# Copy assignment app files
cp -r /path/to/monlam-doccano/patches/assignment/* /doccano/backend/assignment/

# Copy frontend files
cp /path/to/monlam-doccano/patches/frontend/completion-matrix.html /doccano/backend/client/dist/
cp /path/to/monlam-doccano/patches/frontend/status-indicators.js /doccano/backend/client/dist/js/

# Copy i18n files
cp /path/to/monlam-doccano/branding/i18n/bo/projects/completion.js /doccano/frontend/i18n/bo/projects/
cp /path/to/monlam-doccano/branding/i18n/bo/projects/members.js /doccano/frontend/i18n/bo/projects/
```

### 3. Verify Django Settings

Check that the assignment app is in `INSTALLED_APPS`:

```bash
# Edit settings file
vim /doccano/backend/config/settings/base.py
```

Ensure this line exists:

```python
INSTALLED_APPS = [
    # ... other apps ...
    'assignment',  # This should already be there
]
```

### 4. Run Database Migrations

```bash
cd /doccano/backend

# Check migration status
python manage.py showmigrations assignment

# Run migrations
python manage.py migrate assignment

# You should see:
# Running migrations:
#   Applying assignment.0002_completion_tracking... OK
```

### 5. Verify Database Tables

Check that the new tables were created:

```bash
# Connect to your database
psql -U doccano -d doccano

# List tables
\dt assignment_*

# You should see:
# assignment_assignment
# assignment_assignmentbatch
# assignment_annotatorcompletionstatus
# assignment_approvercompletionstatus
```

### 6. Update URL Configuration

Verify URLs are configured in `/doccano/backend/config/urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    # ... existing urls ...
    path('v1/projects/<int:project_id>/assignments/', include('assignment.urls')),
]
```

### 7. Sync Existing Data (Optional but Recommended)

If you have existing assignments, sync them to the completion tracking system:

#### Option A: Via Django Shell

```bash
cd /doccano/backend
python manage.py shell
```

```python
from assignment.completion_tracking import CompletionMatrixUpdater
from projects.models import Project

# Sync all projects
for project in Project.objects.all():
    print(f"Syncing project: {project.name}")
    CompletionMatrixUpdater.sync_from_assignments(project)
    print(f"  ✓ Synced")

print("All projects synced!")
```

#### Option B: Via Management Command (Create this file)

Create `/doccano/backend/assignment/management/commands/sync_completion.py`:

```python
from django.core.management.base import BaseCommand
from assignment.completion_tracking import CompletionMatrixUpdater
from projects.models import Project

class Command(BaseCommand):
    help = 'Sync completion tracking from existing assignments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project-id',
            type=int,
            help='Sync specific project only',
        )

    def handle(self, *args, **options):
        project_id = options.get('project_id')
        
        if project_id:
            projects = Project.objects.filter(id=project_id)
        else:
            projects = Project.objects.all()
        
        for project in projects:
            self.stdout.write(f"Syncing project: {project.name}")
            CompletionMatrixUpdater.sync_from_assignments(project)
            self.stdout.write(self.style.SUCCESS(f"  ✓ Synced"))
        
        self.stdout.write(self.style.SUCCESS('All projects synced!'))
```

Then run:

```bash
python manage.py sync_completion
# Or for specific project:
python manage.py sync_completion --project-id=1
```

### 8. Create Project Manager Users

Assign users to the Project Manager role:

#### Option A: Via Django Admin

1. Go to Django Admin: `http://your-doccano-url/admin/`
2. Navigate to Projects → Project Members
3. Find the member you want to promote
4. Change their role to `project_manager`
5. Save

#### Option B: Via Django Shell

```bash
python manage.py shell
```

```python
from projects.models import Project, Member
from django.contrib.auth import get_user_model

User = get_user_model()

# Get project and user
project = Project.objects.get(id=1)
user = User.objects.get(username='manager_username')

# Update or create member with project_manager role
member, created = Member.objects.update_or_create(
    project=project,
    user=user,
    defaults={'role': 'project_manager'}
)

print(f"User {user.username} is now a Project Manager")
```

### 9. Test the Installation

#### Test 1: Check API Endpoints

```bash
# Get authentication token (replace with your credentials)
TOKEN=$(curl -X POST http://localhost:8000/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' \
  | jq -r '.token')

# Test completion matrix endpoint (as Project Manager)
curl http://localhost:8000/v1/projects/1/assignments/completion-matrix/ \
  -H "Authorization: Bearer $TOKEN"

# Should return JSON with annotators, approvers, and summary
```

#### Test 2: Check Permissions

```bash
# As regular annotator (should see only own data)
curl http://localhost:8000/v1/projects/1/assignments/completion-matrix/annotators/ \
  -H "Authorization: Bearer $ANNOTATOR_TOKEN"

# As Project Manager (should see all annotators)
curl http://localhost:8000/v1/projects/1/assignments/completion-matrix/annotators/ \
  -H "Authorization: Bearer $MANAGER_TOKEN"
```

#### Test 3: Mark Example Complete

```bash
# Mark example as complete
curl -X POST http://localhost:8000/v1/projects/1/assignments/annotator-completion/123/complete/ \
  -H "Authorization: Bearer $TOKEN"

# Should return: {"message": "Marked as complete", "example_id": 123, "is_completed": true}
```

### 10. Integrate Dashboard into Frontend

#### Option A: Add as Separate Page

Add to your frontend routing:

```javascript
// In your Vue/React router
{
  path: '/projects/:projectId/completion-matrix',
  component: CompletionMatrixDashboard,
  meta: { requiresRole: 'project_manager' }
}
```

#### Option B: Add as Tab in Project View

```javascript
// Add tab to project navigation
{
  name: 'Completion Matrix',
  icon: 'mdi-chart-box',
  to: { name: 'completion-matrix' },
  visible: user.role === 'project_manager' || user.role === 'project_admin'
}
```

### 11. Configure Frontend Integration

Update your frontend to use the status indicators:

```html
<!-- Include the status indicators script -->
<script src="/js/status-indicators.js"></script>

<!-- Use in your annotation view -->
<script>
  const api = new StatusAPI(projectId);
  
  // Show status indicator
  async function showStatus(exampleId) {
    const status = await api.getAnnotatorStatus(exampleId);
    const indicator = new StatusIndicator(
      status.is_completed ? 'completed' : 'in_progress'
    );
    document.getElementById('status').innerHTML = indicator.render();
  }
  
  // Mark complete button
  async function markComplete(exampleId) {
    await api.markComplete(exampleId);
    showStatus(exampleId);
  }
</script>
```

### 12. Restart Doccano

```bash
# If using Docker
docker-compose restart

# If using systemd
sudo systemctl restart doccano

# If running manually
# Stop the server (Ctrl+C) and restart:
python manage.py runserver
```

## Verification Checklist

- [ ] All files copied to correct locations
- [ ] Migrations ran successfully
- [ ] Database tables created
- [ ] URL configuration updated
- [ ] Existing data synced (if applicable)
- [ ] Project Manager users created
- [ ] API endpoints responding correctly
- [ ] Permissions working as expected
- [ ] Frontend dashboard accessible
- [ ] Status indicators displaying correctly

## Troubleshooting

### Issue: Migration fails with "table already exists"

**Solution:**
```bash
# Fake the migration if tables already exist
python manage.py migrate assignment 0002_completion_tracking --fake
```

### Issue: Import errors in Django

**Solution:**
```bash
# Check Python path
python manage.py shell
>>> import assignment.completion_tracking
>>> import assignment.roles
>>> import assignment.completion_views

# If errors, check INSTALLED_APPS in settings
```

### Issue: 404 on API endpoints

**Solution:**
```bash
# Check URL configuration
python manage.py show_urls | grep completion

# Should show:
# /v1/projects/<int:project_id>/assignments/completion-matrix/
# /v1/projects/<int:project_id>/assignments/annotator-completion/<int:example_id>/
# etc.
```

### Issue: Permission denied for all users

**Solution:**
```python
# Check user's role in Django shell
from projects.models import Member
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(username='username')
member = Member.objects.get(user=user, project_id=1)
print(member.role)  # Should be 'project_manager' or 'project_admin'
```

### Issue: Frontend dashboard not loading

**Solution:**
1. Check browser console for errors
2. Verify API endpoints are accessible
3. Check authentication token is valid
4. Ensure user has correct role

## Post-Installation

### 1. Train Your Team

- Show Project Managers how to access the dashboard
- Demonstrate status indicators to annotators
- Train approvers on the new approval workflow

### 2. Monitor Performance

```bash
# Check database query performance
python manage.py shell
>>> from django.db import connection
>>> from django.test.utils import override_settings
>>> with override_settings(DEBUG=True):
...     # Run some queries
...     print(len(connection.queries))
```

### 3. Set Up Backups

Ensure your backup strategy includes the new tables:
- `assignment_annotatorcompletionstatus`
- `assignment_approvercompletionstatus`

### 4. Configure Monitoring

Add monitoring for:
- API endpoint response times
- Database table sizes
- User role distribution

## Next Steps

1. Customize the dashboard styling to match your branding
2. Add additional analytics views
3. Implement email notifications for completion milestones
4. Create reports for management
5. Set up automated data exports

## Support

If you encounter issues:

1. Check the logs: `/var/log/doccano/` or Docker logs
2. Review the troubleshooting section above
3. Check the main README for additional documentation
4. Contact your development team

## Rollback (if needed)

If you need to rollback the installation:

```bash
# Rollback migration
python manage.py migrate assignment 0001_initial

# This will drop the completion tracking tables
# WARNING: This will delete all completion tracking data!
```

To preserve data, export before rollback:

```bash
python manage.py dumpdata assignment.annotatorcompletionstatus > annotator_backup.json
python manage.py dumpdata assignment.approvercompletionstatus > approver_backup.json
```

