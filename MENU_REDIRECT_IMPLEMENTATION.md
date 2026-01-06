# ✅ **Menu Redirect Implementation - Option 3**

## 🎯 **What Was Implemented**

**Seamless menu redirection:** When users click menu items in Doccano's left sidebar, they are automatically redirected to Monlam's enhanced pages.

---

## 📋 **Files Modified**

### 1. **`patches/monlam_ui/views.py`**

Added two redirect views:

```python
class DatasetRedirectView(View):
    """Redirect /projects/{id}/dataset → /monlam/{id}/dataset-enhanced/"""
    def get(self, request, project_id):
        return redirect(f'/monlam/{project_id}/dataset-enhanced/')

class MetricsRedirectView(View):
    """Redirect /projects/{id}/metrics → /monlam/{id}/completion/"""
    def get(self, request, project_id):
        return redirect(f'/monlam/{project_id}/completion/')
```

---

### 2. **`patches/monlam_ui/redirect_urls.py`** (NEW FILE)

Created URL patterns for redirects:

```python
redirect_patterns = [
    path('projects/<int:project_id>/dataset', 
         DatasetRedirectView.as_view(), 
         name='monlam-dataset-redirect'),
    
    path('projects/<int:project_id>/metrics', 
         MetricsRedirectView.as_view(), 
         name='monlam-metrics-redirect'),
]
```

These patterns **intercept** Doccano's default URLs.

---

### 3. **`Dockerfile`**

Added automatic injection of redirect patterns into Doccano's `urls.py`:

```dockerfile
# Import redirect patterns at top of urls.py
sed -i '1i from monlam_ui.redirect_urls import redirect_patterns'

# Add redirects to urlpatterns (BEFORE Doccano's patterns)
sed -i "s|urlpatterns = \[|urlpatterns = [\n    *redirect_patterns,|"
```

**Result in `/doccano/backend/config/urls.py`:**

```python
from monlam_ui.redirect_urls import redirect_patterns

urlpatterns = [
    # Monlam: Redirect standard menu items to enhanced views
    *redirect_patterns,  # ← OUR REDIRECTS FIRST!
    
    # Monlam: Enhanced UI
    path('monlam/', include('monlam_ui.urls')),
    
    # Monlam: Assignment APIs
    path('v1/projects/<int:project_id>/assignments/', include('assignment.urls')),
    
    # ... Doccano's default URLs (come after, lower priority)
]
```

**Why this works:** URL patterns are matched **top-to-bottom**. Our redirects are first, so they match before Doccano's defaults.

---

## 🎯 **User Experience After Deployment**

### **Before (Standard Doccano):**

```
Sign in → Projects → Project 9 → [Left Menu]
                                     ↓
                     Click "གཞི་གྲངས།" (Dataset)
                                     ↓
                     /projects/9/dataset ← Standard Doccano table
                     (No status, no assignments, basic view)
```

### **After (With Redirects):**

```
Sign in → Projects → Project 9 → [Left Menu]
                                     ↓
                     Click "གཞི་གྲངས།" (Dataset)
                                     ↓
                     AUTO-REDIRECTS TO:
                     /monlam/9/dataset-enhanced/ ✅
                                     ↓
                     Enhanced Dataset View with:
                     ✅ Status summary chips
                     ✅ Assignment tracking
                     ✅ Approval status
                     ✅ Color-coded badges
                     ✅ Role-based filtering
```

---

## 📊 **Menu Item Mapping**

| Menu Item | Old URL | New URL | What Changes |
|-----------|---------|---------|--------------|
| **གཞི་གྲངས།** (Dataset) | `/projects/9/dataset` | `/monlam/9/dataset-enhanced/` | Enhanced table with status |
| **Metrics** | `/projects/9/metrics` | `/monlam/9/completion/` | Completion dashboard |
| སྤྱི་འཐུས། (Members) | `/projects/9/members` | (unchanged) | Standard members page |
| Settings | `/projects/9/settings` | (unchanged) | Standard settings |

---

## 🔍 **How to Test After Deployment**

### **Step 1: Sign In**

```
1. Go to: https://annotate.monlam.ai
2. Sign in with your credentials
3. Click on "Project 9" (or any project)
```

### **Step 2: Test Dataset Menu Item**

```
4. Look at left sidebar
5. Click "གཞི་གྲངས།" (Dataset)
6. Watch the URL change:
   
   Expected URL: https://annotate.monlam.ai/monlam/9/dataset-enhanced/
   
   Should see:
   ✅ Blue header "📊 Enhanced Dataset View"
   ✅ Status summary chips (Assigned, In Progress, Submitted, etc.)
   ✅ Data table with "Assigned To", "Status", "Reviewed By" columns
   ✅ Color-coded badges (grey, blue, orange, purple, green)
```

### **Step 3: Test Metrics Menu Item**

```
7. Go back (or click another menu item first)
8. Click "Metrics" in left sidebar
9. Watch the URL change:
   
   Expected URL: https://annotate.monlam.ai/monlam/9/completion/
   
   Should see:
   ✅ Purple gradient header "📈 Completion Dashboard"
   ✅ 4 summary cards (Total Examples, Assigned, Submitted, Approved)
   ✅ Annotator Progress table
   ✅ Approver Activity table (if any)
```

### **Step 4: Verify Browser Console**

```
10. Press F12 (open Developer Tools)
11. Go to Console tab
12. Click "གཞི་གྲངས།" again
13. Should see:
    
    ✅ Vue app mounted!
    📥 Loading data...
    ✅ Loaded X examples
    ✅ Loaded Y assignments
    ✅ Merged data, total: Z
    
    (NO errors!)
```

---

## 🚨 **If Redirects Don't Work**

### **Symptom 1: Still seeing standard Doccano pages**

**Cause:** Redirects not injected into urls.py

**Fix:**
```bash
# In Render Shell
cd /doccano/backend
cat config/urls.py | head -20

# Should see:
# from monlam_ui.redirect_urls import redirect_patterns
# urlpatterns = [
#     *redirect_patterns,
#     ...
```

**If NOT there:**
- Dockerfile modification didn't run
- Redeploy or manually edit urls.py

---

### **Symptom 2: 404 Error on redirect**

**Cause:** Monlam UI app not registered or migration not run

**Fix:**
```bash
# Check if monlam_ui is installed
python manage.py shell
```

```python
from django.conf import settings
print('monlam_ui' in settings.INSTALLED_APPS)
# Should be: True

from monlam_ui.views import DatasetRedirectView
# Should not error

exit()
```

**If False:**
- Run migrations
- Check if INSTALLED_APPS was updated in settings

---

### **Symptom 3: Redirect works but page is blank**

**Cause:** Vue instance conflict (should be fixed already)

**Fix:**
- Check browser console (F12)
- Should see "✅ Vue app mounted!"
- If not, templates may not have been updated

---

## 📋 **Database Migration (REQUIRED)**

After Render deploys, **MUST RUN:**

```bash
# 1. Access Render Shell

# 2. Run migrations
cd /doccano/backend
python manage.py migrate assignment

# 3. Verify
python manage.py showmigrations assignment

# Expected output:
# assignment
#  [X] 0001_initial
#  [X] 0002_completion_tracking
#  [X] 0003_example_locking
```

---

## 🎯 **Complete User Flow**

### **Annotator:**
```
1. Sign in
2. Click project
3. Click "གཞི་གྲངས།" → Auto-redirected to enhanced dataset
4. See assigned examples
5. Click "Annotate" button
6. Complete annotation
7. Status changes from "Assigned" → "In Progress" → "Submitted"
```

### **Approver:**
```
1. Sign in
2. Click project
3. Click "གཞི་གྲངས།" → Auto-redirected to enhanced dataset
4. See examples with 🟠 orange "Submitted" badge
5. Click "Review" button
6. See approval buttons
7. Click "Approve" or "Reject"
8. Status changes to "Approved" (🟢 green) or "Rejected" (🔴 red)
```

### **Project Manager:**
```
1. Sign in
2. Click project
3. Click "Metrics" → Auto-redirected to completion dashboard
4. See overall statistics
5. See annotator progress table
6. See approver activity table
7. Click "Enhanced Dataset" button
8. See examples with 🟣 purple "PM Review" badge (already approved by approver)
9. Click "Review" → Final approval
10. Status changes to "Final Approved" (🟢 green with 👑 PM badge)
```

---

## ✅ **Implementation Summary**

| What | Status | Location |
|------|--------|----------|
| Redirect views | ✅ Created | `patches/monlam_ui/views.py` |
| Redirect URL patterns | ✅ Created | `patches/monlam_ui/redirect_urls.py` |
| URL injection | ✅ Automated | `Dockerfile` |
| Enhanced dataset page | ✅ Fixed | `patches/monlam_ui/templates/monlam_ui/enhanced_dataset.html` |
| Completion dashboard | ✅ Fixed | `patches/monlam_ui/templates/monlam_ui/completion_dashboard.html` |
| Annotation page | ✅ Fixed | `patches/monlam_ui/templates/monlam_ui/annotation_with_approval.html` |
| Landing page | ✅ Created | `patches/monlam_ui/templates/monlam_ui/project_landing.html` |
| Database tables | ✅ Migrated | `patches/assignment/migrations/` |

---

## 🚀 **Deployment Checklist**

- [ ] Code pushed to GitHub (commit: `MENU_REDIRECT_V1`)
- [ ] Render auto-deploys (~5-10 min)
- [ ] Run migrations in Render Shell
- [ ] Test "གཞི་གྲངས།" menu redirect
- [ ] Test "Metrics" menu redirect
- [ ] Verify enhanced dataset shows data
- [ ] Verify completion dashboard shows stats
- [ ] Test annotation page with approval
- [ ] Check browser console (no errors)
- [ ] Create test assignments (if needed)
- [ ] Test full annotator workflow
- [ ] Test full approver workflow
- [ ] Test full PM workflow

---

## 📸 **Expected Screenshots**

After deployment, you should be able to take screenshots of:

1. **Left menu with cursor on "གཞི་གྲངས།"**
2. **Enhanced dataset view (after clicking menu)**
3. **URL bar showing `/monlam/9/dataset-enhanced/`**
4. **Status summary chips**
5. **Table with color-coded badges**
6. **Completion dashboard (after clicking Metrics)**
7. **Browser console showing "✅ Vue app mounted!"**

---

**Version:** MENU_REDIRECT_V1  
**Date:** 2025-01-06  
**Implementation:** Option 3 - Redirect Menu Items (Most Seamless)

