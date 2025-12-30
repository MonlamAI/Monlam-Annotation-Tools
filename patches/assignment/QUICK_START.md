# Quick Start: Completion Tracking System

Get up and running with the custom annotation status tracking system in 5 minutes.

## What You Get

✅ **Per-annotator completion status** - Track each annotator's progress on every example  
✅ **Per-approver approval status** - Track each approver's reviews  
✅ **Visual indicators** - Beautiful status badges and progress bars  
✅ **Project Manager role** - New role with full visibility of completion matrix  
✅ **Admin dashboard** - Comprehensive dashboard for project oversight  

## Quick Install (3 Steps)

### 1. Run Migration

```bash
cd /doccano/backend
python manage.py migrate assignment
```

### 2. Sync Existing Data

```bash
python manage.py shell
```

```python
from assignment.completion_tracking import CompletionMatrixUpdater
from projects.models import Project

for project in Project.objects.all():
    CompletionMatrixUpdater.sync_from_assignments(project)
```

### 3. Create a Project Manager

```python
from projects.models import Project, Member
from django.contrib.auth import get_user_model

User = get_user_model()
project = Project.objects.get(id=1)  # Your project ID
user = User.objects.get(username='manager_username')

Member.objects.update_or_create(
    project=project,
    user=user,
    defaults={'role': 'project_manager'}
)
```

Done! 🎉

## Quick Test

### Test API Access

```bash
# Get your auth token
TOKEN="your_auth_token_here"

# View completion matrix (as Project Manager)
curl http://localhost:8000/v1/projects/1/assignments/completion-matrix/ \
  -H "Authorization: Bearer $TOKEN"
```

### Test in Browser

1. Open: `http://localhost:8000/projects/1/completion-matrix/`
2. Login as Project Manager
3. View the dashboard with all completion data

## Quick Usage Examples

### For Annotators

```javascript
// Mark example as complete
const api = new StatusAPI(projectId);
await api.markComplete(exampleId);
```

### For Approvers

```javascript
// Approve an example
await api.approve(exampleId, "Looks good!");

// Reject an example
await api.reject(exampleId, "Please revise");
```

### For Project Managers

```javascript
// Get complete matrix
const matrix = await api.getCompletionMatrix();

// View summary
console.log(matrix.summary);
// {
//   total_examples: 1000,
//   completed_examples: 620,
//   completion_rate: 62.0,
//   ...
// }
```

## Key Endpoints

| Endpoint | Who Can Access | What It Does |
|----------|----------------|--------------|
| `/completion-matrix/` | PM, Admin | Full completion matrix |
| `/completion-matrix/my/` | Everyone | Your own stats |
| `/completion-matrix/summary/` | Everyone | Project summary |
| `/annotator-completion/{id}/complete/` | Annotators | Mark complete |
| `/approver-completion/{id}/approve/` | Approvers+ | Approve example |

**PM = Project Manager**

## Role Comparison

| Can Do | Annotator | Approver | **Project Manager** | Admin |
|--------|-----------|----------|---------------------|-------|
| Annotate | ✅ | ✅ | ✅ | ✅ |
| Approve | ❌ | ✅ | ✅ | ✅ |
| **See full matrix** | ❌ | ❌ | **✅** | ✅ |
| Assign tasks | ❌ | ❌ | ❌ | ✅ |

**Key:** Project Manager = Approver + Full Matrix Visibility

## Visual Indicators

The system uses color-coded status indicators:

- 🔴 **Red** - Low progress (0-49%)
- 🟠 **Orange** - Medium progress (50-79%)
- 🟢 **Green** - High progress (80-100%)

Status icons:
- ○ Pending
- ◐ In Progress
- ✓ Completed
- ✓✓ Approved
- ✗ Rejected

## Common Tasks

### View Your Progress

```bash
curl http://localhost:8000/v1/projects/1/assignments/completion-matrix/my/ \
  -H "Authorization: Bearer $TOKEN"
```

### Export Data

```bash
curl http://localhost:8000/v1/projects/1/assignments/completion-matrix/export/ \
  -H "Authorization: Bearer $TOKEN" > completion_matrix.csv
```

### Sync After Bulk Changes

```bash
curl -X POST http://localhost:8000/v1/projects/1/assignments/completion-matrix/sync/ \
  -H "Authorization: Bearer $TOKEN"
```

## Dashboard Features

The Project Manager dashboard shows:

1. **Summary Cards**
   - Total examples
   - Completion rate
   - Approval rate
   - Pending work

2. **Annotator Matrix**
   - Each annotator's progress
   - Completion percentages
   - Status breakdown

3. **Approver Matrix**
   - Each approver's reviews
   - Approval rates
   - Pending reviews

4. **Export Function**
   - Download as CSV
   - Full data export

## Troubleshooting

### "Permission denied"
→ Check user has `project_manager` or `project_admin` role

### "404 Not Found"
→ Verify URLs are configured in `config/urls.py`

### Data not showing
→ Run sync: `CompletionMatrixUpdater.sync_from_assignments(project)`

### Migration errors
→ Check database connection and run: `python manage.py migrate --fake-initial`

## Next Steps

1. ✅ Read full documentation: `COMPLETION_TRACKING_README.md`
2. ✅ Follow detailed installation: `INSTALLATION_GUIDE.md`
3. ✅ Customize the dashboard UI
4. ✅ Train your team on the new features
5. ✅ Set up monitoring and backups

## Need Help?

- 📖 Full docs: `COMPLETION_TRACKING_README.md`
- 🔧 Installation: `INSTALLATION_GUIDE.md`
- 💬 Issues: Check logs in `/var/log/doccano/`

## Files Overview

```
patches/assignment/
├── completion_tracking.py      # Core models
├── roles.py                    # Permission system
├── completion_views.py         # API endpoints
├── completion_serializers.py   # REST serializers
├── urls.py                     # URL routing
├── migrations/
│   └── 0002_completion_tracking.py
└── docs/
    ├── COMPLETION_TRACKING_README.md
    ├── INSTALLATION_GUIDE.md
    └── QUICK_START.md (this file)

patches/frontend/
├── completion-matrix.html      # Dashboard UI
└── status-indicators.js        # UI components

branding/i18n/bo/projects/
├── completion.js              # Tibetan translations
└── members.js                 # Updated with PM role
```

## Quick Reference Card

```
┌─────────────────────────────────────────────────────┐
│  COMPLETION TRACKING QUICK REFERENCE                │
├─────────────────────────────────────────────────────┤
│  Roles:                                             │
│    • Annotator      - Can annotate                  │
│    • Approver       - Can approve                   │
│    • Project Mgr    - Can see full matrix          │
│    • Admin          - Can do everything             │
├─────────────────────────────────────────────────────┤
│  Key Endpoints:                                     │
│    GET  /completion-matrix/        Full matrix     │
│    GET  /completion-matrix/my/     My stats        │
│    POST /annotator-completion/{id}/complete/       │
│    POST /approver-completion/{id}/approve/         │
├─────────────────────────────────────────────────────┤
│  Status Colors:                                     │
│    🔴 0-49%   🟠 50-79%   🟢 80-100%               │
├─────────────────────────────────────────────────────┤
│  Quick Sync:                                        │
│    CompletionMatrixUpdater.sync_from_assignments() │
└─────────────────────────────────────────────────────┘
```

---

**Ready to go!** Your completion tracking system is now set up. 🚀

