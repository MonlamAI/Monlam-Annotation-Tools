# Custom Annotation Status Tracking System

A comprehensive completion tracking system with Project Manager role for Monlam Doccano.

## ✅ Features Implemented

### 1. Per-Annotator Completion Status
- ✅ Track individual annotator's completion status on each example
- ✅ Record completion timestamps and annotation counts
- ✅ Support for marking examples as complete/incomplete
- ✅ Historical tracking of completion changes

### 2. Per-Approver Approval Status
- ✅ Track individual approver's approval status on each example
- ✅ Support for approved/rejected/pending states
- ✅ Review notes and timestamps
- ✅ Multiple approvers can review the same example

### 3. Visual Indicators in UI
- ✅ Status badges with color coding
- ✅ Progress bars with percentage
- ✅ Status icons (○ pending, ◐ in-progress, ✓ completed, ✗ rejected)
- ✅ Multi-user status indicators
- ✅ Example status cards

### 4. Admin Dashboard (Completion Matrix)
- ✅ Full-featured dashboard for Project Managers
- ✅ Summary cards with key metrics
- ✅ Annotator completion matrix
- ✅ Approver completion matrix
- ✅ Export to CSV functionality
- ✅ Real-time status updates

### 5. Project Manager Role
- ✅ New role with same features as Approver + full matrix visibility
- ✅ Permission system with role hierarchy
- ✅ Can view all annotators' and approvers' completion status
- ✅ Access to comprehensive completion matrix
- ✅ Cannot assign tasks (unlike Project Admin)

## 📁 Files Created

### Backend Files

1. **`completion_tracking.py`** - Core models and utilities
   - `AnnotatorCompletionStatus` model
   - `ApproverCompletionStatus` model
   - `CompletionMatrix` utility class
   - `CompletionMatrixUpdater` helper class

2. **`roles.py`** - Role and permission system
   - `ROLE_PROJECT_MANAGER` constant
   - `ProjectManagerMixin` for role checks
   - `IsProjectManager` permission class
   - `IsApproverOrHigher` permission class
   - `CanViewCompletionMatrix` permission class
   - Role capabilities mapping

3. **`completion_views.py`** - API endpoints
   - `CompletionMatrixViewSet` - Full matrix views
   - `AnnotatorCompletionViewSet` - Annotator status tracking
   - `ApproverCompletionViewSet` - Approver status tracking

4. **`completion_serializers.py`** - REST serializers
   - Serializers for all completion tracking models
   - Matrix data serializers
   - Action serializers

5. **`urls.py`** - Updated with new endpoints
   - Completion matrix URLs
   - Per-example completion tracking URLs

6. **`migrations/0002_completion_tracking.py`** - Database migration
   - Creates completion tracking tables
   - Adds indexes and constraints

### Frontend Files

1. **`completion-matrix.html`** - Dashboard UI
   - Full-featured Project Manager dashboard
   - Summary cards
   - Annotator and approver matrices
   - Visual indicators
   - Export functionality

2. **`status-indicators.js`** - UI components
   - `StatusIndicator` component
   - `CompletionBadge` component
   - `MultiUserStatusIndicator` component
   - `ExampleStatusCard` component
   - `StatusAPI` helper class
   - `StatusAutoUpdater` for real-time updates

### Internationalization

1. **`branding/i18n/bo/projects/completion.js`** - Tibetan translations
   - All completion tracking UI strings
   - Status labels
   - Action labels
   - Messages

2. **`branding/i18n/bo/projects/members.js`** - Updated with Project Manager role
   - Added `projectManager` role translation
   - Added role descriptions

## 🚀 Installation

### Step 1: Copy Files

```bash
# Already in patches/assignment/ directory
# No additional copying needed if using the patches structure
```

### Step 2: Update Doccano Configuration

Add to `/doccano/backend/config/settings/base.py`:

```python
INSTALLED_APPS = [
    # ... existing apps ...
    'assignment',  # Should already be added
]
```

### Step 3: Run Migrations

```bash
cd /doccano/backend
python manage.py migrate assignment
```

### Step 4: Sync Existing Data (Optional)

If you have existing assignments, sync them to the completion tracking system:

```bash
# Via Django shell
python manage.py shell

from assignment.completion_tracking import CompletionMatrixUpdater
from projects.models import Project

# Sync all projects
for project in Project.objects.all():
    CompletionMatrixUpdater.sync_from_assignments(project)
```

Or via API (Project Admin only):

```bash
curl -X POST http://localhost:8000/v1/projects/{project_id}/assignments/completion-matrix/sync/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📡 API Endpoints

### Completion Matrix (Project Manager Dashboard)

#### Get Complete Matrix
```http
GET /v1/projects/{project_id}/assignments/completion-matrix/
```
**Permission:** Project Manager or Admin only

**Response:**
```json
{
  "project_id": 1,
  "project_name": "Tibetan Speech Transcription",
  "annotators": [
    {
      "annotator_id": 5,
      "annotator_username": "tenzin",
      "total_assigned": 200,
      "completed": 150,
      "in_progress": 30,
      "submitted": 100,
      "approved": 80,
      "completion_rate": 75.0,
      "examples": [...]
    }
  ],
  "approvers": [
    {
      "approver_id": 3,
      "approver_username": "karma",
      "total_to_review": 300,
      "approved": 200,
      "rejected": 30,
      "pending": 70,
      "approval_rate": 66.7,
      "examples": [...]
    }
  ],
  "summary": {
    "total_examples": 1000,
    "assigned_examples": 850,
    "completed_examples": 620,
    "approved_examples": 480,
    "completion_rate": 62.0,
    "approval_rate": 48.0
  }
}
```

#### Get Annotator Matrix
```http
GET /v1/projects/{project_id}/assignments/completion-matrix/annotators/
```
**Permission:** Project Manager sees all, others see own data

#### Get Approver Matrix
```http
GET /v1/projects/{project_id}/assignments/completion-matrix/approvers/
```
**Permission:** Project Manager sees all, Approvers see own data

#### Get My Stats
```http
GET /v1/projects/{project_id}/assignments/completion-matrix/my/
```
**Permission:** All project members

**Response:**
```json
{
  "user_id": 5,
  "username": "tenzin",
  "role": "annotator",
  "annotator_stats": {
    "total_assigned": 200,
    "completed": 150,
    "in_progress": 50
  },
  "approver_stats": {
    "total_to_review": 0,
    "approved": 0,
    "rejected": 0,
    "pending": 0
  }
}
```

#### Get Project Summary
```http
GET /v1/projects/{project_id}/assignments/completion-matrix/summary/
```
**Permission:** All project members

#### Export Matrix as CSV
```http
GET /v1/projects/{project_id}/assignments/completion-matrix/export/
```
**Permission:** Project Manager or Admin only

### Per-Example Completion Tracking

#### Get Annotator Completion Status
```http
GET /v1/projects/{project_id}/assignments/annotator-completion/{example_id}/
```

#### Mark Example as Complete
```http
POST /v1/projects/{project_id}/assignments/annotator-completion/{example_id}/complete/
```

#### Mark Example as Incomplete
```http
POST /v1/projects/{project_id}/assignments/annotator-completion/{example_id}/incomplete/
```

#### Get Approver Completion Status
```http
GET /v1/projects/{project_id}/assignments/approver-completion/{example_id}/
```

#### Approve Example
```http
POST /v1/projects/{project_id}/assignments/approver-completion/{example_id}/approve/
Content-Type: application/json

{
  "notes": "Looks good!"
}
```

#### Reject Example
```http
POST /v1/projects/{project_id}/assignments/approver-completion/{example_id}/reject/
Content-Type: application/json

{
  "notes": "Please fix the transcription"
}
```

## 👥 Role Comparison

| Feature | Annotator | Approver | Project Manager | Project Admin |
|---------|-----------|----------|-----------------|---------------|
| Annotate examples | ✅ | ✅ | ✅ | ✅ |
| View own assignments | ✅ | ✅ | ✅ | ✅ |
| View own completion | ✅ | ✅ | ✅ | ✅ |
| Approve/reject | ❌ | ✅ | ✅ | ✅ |
| View approval queue | ❌ | ✅ | ✅ | ✅ |
| **View full completion matrix** | ❌ | ❌ | **✅** | ✅ |
| **View all annotators' progress** | ❌ | ❌ | **✅** | ✅ |
| **View all approvers' stats** | ❌ | ❌ | **✅** | ✅ |
| Assign tasks | ❌ | ❌ | ❌ | ✅ |
| Manage project settings | ❌ | ❌ | ❌ | ✅ |
| Delete project | ❌ | ❌ | ❌ | ✅ |

**Key Difference:** Project Manager has the same approval capabilities as Approver, but can see the complete completion matrix for all team members. They cannot assign tasks or manage project settings (unlike Project Admin).

## 🎨 Visual Indicators

### Status Colors

- **Pending/Not Started:** Gray (○)
- **In Progress:** Orange (◐)
- **Submitted:** Cyan (✓)
- **Completed:** Green (✓)
- **Approved:** Blue (✓✓)
- **Rejected:** Red (✗)

### Progress Bars

- **0-49%:** Red (Low)
- **50-79%:** Orange (Medium)
- **80-100%:** Green (High)

## 🔧 Integration with Existing Assignment System

The completion tracking system integrates seamlessly with the existing assignment system:

1. **Automatic Updates:** When assignments change status, completion tracking is automatically updated
2. **Backward Compatible:** Existing assignments continue to work without modification
3. **Sync Utility:** Use `CompletionMatrixUpdater.sync_from_assignments()` to migrate existing data
4. **Non-Invasive:** Completion tracking is in separate tables, doesn't modify core models

## 📊 Usage Examples

### For Annotators

```javascript
// Mark example as complete after annotation
const api = new StatusAPI(projectId);
await api.markComplete(exampleId);

// Check own completion status
const status = await api.getAnnotatorStatus(exampleId);
console.log(status.is_completed); // true/false
```

### For Approvers

```javascript
// Approve an example
const api = new StatusAPI(projectId);
await api.approve(exampleId, "Great work!");

// Reject an example
await api.reject(exampleId, "Please revise the transcription");
```

### For Project Managers

```javascript
// Get complete matrix
const api = new StatusAPI(projectId);
const matrix = await api.getCompletionMatrix();

// View all annotators
matrix.annotators.forEach(annotator => {
  console.log(`${annotator.annotator_username}: ${annotator.completion_rate}%`);
});

// View all approvers
matrix.approvers.forEach(approver => {
  console.log(`${approver.approver_username}: ${approver.approval_rate}%`);
});
```

## 🔄 Auto-Update Status Indicators

Enable real-time status updates in the UI:

```javascript
// Start auto-updating every 30 seconds
const updater = new StatusAutoUpdater(projectId, 30000);
updater.start();

// Stop auto-updating
updater.stop();
```

## 🌐 Accessing the Dashboard

### For Project Managers

1. Navigate to your project
2. Go to the "Completion Matrix" tab (or integrate the dashboard into your UI)
3. View the complete matrix with all annotators and approvers
4. Export data as CSV for reporting

### URL Structure

```
/projects/{project_id}/completion-matrix/
```

## 🐛 Troubleshooting

### Issue: "Only Project Managers can view the complete matrix"

**Solution:** Ensure the user has the `project_manager` or `project_admin` role in the project.

### Issue: Completion tracking not updating

**Solution:** Run the sync command:
```bash
curl -X POST http://localhost:8000/v1/projects/{project_id}/assignments/completion-matrix/sync/
```

### Issue: Permission denied errors

**Solution:** Check user's role with:
```http
GET /v1/projects/{project_id}/assignments/completion-matrix/my/
```

## 📝 Database Schema

### AnnotatorCompletionStatus Table

| Column | Type | Description |
|--------|------|-------------|
| id | BigInt | Primary key |
| example_id | ForeignKey | Reference to Example |
| project_id | ForeignKey | Reference to Project |
| annotator_id | ForeignKey | Reference to User |
| assignment_id | ForeignKey | Reference to Assignment (nullable) |
| is_completed | Boolean | Completion status |
| completed_at | DateTime | Completion timestamp |
| annotation_count | Integer | Number of annotations |

**Indexes:**
- `(project, annotator, is_completed)`
- `(example, is_completed)`

**Constraints:**
- Unique: `(example, annotator)`

### ApproverCompletionStatus Table

| Column | Type | Description |
|--------|------|-------------|
| id | BigInt | Primary key |
| example_id | ForeignKey | Reference to Example |
| project_id | ForeignKey | Reference to Project |
| approver_id | ForeignKey | Reference to User |
| assignment_id | ForeignKey | Reference to Assignment (nullable) |
| status | CharField | pending/approved/rejected |
| reviewed_at | DateTime | Review timestamp |
| review_notes | TextField | Review comments |

**Indexes:**
- `(project, approver, status)`
- `(example, status)`

**Constraints:**
- Unique: `(example, approver)`

## 🎯 Next Steps

1. **Integrate Dashboard:** Add the completion matrix dashboard to your Doccano frontend
2. **Add Role Management:** Update user management UI to support Project Manager role
3. **Customize Visuals:** Adjust colors and styling to match your branding
4. **Add Notifications:** Implement notifications for completion milestones
5. **Add Analytics:** Create additional analytics views for deeper insights

## 📞 Support

For issues or questions about this implementation, refer to the main Monlam Doccano repository or contact the development team.

## 📄 License

This implementation is part of Monlam Doccano and follows the same license as the main project.

