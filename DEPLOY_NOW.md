# 🚀 **Deployment Guide - Everything Ready!**

## ✅ **What's Been Pushed to GitHub:**

| Commit | Description |
|--------|-------------|
| 1️⃣ `6eee5e4` | Simple tracking system + visibility + locking + fixed metrics |
| 2️⃣ `083704f` | Dockerfile integration for tracking system |

**Status:** ✅ All code pushed to `main` branch

---

## 📦 **What Render Will Deploy:**

### **Backend Changes:**

1. **New Database Table:** `annotation_tracking`
   - Tracks who annotated, who reviewed
   - Example locking (5-minute locks)
   - Status tracking (pending/submitted/approved/rejected)

2. **Visibility Filtering:**
   - Annotators see: Unannotated + own rejected
   - Reviewers see: ALL examples
   - First-come-first-serve (no assignments)

3. **New API Endpoints:**
   ```
   POST /v1/projects/{id}/tracking/{example_id}/approve/
   POST /v1/projects/{id}/tracking/{example_id}/reject/
   GET  /v1/projects/{id}/tracking/{example_id}/status/
   POST /v1/projects/{id}/tracking/{example_id}/lock/
   POST /v1/projects/{id}/tracking/{example_id}/unlock/
   ```

### **Frontend Changes:**

4. **Metrics Redirect Fix:**
   - Now works on first click (not just refresh)
   - Intercepts before Vue Router

5. **Dataset Columns:**
   - Position 4: Annotated By
   - Position 5: Reviewed By
   - Position 6: Status (colored badge)

6. **Approve/Reject Buttons:**
   - On annotation page
   - Underneath label box
   - Auto-advance after action

---

## 🔧 **Render Deployment Process:**

### **Step 1: Render Auto-Detects Changes** ⏳

Render will:
1. Pull latest code from GitHub
2. Build new Docker image
3. Apply Dockerfile changes:
   - Copy tracking files
   - Register tracking URLs
   - Apply visibility filter
4. Start new container
5. Run health checks

**Expected Time:** 5-10 minutes

### **Step 2: Wait for "Live" Status** ⏰

Watch Render dashboard:
- ⏳ "Building..." → Docker image being created
- ⏳ "Deploying..." → Container starting
- ✅ "Live" → Deployment successful!

---

## 🗄️ **Step 3: Run Database Migration** (CRITICAL!)

**After Render shows "Live":**

1. Open Render Dashboard
2. Click your service: `monlam-doccano`
3. Click **"Shell"** button (top right)
4. Run this command:

```bash
python manage.py migrate assignment --noinput
```

**Expected Output:**
```
Running migrations:
  Applying assignment.0005_annotation_tracking... OK
```

**What This Does:**
- Creates `annotation_tracking` table in PostgreSQL
- Adds indexes for performance
- Enables all tracking features

**⚠️ IMPORTANT:** Features won't work until migration is run!

---

## ✅ **Step 4: Test Features**

After migration, test these:

### **Test 1: Metrics Redirect** 🔄
```
1. Login to https://annotate.monlam.ai
2. Open any project
3. Click "Metrics" in left menu
4. Should redirect IMMEDIATELY (no refresh needed) ✅
5. Should show completion dashboard
```

### **Test 2: Dataset Columns** 📊
```
1. Go to dataset page
2. Look at columns 4, 5, 6
3. Should see:
   - Column 4: Annotated By (username or —)
   - Column 5: Reviewed By (username or —)
   - Column 6: Status (colored badge) ✅
4. Data should be from database
```

### **Test 3: Example Visibility** 👁️
```
As Annotator A:
1. Annotate example #5
2. Save
3. Go back to dataset
4. Example #5 should be HIDDEN ✅

As Annotator B:
1. Go to dataset
2. Example #5 should be HIDDEN ✅
3. Can only see unannotated examples

As Reviewer/PM:
1. Go to dataset
2. Example #5 should be VISIBLE ✅
3. Can see ALL examples
```

### **Test 4: Example Locking** 🔒
```
As Annotator A:
1. Open example #10 (click Annotate)
2. Example locks automatically

As Annotator B (simultaneously):
1. Try to open example #10
2. Should see "locked by Annotator A" ✅
OR
3. Example hidden from list (already being edited)

After 5 minutes OR Annotator A closes:
1. Example unlocks
2. Available for others
```

### **Test 5: Approve/Reject Buttons** ✅❌
```
As Reviewer:
1. Go to annotation page of submitted example
2. Look underneath label box
3. Should see:
   ┌─────────────────────────────────────┐
   │ ⏳ Review Status                    │
   │ Annotated by: john_doe              │
   │ Reviewed by: Not yet                │
   │ Status: SUBMITTED                   │
   │                                      │
   │  [✓ Approve]     [✗ Reject]         │
   └─────────────────────────────────────┘
4. Click Approve
5. Should save to database ✅
6. Should auto-advance to next example
```

---

## 📊 **Verification Queries**

After migration, verify in database:

### **Check Table Exists:**
```sql
\d annotation_tracking
```

**Expected:**
```
Table "public.annotation_tracking"
Column          | Type                     | Nullable
----------------|--------------------------|----------
id              | bigint                   | not null
project_id      | integer                  | not null
example_id      | integer                  | not null
annotated_by_id | integer                  | 
annotated_at    | timestamp with time zone | 
reviewed_by_id  | integer                  | 
reviewed_at     | timestamp with time zone | 
status          | character varying(20)    | 
locked_by_id    | integer                  | 
locked_at       | timestamp with time zone | 
review_notes    | text                     | 
```

### **Check Initial Data:**
```sql
SELECT COUNT(*) FROM annotation_tracking;
```

**Expected:** `0` (no data yet - will be created as users annotate)

---

## 🐛 **Troubleshooting:**

### **Problem: "Table annotation_tracking does not exist"**

**Solution:**
```bash
# Run migration
python manage.py migrate assignment --noinput

# Verify
python manage.py showmigrations assignment
```

### **Problem: "Metrics redirect doesn't work"**

**Solution:**
1. Clear browser cache: Ctrl+Shift+R (or Cmd+Shift+R)
2. Hard refresh the page
3. Try in incognito/private window

### **Problem: "Dataset columns don't show"**

**Check:**
```bash
# Verify tracking API is registered
grep "tracking.urls" /doccano/backend/config/urls.py

# Should output:
# path('v1/projects/<int:project_id>/tracking/', include('assignment.tracking_urls')),
```

### **Problem: "Visibility filtering not working"**

**Check:**
```bash
# Verify mixin is applied
grep "SimpleExampleFilterMixin" /doccano/backend/examples/views.py

# Should output:
# from assignment.simple_filtering import SimpleExampleFilterMixin
# class ExampleListAPI(SimpleExampleFilterMixin, ...
```

### **Problem: "Approve buttons don't show"**

**Check:**
1. Open browser console (F12)
2. Look for errors
3. Verify you're on an annotation page (not dataset page)
4. Buttons only show for reviewers/project managers

---

## 📝 **Summary:**

| Step | Action | Status |
|------|--------|--------|
| 1 | Code pushed to GitHub | ✅ Done |
| 2 | Dockerfile updated | ✅ Done |
| 3 | Render auto-deploys | ⏳ In Progress |
| 4 | Wait for "Live" | ⏰ Waiting |
| 5 | Run migration | ⏳ To Do |
| 6 | Test features | ⏳ To Do |

---

## 🎯 **What You Should See:**

### **Before Migration:**
- ❌ Tracking features don't work
- ❌ API returns "table doesn't exist"
- ❌ Approve buttons may error

### **After Migration:**
- ✅ Metrics redirect works on first click
- ✅ Dataset columns show tracking data
- ✅ Annotators see only their examples
- ✅ Example locking prevents conflicts
- ✅ Approve/reject buttons work
- ✅ Auto-advance after review

---

## 🎉 **Ready to Monitor Deployment!**

**Next steps:**
1. Watch Render dashboard for "Live" status
2. Run migration command in Shell
3. Test all features
4. Report any issues

**I'll be here to help with any problems!** 🚀

---

## 📞 **Need Help?**

If something doesn't work:
1. Share the error message
2. Share browser console logs (F12)
3. Share Render deployment logs
4. I'll help debug!

**The system is ready - just needs deployment + migration!** ✅

