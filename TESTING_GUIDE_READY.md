# 🧪 COMPREHENSIVE TESTING GUIDE

**Status:** ✅ Database Fixed - Ready for Testing  
**Date:** January 7, 2026

---

## 🎯 WHAT WAS FIXED

✅ Database migration records cleaned up  
✅ `locked_by` and `locked_at` columns added  
✅ All indexes and constraints in place  
✅ Migration state matches codebase  
✅ Server will start cleanly on next deploy

---

## 🚀 STEP 1: VERIFY DEPLOYMENT

### Check Server Logs (Render Dashboard)
Look for these success messages:

```
✅ Expected logs:
[Monlam Tracking] App initializing...
[Monlam Filter] ✅ Added monlam_tracking.filters.AnnotationVisibilityFilter
[Monlam Tracking] ✅ Visibility filter registered
[Monlam Signals] ✅ Connected tracking for Category
[Monlam Signals] ✅ Connected tracking for Span
[Monlam Signals] ✅ Connected tracking for TextLabel
[Monlam Tracking] ✅ Auto-tracking signals connected
```

### Check Migration Status
If you have access to Render Shell:
```bash
python manage.py showmigrations assignment
```

Expected output:
```
assignment
 [X] 0001_initial
 [X] 0002_completion_tracking
 [X] 0003_example_locking
 [X] 0006_annotation_tracking_simple  ← Should be checked ✅
```

---

## 🧪 STEP 2: TEST DATASET TABLE COLUMNS

### 2.1 Access Dataset Page
1. Login to Doccano
2. Navigate to your project
3. Click "གཞི་གྲངས།" (Dataset) in left menu

### 2.2 Verify Columns Appear
Check for these columns in order:

| Position | Column Name    | What to Check                          |
|----------|----------------|----------------------------------------|
| 1        | ID             | (Original)                             |
| 2        | Text/Data      | (Original)                             |
| 3        | (Original)     | (Original)                             |
| 4        | **Annotated By** | ✅ Should show username or "N/A"       |
| 5        | **Reviewed By**  | ✅ Should show username or "N/A"       |
| 6        | **Status**       | ✅ Should show pending/submitted/etc.  |

### 2.3 Check Data
- ✅ Columns are aligned (no data shifting)
- ✅ Headers match data
- ✅ Status shows correct values: `pending`, `submitted`, `approved`, `rejected`

---

## 🔒 STEP 3: TEST VISIBILITY FILTERING

### Setup: Create Test Users
You need 3 users with different roles:

1. **Annotator A** (role: `annotator`)
2. **Annotator B** (role: `annotator`)
3. **Reviewer** (role: `approver` or `project_manager`)

### Test 3.1: Annotator A Workflow

```
1. Login as Annotator A
2. Go to project dataset
3. Count examples visible: _____ (note this number)

4. Click "Start Annotation" or click on first example
5. Add an annotation (label/text/etc.)
6. Save the annotation

7. Go back to dataset page
8. Count examples visible: _____ (should be 1 less than before)
9. The example you just annotated should NOT be visible ✅
```

**Expected Result:**
- ✅ After annotation, that example disappears from Annotator A's view
- ✅ Status in database is now `submitted`
- ✅ `annotated_by` shows Annotator A's username

### Test 3.2: Annotator B Cannot See Annotator A's Work

```
1. Login as Annotator B
2. Go to project dataset
3. The example that Annotator A just annotated should NOT be visible ✅
4. Annotator B should only see unannotated examples
```

**Expected Result:**
- ✅ Annotator B does NOT see examples annotated by Annotator A
- ✅ Prevents double-editing and confusion

### Test 3.3: Reviewer Can See Everything

```
1. Login as Reviewer
2. Go to project dataset
3. Should see ALL examples, including:
   - ✅ Unannotated (pending)
   - ✅ Annotated by Annotator A (submitted)
   - ✅ Annotated by Annotator B (submitted)
   - ✅ Previously approved examples
   - ✅ Previously rejected examples
```

**Expected Result:**
- ✅ Reviewer has full visibility
- ✅ Can review any example regardless of status

### Test 3.4: Rejection Flow

```
1. As Reviewer, reject the example annotated by Annotator A
   (Use approval buttons if visible, or mark as rejected)

2. Logout, login as Annotator A
3. Go to project dataset
4. The rejected example should NOW be visible to Annotator A ✅
5. Status should show "rejected" in column 6

6. Logout, login as Annotator B
7. The rejected example should NOT be visible to Annotator B ✅
```

**Expected Result:**
- ✅ Rejected examples are visible ONLY to the original annotator
- ✅ Other annotators still can't see them
- ✅ This allows re-work without confusion

---

## 🔐 STEP 4: TEST EXAMPLE LOCKING

### Test 4.1: Basic Locking

```
1. Login as Annotator A
2. Open an example for annotation
3. Check database (or use Django admin):
   - annotation_tracking table
   - Find record for this example
   - locked_by_id should be Annotator A's user ID ✅
   - locked_at should be current timestamp ✅

4. In another browser/incognito window, login as Annotator B
5. Try to open the SAME example
   - Should see "locked" message or cannot edit ✅

6. As Annotator A, close/save the example
7. Check database again:
   - locked_by_id should be NULL ✅
   - locked_at should be NULL ✅

8. As Annotator B, try to open the example again
   - Should now be able to edit ✅
```

**Expected Result:**
- ✅ Only one user can edit an example at a time
- ✅ Lock is released when user saves/closes
- ✅ Prevents simultaneous editing conflicts

### Test 4.2: Lock Timeout (if implemented)

```
1. As Annotator A, open an example
2. Wait for lock timeout period (e.g., 15 minutes)
3. Check database:
   - locked_at timestamp is > 15 minutes ago
   - System should auto-release the lock ✅

4. As Annotator B, try to open the example
   - Should now be able to edit ✅
```

**Note:** Lock timeout may not be implemented yet. If not, that's a future enhancement.

---

## 📊 STEP 5: TEST AUTO-TRACKING

### Test 5.1: Annotation Tracking

```
1. Login as Annotator A
2. Annotate Example #50 (or any example)
3. Save the annotation

4. Check dataset table:
   - Column 4 (Annotated By): "Annotator A" ✅
   - Column 5 (Reviewed By): "N/A" ✅
   - Column 6 (Status): "submitted" ✅

5. Check database directly:
   SELECT * FROM annotation_tracking WHERE example_id = 50;
   
   Expected:
   - project_id: (your project ID)
   - example_id: 50
   - annotated_by_id: (Annotator A's user ID) ✅
   - annotated_at: (timestamp when saved) ✅
   - reviewed_by_id: NULL
   - reviewed_at: NULL
   - status: 'submitted' ✅
   - review_notes: ''
   - locked_by_id: NULL (after saving)
   - locked_at: NULL
```

**Expected Result:**
- ✅ Tracking record created automatically
- ✅ No manual intervention needed
- ✅ Data shows in dataset table

### Test 5.2: Review Tracking

```
1. Login as Reviewer
2. Find Example #50 (the one Annotator A annotated)
3. Approve the annotation
   (If approve buttons exist, click "Approve")

4. Check dataset table:
   - Column 4 (Annotated By): "Annotator A" ✅
   - Column 5 (Reviewed By): "Reviewer" ✅
   - Column 6 (Status): "approved" ✅

5. Check database:
   SELECT * FROM annotation_tracking WHERE example_id = 50;
   
   Expected:
   - annotated_by_id: (Annotator A's user ID) ✅
   - reviewed_by_id: (Reviewer's user ID) ✅
   - reviewed_at: (timestamp when approved) ✅
   - status: 'approved' ✅
```

**Expected Result:**
- ✅ Review is tracked automatically
- ✅ Dataset table updates in real-time
- ✅ Full audit trail maintained

---

## 📈 STEP 6: TEST COMPLETION METRICS

### Test 6.1: Metrics Page Redirect

```
1. Login to Doccano
2. Go to your project
3. Click "གཞི་གྲངས།" (Metrics) in left menu
4. Page should redirect to: /monlam/{project_id}/completion/ ✅
```

**Expected Result:**
- ✅ Old metrics page is replaced
- ✅ New completion matrix shows

### Test 6.2: Completion Matrix Data

```
Check the completion matrix for:

1. Annotator section:
   - ✅ Shows all annotators
   - ✅ Shows count of examples they annotated
   - ✅ Shows % completion

2. Reviewer section:
   - ✅ Shows all reviewers/approvers
   - ✅ Shows count of examples they reviewed
   - ✅ Shows % of examples approved vs rejected

3. Overall stats:
   - ✅ Total examples
   - ✅ Pending count
   - ✅ In Progress count
   - ✅ Submitted count
   - ✅ Approved count
   - ✅ Rejected count
```

**Expected Result:**
- ✅ Data is accurate and up-to-date
- ✅ Reflects current state of annotation_tracking table

---

## 🔧 STEP 7: TEST MONLAM UI PAGES

### Test 7.1: Enhanced Dataset Page

```
1. Navigate to: https://annotate.monlam.ai/monlam/{project_id}/dataset-enhanced/
2. Check if page loads ✅
3. Verify:
   - ✅ Shows all examples with full data
   - ✅ Shows annotated_by, reviewed_by, status columns
   - ✅ "Back to Project" button works
   - ✅ "Annotate" buttons work (if present)
```

### Test 7.2: Completion Dashboard

```
1. Navigate to: https://annotate.monlam.ai/monlam/{project_id}/completion/
2. Check if page loads ✅
3. Verify:
   - ✅ Completion matrix displays
   - ✅ Data is accurate
   - ✅ "Back to Project" button works
```

### Test 7.3: Project Landing Page

```
1. Navigate to: https://annotate.monlam.ai/projects/{project_id}/
2. Check if page loads ✅
3. Verify:
   - ✅ Shows project overview
   - ✅ Quick stats display
   - ✅ Links to dataset, metrics, etc. work
```

---

## ⚠️ TROUBLESHOOTING

### Issue: Columns Don't Appear

**Check:**
1. Open browser console (F12)
2. Look for errors related to `enhanceDatasetTable`
3. Check if API call to `/v1/projects/{id}/examples` succeeds
4. Verify `assignment_status`, `annotated_by`, `reviewed_by` are in API response

**Fix:**
- Clear browser cache
- Hard refresh (Ctrl+Shift+R)
- Check if `examples_serializer_patch.py` is applied

### Issue: Visibility Not Working

**Check:**
1. Server logs for `[Monlam Filter]` messages
2. Verify filter is registered:
   ```
   [Monlam Filter] ✅ Added monlam_tracking.filters.AnnotationVisibilityFilter
   ```
3. Check user's role in project members

**Fix:**
- Ensure `monlam_tracking` app is in `INSTALLED_APPS`
- Verify `AppConfig.ready()` method runs
- Check if `DEFAULT_FILTER_BACKENDS` includes our filter

### Issue: Auto-Tracking Not Working

**Check:**
1. Server logs for `[Monlam Signals]` messages
2. Verify signals are connected:
   ```
   [Monlam Signals] ✅ Connected tracking for Category
   [Monlam Signals] ✅ Connected tracking for Span
   [Monlam Signals] ✅ Connected tracking for TextLabel
   ```
3. Check if annotation save triggers signal

**Fix:**
- Ensure `monlam_tracking/apps.py` imports signals
- Verify `ready()` method runs
- Check if annotation models are correct (Category, Span, TextLabel)

### Issue: Migration Errors

**Check:**
```bash
python manage.py showmigrations assignment
```

**Fix:**
- If `0006_annotation_tracking_simple` is not checked:
  ```bash
  python manage.py migrate assignment --fake-initial
  ```
- If other migration errors, see `DATABASE_FIX_COMPLETE.md`

---

## 📊 RESULTS TRACKING

### Test Results Summary

| Test                        | Status | Notes                        |
|-----------------------------|--------|------------------------------|
| Dataset Table Columns       | ⬜     | (Mark ✅ or ❌ after testing) |
| Annotator A Visibility      | ⬜     |                              |
| Annotator B Visibility      | ⬜     |                              |
| Reviewer Visibility         | ⬜     |                              |
| Rejection Flow              | ⬜     |                              |
| Example Locking             | ⬜     |                              |
| Auto-Tracking (Annotate)    | ⬜     |                              |
| Auto-Tracking (Review)      | ⬜     |                              |
| Metrics Page Redirect       | ⬜     |                              |
| Completion Matrix Data      | ⬜     |                              |
| Enhanced Dataset Page       | ⬜     |                              |
| Completion Dashboard        | ⬜     |                              |
| Project Landing Page        | ⬜     |                              |

---

## 🔒 POST-TESTING: SECURITY

### ⚠️ IMPORTANT: Rotate Database Password

Your database credentials were shared in this conversation. After testing:

1. Go to Render Dashboard
2. Navigate to your PostgreSQL database
3. Click "Info" or "Settings"
4. Find "Reset Password" or "Rotate Password"
5. Update the new password in your Doccano app's environment variables
6. Redeploy the app

**Current password:** `idwVrb3iVBs0edlU2Uh1zaQmjPCVpQQ6`  
**Action Required:** Change this! 🔒

---

## ✅ SIGN-OFF CHECKLIST

Before considering this complete, verify:

- [ ] All migrations applied successfully
- [ ] Server starts without errors
- [ ] Dataset table shows tracking columns
- [ ] Visibility filtering works for annotators
- [ ] Reviewers can see all examples
- [ ] Auto-tracking creates/updates records
- [ ] Example locking prevents conflicts
- [ ] Completion metrics display correctly
- [ ] Monlam UI pages load without errors
- [ ] Database password rotated (security)

---

## 🎉 CONGRATULATIONS!

If all tests pass, you now have:

✅ **Production-grade annotation tracking system**
✅ **Expert visibility filtering** (prevents double-editing)
✅ **Auto-tracking** (no manual data entry)
✅ **Example locking** (prevents conflicts)
✅ **Comprehensive metrics** (completion matrix)
✅ **Clean database** (no migration issues)

**You're ready for production use! 🚀**

---

**Questions or issues? Refer to:**
- `DATABASE_FIX_COMPLETE.md` - Database fix details
- `COMPLETE_IMPLEMENTATION_READY.md` - Full implementation guide
- `APPROVER_WORKFLOW_GUIDE.md` - Approval workflow details
- `MIGRATION_GUIDE.md` - Migration troubleshooting

**Happy annotating! 📝✨**

