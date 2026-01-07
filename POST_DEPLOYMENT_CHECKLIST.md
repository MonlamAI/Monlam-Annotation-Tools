# ✅ Post-Deployment Checklist & Database Updates

## 📋 **After Render Deploys - Complete Checklist**

Use this checklist **every time** you deploy to Render.

---

## 🗄️ **DATABASE MIGRATIONS REQUIRED**

### ⚠️ **CRITICAL: Run These Commands After EVERY Deployment**

```bash
# 1. Access Render Shell
# Dashboard → Your Service → Shell tab

# 2. Navigate to backend
cd /doccano/backend

# 3. Check migration status
python manage.py showmigrations assignment

# Expected output:
# assignment
#  [X] 0001_initial
#  [X] 0002_completion_tracking
#  [X] 0003_example_locking

# 4. If any show [ ], run migrations:
python manage.py migrate assignment

# 5. Verify all are [X]:
python manage.py showmigrations assignment
```

---

## 📊 **Database Tables Created**

After running migrations, these tables exist:

| Table Name | Purpose | Key Fields |
|------------|---------|------------|
| `assignment_assignment` | Main assignments | `example_id`, `assigned_to_id`, `status`, `locked_by_id`, `locked_at` |
| `assignment_annotatorcompletionstatus` | Per-example annotator tracking | `example_id`, `annotator_id`, `status`, `completed_at` |
| `assignment_approvercompletionstatus` | Per-example approval tracking | `example_id`, `approver_id`, `status`, `reviewed_at` |
| `assignment_assignmentbatch` | Bulk assignment tracking | `project_id`, `assigned_by_id`, `example_count` |

---

## 🔍 **Verification Steps**

### **Step 1: Verify Tables Exist**

```bash
python manage.py shell
```

```python
from assignment.models_separate import Assignment
from django.db import connection

# Check if tables exist
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name LIKE 'assignment_%';
    """)
    tables = cursor.fetchall()
    print(f"Assignment tables: {tables}")

# Should show 4 tables

# Check if locking fields exist
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='assignment_assignment' 
        AND column_name IN ('locked_by_id', 'locked_at');
    """)
    columns = cursor.fetchall()
    print(f"Locking columns: {columns}")

# Should show: [('locked_at',), ('locked_by_id',)]

print("✅ Database verified!")
exit()
```

---

### **Step 2: Test URLs**

**Test these URLs in your browser (logged in):**

| URL | Expected Result |
|-----|-----------------|
| `/monlam/9/` | Project landing page with cards |
| `/monlam/9/dataset-enhanced/` | Enhanced dataset view |
| `/monlam/9/completion/` | Completion dashboard |
| `/monlam/9/api/dataset-assignments/` | JSON with assignments |
| `/v1/projects/9/assignments/` | JSON with assignments (DRF API) |

**All should return 200 OK (not 404 or 500).**

---

### **Step 3: Test Creating Assignment**

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from projects.models import Project
from examples.models import Example
from assignment.models_separate import Assignment

User = get_user_model()

# Get project and user
project = Project.objects.get(pk=9)
user = User.objects.first()

print(f"Project: {project.name}")
print(f"User: {user.username}")

# Get one example
example = Example.objects.filter(project=project).first()

# Create test assignment
assignment = Assignment.objects.create(
    project=project,
    example=example,
    assigned_to=user,
    assigned_by=user,
    status='assigned'
)

print(f"✅ Created assignment #{assignment.id}")
print(f"   Example: {example.id}")
print(f"   Assigned to: {user.username}")
print(f"   Status: {assignment.status}")
print(f"   Can lock? locked_by={assignment.locked_by}, locked_at={assignment.locked_at}")

exit()
```

**Expected:** No errors, assignment created successfully.

---

### **Step 4: Test Enhanced Dataset UI**

1. **Open:** `https://annotate.monlam.ai/monlam/9/dataset-enhanced/`

2. **Check for:**
   - [ ] Page loads (not blank)
   - [ ] Blue header visible
   - [ ] Status summary chips show
   - [ ] Table visible (might be empty)
   - [ ] No console errors (F12)

3. **Browser Console (F12 → Console) should show:**
   ```
   ✅ Vue app mounted!
   📥 Loading data...
   ✅ Loaded X examples
   ✅ Loaded Y assignments
   ```

4. **If table is empty:**
   - Create assignments (Step 3 above)
   - Refresh page
   - Table should show data

---

### **Step 5: Test Landing Page**

1. **Open:** `https://annotate.monlam.ai/monlam/9/`

2. **Check for:**
   - [ ] Purple hero header
   - [ ] 4 cards: Enhanced Dataset, Dashboard, Standard, Quick Links
   - [ ] All buttons clickable
   - [ ] Links work

---

## 🔧 **Common Issues & Fixes**

### **Issue 1: Blank Enhanced Dataset Page**

**Check:**
```bash
# In browser console (F12)
# Look for errors
```

**Fix:**
- Check Render logs for errors
- Verify template exists: `/doccano/backend/monlam_ui/templates/monlam_ui/enhanced_dataset.html`

---

### **Issue 2: 404 on `/monlam/...` URLs**

**Cause:** URLs not registered

**Fix:**
```bash
python manage.py shell
```

```python
from django.urls import get_resolver
resolver = get_resolver()

for pattern in resolver.url_patterns:
    if 'monlam' in str(pattern.pattern):
        print(f"✅ Found: {pattern.pattern}")

# Should show: monlam/
```

**If not found:**
- Check `/doccano/backend/config/urls.py` includes `monlam_ui.urls`

---

### **Issue 3: Relation Does Not Exist Error**

**Error:** `relation "assignment_assignment" does not exist`

**Cause:** Migrations not run

**Fix:**
```bash
cd /doccano/backend
python manage.py migrate assignment
```

---

### **Issue 4: Column Does Not Exist**

**Error:** `column "locked_by_id" does not exist`

**Cause:** Migration 0003 not applied

**Fix:**
```bash
python manage.py migrate assignment 0003
```

---

## 📝 **Data Population (Optional)**

### **Create Sample Assignments**

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from projects.models import Project
from examples.models import Example
from assignment.models_separate import Assignment
from django.utils import timezone

User = get_user_model()

project = Project.objects.get(pk=9)
user = User.objects.first()

# Get 10 examples
examples = Example.objects.filter(project=project)[:10]

# Create assignments with different statuses
for i, ex in enumerate(examples):
    if i < 3:
        status = 'assigned'
    elif i < 5:
        status = 'in_progress'
        started_at = timezone.now()
    elif i < 7:
        status = 'submitted'
        submitted_at = timezone.now()
    elif i < 9:
        status = 'approved'
    else:
        status = 'rejected'
    
    assignment, created = Assignment.objects.get_or_create(
        project=project,
        example=ex,
        defaults={
            'assigned_to': user,
            'assigned_by': user,
            'status': status,
        }
    )
    
    if created:
        if status == 'in_progress':
            assignment.started_at = timezone.now()
        elif status == 'submitted':
            assignment.submitted_at = timezone.now()
        assignment.save()
        print(f"✓ {ex.id} → {status}")

print("\n✅ Created 10 sample assignments with varied statuses")
exit()
```

**Now refresh enhanced dataset - should see all statuses!**

---

## 🎯 **Complete Deployment Workflow**

```
1. Code changes locally
   ↓
2. Git commit & push to GitHub
   ↓
3. Render auto-deploys (5-10 min)
   ↓
4. ⚠️ RUN MIGRATIONS ⚠️
   python manage.py migrate assignment
   ↓
5. Verify database (Step 1)
   ↓
6. Test URLs (Step 2)
   ↓
7. Create test data (Step 3, 4)
   ↓
8. Test UI (Step 5)
   ↓
9. ✅ DONE!
```

---

## 📊 **Current Deployment Status**

**Latest Features:**
- ✅ Enhanced Dataset View (standalone template)
- ✅ Project Landing Page
- ✅ Two-level approval chain
- ✅ Example locking
- ✅ Status-based visibility

**URLs Available:**
- `/monlam/9/` - Landing page ⭐
- `/monlam/9/dataset-enhanced/` - Enhanced dataset
- `/monlam/9/completion/` - Completion dashboard
- `/monlam/9/annotate/{id}/` - Annotation with approval

---

## ✅ **Final Checklist**

After deployment, mark these as complete:

- [ ] Migrations run (`showmigrations` shows all [X])
- [ ] Database verified (tables exist, columns exist)
- [ ] Landing page works (`/monlam/9/`)
- [ ] Enhanced dataset works (`/monlam/9/dataset-enhanced/`)
- [ ] Dashboard works (`/monlam/9/completion/`)
- [ ] APIs work (`/monlam/9/api/dataset-assignments/`)
- [ ] Sample assignments created
- [ ] UI shows data correctly
- [ ] No errors in browser console
- [ ] No errors in Render logs

---

## 🆘 **Need Help?**

**If something doesn't work:**

1. Check Render logs (Dashboard → Logs tab)
2. Check browser console (F12 → Console)
3. Run verification steps above
4. Check migrations status
5. Create test data

**All issues are usually:**
- Migrations not run
- No test data created
- Caching (clear browser cache)

---

**Version:** 1.0  
**Last Updated:** 2025-01-06



