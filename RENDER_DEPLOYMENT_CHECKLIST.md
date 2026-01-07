# ✅ Render Deployment Checklist

## 📋 After Each Render Deployment

Use this checklist to ensure everything works after deployment:

---

## 🚨 **STEP 1: Run Database Migrations** (CRITICAL!)

⚠️ **Do this IMMEDIATELY after Render deploys!**

```bash
# 1. Open Render Dashboard
https://dashboard.render.com/

# 2. Click on your service

# 3. Click "Shell" tab

# 4. Run these commands:
cd /doccano/backend
python manage.py migrate assignment

# 5. Verify migrations applied:
python manage.py showmigrations assignment

# Expected: All migrations should have [X]
# assignment
#  [X] 0001_initial
#  [X] 0002_completion_tracking
#  [X] 0003_example_locking
```

**Why?** Database schema changes don't happen automatically. Without migrations, features will crash.

---

## ✅ **STEP 2: Test Monlam UI Pages**

### **A) Enhanced Dataset View**

```
URL: https://annotate.monlam.ai/monlam/9/dataset-enhanced/
```

**Check:**
- [ ] Page loads without errors
- [ ] Status summary dashboard appears at top
- [ ] Orange "Needs Review" badge shows count
- [ ] Filter tabs work (All, Needs Review, etc.)
- [ ] Table shows examples with status badges
- [ ] Colors are correct (Orange=Submitted, Green=Approved, etc.)
- [ ] Action buttons appear ("Review" or "Annotate")

**If broken:**
- Check browser console (F12) for errors
- Check Render logs for API errors
- Verify migrations ran

---

### **B) Completion Dashboard**

```
URL: https://annotate.monlam.ai/monlam/9/completion/
```

**Check:**
- [ ] Page loads
- [ ] Summary statistics display (Total, Assigned, etc.)
- [ ] Annotator progress table shows data
- [ ] No errors in console

---

### **C) Annotation with Approval**

```
URL: https://annotate.monlam.ai/monlam/9/annotate/2446/
```

**Check:**
- [ ] Page loads
- [ ] Approval status chain appears
- [ ] Shows annotator status
- [ ] Shows approver status
- [ ] [Approve] and [Reject] buttons visible (for approvers/PMs)
- [ ] Audio auto-plays and loops (for STT projects)

---

## ✅ **STEP 3: Test Assignment System**

### **A) Create Test Assignment**

```bash
# In Render Shell
cd /doccano/backend
python manage.py shell

# Then in Python shell:
from django.contrib.auth import get_user_model
from projects.models import Project
from examples.models import Example
from assignment.models_separate import Assignment

User = get_user_model()

# Get project, user, and example
project = Project.objects.get(pk=9)
user = User.objects.get(username='annotator01')  # Replace with real user
example = Example.objects.filter(project=project).first()

# Create assignment
assignment = Assignment.objects.create(
    project=project,
    example=example,
    assigned_to=user,
    assigned_by=user,
    status='assigned'
)

print(f"✅ Created assignment #{assignment.id}")
exit()
```

### **B) Verify Assignment Shows in UI**

```
1. Go to: /monlam/9/dataset-enhanced/
2. Find the example you assigned
3. Check:
   - [ ] "Assigned To" column shows username
   - [ ] "Status" column shows "ASSIGNED"
   - [ ] Status badge is grey
```

---

## ✅ **STEP 4: Test Status Workflow**

### **A) Test Status Change: assigned → submitted**

```bash
# In Render Shell
cd /doccano/backend
python manage.py shell

from assignment.models_separate import Assignment

# Get the assignment
assignment = Assignment.objects.last()  # Or use .get(id=X)

# Change status
assignment.status = 'submitted'
assignment.submitted_at = timezone.now()
assignment.save()

print(f"✅ Changed to submitted")
exit()
```

### **B) Verify in UI**

```
1. Refresh: /monlam/9/dataset-enhanced/
2. Check:
   - [ ] Status badge is now ORANGE "SUBMITTED"
   - [ ] "Needs Review" tab count increased by 1
   - [ ] Warning alert appears: "X examples awaiting review"
   - [ ] Action button changed to orange "Review"
```

### **C) Test Approval**

```
1. Click orange "Review" button
2. Opens annotation page
3. Check:
   - [ ] Approval status chain shows "SUBMITTED"
   - [ ] [Approve] button visible
   - [ ] [Reject] button visible
4. Click [Approve]
5. Check:
   - [ ] Success message appears
   - [ ] Returns to dataset
   - [ ] Example now shows GREEN "APPROVED"
   - [ ] Removed from "Needs Review" tab
   - [ ] Appears in "Approved" tab
```

---

## ✅ **STEP 5: Test Locking Feature**

### **A) Test Example Lock**

**Setup:** Need 2 users (annotator01, annotator02)

1. **Browser 1:** Login as annotator01
2. Navigate to example: `/monlam/9/annotate/2446/`
3. Example should lock to annotator01

4. **Browser 2 (Incognito):** Login as annotator02
5. Try to open SAME example: `/monlam/9/annotate/2446/`
6. Check:
   - [ ] Access denied OR
   - [ ] Message: "Locked by annotator01"

### **B) Test Lock Expiration**

1. Wait 10 minutes (or manually update `locked_at` in database)
2. Browser 2 should now be able to access the example

---

## ✅ **STEP 6: Test Visibility Rules**

### **A) Annotator Sees Only Assigned Examples**

1. Login as annotator01
2. Go to: `/monlam/9/dataset-enhanced/` (or regular dataset)
3. Check:
   - [ ] See only examples assigned to them
   - [ ] Don't see examples assigned to annotator02
   - [ ] Don't see submitted examples (their own!)
   - [ ] See rejected examples (need fixing)

### **B) Approver Sees Only Submitted Examples**

1. Login as approver01
2. Go to: `/monlam/9/dataset-enhanced/`
3. Check:
   - [ ] See submitted examples
   - [ ] See approved examples
   - [ ] See rejected examples
   - [ ] Don't see "assigned" or "in_progress"

### **C) Project Manager Sees Everything**

1. Login as project manager
2. Go to: `/monlam/9/dataset-enhanced/`
3. Check:
   - [ ] See ALL examples (all statuses)
   - [ ] See all users' work
   - [ ] Can access completion dashboard

---

## ✅ **STEP 7: Check API Endpoints**

Test these URLs in browser (must be logged in):

### **A) Assignment API**
```
https://annotate.monlam.ai/v1/projects/9/assignments/

Expected: JSON list of assignments
Should NOT return: "relation does not exist" error
```

### **B) Completion Matrix API**
```
https://annotate.monlam.ai/v1/projects/9/assignments/completion-matrix/summary/

Expected: JSON with total_examples, assigned_examples, etc.
```

### **C) Dataset Assignments API**
```
https://annotate.monlam.ai/monlam/9/api/dataset-assignments/

Expected: JSON list of assignments for dataset view
```

### **D) Completion Stats API**
```
https://annotate.monlam.ai/monlam/9/api/completion-stats/

Expected: JSON with summary, annotators, approvers
```

---

## 🚨 **Common Issues and Fixes**

### **Issue 1: "relation 'assignment_assignment' does not exist"**

**Cause:** Migrations not run.

**Fix:**
```bash
cd /doccano/backend
python manage.py migrate assignment
```

---

### **Issue 2: 404 on /monlam/... pages**

**Cause:** `monlam_ui` app not registered or URLs not included.

**Fix:** Check Dockerfile:
```dockerfile
# Should have:
COPY patches/monlam_ui /doccano/backend/monlam_ui
RUN echo "INSTALLED_APPS += ['monlam_ui']" >> /doccano/backend/config/settings/base.py
```

Redeploy if missing.

---

### **Issue 3: Blank/empty dataset view**

**Cause:** No assignments created yet.

**Fix:** Create assignments (see STEP 3A above).

---

### **Issue 4: Status doesn't update after approve/reject**

**Cause:** API call failing (check console).

**Possible reasons:**
- CSRF token issue
- Permissions issue
- API endpoint not found

**Fix:** Check browser console (F12) and Render logs.

---

### **Issue 5: Audio doesn't loop**

**Cause:** Audio loop script not initialized.

**Fix:** Check `patches/monlam_ui/templates/monlam_ui/annotation_with_approval.html` includes audio loop code.

---

## 📊 **Success Criteria**

All checkboxes above should be ✅ before considering deployment complete.

**Minimum for Production:**
- [ ] Migrations ran successfully
- [ ] Enhanced Dataset View loads and shows data
- [ ] Status workflow works (assigned → submitted → approved)
- [ ] Approvers can see submitted examples
- [ ] Approve/Reject buttons work
- [ ] No errors in Render logs
- [ ] No errors in browser console

---

## 📝 **After Testing, Update Team**

Once everything works:

1. **Email/Message team:**
   ```
   ✅ Deployment complete!
   
   New Features:
   - Enhanced Dataset View: /monlam/{project_id}/dataset-enhanced/
   - Completion Dashboard: /monlam/{project_id}/completion/
   - Annotation Approval: Approve/reject buttons on each example
   
   Approvers: Use "Needs Review" tab to see what needs approval.
   PMs: Check completion dashboard for progress overview.
   ```

2. **Share guides:**
   - APPROVER_WORKFLOW_GUIDE.md
   - ASSIGNMENT_WORKFLOW_GUIDE.md
   - MONLAM_UI_USER_GUIDE.md

---

**Keep this checklist handy for every deployment!** 📋✅

---

**Version:** 1.0  
**Last Updated:** 2025-01-06



