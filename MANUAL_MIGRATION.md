# Manual Migration Guide

## Why Manual Migration is Needed

The `assignment` app migrations cannot run during Docker build because:
1. No database connection exists during build
2. Foreign keys reference `projects.Project` which doesn't exist yet
3. Migrations must run at **runtime** when database is available

## How to Run Migrations (One-Time Setup)

### Method 1: Via Render Shell (Recommended)

1. **Go to Render Dashboard**
2. **Click your Web Service**
3. **Click "Shell" tab** (opens a terminal in the running container)
4. **Run this command:**
   ```bash
   python manage.py migrate assignment --noinput
   ```

5. **Verify migrations ran:**
   ```bash
   python manage.py showmigrations assignment
   ```
   
   Should show:
   ```
   assignment
    [X] 0001_initial
    [X] 0002_completion_tracking
   ```

### Method 2: Via Render Manual Deploy

Add a one-time migration command:

1. Go to Render Dashboard → Your Service
2. Click "Manual Deploy"
3. In the deploy dialog, add a **Post-Deploy Command:**
   ```bash
   python manage.py migrate assignment --noinput
   ```
4. Deploy

This will run migrations automatically after each deploy.

## Verification

After running migrations, test the API:

```javascript
// In browser console at https://annotate.monlam.ai
fetch('/v1/projects/9/assignments/completion-matrix/summary/')
  .then(r => r.json())
  .then(d => console.log('✅ API works!', d))
  .catch(e => console.error('❌ Failed:', e));
```

Should return:
```json
{
  "annotators": [],
  "approvers": [],
  "project_summary": {
    "total_examples": X,
    "completed_examples": Y,
    ...
  }
}
```

## Tables Created

The migration creates these tables:
- `assignment_assignment` - Task assignments
- `assignment_assignmentbatch` - Bulk assignment tracking
- `assignment_annotatorcompletionstatus` - Annotator progress per example
- `assignment_approvercompletionstatus` - Approver review status per example

## Troubleshooting

### Error: "relation already exists"
The tables were already created. Run:
```bash
python manage.py migrate assignment --fake
```

### Error: "no such table: django_migrations"
The database isn't initialized. Wait for Doccano to start fully, then try again.

### Error: "cannot import name Assignment"
The assignment app isn't in INSTALLED_APPS. Check:
```bash
python -c "from django.conf import settings; print('assignment' in settings.INSTALLED_APPS)"
```

Should print: `True`







